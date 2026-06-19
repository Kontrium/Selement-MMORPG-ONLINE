import fs from "fs";
import path from "path";

function bundleHTML() {
  try {
    const distPath = path.resolve("dist");
    const assetsPath = path.join(distPath, "assets");

    if (!fs.existsSync(distPath) || !fs.existsSync(assetsPath)) {
      console.error("Error: 'dist' or 'dist/assets' directory does not exist. Run 'npm run build' first.");
      process.exit(1);
    }

    // Read the contents of the assets directory
    const files = fs.readdirSync(assetsPath);
    const jsFile = files.find(file => file.endsWith(".js"));
    const cssFile = files.find(file => file.endsWith(".css"));

    if (!jsFile || !cssFile) {
      console.error("Error: Could not find compiled .js and .css files in 'dist/assets'.");
      process.exit(1);
    }

    const jsContent = fs.readFileSync(path.join(assetsPath, jsFile), "utf-8");
    const cssContent = fs.readFileSync(path.join(assetsPath, cssFile), "utf-8");

    // Read dist/index.html
    const indexHtmlPath = path.join(distPath, "index.html");
    let htmlContent = fs.readFileSync(indexHtmlPath, "utf-8");

    // Replace the script with inline module script
    // Regex matches the script tag referencing our bundle
    const scriptRegex = /<script type="module" crossorigin src="\/assets\/index-[^"]+\.js"><\/script>/i;
    if (scriptRegex.test(htmlContent)) {
      htmlContent = htmlContent.replace(scriptRegex, `<script type="module">\n${jsContent}\n</script>`);
    } else {
      // Fallback matching
      const fallbackScriptRegex = /<script[^>]*src="[^"]*assets\/index-[^"]+\.js"[^>]*><\/script>/gi;
      htmlContent = htmlContent.replace(fallbackScriptRegex, `<script type="module">\n${jsContent}\n</script>`);
    }

    // Replace the stylesheet with inline styles
    const cssRegex = /<link rel="stylesheet" crossorigin href="\/assets\/index-[^"]+\.css">/i;
    if (cssRegex.test(htmlContent)) {
      htmlContent = htmlContent.replace(cssRegex, `<style>\n${cssContent}\n</style>`);
    } else {
      // Fallback matching
      const fallbackCssRegex = /<link[^>]*href="[^"]*assets\/index-[^"]+\.css"[^>]*>/gi;
      htmlContent = htmlContent.replace(fallbackCssRegex, `<style>\n${cssContent}\n</style>`);
    }

    // Update title
    htmlContent = htmlContent.replace(
      /<title>[^<]+<\/title>/i,
      "<title>Kontrium RPG - Online Standalone Edition</title>"
    );

    // Write stand-alone html file
    const rootStandalonePath = path.resolve("index_standalone.html");
    const distStandalonePath = path.join(distPath, "index_standalone.html");
    const distIndexPath = path.join(distPath, "index.html");

    fs.writeFileSync(rootStandalonePath, htmlContent, "utf-8");
    fs.writeFileSync(distStandalonePath, htmlContent, "utf-8");
    fs.writeFileSync(distIndexPath, htmlContent, "utf-8");

    console.log("Success! Compiled game successfully into a single standalone file:");
    console.log(`- Saved inside workspace as: /index_standalone.html`);
    console.log(`- Saved as production index: /dist/index.html`);
    console.log(`- Available online at: /index_standalone.html`);
  } catch (err) {
    console.error("An error occurred during standalone HTML compilation:", err);
    process.exit(1);
  }
}

bundleHTML();
