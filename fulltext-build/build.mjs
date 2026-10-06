// Build the Pagefind full-text index from records.jsonl (made by prepare.py) into ../pagefind/
import * as pagefind from "pagefind";
import fs from "node:fs";
import readline from "node:readline";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const out = process.env.PF_OUT || path.join(here, "..", "pagefind");
const { index, errors } = await pagefind.createIndex({ forceLanguage: "en" });
if (errors.length) { console.error(errors); process.exit(1); }

let n = 0;
const rl = readline.createInterface({ input: fs.createReadStream(path.join(here, "records.jsonl")) });
for await (const line of rl) {
  if (!line.trim()) continue;
  const r = JSON.parse(line);
  const res = await index.addCustomRecord({ url: r.url, content: r.content, language: "en", meta: r.meta, filters: r.filters, sort: r.sort });
  if (res.errors.length) { console.error(res.errors); process.exit(1); }
  if (++n % 5000 === 0) console.log(n, "pages indexed");
}
// write beside the live index and swap it in, so a page loaded mid-build never sees half an index
const fresh = out + ".new", old = out + ".old";
fs.rmSync(fresh, { recursive: true, force: true, maxRetries: 5 });
const w = await index.writeFiles({ outputPath: fresh });
if (w.errors.length) { console.error(w.errors); process.exit(1); }
if (fs.existsSync(old)) fs.rmSync(old, { recursive: true, force: true, maxRetries: 5 });
if (fs.existsSync(out)) fs.renameSync(out, old);
fs.renameSync(fresh, out);
try { fs.rmSync(old, { recursive: true, force: true, maxRetries: 5 }); } catch (e) { console.warn("left", old, e.code); }
console.log(`${n} pages -> ${out}`);
await pagefind.close();
