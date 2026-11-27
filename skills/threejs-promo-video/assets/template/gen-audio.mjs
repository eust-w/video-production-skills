#!/usr/bin/env node
// Synthesizes a royalty-free soundtrack synced to storyboard.json: pad chords, a beat that starts after
// the hook, risers/impacts on section cuts, whooshes on shot changes, pings for checklist ticks and
// spotlight reveals, and a final hit on the lockup. No samples, no network.
//
//   node gen-audio.mjs [--storyboard storyboard.json] [--out music.wav]
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2), opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
const sb = JSON.parse(fs.readFileSync(path.resolve(ROOT, opt('--storyboard', 'storyboard.json')), 'utf8'));
const OUT = path.resolve(process.cwd(), opt('--out', path.join(ROOT, 'music.wav')));
const SR = 48000, D = sb.duration || 30, N = Math.round(SR * D);
const shots = (sb.shots || []).map(s => ({ ...s, t0: s.t[0], t1: s.t[1] }));
const HOOK_END = sb.hook ? sb.hook.end : 0, END = sb.lockup ? sb.lockup.t : D;
const nSteps = Math.max(0, ...shots.map(s => s.step + 1));
const stepStart = Array.from({ length: nSteps }, (_, i) => shots.find(s => s.step === i)?.t0 ?? END);
const BEAT0 = shots.length ? shots[0].t0 : HOOK_END;

const L = new Float32Array(N), Rt = new Float32Array(N), SEND = new Float32Array(N);
const mf = m => 440 * Math.pow(2, (m - 69) / 12);
function rng(seed) { return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const rnd = rng(3), clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x)), seg = (t, a, b) => clamp((t - a) / (b - a));
function put(i, v, pan = 0, send = 0) { if (i < 0 || i >= N) return; L[i] += v * (1 - Math.max(0, pan)); Rt[i] += v * (1 + Math.min(0, pan)); SEND[i] += v * send; }

// chord timeline: Am (hook) → F → C → G … cycling at every section / shot boundary, Cadd9 on the lockup
const PROG = [[53, 57, 60, 65], [48, 55, 60, 64], [43, 55, 59, 62], [45, 57, 60, 64]];
const bounds = [...new Set([0, HOOK_END, ...shots.map(s => s.t0)].filter(x => x < END))].sort((a, b) => a - b);
const CH = bounds.map((t, i) => [t, t < HOOK_END || (i === 0 && HOOK_END) ? [57, 60, 64, 69] : PROG[(i - (HOOK_END ? 1 : 0)) % PROG.length]]);
CH.push([END, [48, 55, 62, 64, 67, 72]]);
for (let c = 0; c < CH.length; c++) {
  const [t0, notes] = CH[c], t1 = c + 1 < CH.length ? CH[c + 1][0] : D, last = t0 >= END;
  const a = Math.floor(Math.max(0, t0 - .05) * SR), b = Math.min(N, Math.floor((t1 + .6) * SR)), lvl = last ? .05 : t0 >= BEAT0 ? .034 : .03;
  for (const m of notes) for (const det of [-.0025, .0025]) {
    const f = mf(m) * (1 + det), pan = det < 0 ? -.35 : .35;
    for (let i = a; i < b; i++) {
      const t = i / SR, lt = t - t0;
      const env = Math.min(1, lt / .5) * (t > t1 ? Math.max(0, 1 - (t - t1) / .6) : 1) * (last ? Math.max(0, 1 - lt / 4) : 1);
      let v = 0; for (let h = 1; h <= 5; h++) v += Math.sin(2 * Math.PI * f * h * t) / (h * h * .8 + .2);
      put(i, v * env * lvl * (1 + .15 * Math.sin(t * 1.3 + m)), pan, .5);
    }
  }
}
const chordAt = t => { let r = CH[0][1]; for (const [t0, n] of CH) if (t >= t0) r = n; return r; };
function kick(t0, amp) { const a = Math.floor(t0 * SR); let ph = 0; for (let k = 0; k < SR * .45; k++) { const t = k / SR; ph += 2 * Math.PI * (45 + 110 * Math.exp(-t * 28)) / SR; put(a + k, Math.sin(ph) * Math.exp(-t * 7) * amp); } }
function hat(t0, amp = .07) { const a = Math.floor(t0 * SR); let prev = 0; for (let k = 0; k < SR * .05; k++) { const n = rnd() * 2 - 1, hp = n - prev; prev = n; put(a + k, hp * Math.exp(-k / SR * 90) * amp, .25, .1); } }
function bass(t0, m, amp = .2) { const a = Math.floor(t0 * SR), f = mf(m); for (let k = 0; k < SR * .22; k++) { const t = k / SR; put(a + k, (Math.tanh(2.2 * Math.sin(2 * Math.PI * f * t)) * .7 + Math.sin(Math.PI * f * t) * .5) * Math.exp(-t * 9) * Math.min(1, t / .004) * amp); } }
function riser(t1, len = 1, amp = .2) { const a = Math.floor((t1 - len) * SR); let lp = 0; for (let k = 0; k < SR * len; k++) { const x = k / (SR * len); lp += (.02 + .5 * x * x) * ((rnd() * 2 - 1) - lp); put(a + k, lp * x * x * amp, Math.sin(x * 9) * .4, .4); } }
function impact(t0, amp = .6) { const a = Math.floor(t0 * SR); let lp = 0; for (let k = 0; k < SR * 2.2; k++) { const t = k / SR; lp += .08 * ((rnd() * 2 - 1) - lp); put(a + k, (Math.sin(2 * Math.PI * (38 + 30 * Math.exp(-t * 6)) * t) * Math.exp(-t * 2.2) + lp * 2.5 * Math.exp(-t * 5)) * amp, 0, .6); } }
function whoosh(a0, b0, pan = .6, amp = .2) { const a = Math.floor(a0 * SR), n = Math.floor((b0 - a0) * SR); let lp = 0; for (let k = 0; k < n; k++) { const x = k / n; lp += (.05 + .3 * Math.sin(Math.PI * x)) * ((rnd() * 2 - 1) - lp); put(a + k, lp * Math.sin(Math.PI * x) * amp, pan * (x * 2 - 1), .3); } }
function ping(t0, m, amp = .09, dec = 6, pan = 0) { const a = Math.floor(t0 * SR), f = mf(m); for (let k = 0; k < SR * .9; k++) { const t = k / SR; put(a + k, (Math.sin(2 * Math.PI * f * t) + .25 * Math.sin(4 * Math.PI * f * t)) * Math.exp(-t * dec) * amp, pan, .7); } }
function ticks(a0, b0, n, amp = .12) { for (let i = 0; i < n; i++) { const a = Math.floor((a0 + i * (b0 - a0) / n) * SR); for (let k = 0; k < SR * .01; k++) put(a + k, (rnd() * 2 - 1) * Math.exp(-k / SR * 400) * amp, .4); } }

// rhythm
for (let t = .4; t < BEAT0; t += 1) kick(t, .35);
for (let t = BEAT0; t < END; t += .5) kick(t, t < (stepStart[1] ?? END) ? .7 : .88);
for (let t = BEAT0; t < END; t += .25) bass(t, chordAt(t)[0] - 12 + (Math.round((t - BEAT0) * 4) % 4 === 3 ? 12 : 0));
for (let t = (stepStart[1] ?? END) + .25; t < END; t += .5) { hat(t); hat(t + .25, .035); }
// hook: typing, smug "done" ding, stamp slam (timings mirror public/main.js)
if (sb.hook) {
  const h = HOOK_END; ticks(h * .09, h * .27, 9); ticks(h * .28, h * .45, 9); ping(h * .53, 76); ping(h * .53 + .08, 83, .08); impact(h * .67, .7);
  const a = Math.floor(h * .67 * SR); for (let k = 0; k < SR * .3; k++) { const t = k / SR; put(a + k, Math.sign(Math.sin(2 * Math.PI * 160 * Math.exp(-t * 3) * t)) * Math.exp(-t * 7) * .12, 0, .2); }
}
// cuts
for (const c of stepStart) if (c < END) { riser(c); impact(c, .55); }
shots.forEach((s, i) => { if (i && !stepStart.includes(s.t0)) whoosh(s.t0 - .25, s.t0 + .35, .6, .22); if (s.pan) whoosh(s.pan[0], s.pan[1], -.6, .18); });
// spotlight reveal + checklist ticks
shots.forEach((s, i) => {
  if (s.spot) ping((s.pan ? s.pan[1] : s.t0 + .7) + .05, [72, 74, 76, 79][i % 4], .07, 7);
  if (s.checks) s.checks.ys.forEach((_, j) => ping(s.checks.start + j * (s.checks.gap ?? .28), [72, 74, 76, 79, 81, 84, 86][j % 7], .09, 8, (j - 2.5) * .25));
});
// lockup
if (sb.lockup) { riser(END, 1.6, .3); impact(END, 1); for (let j = 0; j < 14; j++) ping(END + .1 + j * .12 + rnd() * .05, [84, 88, 91, 96][j % 4], .04, 5, rnd() - .5); }

// reverb + master
function reverb(x, combs, aps) {
  const y = new Float32Array(N);
  for (const [d, g] of combs) { const buf = new Float32Array(d); let p = 0, lp = 0; for (let i = 0; i < N; i++) { const o = buf[p]; lp = o * .7 + lp * .3; buf[p] = x[i] + lp * g; p = (p + 1) % d; y[i] += o / combs.length; } }
  for (const [d, g] of aps) { const buf = new Float32Array(d); let p = 0; for (let i = 0; i < N; i++) { const b = buf[p], v = y[i] + b * g; buf[p] = v; y[i] = b - v * g; p = (p + 1) % d; } }
  return y;
}
const rvL = reverb(SEND, [[1557, .84], [1617, .84], [1491, .84], [1422, .84]], [[225, .5], [556, .5]]);
const rvR = reverb(SEND, [[1277, .84], [1356, .84], [1188, .84], [1116, .84]], [[341, .5], [441, .5]]);
let peak = 0; const out = new Float32Array(N * 2);
for (let i = 0; i < N; i++) {
  const t = i / SR, g = Math.min(1, t / .4) * (1 - seg(t, D - 1.4, D));
  out[i * 2] = Math.tanh((L[i] + rvL[i] * .55) * 1.1) * g; out[i * 2 + 1] = Math.tanh((Rt[i] + rvR[i] * .55) * 1.1) * g;
  peak = Math.max(peak, Math.abs(out[i * 2]), Math.abs(out[i * 2 + 1]));
}
const norm = .89 / (peak || 1), buf = Buffer.alloc(44 + N * 4);
buf.write('RIFF', 0); buf.writeUInt32LE(36 + N * 4, 4); buf.write('WAVEfmt ', 8); buf.writeUInt32LE(16, 16); buf.writeUInt16LE(1, 20); buf.writeUInt16LE(2, 22);
buf.writeUInt32LE(SR, 24); buf.writeUInt32LE(SR * 4, 28); buf.writeUInt16LE(4, 32); buf.writeUInt16LE(16, 34); buf.write('data', 36); buf.writeUInt32LE(N * 4, 40);
for (let i = 0; i < N * 2; i++) buf.writeInt16LE(Math.round(clamp(out[i] * norm, -1, 1) * 32767), 44 + i * 2);
fs.writeFileSync(OUT, buf); console.log('wrote', OUT);
