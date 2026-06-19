import pygame
import sys
import math
import random
import time

# Initialize pygame
pygame.init()
pygame.font.init()

# Screen Configuration
SCREEN_WIDTH = 1100
SCREEN_HEIGHT = 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Survival RPG - Python Edition")
clock = pygame.time.Clock()

# Fonts
font_title = pygame.font.SysFont("Arial", 42, bold=True)
font_subtitle = pygame.font.SysFont("Arial", 22, bold=True)
font_ui = pygame.font.SysFont("Consolas", 14, bold=True)
font_log = pygame.font.SysFont("Consolas", 12)
font_large_ui = pygame.font.SysFont("Arial", 24, bold=True)

# Colors
COLOR_BG = (10, 14, 23)
COLOR_WHITE = (255, 255, 255)
COLOR_SLATE = (100, 116, 139)
COLOR_RED = (239, 68, 68)
COLOR_ORANGE = (249, 115, 22)
COLOR_YELLOW = (234, 179, 8)
COLOR_GREEN = (34, 197, 94)
COLOR_TEAL = (20, 184, 166)
COLOR_BLUE = (59, 130, 246)
COLOR_PURPLE = (168, 85, 247)
COLOR_PINK = (236, 72, 153)

# Biome definitions matching TypeScript
BIOME_CONFIGS = {
    'WATER': {'col1': (41, 128, 185), 'col2': (31, 97, 141), 'name': 'Woda'},
    'SAND': {'col1': (241, 196, 15), 'col2': (212, 172, 13), 'name': 'Piasek'},
    'GRASS': {'col1': (76, 175, 80), 'col2': (69, 160, 73), 'name': 'Łąka'},
    'FOREST': {'col1': (30, 132, 73), 'col2': (25, 111, 61), 'name': 'Las'},
    'RAINFOREST': {'col1': (17, 122, 101), 'col2': (14, 98, 81), 'name': 'Dżungla'},
    'MOUNTAIN': {'col1': (127, 140, 141), 'col2': (149, 165, 166), 'name': 'Góry'},
    'LAVA': {'col1': (207, 16, 16), 'col2': (255, 69, 0), 'name': 'Lawa'},
    'ICE': {'col1': (189, 236, 255), 'col2': (93, 173, 226), 'name': 'Lodowiec'},
    'SWAMP': {'col1': (60, 77, 61), 'col2': (28, 40, 29), 'name': 'Bagna'}
}

# Math noise approximation using nested sines & cosines
def get_biome_at(x, y):
    val = math.sin(x * 0.04) * math.cos(y * 0.04) + \
          0.5 * math.sin(x * 0.1) * math.sin(y * 0.08) + \
          0.25 * math.cos(x * 0.22 + y * 0.12)
    
    # Map to biome types
    if val < -0.7:
        if val < -1.1:
            return 'LAVA'
        return 'WATER'
    if val < -0.4:
        return 'SAND'
    if val < -0.12:
        return 'SWAMP'
    if val < 0.4:
        return 'GRASS'
    if val < 0.8:
        return 'FOREST'
    if val < 1.15:
        return 'RAINFOREST'
    if val < 1.4:
        return 'MOUNTAIN'
    return 'ICE'

TILE_SIZE = 64
MAP_TILES_WIDTH = 120
MAP_TILES_HEIGHT = 120

class Particle:
    def __init__(self, x, y, dx, dy, color, size, life):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.color = color
        self.size = size
        self.max_life = life
        self.life = life

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.life -= 1
        return self.life > 0

    def draw(self, surface, cam_x, cam_y):
        alpha = int((self.life / self.max_life) * 255)
        # Handle simple transparency by scaling color brightness
        ratio = self.life / self.max_life
        col = (int(self.color[0]*ratio), int(self.color[1]*ratio), int(self.color[2]*ratio))
        pygame.draw.circle(surface, col, (int(self.x - cam_x), int(self.y - cam_y)), int(self.size))

class Projectile:
    def __init__(self, x, y, angle, speed, damage, is_player, color, radius=6):
        self.x = x
        self.y = y
        self.dx = math.cos(angle) * speed
        self.dy = math.sin(angle) * speed
        self.damage = damage
        self.is_player = is_player
        self.color = color
        self.radius = radius
        self.life = 60 # frames

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.life -= 1
        return self.life > 0

    def draw(self, surface, cam_x, cam_y):
        pygame.draw.circle(surface, self.color, (int(self.x - cam_x), int(self.y - cam_y)), self.radius)
        # Draw a little halo
        halo_surface = pygame.Surface((self.radius*4, self.radius*4), pygame.SRCALPHA)
        pygame.draw.circle(halo_surface, (self.color[0], self.color[1], self.color[2], 50), (self.radius*2, self.radius*2), self.radius*2)
        surface.blit(halo_surface, (int(self.x - cam_x - self.radius*2), int(self.y - cam_y - self.radius*2)))

class Enemy:
    def __init__(self, id_str, x, y, enemy_type):
        self.id = id_str
        self.x = x
        self.y = y
        self.type = enemy_type  # 'monster', 'boss', 'animal'
        self.state = "passive" if enemy_type == 'animal' else "aggressive"
        self.hp = 250 if enemy_type == 'boss' else (35 if enemy_type == 'monster' else 15)
        self.max_hp = self.hp
        self.speed = 1.8 if enemy_type == 'boss' else (2.4 if enemy_type == 'monster' else 1.5)
        self.alert_progress = 0
        self.last_attack_time = 0
        self.name = "Smok Boss" if enemy_type == 'boss' else ("Potwór" if enemy_type == 'monster' else "Płochliwe Zwierzę")
        self.size = 28 if enemy_type == 'boss' else (16 if enemy_type == 'monster' else 12)
        self.color = COLOR_PURPLE if enemy_type == 'boss' else (COLOR_RED if enemy_type == 'monster' else COLOR_GREEN)
        self.target_x = x
        self.target_y = y

    def update(self, player_x, player_y, water_slow):
        dist = math.hypot(player_x - self.x, player_y - self.y)
        current_speed = self.speed * water_slow

        if self.type == 'animal':
            # Run away from player if close
            if dist < 180:
                self.state = "scared"
                angle = math.atan2(self.y - player_y, self.x - player_x)
                self.x += math.cos(angle) * (current_speed * 1.5)
                self.y += math.sin(angle) * (current_speed * 1.5)
            else:
                self.state = "passive"
                # Wander randomly
                if random.random() < 0.02:
                    angle = random.uniform(0, math.PI * 2)
                    self.target_x = self.x + math.cos(angle) * 80
                    self.target_y = self.y + math.sin(angle) * 80
                
                # Smooth move to target
                tx_dist = math.hypot(self.target_x - self.x, self.target_y - self.y)
                if tx_dist > 5:
                    self.x += ((self.target_x - self.x) / tx_dist) * current_speed
                    self.y += ((self.target_y - self.y) / tx_dist) * current_speed
        else:
            # Aggressive logic
            if dist < 450:
                # Pursuit player
                angle = math.atan2(player_y - self.y, player_x - self.x)
                self.x += math.cos(angle) * current_speed
                self.y += math.sin(angle) * current_speed
                self.state = "aggressive"
                self.alert_progress = min(100, self.alert_progress + 1)
            else:
                self.state = "idle"
                self.alert_progress = max(0, self.alert_progress - 1)

    def draw(self, surface, cam_x, cam_y):
        rx, ry = int(self.x - cam_x), int(self.y - cam_y)
        # Shadow
        pygame.draw.ellipse(surface, (0, 0, 0, 80), (rx - self.size, ry + self.size - 6, self.size*2, 12))
        # Body
        pygame.draw.circle(surface, self.color, (rx, ry), self.size)
        # Core highlight
        pygame.draw.circle(surface, COLOR_WHITE, (rx - int(self.size*0.3), ry - int(self.size*0.3)), int(self.size*0.2))
        
        # Draw HP bar
        bar_width = self.size * 2
        bar_height = 4
        pygame.draw.rect(surface, (30, 30, 30), (rx - self.size, ry - self.size - 10, bar_width, bar_height))
        hp_ratio = max(0.0, min(1.0, self.hp / self.max_hp))
        pygame.draw.rect(surface, COLOR_RED, (rx - self.size, ry - self.size - 10, int(bar_width * hp_ratio), bar_height))


class Loot:
    def __init__(self, x, y, loot_type):
        self.x = x
        self.y = y
        self.type = loot_type # "gold", "potion", "scroll"
        self.pulse = 0
        self.color = COLOR_YELLOW if loot_type == "gold" else (COLOR_RED if loot_type == "potion" else COLOR_BLUE)

    def draw(self, surface, cam_x, cam_y):
        self.pulse = (self.pulse + 0.1) % (math.PI * 2)
        offset = math.sin(self.pulse) * 3
        rx, ry = int(self.x - cam_x), int(self.y - cam_y + offset)
        
        # Shadow
        pygame.draw.circle(surface, (0, 0, 0, 60), (int(self.x - cam_x), int(self.y - cam_y + 8)), 6)
        
        # Core icon
        if self.type == "gold":
            pygame.draw.circle(surface, COLOR_YELLOW, (rx, ry), 7)
            pygame.draw.circle(surface, (255, 230, 100), (rx, ry), 5)
        elif self.type == "potion":
            pygame.draw.rect(surface, COLOR_RED, (rx - 4, ry - 2, 8, 8), border_radius=2)
            pygame.draw.rect(surface, COLOR_WHITE, (rx - 2, ry - 6, 4, 4))
        else:
            pygame.draw.polygon(surface, COLOR_BLUE, [(rx, ry - 6), (rx - 5, ry + 4), (rx + 5, ry + 4)])


class GameState:
    def __init__(self):
        # Character select or main game loop
        self.phase = "START_MENU"
        
        # Player attributes
        self.player_name = "Kontrium"
        self.char_class = "Mage"  # "Mage", "Warrior", "Rogue", "Priest"
        
        self.world_x = MAP_TILES_WIDTH * TILE_SIZE / 2
        self.world_y = MAP_TILES_HEIGHT * TILE_SIZE / 2
        self.vx = 0
        self.vy = 0
        
        # Character core stats
        self.level = 1
        self.xp = 0
        self.xp_needed = 100
        self.score = 0
        
        self.hp = 100
        self.max_hp = 100
        self.mana = 100
        self.max_mana = 100
        self.stamina = 120
        self.max_stamina = 120
        
        # Dynamic Protection
        self.protection_until = time.time() + 15.0
        
        # Allocated stat points
        self.stat_points = 0
        self.strength = 10
        self.energy = 10
        self.life = 10
        self.stamina_stat = 10
        self.speed_stat = 10
        
        # Cooldowns
        self.spell1_cooldown = 0
        self.spell2_cooldown = 0
        self.spell3_cooldown = 0
        self.dash_cooldown = 0
        
        # List of elements
        self.projectiles = []
        self.enemies = []
        self.loots = []
        self.particles = []
        self.event_log = []
        
        # Control states
        self.selected_spell = 1
        self.is_running = False
        
        # Add initial log
        self.log_event("Witaj w świecie RPG! Wybierz klasę i rozpocznij przygodę.", "join")

    def log_event(self, text, event_type="system"):
        self.event_log.append({
            'text': text,
            'type': event_type,
            'time': time.strftime("%H:%M:%S")
        })
        if len(self.event_log) > 25:
            self.event_log.pop(0)

    def level_up(self):
        self.level += 1
        self.xp -= self.xp_needed
        self.xp_needed = int(self.xp_needed * 1.55)
        self.stat_points += 4
        
        # Recalc max capacities
        self.max_hp = int(self.max_hp * 1.05)
        self.hp = self.max_hp
        self.max_mana = int(self.max_mana * 1.05)
        self.mana = self.max_mana
        self.max_stamina = int(self.max_stamina * 1.05)
        self.stamina = self.max_stamina
        
        self.log_event(f"⭐ AWANS! Osiągnięto poziom {self.level}!", "level")
        
        # Spawn some fancy level-up particles
        for _ in range(30):
            self.particles.append(Particle(
                self.world_x, self.world_y,
                random.uniform(-4, 4), random.uniform(-4, 4),
                COLOR_PINK, random.uniform(3, 8), random.randint(20, 50)
            ))

    def reset_player(self):
        self.world_x = MAP_TILES_WIDTH * TILE_SIZE / 2
        self.world_y = MAP_TILES_HEIGHT * TILE_SIZE / 2
        self.hp = self.max_hp
        self.mana = self.max_mana
        self.stamina = self.max_stamina
        self.vx = 0
        self.vy = 0
        self.protection_until = time.time() + 15.0
        self.log_event("☠️ Odrodziłeś się w bezpiecznym punkcie startowym!", "death")

    def cast_spell(self, mouse_world_x, mouse_world_y):
        angle = math.atan2(mouse_world_y - self.world_y, mouse_world_x - self.world_x)
        
        # Spell 1: Fireball (Lmb)
        if self.selected_spell == 1:
            cost = 12
            if self.mana >= cost:
                self.mana -= cost
                dmg = 15 + self.energy * 0.8
                self.projectiles.append(Projectile(
                    self.world_x, self.world_y, angle, 9.0, dmg, True, COLOR_ORANGE, radius=7
                ))
                self.log_event(f"🔥 Rzucono Kule Ognia (-12 Mana)", "spell")
                # Sparkles
                for _ in range(8):
                    self.particles.append(Particle(
                        self.world_x, self.world_y, math.cos(angle)*4 + random.uniform(-2, 2), math.sin(angle)*4 + random.uniform(-2, 2),
                        COLOR_ORANGE, random.uniform(2, 4), 15
                    ))
            else:
                self.log_event("⚠️ Brak Many!", "system")
                
        # Spell 2: Frost Nova
        elif self.selected_spell == 2:
            cost = 25
            if self.mana >= cost and self.spell2_cooldown <= 0:
                self.mana -= cost
                self.spell2_cooldown = 180 # 3 seconds at 60 fps
                
                # Radiating circle of ice shards
                for i in range(12):
                    sub_angle = angle + (i * (math.PI * 2 / 12))
                    self.projectiles.append(Projectile(
                        self.world_x, self.world_y, sub_angle, 6.0, 10 + self.energy*0.4, True, COLOR_BLUE, radius=5
                    ))
                
                self.log_event("❄️ Frost Nova zamroziła otoczenie (-25 Mana)", "spell")
                for _ in range(25):
                    self.particles.append(Particle(
                        self.world_x, self.world_y, random.uniform(-5, 5), random.uniform(-5, 5),
                        COLOR_BLUE, random.uniform(3, 6), 30
                    ))
            elif self.spell2_cooldown > 0:
                self.log_event("⏳ Zaklęcie się odnawia!", "system")
            else:
                self.log_event("⚠️ Brak Many!", "system")

        # Spell 3: Solar Wrath (Heal/Buff or Area Burn)
        elif self.selected_spell == 3:
            cost = 40
            if self.mana >= cost and self.spell3_cooldown <= 0:
                self.mana -= cost
                self.spell3_cooldown = 420 # 7 seconds
                
                # Heal player
                heal_amount = 30 + self.energy * 1.5
                self.hp = min(self.max_hp, self.hp + heal_amount)
                self.log_event(f"☀️ Słoneczny Gniew: Uleczono +{int(heal_amount)} HP! (-40 Mana)", "spell")
                
                # Create massive bright expanding circle
                for _ in range(35):
                    self.particles.append(Particle(
                        self.world_x, self.world_y, random.uniform(-7, 7), random.uniform(-7, 7),
                        COLOR_YELLOW, random.uniform(4, 9), 40
                    ))
            elif self.spell3_cooldown > 0:
                self.log_event("⏳ Zaklęcie się odnawia!", "system")
            else:
                self.log_event("⚠️ Brak Many!", "system")


# Game initialization
state = GameState()

# Main Game Loop
while True:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            
        if state.phase == "START_MENU":
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                # Class selector buttons
                # Mage (150, 420)
                if 150 <= mx <= 280 and 420 <= my <= 470:
                    state.char_class = "Mage"
                # Warrior (290, 420)
                elif 290 <= mx <= 420 and 420 <= my <= 470:
                    state.char_class = "Warrior"
                # Rogue (430, 420)
                elif 430 <= mx <= 560 and 420 <= my <= 470:
                    state.char_class = "Rogue"
                # Priest (570, 420)
                elif 570 <= mx <= 700 and 420 <= my <= 470:
                    state.char_class = "Priest"
                
                # Start button
                if 350 <= mx <= 700 and 580 <= my <= 640:
                    state.phase = "PLAYING"
                    state.is_running = True
                    # Set up class multipliers
                    if state.char_class == "Warrior":
                        state.max_hp = 140
                        state.hp = 140
                        state.max_mana = 40
                        state.mana = 40
                        state.strength = 18
                        state.energy = 5
                    elif state.char_class == "Rogue":
                        state.max_stamina = 180
                        state.stamina = 180
                        state.speed_stat = 16
                    elif state.char_class == "Priest":
                        state.max_mana = 150
                        state.mana = 150
                        state.energy = 15
                    
                    state.log_event(f"⚔️ Opublikowano Twoją postać: {state.char_class}! Powodzenia.", "kill")
                    
        elif state.phase == "PLAYING":
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                
                # UI Sidebar click checking for Attribute assignment
                is_sidebar_click = False
                if mx > SCREEN_WIDTH - 250:
                    # Sidebar bounds
                    # Allocated buttons: '+' at specific rects
                    # Strength +: y=420
                    # Energy +: y=455
                    # Life +: y=490
                    # Stamina +: y=525
                    # Speed +: y=560
                    if state.stat_points > 0:
                        is_sidebar_click = True
                        if SCREEN_WIDTH - 40 <= mx <= SCREEN_WIDTH - 15:
                            if 418 <= my <= 438:
                                state.strength += 1
                                state.stat_points -= 1
                                state.log_event("💪 Dodano punkt do Siły", "system")
                            elif 453 <= my <= 473:
                                state.energy += 1
                                state.stat_points -= 1
                                state.log_event("🔮 Dodano punkt do Energii", "system")
                            elif 488 <= my <= 508:
                                state.life += 1
                                state.max_hp += 8
                                state.hp += 8
                                state.stat_points -= 1
                                state.log_event("❤️ Dodano punkt do Żywotności", "system")
                            elif 523 <= my <= 543:
                                state.stamina_stat += 1
                                state.max_stamina += 10
                                state.stamina += 10
                                state.stat_points -= 1
                                state.log_event("⚡ Dodano punkt do Wytrzymałości", "system")
                            elif 558 <= my <= 578:
                                state.speed_stat += 1
                                state.stat_points -= 1
                                state.log_event("👟 Dodano punkt do Zręczności", "system")
                
                if not is_sidebar_click:
                    # Casting currently selected spell
                    # Work out world mouse
                    cam_x = state.world_x - (SCREEN_WIDTH - 250) / 2
                    cam_y = state.world_y - SCREEN_HEIGHT / 2
                    world_mouse_x = mx + cam_x
                    world_mouse_y = my + cam_y
                    state.cast_spell(world_mouse_x, world_mouse_y)
                    
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    state.selected_spell = 1
                elif event.key == pygame.K_2:
                    state.selected_spell = 2
                elif event.key == pygame.K_3:
                    state.selected_spell = 3
                elif event.key == pygame.K_SPACE:
                    # Dash capability (needs Stamina)
                    cost = 25
                    if state.stamina >= cost and state.dash_cooldown <= 0:
                        state.stamina -= cost
                        state.dash_cooldown = 40 # frames
                        # Work out movement direction keys
                        keys = pygame.key.get_pressed()
                        dx, dy = 0, 0
                        if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx = -1
                        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx = 1
                        if keys[pygame.K_w] or keys[pygame.K_UP]: dy = -1
                        if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy = 1
                        
                        if dx == 0 and dy == 0:
                            dx = 1 # default facing
                        
                        mag = math.hypot(dx, dy)
                        dx, dy = dx/mag, dy/mag
                        
                        state.vx += dx * 16.0
                        state.vy += dy * 16.0
                        state.log_event("💨 Unik (Dash)! (-25 Stamina)", "spell")
                        for _ in range(12):
                            state.particles.append(Particle(
                                state.world_x, state.world_y, -dx*4 + random.uniform(-2,2), -dy*4 + random.uniform(-2,2),
                                COLOR_WHITE, random.uniform(2, 5), 12
                            ))

    # --- UPDATES (only in PLAYING state) ---
    if state.phase == "PLAYING" and state.is_running:
        # Cooldown ticks
        if state.spell2_cooldown > 0: state.spell2_cooldown -= 1
        if state.spell3_cooldown > 0: state.spell3_cooldown -= 1
        if state.dash_cooldown > 0: state.dash_cooldown -= 1
        
        # Identify tile beneath player
        tile_col_x = int(state.world_x / TILE_SIZE)
        tile_col_y = int(state.world_y / TILE_SIZE)
        current_biome = get_biome_at(tile_col_x, tile_col_y)
        
        # Apply biome rules mimicking TS edits
        speed_multiplier = 1.0
        friction_modifier = 1.0
        
        if current_biome == 'WATER':
            speed_multiplier = 0.52
        elif current_biome == 'LAVA':
            speed_multiplier = 0.38
            # Lava damage check (burns occasional 1 dmg)
            protected = state.protection_until > time.time()
            if not protected and random.random() < 0.015:
                state.hp = max(0, state.hp - 1)
                state.log_event("🔥 Oparzenie głębi lawowej! (-1 HP)", "death")
                # Spark particles
                for _ in range(3):
                    state.particles.append(Particle(
                        state.world_x, state.world_y, random.uniform(-2, 2), random.uniform(-2, 0),
                        COLOR_ORANGE, random.uniform(1.5, 3), 10
                    ))
        elif current_biome == 'ICE':
            speed_multiplier = 1.35
            friction_modifier = 1.12
        elif current_biome == 'SWAMP':
            speed_multiplier = 0.44

        # Keyboard movement
        keys = pygame.key.get_pressed()
        move_x = 0
        move_y = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: move_x = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: move_x = 1
        if keys[pygame.K_w] or keys[pygame.K_UP]: move_y = -1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: move_y = 1
        
        # Normalize movement vector
        if move_x != 0 or move_y != 0:
            length = math.hypot(move_x, move_y)
            move_x /= length
            move_y /= length
            
            # Stamina Sprint modifier (Shift key)
            is_sprinting = False
            base_accel = 0.7 + (state.speed_stat * 0.02)
            if keys[pygame.K_LSHIFT] and state.stamina > 4:
                is_sprinting = True
                base_accel *= 1.6
                state.stamina = max(0, state.stamina - 0.4)
            else:
                state.stamina = min(state.max_stamina, state.stamina + 0.15)
                
            state.vx += move_x * base_accel
            state.vy += move_y * base_accel
        else:
            state.stamina = min(state.max_stamina, state.stamina + 0.25)
            
        # Apply friction
        friction = 0.88 * friction_modifier
        state.vx *= friction
        state.vy *= friction
        
        # Max speed limiters
        max_speed = (4.5 if keys[pygame.K_LSHIFT] and state.stamina > 0 else 3.0) + (state.speed_stat * 0.08)
        max_speed *= speed_multiplier
        
        speed = math.hypot(state.vx, state.vy)
        if speed > max_speed:
            state.vx = (state.vx / speed) * max_speed
            state.vy = (state.vy / speed) * max_speed
            
        # Update coordinate position
        state.world_x += state.vx
        state.world_y += state.vy
        
        # Map boundaries clamping
        state.world_x = max(TILE_SIZE, min(MAP_TILES_WIDTH * TILE_SIZE - TILE_SIZE, state.world_x))
        state.world_y = max(TILE_SIZE, min(MAP_TILES_HEIGHT * TILE_SIZE - TILE_SIZE, state.world_y))

        # Mana passive recovery
        state.mana = min(state.max_mana, state.mana + 0.08 + (state.energy * 0.005))

        # Update Projectiles
        active_projectiles = []
        for p in state.projectiles:
            keep = p.update()
            if keep:
                active_projectiles.append(p)
        state.projectiles = active_projectiles

        # Update Particles
        active_particles = []
        for part in state.particles:
            keep = part.update()
            if keep:
                active_particles.append(part)
        state.particles = active_particles

        # Enemy spawning
        max_enemies = 15
        if len([e for e in state.enemies if e.type == 'monster']) < max_enemies and random.random() < 0.015:
            # Spawn random monster offset from player
            angle = random.uniform(0, math.PI * 2)
            dist = random.uniform(350, 600)
            sx = state.world_x + math.cos(angle) * dist
            sy = state.world_y + math.sin(angle) * dist
            state.enemies.append(Enemy(f"enemy_{int(time.time()*1000)}", sx, sy, 'monster'))
            
        # Boss spawning
        if len([e for e in state.enemies if e.type == 'boss']) < 1 and random.random() < 0.0015:
            angle = random.uniform(0, math.PI * 2)
            dist = random.uniform(400, 650)
            bx = state.world_x + math.cos(angle) * dist
            by = state.world_y + math.sin(angle) * dist
            state.enemies.append(Enemy(f"boss_{int(time.time()*1000)}", bx, by, 'boss'))
            state.log_event("⚠️ POTĘŻNY SMOK BOSS pojawił się w okolicy!", "spawn")

        # Animal spawning
        if len([e for e in state.enemies if e.type == 'animal']) < 8 and random.random() < 0.01:
            angle = random.uniform(0, math.PI * 2)
            dist = random.uniform(400, 650)
            ax = state.world_x + math.cos(angle) * dist
            ay = state.world_y + math.sin(angle) * dist
            state.enemies.append(Enemy(f"animal_{int(time.time()*1000)}", ax, ay, 'animal'))

        # Update Enemies
        for e in state.enemies:
            # Check water slowing on enemies
            etile_col_x = int(e.x / TILE_SIZE)
            etile_col_y = int(e.y / TILE_SIZE)
            ebp = get_biome_at(etile_col_x, etile_col_y)
            water_slow = 0.55 if ebp == 'WATER' or ebp == 'SWAMP' else 1.0
            
            e.update(state.world_x, state.world_y, water_slow)
            
            # Enemy physical contact damage logic
            if e.type != 'animal':
                dist = math.hypot(e.x - state.world_x, e.y - state.world_y)
                if dist < e.size + 16:
                    now = time.time()
                    if now - e.last_attack_time > 1.2:
                        e.last_attack_time = now
                        protected = state.protection_until > time.time()
                        if not protected:
                            dmg = 12 if e.type == 'boss' else 6
                            state.hp = max(0, state.hp - dmg)
                            state.log_event(f"💥 Otrzymano {dmg} obrażeń od: {e.name}", "death")
                            if state.hp <= 0:
                                state.reset_player()
                        else:
                            state.log_event("🛡️ Ochrona chroni Cię przed atakiem!", "system")

        # Projectile-Enemy Collision
        for p in state.projectiles:
            if p.is_player:
                for e in state.enemies:
                    dist = math.hypot(p.x - e.x, p.y - e.y)
                    if dist < e.size + p.radius:
                        # Hit!
                        e.hp -= p.damage
                        p.life = 0 # kill projectile
                        
                        # Pain particles
                        for _ in range(5):
                            state.particles.append(Particle(
                                e.x, e.y, random.uniform(-3, 3), random.uniform(-3, 3),
                                COLOR_RED, random.uniform(2, 4), 12
                            ))
                            
                        if e.hp <= 0:
                            # Monster Slain!
                            state.score += 50 if e.type == 'boss' else 15
                            state.xp += 40 if e.type == 'boss' else 18
                            state.log_event(f"⚔️ Pokonano {e.name}! (+{50 if e.type=='boss' else 15} Wynik/Punktów)", "kill")
                            
                            # Loot chance
                            if random.random() < 0.65:
                                ltype = "gold"
                                if random.random() < 0.25:
                                    ltype = "potion"
                                elif random.random() < 0.15:
                                    ltype = "scroll"
                                state.loots.append(Loot(e.x, e.y, ltype))
                                
                            state.enemies.remove(e)
                            
                            # Check Level up
                            if state.xp >= state.xp_needed:
                                state.level_up()
                            break

        # Loot pickup calculation
        active_loots = []
        for l in state.loots:
            dist = math.hypot(l.x - state.world_x, l.y - state.world_y)
            if dist < 32:
                # Pickup
                if l.type == "gold":
                    state.score += 25
                    state.log_event("🪙 Podniesiono Złoto! (+25 Wynik)", "kill")
                    # sparkles
                    for _ in range(6):
                        state.particles.append(Particle(
                            l.x, l.y, random.uniform(-2, 2), random.uniform(-2, 2),
                            COLOR_YELLOW, random.uniform(2, 4), 15
                        ))
                elif l.type == "potion":
                    heal = int(state.max_hp * 0.35)
                    state.hp = min(state.max_hp, state.hp + heal)
                    state.log_event(f"🧪 Wypito Miksturę Życia! (+{heal} HP)", "system")
                    for _ in range(6):
                        state.particles.append(Particle(
                            l.x, l.y, random.uniform(-2, 2), random.uniform(-2, 2),
                            COLOR_RED, random.uniform(2, 4), 15
                        ))
                elif l.type == "scroll":
                    mana_res = int(state.max_mana * 0.4)
                    state.mana = min(state.max_mana, state.mana + mana_res)
                    state.log_event(f"📜 Przeczytano Zwój Many! (+{mana_res} Mana)", "system")
                    for _ in range(6):
                        state.particles.append(Particle(
                            l.x, l.y, random.uniform(-2, 2), random.uniform(-2, 2),
                            COLOR_BLUE, random.uniform(2, 4), 15
                        ))
            else:
                active_loots.append(l)
        state.loots = active_loots


    # --- RENDER/DRAW ---
    screen.fill(COLOR_BG)
    
    if state.phase == "START_MENU":
        # Draw dynamic procedural background grid of biomes
        menu_pulse = (pygame.time.get_ticks() / 120)
        for tx in range(0, SCREEN_WIDTH, TILE_SIZE):
            for ty in range(0, SCREEN_HEIGHT, TILE_SIZE):
                wx = tx / TILE_SIZE + menu_pulse*0.05
                wy = ty / TILE_SIZE
                b = get_biome_at(wx, wy)
                pygame.draw.rect(screen, BIOME_CONFIGS[b]['col1'], (tx, ty, TILE_SIZE, TILE_SIZE))
                
        # Draw modern glass overlay panel
        overlay = pygame.Surface((750, 560), pygame.SRCALPHA)
        overlay.fill((8, 10, 16, 238))
        screen.blit(overlay, (175, 120))
        pygame.draw.rect(screen, (255, 255, 255, 15), (175, 120, 750, 560), width=1, border_radius=12)
        
        # Menu Header
        title_surf = font_title.render("SURVIVAL RPG - PYTHON", True, COLOR_WHITE)
        subtitle_surf = font_subtitle.render("Wybierz klasę bohatera i wejdź do rozgrywki", True, COLOR_SLATE)
        screen.blit(title_surf, (SCREEN_WIDTH/2 - title_surf.get_width()/2, 160))
        screen.blit(subtitle_surf, (SCREEN_WIDTH/2 - subtitle_surf.get_width()/2, 215))
        
        # Display selected attributes per class
        mage_desc = ["Klasa: Czarodziej", "Duży bonus many", "Duża energia czarów", "Niewielkie zdrowie"]
        warrior_desc = ["Klasa: Wojownik", "Bonus życia (+140 max)", "Brak wielu spelli", "Duża siła fizyczna"]
        rogue_desc = ["Klasa: Łotr", "Ponadprzeciętna stamina", "Szybkość i zręczność", "Uniki do dasha"]
        priest_desc = ["Klasa: Kapłan", "Bardzo wysoka mana", "Skuteczne leczenie słoneczne", "Zbalansowany styl"]
        
        # Render Choice Cards
        classes = ["Mage", "Warrior", "Rogue", "Priest"]
        coords = [150, 290, 430, 570]
        descs = [mage_desc, warrior_desc, rogue_desc, priest_desc]
        colors = [COLOR_BLUE, COLOR_RED, COLOR_YELLOW, COLOR_TEAL]
        
        for k, name in enumerate(classes):
            x = coords[k]
            is_hover = state.char_class == name
            border_col = colors[k] if is_hover else (60, 60, 80)
            card_col = (15, 20, 32, 230) if is_hover else (12, 15, 22, 170)
            
            card_surf = pygame.Surface((130, 190), pygame.SRCALPHA)
            card_surf.fill(card_col)
            screen.blit(card_surf, (x, 280))
            pygame.draw.rect(screen, border_col, (x, 280, 130, 190), width=2 if is_hover else 1, border_radius=4)
            
            lbl = font_subtitle.render(name, True, COLOR_WHITE if is_hover else COLOR_SLATE)
            screen.blit(lbl, (x + 15, 295))
            
            # draw specific colored indicator
            pygame.draw.circle(screen, colors[k], (x + 65, 335), 10)
            
            y_offset = 360
            for desc_line in descs[k][1:]:
                desc_surf = font_ui.render(desc_line, True, (160, 170, 190) if is_hover else (100, 110, 120))
                screen.blit(desc_surf, (x + 8, y_offset))
                y_offset += 16
                
        # Launch build button
        btn_col = COLOR_GREEN if (pygame.time.get_ticks() // 500) % 2 == 0 else (46, 117, 89)
        pygame.draw.rect(screen, btn_col, (350, 580, 400, 60), border_radius=8)
        btn_text = font_subtitle.render("WEJDŹ DO ŚWIATA GRY (GRAJ)", True, COLOR_WHITE)
        screen.blit(btn_text, (SCREEN_WIDTH/2 - btn_text.get_width()/2, 595))
        
    elif state.phase == "PLAYING":
        # Render World Map viewport
        # Calculate camera following player smoothly
        cam_x = state.world_x - (SCREEN_WIDTH - 250) / 2
        cam_y = state.world_y - SCREEN_HEIGHT / 2
        
        # Grid range to render dynamically based on camera viewpoint
        start_col = max(0, int(cam_x / TILE_SIZE))
        end_col = min(MAP_TILES_WIDTH, int((cam_x + (SCREEN_WIDTH - 250)) / TILE_SIZE) + 1)
        start_row = max(0, int(cam_y / TILE_SIZE))
        end_row = min(MAP_TILES_HEIGHT, int((cam_y + SCREEN_HEIGHT) / TILE_SIZE) + 1)
        
        # Render tiles
        for col in range(start_col, end_col):
            for row in range(start_row, end_row):
                rx = col * TILE_SIZE - cam_x
                ry = row * TILE_SIZE - cam_y
                biome = get_biome_at(col, row)
                cfg = BIOME_CONFIGS[biome]
                
                # Check tile accent grids (check patterns)
                is_alt = (col + row) % 2 == 0
                col_to_use = cfg['col1'] if is_alt else cfg['col2']
                
                pygame.draw.rect(screen, col_to_use, (rx, ry, TILE_SIZE, TILE_SIZE))
                
                # Biome detailings (Draw lava bubbles, ice crystals, grass flowers)
                seed_expr = (col * 31 + row * 17) % 100
                if biome == "LAVA" and seed_expr < 12:
                    pygame.draw.circle(screen, (255, 120, 0, 80), (int(rx + TILE_SIZE/2), int(ry + TILE_SIZE/2)), 4, width=1)
                elif biome == "ICE" and seed_expr < 15:
                    pygame.draw.circle(screen, COLOR_WHITE, (int(rx + TILE_SIZE/2 + seed_expr*0.5), int(ry + TILE_SIZE/2)), 1)
                elif biome == "SWAMP" and seed_expr < 10:
                    pygame.draw.ellipse(screen, (15, 25, 15), (rx + 10, ry + 20, 20, 6))

        # Render Loots
        for l in state.loots:
            l.draw(screen, cam_x, cam_y)

        # Render Projectiles
        for p in state.projectiles:
            p.draw(screen, cam_x, cam_y)

        # Render Enemies
        for e in state.enemies:
            e.draw(screen, cam_x, cam_y)

        # Render Particles
        for part in state.particles:
            part.draw(screen, cam_x, cam_y)

        # Render Player Character
        prx = int(state.world_x - cam_x)
        pry = int(state.world_y - cam_y)
        
        # Drop shadow
        pygame.draw.ellipse(screen, (0, 0, 0, 70), (prx - 20, pry + 12, 40, 14))
        
        # Base Body
        player_color = COLOR_TEAL if state.char_class == "Priest" else (COLOR_BLUE if state.char_class == "Mage" else COLOR_SLATE)
        if state.char_class == "Warrior": player_color = COLOR_RED
        
        # Protection shield aura
        if state.protection_until > time.time():
            rem_prot = state.protection_until - time.time()
            pulse_alpha = int(abs(math.sin(time.time()*5)) * 80) + 40
            pygame.draw.circle(screen, (241, 196, 15), (prx, pry), 26, width=2)
            
        pygame.draw.circle(screen, player_color, (prx, pry), 18)
        # Inner core head highlight
        pygame.draw.circle(screen, COLOR_WHITE, (prx - 5, pry - 5), 5)
        
        # Weapon/Stave
        pygame.draw.line(screen, COLOR_WHITE, (prx + 12, pry - 12), (prx + 22, pry - 26), 3)
        pygame.draw.circle(screen, COLOR_YELLOW, (prx + 22, pry - 26), 5)

        # Visual indicator of Active Selected Spell weapon light
        if state.selected_spell == 1:
            pygame.draw.circle(screen, COLOR_ORANGE, (prx + 22, pry - 26), 2)
        elif state.selected_spell == 2:
            pygame.draw.circle(screen, COLOR_BLUE, (prx + 22, pry - 26), 2)
        elif state.selected_spell == 3:
            pygame.draw.circle(screen, COLOR_YELLOW, (prx + 22, pry - 26), 2)


        # --- RIGHT SIDEBAR DATA PANEL (UI/HUD) ---
        sidebar_x = SCREEN_WIDTH - 250
        pygame.draw.rect(screen, (15, 23, 42), (sidebar_x, 0, 250, SCREEN_HEIGHT))
        pygame.draw.line(screen, (40, 50, 70), (sidebar_x, 0), (sidebar_x, SCREEN_HEIGHT), 2)
        
        # Title of region
        hdr_surf = font_large_ui.render("RPG BOHATER", True, COLOR_WHITE)
        name_surf = font_subtitle.render(f"@{state.player_name}", True, COLOR_YELLOW)
        class_surf = font_ui.render(f"Klasa: {state.char_class}", True, COLOR_SLATE)
        
        screen.blit(hdr_surf, (sidebar_x + 20, 20))
        screen.blit(name_surf, (sidebar_x + 20, 55))
        screen.blit(class_surf, (sidebar_x + 20, 80))
        
        # Biome footprint indicator text
        biome_lbl = font_ui.render(f"Lokacja: {BIOME_CONFIGS[current_biome]['name']}", True, BIOME_CONFIGS[current_biome]['col1'])
        screen.blit(biome_lbl, (sidebar_x + 20, 105))
        
        # Core Attribute Bars
        labels = ["ŻYCIE (HP)", "MANA", "SPAWN PROTECT", "STAMINA"]
        cur_vals = [state.hp, state.mana, max(0.0, state.protection_until - time.time()), state.stamina]
        max_vals = [state.max_hp, state.max_mana, 15.0, state.max_stamina]
        colors = [COLOR_RED, COLOR_BLUE, COLOR_YELLOW, COLOR_GREEN]
        
        y_pos = 145
        for idx in range(4):
            lbl_surf = font_ui.render(f"{labels[idx]} ({int(cur_vals[idx])}/{int(max_vals[idx])})", True, COLOR_WHITE)
            screen.blit(lbl_surf, (sidebar_x + 20, y_pos))
            y_pos += 18
            
            # bar exterior container
            pygame.draw.rect(screen, (30, 41, 59), (sidebar_x + 20, y_pos, 210, 10), border_radius=2)
            pct = max(0.0, min(1.0, cur_vals[idx] / max_vals[idx]))
            pygame.draw.rect(screen, colors[idx], (sidebar_x + 20, y_pos, int(210 * pct), 10), border_radius=2)
            y_pos += 22

        # Level up mechanics
        lvl_lbl = font_ui.render(f"POZIOM: {state.level}  Score: {state.score}", True, COLOR_PINK)
        screen.blit(lvl_lbl, (sidebar_x + 20, 315))
        
        xp_lbl = font_ui.render(f"XP: {state.xp}/{state.xp_needed}", True, COLOR_WHITE)
        screen.blit(xp_lbl, (sidebar_x + 20, 335))
        pygame.draw.rect(screen, (30, 41, 59), (sidebar_x + 20, 355, 210, 8), border_radius=2)
        xp_pct = max(0.0, min(1.0, state.xp / state.xp_needed))
        pygame.draw.rect(screen, COLOR_PINK, (sidebar_x + 20, 355, int(210 * xp_pct), 8), border_radius=2)

        # Character Stats (Attributes window modifier)
        stats_header = font_subtitle.render("STATYSTYKI", True, COLOR_WHITE)
        screen.blit(stats_header, (sidebar_x + 20, 385))
        
        # Skill Allocation points left
        pts_lbl = font_ui.render(f"Wolne punkty: {state.stat_points}", True, COLOR_YELLOW if state.stat_points > 0 else COLOR_SLATE)
        screen.blit(pts_lbl, (sidebar_x + 20, 403))
        
        stat_names = ["Siła (Str)", "Energia (Ene)", "Witalność (Life)", "Kondycja (Stam)", "Szybkość (Dext)"]
        stat_current_values = [state.strength, state.energy, state.life, state.stamina_stat, state.speed_stat]
        
        stat_y = 420
        for i, val in enumerate(stat_current_values):
            col_txt = COLOR_WHITE if state.stat_points > 0 else COLOR_SLATE
            txt = font_ui.render(f"{stat_names[i]}: {val}", True, col_txt)
            screen.blit(txt, (sidebar_x + 20, stat_y))
            
            # Show positive plus adder
            if state.stat_points > 0:
                pygame.draw.rect(screen, COLOR_GREEN, (SCREEN_WIDTH - 40, stat_y - 2, 25, 20), border_radius=3)
                plus_char = font_ui.render("+", True, COLOR_WHITE)
                screen.blit(plus_char, (SCREEN_WIDTH - 32, stat_y))
                
            stat_y += 35

        # Spell Selector HUD icons
        spells_y = 595
        pygame.draw.line(screen, (40, 50, 70), (sidebar_x, spells_y - 10), (SCREEN_WIDTH, spells_y - 10), 1)
        hud_spells_title = font_ui.render("Wybór Zaklęć (klawisze 1-3):", True, COLOR_WHITE)
        screen.blit(hud_spells_title, (sidebar_x + 20, spells_y))
        
        # Spell cards
        spell_icons = ["1: Fireball", "2: Frost Nova", "3: Solar Wrath"]
        cooldowns = [0, state.spell2_cooldown, state.spell3_cooldown]
        colors_spells = [COLOR_ORANGE, COLOR_BLUE, COLOR_YELLOW]
        
        spells_draw_y = spells_y + 20
        for idx in range(3):
            is_sel = (state.selected_spell == idx + 1)
            b_col = COLOR_WHITE if is_sel else (50, 50, 60)
            
            # Draw spell container card
            pygame.draw.rect(screen, (20, 30, 45), (sidebar_x + 20, spells_draw_y, 210, 30), border_radius=4)
            pygame.draw.rect(screen, b_col, (sidebar_x + 20, spells_draw_y, 210, 30), width=1 if is_sel else 1, border_radius=4)
            
            # Left colored tab
            pygame.draw.rect(screen, colors_spells[idx], (sidebar_x + 22, spells_draw_y + 2, 6, 26), border_radius=1)
            
            # Label
            lbl_col = COLOR_WHITE if is_sel else COLOR_SLATE
            cd_txt = f" (CD: {cooldowns[idx] // 60}s)" if cooldowns[idx] > 0 else ""
            txt_surf = font_ui.render(f"{spell_icons[idx]}{cd_txt}", True, lbl_col)
            screen.blit(txt_surf, (sidebar_x + 35, spells_draw_y + 8))
            
            spells_draw_y += 35


        # --- BOTTOM CHAT JOURNAL LOG DIRECTLY SYNCED ---
        pygame.draw.rect(screen, (8, 11, 20, 240), (20, SCREEN_HEIGHT - 170, 420, 150), border_radius=8)
        pygame.draw.rect(screen, (30, 40, 55), (20, SCREEN_HEIGHT - 170, 420, 150), width=1, border_radius=8)
        
        chat_hdr = font_ui.render("DZIENNIK ZDARZEŃ SURVIVAL:", True, COLOR_YELLOW)
        screen.blit(chat_hdr, (30, SCREEN_HEIGHT - 162))
        
        chat_draw_y = SCREEN_HEIGHT - 145
        for ev in state.event_log[-5:][::-1]:
            # Select color based on action type
            tc = COLOR_WHITE
            if ev['type'] == "death": tc = COLOR_RED
            elif ev['type'] == "level": tc = COLOR_PINK
            elif ev['type'] == "kill": tc = COLOR_YELLOW
            elif ev['type'] == "join": tc = COLOR_GREEN
            elif ev['type'] == "spell": tc = COLOR_BLUE
            
            msg = f"[{ev['time']}] {ev['text']}"
            msg_surf = font_log.render(msg, True, tc)
            screen.blit(msg_surf, (30, chat_draw_y))
            chat_draw_y += 22

    # Draw layout screen update
    pygame.display.flip()
    clock.tick(60)
