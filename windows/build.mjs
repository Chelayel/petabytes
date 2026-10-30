// Fills web/pet.html and web/picker.html with the pets for the Windows app, into dist/ (Tauri's frontend).
// The pages talk to the app through acquireVsCodeApi(), which the app provides (src-tauri/src/main.rs), so
// they're the same pages VS Code shows.
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const web = join(here, "..", "web");
const pets = readFileSync(join(web, "pets.json"), "utf8").replace(/</g, "\\u003c");
// Tauri's IPC goes through ipc: (http://ipc.localhost on Windows).
const csp = "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src ipc: http://ipc.localhost";
const fill = (file, extra = {}) => {
  let page = readFileSync(join(web, file), "utf8");
  for (const [key, value] of Object.entries({ csp, nonce: "petabytes", pets, ...extra })) page = page.replaceAll(`{{${key}}}`, value);
  return page;
};
mkdirSync(join(here, "dist"), { recursive: true });
writeFileSync(join(here, "dist", "index.html"), fill("pet.html"));
// The pet chosen now comes from the app when the window opens.
writeFileSync(join(here, "dist", "picker.html"), fill("picker.html", { current: 'window.__petabytesCurrent || "turtle"' }));
console.log("dist/index.html, dist/picker.html");
