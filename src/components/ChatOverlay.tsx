/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect, useRef } from "react";
import { Send, Users, ShieldAlert, X, MessageSquareCode } from "lucide-react";
import { ref, push, onChildAdded, onValue, set, remove, get } from "firebase/database";
import { db } from "../lib/firebase";
import { GameMessage } from "../types";

interface ChatOverlayProps {
  currentUser: string;
  onClose: () => void;
  onViewProfile: (username: string) => void;
}

export default function ChatOverlay({
  currentUser,
  onClose,
  onViewProfile
}: ChatOverlayProps) {
  const [messages, setMessages] = useState<GameMessage[]>([]);
  const [inputText, setInputText] = useState("");
  const [onlineUsers, setOnlineUsers] = useState<string[]>([]);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Scroll to bottom on new messages
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    // 1. Listen for messages
    const messagesRef = ref(db, "messages");
    const unsubscribeMessages = onChildAdded(messagesRef, (snapshot) => {
      const data = snapshot.val();
      if (data) {
        setMessages((prev) => [
          ...prev,
          {
            id: snapshot.key || String(Date.now()),
            user: data.user,
            text: data.text,
            timestamp: data.timestamp,
            worldX: data.worldX,
            worldY: data.worldY,
            type: data.type
          }
        ]);
      }
    });

    // 2. Listen for online users
    const onlineRef = ref(db, "online");
    const unsubscribeOnline = onValue(onlineRef, (snapshot) => {
      if (snapshot.exists()) {
        const users = Object.keys(snapshot.val());
        setOnlineUsers(users);
      } else {
        setOnlineUsers([]);
      }
    });

    return () => {
      // Firebase doesn't explicitly return unsubscribe callbacks but we can clean up
      // through standard off or passing null (handled implicitly when reference is deleted in RTDB SDK)
    };
  }, []);

  const handleSendMessage = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputText.trim()) return;

    const text = inputText.trim();
    const messagesRef = ref(db, "messages");

    // Check for location command keywords
    const isLook = text.startsWith("/look") || text.startsWith("/spojrz");
    const isPing = text.startsWith("/ping") || text.startsWith("/sygnal");

    if (isLook || isPing) {
      const type = isLook ? "look" : "ping";
      const cleanText = text.replace(/^\/(look|spojrz|ping|sygnal)\s*/i, "");
      const finalMsg = cleanText ? `${isLook ? "👀 Spójrz:" : "📍 Sygnał:"} ${cleanText}` : (isLook ? "[👀 Spójrz na moją pozycję!]" : "[📍 Wysłałem sygnał lokalizacji]");

      // Fetch sender's active location from the coordinates database
      get(ref(db, `players/${currentUser}`)).then((snapshot) => {
        let worldX = 1200;
        let worldY = 1200;
        if (snapshot.exists()) {
          const val = snapshot.val();
          worldX = val.worldX !== undefined ? val.worldX : worldX;
          worldY = val.worldY !== undefined ? val.worldY : worldY;
        }

        push(messagesRef, {
          user: currentUser,
          text: finalMsg,
          timestamp: Date.now(),
          worldX,
          worldY,
          type
        }).then(() => {
          setInputText("");
        });
      }).catch((err) => {
        console.error("Failed to fetch coordinates for command:", err);
        push(messagesRef, {
          user: currentUser,
          text: finalMsg,
          timestamp: Date.now(),
          type
        }).then(() => {
          setInputText("");
        });
      });
    } else {
      push(messagesRef, {
        user: currentUser,
        text: text,
        timestamp: Date.now()
      }).then(() => {
        setInputText("");
      });
    }
  };

  return (
    <div className="absolute inset-0 bg-black/80 flex justify-center items-center z-45 p-4 md:p-8 animate-fade-in">
      <div className="w-full max-w-5xl h-[80vh] bg-[#080A0E] border border-white/5 rounded-2xl flex flex-col overflow-hidden shadow-2xl relative">
        {/* Chat header */}
        <div className="bg-[#0A0C10] py-4 px-6 border-b border-white/5 flex justify-between items-center text-slate-300">
          <div className="flex items-center gap-3">
            <MessageSquareCode className="w-5 h-5 text-blue-400" />
            <span className="font-bold tracking-widest text-xs font-mono text-white uppercase">
              # TERMINAL_GLOBAL_COMMUNICATION_BUBBLE
            </span>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5 text-xs text-slate-500 font-mono uppercase">
              <span>ADMIN_ID:</span>
              <span
                onClick={() => onViewProfile(currentUser)}
                className="text-blue-400 font-bold hover:underline cursor-pointer"
              >
                @{currentUser}
              </span>
            </div>

            <button
              onClick={onClose}
              className="bg-white/5 hover:bg-red-500/20 hover:text-red-400 text-slate-400 p-1.5 rounded-lg transition-all cursor-pointer"
              title="Wróć do gry (Esc)"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Chat Body */}
        <div className="flex flex-1 overflow-hidden min-h-0">
          {/* Message log area */}
          <div className="flex-1 flex flex-col bg-[#050608]/50">
            <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4">
              {messages.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center text-slate-500 text-xs py-8 font-mono uppercase tracking-widest">
                  <span>No data packets received. Start typing!</span>
                </div>
              ) : (
                messages.map((msg) => {
                  const isMe = msg.user === currentUser;
                  const isPing = msg.type === "ping";
                  const isLook = msg.type === "look";

                  let bubbleClass = "bg-slate-800/40 border border-white/5 text-slate-300";
                  if (isMe) {
                    bubbleClass = "bg-blue-600/10 border border-blue-500/20 text-blue-200";
                  }
                  if (isPing) {
                    bubbleClass = "bg-[#00ffcc]/10 border border-[#00ffcc]/30 text-[#00ffcc] animate-pulse";
                  } else if (isLook) {
                    bubbleClass = "bg-red-500/10 border border-red-500/30 text-red-300 animate-pulse";
                  }

                  return (
                    <div
                      key={msg.id}
                      className={`flex flex-col max-w-[80%] ${
                        isMe ? "ml-auto items-end" : "mr-auto items-start"
                      }`}
                    >
                      <div className="flex items-center gap-1.5 mb-0.5">
                        <span
                          onClick={() => onViewProfile(msg.user)}
                          className="text-[10px] font-mono text-slate-500 hover:text-blue-400 cursor-pointer"
                        >
                          @{msg.user}
                        </span>
                        {isPing && (
                          <span className="bg-[#00ffcc]/10 border border-[#00ffcc]/30 text-[#00ffcc] text-[7.5px] px-1.5 py-0.5 rounded uppercase tracking-widest font-mono font-bold scale-90">
                            Płaski Sygnał
                          </span>
                        )}
                        {isLook && (
                          <span className="bg-red-500/15 border border-red-500/30 text-red-400 text-[7.5px] px-1.5 py-0.5 rounded uppercase tracking-widest font-mono font-bold scale-90">
                            Wizja
                          </span>
                        )}
                      </div>
                      <div className={`rounded-lg py-2 px-4 shadow text-sm break-all font-mono ${bubbleClass}`}>
                        {msg.text}
                      </div>
                    </div>
                  );
                })
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input area */}
            <form onSubmit={handleSendMessage} className="p-4 border-t border-white/5 bg-[#0A0C10] flex gap-3">
              <input
                type="text"
                placeholder="INPUT DATA PACKET... (Wciśnij Esc lub ` aby wrócić do gry)"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                className="flex-1 bg-[#050608] border border-white/10 focus:border-blue-500 rounded-lg py-2.5 px-4 text-slate-200 text-sm transition-all focus:outline-none placeholder-slate-700 font-mono"
                autoFocus
              />
              <button
                type="submit"
                className="bg-blue-600 hover:bg-blue-500 text-white font-bold px-5 rounded-lg transition-all flex items-center justify-center cursor-pointer text-xs uppercase tracking-wider font-mono"
              >
                <Send className="w-3.5 h-3.5 mr-1" /> Wyślij
              </button>
            </form>
          </div>

          {/* Online status sidebar */}
          <div className="w-64 border-l border-white/5 bg-[#080A0E] hidden md:flex flex-col">
            <div className="p-4 border-b border-white/5 flex justify-between items-center bg-[#0A0C10]">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-widest font-mono">
                <Users className="w-3.5 h-3.5 text-blue-400" />
                <span>Użytkownicy</span>
              </div>
              <span className="bg-blue-500/10 border border-blue-500/20 text-blue-400 text-[10px] font-mono px-2 py-0.5 rounded">
                {onlineUsers.length}
              </span>
            </div>

            <div className="flex-1 overflow-y-auto p-3 space-y-1.5 font-mono">
              {onlineUsers.map((user) => (
                <div
                  key={user}
                  onClick={() => onViewProfile(user)}
                  className="flex items-center justify-between p-2 rounded bg-[#050608]/40 hover:bg-blue-500/5 hover:border-blue-500/15 border border-transparent transition-all cursor-pointer group"
                >
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full shadow-[0_0_6px_#10b981]" />
                    <span className="text-xs text-slate-300 group-hover:text-white">
                      {user} {user === currentUser && "(Ty)"}
                    </span>
                  </div>
                  <span className="text-[9px] text-slate-600 group-hover:text-blue-400 uppercase tracking-wider">
                    PROFIL
                  </span>
                </div>
              ))}
            </div>

            <div className="p-4 border-t border-white/5 bg-[#050608]/60 space-y-2 text-[10px] text-slate-500 font-mono select-none">
              <div className="text-white font-bold tracking-wider text-[11px] mb-1">KOMENDY LOKACJI:</div>
              <div><strong className="text-teal-400">/ping [tekst]</strong>: Wyślij sygnał</div>
              <div><strong className="text-rose-400">/look [tekst]</strong>: Zasygnalizuj spojrzenie</div>
              <div className="text-slate-600 mt-2 text-[9px] leading-relaxed">Sygnały pojawią się w czasie rzeczywistym u wszystkich zalogowanych graczy bezpośrednio na arenie i fali minimapy!</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
