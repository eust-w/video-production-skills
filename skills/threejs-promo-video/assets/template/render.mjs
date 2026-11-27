#!/usr/bin/env node
// Deterministic frame-by-frame renderer for the three.js promo template.
//
//   node render.mjs --stills 2,6.5,11            # write QA stills to stills-<lang>/
//   node render.mjs --video out.mp4 --audio music.wav [--lang en]
//
// Options: --lang <code>  --storyboard <file>  --browser chrome|chromium  --fps <n>
// The page exposes window.renderFrame(t) and window.ready; every frame is a pure
// function of t, so renders are reproducible and independent of machine speed.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const opt = (k, d = null) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
if (args.includes('--help') || (!opt('--stills') && !opt('--video'))) {
  console.log('usage: node render.mjs (--stills t1,t2,... | --video out.mp4 [--audio music.wav]) [--lang zh|en] [--storyboard storyboard.json] [--browser chrome|chromium]');
  process.exit(args.includes('--help') ? 0 : 1);
}
const lang = opt('--lang', 'en');
const sbFile = opt('--storyboard', 'storyboard.json');
const sb = JSON.parse(fs.readFileSync(path.resolve(ROOT, sbFile), 'utf8'));
const fps = Number(opt('--fps', sb.fps || 30)), duration = sb.duration || 30;
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.svg': 'image/svg+xml', '.webp': 'image/webp' };

const server = http.createServer((req, res) => {
  let rel = decodeURIComponent(req.url.split('?')[0]);
  if (rel === '/storyboard.json') rel = '/' + sbFile;
  const p = path.join(ROOT, rel);
  if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(rel === '/favicon.ico' ? 204 : 404); return res.end(); }
  res.writeHead(200, { 'content-type': TYPES[path.extname(p).toLowerCase()] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const port = server.address().port;

// Prefer installed Google Chrome (real GPU via ANGLE/Metal on macOS); fall back to Playwright's Chromium.
const gpuArgs = ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist', '--enable-unsafe-swiftshader'];
let browser;
const want = opt('--browser', 'chrome');
try { browser = await chromium.launch(want === 'chrome' ? { channel: 'chrome', args: gpuArgs } : { args: gpuArgs }); }
catch (e) { console.warn(`[render] ${want} unavailable (${e.message.split('\n')[0]}), using bundled chromium`); browser = await chromium.launch({ args: gpuArgs }); }
const [W, H] = sb.size || [1920, 1080];
const page = await browser.newPage({ viewport: { width: W, height: H } });
page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') console.log('[page]', m.text()); });
page.on('pageerror', e => console.log('[pageerror]', e.message));
await page.goto(`http://127.0.0.1:${port}/public/index.html?lang=${encodeURIComponent(lang)}`);
await page.waitForFunction('window.ready === true || window.renderError', null, { timeout: 90000 });
const err = await page.evaluate('window.renderError || null'); if (err) { console.error('[render] page failed:', err); process.exit(2); }
const toBuf = d => Buffer.from(d.slice(d.indexOf(',') + 1), 'base64');

if (opt('--stills')) {
  const dir = path.join(ROOT, `stills-${lang}`); fs.mkdirSync(dir, { recursive: true });
  for (const s of opt('--stills').split(',').map(x => x.trim()).filter(Boolean)) {
    const t = Number(s);
    await page.evaluate(t => window.renderFrame(Math.max(0, t - 1 / 30)), t); // warm-up frame (texture upload)
    const d = await page.evaluate(t => window.renderFrame(t), t);
    const name = `t${t.toFixed(2).padStart(6, '0')}.jpg`; // zero-padded so globbing sorts by time
    fs.writeFileSync(path.join(dir, name), toBuf(d)); console.log('still', path.join(path.basename(dir), name));
  }
} else {
  const out = path.resolve(process.cwd(), opt('--video')), audio = opt('--audio');
  const ff = spawn('ffmpeg', ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
    ...(audio ? ['-i', path.resolve(process.cwd(), audio)] : []), '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
    ...(audio ? ['-c:a', 'aac', '-b:a', '192k', '-shortest'] : []), out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const N = Math.round(duration * fps), t0 = Date.now();
  for (let f = 0; f < N; f++) {
    const d = await page.evaluate(([f, fps]) => window.renderFrame(f / fps, f), [f, fps]);
    if (!ff.stdin.write(toBuf(d))) await new Promise(r => ff.stdin.once('drain', r));
    if (f % (fps * 2) === 0) console.log(`frame ${f}/${N}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end(); const code = await new Promise(r => ff.on('close', r));
  if (code !== 0) { console.error('[render] ffmpeg exited with', code); process.exit(3); }
  console.log('done', out, ((Date.now() - t0) / 1000).toFixed(0) + 's');
}
await browser.close(); server.close();
