import { cp, mkdir, rm } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(scriptDir, "../..");
const output = path.join(root, "dist");

const files = ["index.html", "main.js", "character.js", "architecture.js", "_headers"];
const directories = ["assets", "vendor", "licenses"];

await rm(output, { recursive: true, force: true });
await mkdir(output, { recursive: true });

for (const file of files) {
  await cp(path.join(root, file), path.join(output, file));
}

for (const directory of directories) {
  await cp(path.join(root, directory), path.join(output, directory), {
    recursive: true,
  });
}

console.log(`Cloudflare Pages output created at ${output}`);
