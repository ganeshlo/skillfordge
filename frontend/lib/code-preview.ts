import { transform } from "sucrase";
import type { CodingFile } from "@/lib/types";

const PREVIEW_CSP = "default-src 'none'; script-src 'unsafe-inline' https://esm.sh; style-src 'unsafe-inline'; img-src data: blob:; font-src data:; connect-src 'none';";

function escapeClosingScript(value: string) {
  return value.replace(/<\/script/gi, "<\\/script");
}

function errorReporter() {
  return `<script>
    window.addEventListener("error", event => {
      const output = document.getElementById("learnos-preview-error");
      if (output) { output.hidden = false; output.textContent = event.message; }
    });
  </script>`;
}

export function buildWebPreview(files: CodingFile[], activeFile: CodingFile) {
  if (activeFile.language === "react") {
    const styles = files.filter(file => file.language === "css").map(file => file.content).join("\n");
    const compiled = transform(activeFile.content, {
      transforms: ["typescript", "jsx", "imports"],
      jsxRuntime: "classic",
      production: true,
    }).code;
    return `<!doctype html><html><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="${PREVIEW_CSP}"><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0;font-family:Inter,system-ui,sans-serif;color:#0f172a}#learnos-preview-error{margin:16px;padding:12px;border-radius:8px;background:#fff1f2;color:#be123c;white-space:pre-wrap}${styles}</style></head><body><div id="root"></div><pre id="learnos-preview-error" hidden></pre>${errorReporter()}<script type="module">
      import React from "https://esm.sh/react@19";
      import { createRoot } from "https://esm.sh/react-dom@19/client";
      const exports = {}; const module = { exports };
      const require = name => name === "react" ? React : name === "react-dom/client" ? { createRoot } : (() => { throw new Error("Preview import is not allowed: " + name); })();
      try {
        ${escapeClosingScript(compiled)}
        const App = module.exports.default || exports.default || module.exports;
        if (typeof App !== "function") throw new Error("Export a default React component to preview it.");
        createRoot(document.getElementById("root")).render(React.createElement(App));
      } catch (error) {
        const output = document.getElementById("learnos-preview-error"); output.hidden = false; output.textContent = error instanceof Error ? error.stack || error.message : String(error);
      }
    </script></body></html>`;
  }

  const html = files.find(file => file.language === "html")?.content ?? "<main><h1>LearnOS preview</h1></main>";
  const css = files.filter(file => file.language === "css").map(file => file.content).join("\n");
  const javascript = files.filter(file => file.language === "javascript").map(file => file.content).join("\n");
  return `<!doctype html><html><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="${PREVIEW_CSP}"><meta name="viewport" content="width=device-width,initial-scale=1"><style>${css}</style></head><body>${html}<pre id="learnos-preview-error" hidden></pre>${errorReporter()}${javascript ? `<script>${escapeClosingScript(javascript)}</script>` : ""}</body></html>`;
}
