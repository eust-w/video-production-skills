#!/usr/bin/env node
// Generates fictional sample screenshots (1920×960) into shots/ so the template renders out of the box.
// Replace them with frames from your real product recording for a real video.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const out = path.join(ROOT, 'shots'); fs.mkdirSync(out, { recursive: true });
let browser;
try { browser = await chromium.launch({ channel: 'chrome' }); } catch { browser = await chromium.launch(); }
const page = await browser.newPage({ viewport: { width: 1920, height: 960 } });
const url = q => 'file://' + path.join(ROOT, 'sample', 'app.html') + '?' + q;
const jobs = [['describe', 'view=describe'], ['criteria', 'view=criteria'], ['verify', 'view=verify'], ['release', 'view=release'],
  ...[1, 2, 3, 4].map(s => [`run-${s - 1}`, `view=run&stage=${s}`])];
for (const [name, q] of jobs) { await page.goto(url(q)); await page.screenshot({ path: path.join(out, `${name}.png`) }); console.log('shot', name); }
await browser.close();
