// three.js promo template: hook → real-product "path" shots with spotlight callouts → brand lockup.
// Everything is driven by /storyboard.json and is a pure function of time t (deterministic rendering).
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

try {
const SB = await (await fetch('/storyboard.json')).json();
const LANG = new URLSearchParams(location.search).get('lang') || 'en';
const CJK = /^(zh|ja|ko)/.test(LANG);
const tr = v => v == null ? '' : typeof v === 'string' ? v : (v[LANG] ?? v.en ?? Object.values(v)[0]);
const trArr = v => Array.isArray(v) ? v : (v?.[LANG] ?? v?.en ?? []);
const SANS_CJK = '"PingFang SC","Hiragino Sans GB","Noto Sans CJK SC","Microsoft YaHei",sans-serif';
const SANS_LAT = '"Avenir Next","Helvetica Neue","Inter","Segoe UI",sans-serif';
const SANS = CJK ? SANS_CJK : SANS_LAT;
const MONO = '"SF Mono",Menlo,Consolas,monospace';

const [W, H] = SB.size || [1920, 1080], FPS = SB.fps || 30, DUR = SB.duration || 30;
const TH = { accent: '#ff5a1f', accent2: '#ff8a3d', background: '#0b0504', haze: '#7a2208', dots: true, ...(SB.theme || {}) };
const OR = TH.accent, OR2 = TH.accent2, RED = '#ff3b3b', GREEN = '#4ade80';
const SCR = { width: 1920, height: 960, ...(SB.screen || {}) };
const SHOTS = (SB.shots || []).map(s => ({ ...s, t0: s.t[0], t1: s.t[1] }));
const HOOK = SB.hook || null, HOOK_END = HOOK ? HOOK.end : 0;
const END = SB.lockup ? SB.lockup.t : DUR;
const STEPS = trArr(SB.steps);
const stepStart = STEPS.map((_, i) => SHOTS.find(s => s.step === i)?.t0 ?? END);
const CUTS = [...new Set([HOOK_END, ...stepStart, END].filter(x => x > 0 && x < DUR))];

// ---------- utils ----------
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const seg = (t, a, b) => clamp((t - a) / (b - a));
const ease = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
const eout = x => 1 - Math.pow(1 - x, 3);
const eback = x => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };
const lerp = (a, b, x) => a + (b - a) * x;
const win = (t, a, b, fi = .4, fo = .4) => Math.min(seg(t, a, a + fi), 1 - seg(t, b - fo, b));
function rng(seed) { return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const hdr = (hex, k) => new THREE.Color(hex).multiplyScalar(k);
const typed = (s, t, a, b) => s.slice(0, Math.floor(seg(t, a, b) * s.length + 1e-6));

// ---------- renderer ----------
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setSize(W, H); renderer.setPixelRatio(1); document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene(); scene.background = new THREE.Color(TH.background);
const camera = new THREE.PerspectiveCamera(42, W / H, 0.1, 500); scene.add(camera);
const composer = new EffectComposer(renderer, new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: 4 }));
composer.addPass(new RenderPass(scene, camera));
// Threshold above the screenshot brightness so light UIs never bloom; only HDR accents glow.
composer.addPass(new UnrealBloomPass(new THREE.Vector2(W, H), .6, .6, .9));
composer.addPass(new OutputPass());

const GLOW = (() => { const c = document.createElement('canvas'); c.width = c.height = 128; const g = c.getContext('2d'); const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(.18, 'rgba(255,255,255,.55)'); gr.addColorStop(.5, 'rgba(255,255,255,.12)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 128, 128); return new THREE.CanvasTexture(c); })();
const glow = (color, size, k = 1) => { const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: GLOW, color: hdr(color, k), blending: THREE.AdditiveBlending, transparent: true, depthWrite: false, toneMapped: false })); s.scale.setScalar(size); return s; };
function setOpacity(obj, f) { obj.visible = f > 0.001; obj.traverse(o => { for (const m of o.material ? [].concat(o.material) : []) { if (m.userData.base === undefined) m.userData.base = m.opacity; m.transparent = true; m.opacity = m.userData.base * f; } }); }
function card(w, h, res = 300) {
  const c = document.createElement('canvas'); c.width = Math.round(w * res); c.height = Math.round(h * res);
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
  const mat = new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false, toneMapped: false });
  return { mesh: new THREE.Mesh(new THREE.PlaneGeometry(w, h), mat), c, ctx: c.getContext('2d'), tex, mat, key: null };
}
// Redraw a canvas texture only when its visual state changes. ctx.reset() matters: canvas state
// (textAlign, letterSpacing, …) otherwise leaks between redraws and shifts text.
function upd(cd, key, fn) { if (cd.key === key) return; cd.key = key; cd.ctx.reset(); fn(cd.ctx, cd.c); cd.tex.needsUpdate = true; }
function panel(ctx, c, accent, alpha = .92) {
  const p = 26, r = 30, w = c.width - 2 * p, h = c.height - 2 * p;
  ctx.save(); ctx.shadowColor = accent; ctx.shadowBlur = 34; ctx.beginPath(); ctx.roundRect(p, p, w, h, r); ctx.lineWidth = 4; ctx.strokeStyle = accent; ctx.stroke(); ctx.restore();
  ctx.beginPath(); ctx.roundRect(p, p, w, h, r); ctx.fillStyle = `rgba(24,14,11,${alpha})`; ctx.fill(); ctx.lineWidth = 3; ctx.strokeStyle = accent; ctx.stroke();
  const s = ctx.createLinearGradient(p, 0, p + w, 0); s.addColorStop(0, 'rgba(255,120,60,0)'); s.addColorStop(.5, 'rgba(255,190,140,.95)'); s.addColorStop(1, 'rgba(255,120,60,0)');
  ctx.fillStyle = s; ctx.fillRect(p + 20, p + h - 3, w - 40, 5);
}

// ---------- background: dot grid + haze, attached to the camera ----------
const bg = new THREE.Group(); camera.add(bg); bg.position.z = -42;
const haze = glow(TH.haze, 1, 1); haze.scale.set(80, 50, 1); haze.material.opacity = .5; haze.position.z = -2; bg.add(haze);
const accRGB = new THREE.Color(OR);
const dotGrid = (() => {
  const cols = 38, rows = 23, sp = 1.65, pos = [];
  for (let i = 0; i < cols; i++) for (let j = 0; j < rows; j++) pos.push((i - (cols - 1) / 2) * sp, (j - (rows - 1) / 2) * sp, 0);
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  const m = new THREE.ShaderMaterial({ transparent: true, depthWrite: false, uniforms: { uTime: { value: 0 }, uOp: { value: 1 }, uAcc: { value: new THREE.Vector3(accRGB.r, accRGB.g, accRGB.b) } },
    vertexShader: `varying vec2 vP; void main(){ vP = position.xy; gl_PointSize = 7.0; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
    fragmentShader: `uniform float uTime; uniform float uOp; uniform vec3 uAcc; varying vec2 vP;
      void main(){ vec2 d = gl_PointCoord - .5; if(length(d) > .5) discard;
        float side = smoothstep(9.0, 26.0, abs(vP.x + sin(uTime*.2)*3.0));
        float o = side * (.35 + .65*(.5 + .5*sin(length(vP*vec2(1.0,1.4))*.32 - uTime*1.1)));
        gl_FragColor = vec4(mix(vec3(.20,.14,.12), uAcc*.85, o), (.35 + .5*o) * smoothstep(.5,.25,length(d)) * uOp); }` });
  const p = new THREE.Points(g, m); p.visible = TH.dots !== false; bg.add(p); return p;
})();

// ---------- hook: an agent claims "done", stamped UNVERIFIED ----------
const gHook = new THREE.Group(); scene.add(gHook);
const hookCard = card(7.4, 3.3); gHook.add(hookCard.mesh); hookCard.mesh.position.y = .35;
const HT = HOOK ? { a: HOOK_END * .09, b: HOOK_END * .27, c: HOOK_END * .28, d: HOOK_END * .45, done: HOOK_END * .53, stamp: HOOK_END * .67 } : null;
function drawHook(t) {
  const L = trArr(HOOK.lines); const lines = [{ s: typed(L[0] || '', t, HT.a, HT.b) }];
  if (t > HT.c && L[1]) lines.push({ s: typed(L[1], t, HT.c, HT.d) });
  if (t > HT.done && L[2]) lines.push({ s: L[2], c: GREEN });
  const st = t > HT.stamp ? Math.round(eout(seg(t, HT.stamp, HT.stamp + .2)) * 6) / 6 : -1;
  upd(hookCard, JSON.stringify([lines, st]), (ctx, c) => {
    panel(ctx, c, st >= 0 ? RED : OR);
    ['#ff5f57', '#febc2e', '#28c840'].forEach((col, i) => { ctx.beginPath(); ctx.arc(80 + i * 40, 84, 12, 0, 7); ctx.fillStyle = col; ctx.fill(); });
    ctx.font = `600 36px ${SANS_LAT}`; ctx.fillStyle = OR2; ctx.letterSpacing = '6px'; ctx.fillText(tr(HOOK.title), 216, 97); ctx.letterSpacing = '0px';
    ctx.fillStyle = 'rgba(255,255,255,.08)'; ctx.fillRect(50, 134, c.width - 100, 2);
    ctx.font = `500 66px ${MONO}`; lines.forEach((l, i) => { ctx.fillStyle = l.c || '#e6d8d0'; ctx.fillText(l.s, 80, 260 + i * 120); });
    if (st >= 0) {
      ctx.save(); ctx.translate(c.width - 470, c.height - 250); ctx.rotate(-.12); const k = lerp(1.6, 1, st); ctx.scale(k, k); ctx.globalAlpha = st;
      ctx.lineWidth = 10; ctx.strokeStyle = RED; ctx.shadowColor = RED; ctx.shadowBlur = 30;
      ctx.font = `800 ${CJK ? 120 : 104}px ${SANS}`; const w = Math.max(ctx.measureText(tr(HOOK.stamp)).width + 90, 560);
      ctx.beginPath(); ctx.roundRect(-w / 2, -100, w, 200, 24); ctx.stroke(); ctx.shadowBlur = 0;
      ctx.fillStyle = RED; ctx.textAlign = 'center'; ctx.fillText(tr(HOOK.stamp), 0, CJK ? 20 : 15);
      ctx.font = `600 46px ${SANS}`; ctx.fillStyle = '#ff9a8f'; ctx.fillText(tr(HOOK.stampSub), 0, 74); ctx.restore();
    }
  });
}

// ---------- the real product screen (two planes for crossfades) ----------
const SW = 16, SH = SW * SCR.height / SCR.width, PX = SW / SCR.width;
const gScreen = new THREE.Group(); gScreen.rotation.y = -.07; scene.add(gScreen);
const mkPlane = z => { const p = new THREE.Mesh(new THREE.PlaneGeometry(SW, SH), new THREE.MeshBasicMaterial({ color: 0xeeeeee, transparent: true, depthWrite: false })); p.position.z = z; gScreen.add(p); return p; };
const planeA = mkPlane(0), planeB = mkPlane(.005);
const scrGlow = glow(OR, 1, 1); scrGlow.scale.set(SW * 1.35, SH * 1.5, 1); scrGlow.material.opacity = .25; scrGlow.position.z = -.1; gScreen.add(scrGlow);
gScreen.add(new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints([[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([x, y]) => new THREE.Vector3(x * SW / 2 * 1.003, y * SH / 2 * 1.006, .01))),
  new THREE.LineBasicMaterial({ color: hdr(OR, 2.2), transparent: true, toneMapped: false })));
const pxToLocal = (x, y) => new THREE.Vector3(x * PX - SW / 2, SH / 2 - y * PX, 0);
const TAN_V = Math.tan(THREE.MathUtils.degToRad(21)), TAN_H = TAN_V * W / H;
function rectCam(rect) {
  const [x0, y0, x1, y1] = rect, c = pxToLocal((x0 + x1) / 2, (y0 + y1) / 2), w = (x1 - x0) * PX, h = (y1 - y0) * PX;
  const d = Math.max(w * 1.12 / (2 * TAN_H), h * 1.75 / (2 * TAN_V)); // leave room for header, callout and captions
  const look = gScreen.localToWorld(c.clone()).add(new THREE.Vector3(0, -d * .1, 0));
  return { pos: look.clone().add(new THREE.Vector3(d * .1, d * .03, d)), look, d };
}
function shotCam(s, t) {
  if (!s.frame2) return rectCam(s.frame);
  const k = ease(seg(t, s.pan[0], s.pan[1])), a = rectCam(s.frame), b = rectCam(s.frame2);
  return { pos: a.pos.lerp(b.pos, k), look: a.look.lerp(b.look, k), d: lerp(a.d, b.d, k) };
}
const files = s => s.seq ? Array.from({ length: s.seq }, (_, k) => `${s.img}${k}${s.ext || '.png'}`) : [s.img];
const textures = {};
const texFor = (s, t) => { const f = files(s); return textures[f[s.seq ? Math.min(s.seq - 1, Math.floor(seg(t, s.t0 + .3, s.t1 - .2) * (s.seq - 1) + 1e-6)) : 0]]; };

// ---------- 2D overlay ----------
const comp = document.createElement('canvas'); comp.width = W; comp.height = H; const cx = comp.getContext('2d');
const vign = (() => { const c = document.createElement('canvas'); c.width = W; c.height = H; const g = c.getContext('2d');
  const gr = g.createRadialGradient(W / 2, H / 2, H * .35, W / 2, H / 2, H * 1.05); gr.addColorStop(0, 'rgba(0,0,0,0)'); gr.addColorStop(1, 'rgba(0,0,0,.7)'); g.fillStyle = gr; g.fillRect(0, 0, W, H);
  const b = g.createLinearGradient(0, H * .68, 0, H); b.addColorStop(0, 'rgba(0,0,0,0)'); b.addColorStop(1, 'rgba(0,0,0,.82)'); g.fillStyle = b; g.fillRect(0, H * .68, W, H * .32);
  const tp = g.createLinearGradient(0, 0, 0, H * .2); tp.addColorStop(0, 'rgba(0,0,0,.65)'); tp.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = tp; g.fillRect(0, 0, W, H * .2); return c; })();
const grains = [0, 1, 2, 3].map(k => { const c = document.createElement('canvas'); c.width = c.height = 256; const g = c.getContext('2d'); const d = g.createImageData(256, 256); const r = rng(100 + k);
  for (let i = 0; i < d.data.length; i += 4) { const v = r() * 255; d.data[i] = d.data[i + 1] = d.data[i + 2] = v; d.data[i + 3] = 255; } g.putImageData(d, 0, 0); return c; });
let logoImg = null;
if (SB.brand?.logo) logoImg = await new Promise(res => { const i = new Image(); i.onload = () => res(i); i.onerror = () => res(null); i.src = '/' + SB.brand.logo; });
function mark(ctx, x, y, s, a = 1) { // brand logo image, or a monogram tile
  ctx.save(); ctx.globalAlpha *= a;
  if (logoImg) { const w = s * logoImg.width / logoImg.height; ctx.drawImage(logoImg, x, y, w, s); ctx.restore(); return w; }
  ctx.shadowColor = OR; ctx.shadowBlur = s * .3; ctx.beginPath(); ctx.roundRect(x, y, s, s, s * .26); ctx.fillStyle = OR; ctx.fill(); ctx.shadowBlur = 0;
  ctx.fillStyle = '#fff'; ctx.font = `800 ${s * .62}px ${SANS_LAT}`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(SB.brand?.monogram || tr(SB.brand?.product || '?')[0], x + s / 2, y + s * .54);
  ctx.restore(); return s;
}
const project = (x, y) => { const v = gScreen.localToWorld(pxToLocal(x, y)).project(camera); return [(v.x + 1) / 2 * W, (1 - v.y) / 2 * H]; };
const quadPath = pts => { cx.beginPath(); pts.forEach(([x, y], i) => i ? cx.lineTo(x, y) : cx.moveTo(x, y)); cx.closePath(); };
function drawHeader(t) {
  const a = (1 - seg(t, END - .4, END)) * seg(t, .3, 1.0); if (a <= 0) return;
  cx.save(); cx.globalAlpha = a; cx.textBaseline = 'middle';
  let x = 66 + mark(cx, 66, 58, 40) + 20;
  const company = tr(SB.brand?.company);
  if (company) { cx.font = `600 32px ${SANS}`; cx.fillStyle = '#efe4de'; cx.fillText(company, x, 78); x += cx.measureText(company).width + 16;
    cx.font = `400 28px ${SANS_LAT}`; cx.fillStyle = 'rgba(255,255,255,.45)'; cx.fillText('×', x, 77); x += 32; }
  cx.font = `600 32px ${SANS_LAT}`; cx.fillStyle = '#efe4de'; cx.fillText(tr(SB.brand?.product), x, 77);
  cx.restore();
}
function drawStepper(t) {
  if (!STEPS.length || !SHOTS.length) return;
  const a = win(t, SHOTS[0].t0 - .2, END, .5, .4); if (a <= 0) return;
  let cur = 0; stepStart.forEach((s, i) => { if (t >= s) cur = i; });
  cx.save(); cx.globalAlpha = a; cx.textBaseline = 'middle';
  const font = `600 26px ${SANS}`; cx.font = font;
  const items = STEPS.map(s => ({ s, w: cx.measureText(s).width + 70 }));
  let x = W - 64 - (items.reduce((p, i) => p + i.w, 0) + 46 * (items.length - 1)); const y = 78;
  items.forEach((it, i) => {
    const on = i === cur, done = i < cur;
    cx.beginPath(); cx.roundRect(x, y - 24, it.w, 48, 24); cx.fillStyle = on ? OR : done ? 'rgba(255,90,31,.18)' : 'rgba(255,255,255,.06)'; cx.globalAlpha = a * (on ? .92 : 1); cx.fill(); cx.globalAlpha = a;
    cx.lineWidth = 2; cx.strokeStyle = on ? '#ffb08a' : done ? 'rgba(255,140,90,.5)' : 'rgba(255,255,255,.15)'; cx.stroke();
    cx.font = `700 24px ${SANS_LAT}`; cx.fillStyle = on ? '#fff' : done ? OR2 : 'rgba(255,255,255,.45)'; cx.fillText(done ? '✓' : String(i + 1), x + 20, y + 1);
    cx.font = font; cx.fillStyle = on ? '#fff' : done ? '#f2c8b4' : 'rgba(255,255,255,.5)'; cx.fillText(it.s, x + 48, y + 1);
    x += it.w;
    if (i < items.length - 1) { cx.strokeStyle = done ? OR : 'rgba(255,255,255,.2)'; cx.lineWidth = 2; cx.beginPath(); cx.moveTo(x + 10, y); cx.lineTo(x + 36, y); cx.stroke(); x += 46; }
  });
  cx.restore();
}
function drawCaption(t, cap) {
  const [a, b] = cap.t, f = win(t, a, b, .35, .3); if (f <= 0) return;
  const k = eout(seg(t, a, a + .55)), main = tr(cap);
  const sub = cap.sub?.[LANG] ?? (LANG !== 'en' && cap.en ? cap.en.toUpperCase() : (cap.sub?.en ?? ''));
  cx.save(); cx.globalAlpha = f; cx.textAlign = 'center'; cx.textBaseline = 'alphabetic'; cx.shadowColor = 'rgba(0,0,0,.85)'; cx.shadowBlur = 26;
  let fs = CJK ? 62 : 56; do { cx.font = `${CJK ? 700 : 600} ${fs}px ${SANS}`; cx.letterSpacing = CJK ? '4px' : '1px'; fs -= 2; } while (cx.measureText(main).width > W * .86 && fs > 24);
  cx.fillStyle = '#fff'; cx.fillText(main, W / 2, H - 130 + (1 - k) * 22);
  if (sub) { cx.shadowBlur = 10; cx.font = `500 23px ${SANS_LAT}`; cx.letterSpacing = `${6 + (1 - k) * 8}px`; cx.fillStyle = OR2; cx.globalAlpha = f * seg(t, a + .15, a + .6); cx.fillText(sub, W / 2, H - 75); }
  cx.restore();
}
function drawSpot(t, s, a) {
  const q = [[0, 0], [SCR.width, 0], [SCR.width, SCR.height], [0, SCR.height]].map(([x, y]) => project(x, y));
  const base = .38 * (1 - a) * win(t, SHOTS[0].t0, END, .4, .3);
  if (base > 0) { cx.save(); cx.globalAlpha = base; quadPath(q); cx.fillStyle = 'rgb(14,7,5)'; cx.fill(); cx.restore(); } // calm down white UI between shots
  if (a <= 0 || !s.spot) return;
  const [x0, y0, x1, y1] = s.spot, r = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]].map(([x, y]) => project(x, y));
  cx.save(); cx.globalAlpha = a;
  quadPath(q); r.slice().reverse().forEach(([x, y], i) => i ? cx.lineTo(x, y) : cx.moveTo(x, y)); cx.closePath(); cx.fillStyle = 'rgba(14,7,5,.58)'; cx.fill('evenodd');
  quadPath(r); cx.shadowColor = OR; cx.shadowBlur = 26; cx.lineWidth = 5; cx.strokeStyle = OR2; cx.stroke(); cx.shadowBlur = 0; cx.lineWidth = 2; cx.strokeStyle = '#ffd2b8'; cx.stroke();
  if (s.checks) s.checks.ys.forEach((cy, i) => {
    const k = eout(seg(t, s.checks.start + i * (s.checks.gap ?? .28), s.checks.start + .25 + i * (s.checks.gap ?? .28))); if (k <= 0) return;
    const [px, py] = project(s.checks.x, cy), [px2] = project(s.checks.x + 16, cy), sz = (px2 - px) * lerp(1.8, 1.15, k);
    cx.beginPath(); cx.roundRect(px - sz / 2, py - sz / 2, sz, sz, sz * .2); cx.fillStyle = OR; cx.fill();
    cx.strokeStyle = '#fff'; cx.lineWidth = sz * .14; cx.lineCap = 'round'; cx.beginPath(); cx.moveTo(px - sz * .25, py); cx.lineTo(px - sz * .05, py + sz * .2); cx.lineTo(px + sz * .28, py - sz * .2); cx.stroke();
  });
  const call = tr(s.call);
  if (call) {
    const top = Math.min(...r.map(p => p[1])), bottom = Math.max(...r.map(p => p[1])), left = Math.min(...r.map(p => p[0]));
    const tag = `STEP ${s.step + 1}`; cx.font = `700 22px ${SANS_LAT}`; const tagW = cx.measureText(tag).width + 28;
    cx.font = `600 ${CJK ? 34 : 31}px ${SANS}`; const tw = cx.measureText(call).width, bw = tw + tagW + 58, bh = 64;
    let bx = clamp(left, 60, W - 60 - bw), by = top - bh - 22; if (by < 165) by = bottom + 22; if (by + bh > H - 220) by = Math.max(165, top - bh - 22);
    by += (1 - eout(a)) * 14;
    cx.beginPath(); cx.roundRect(bx, by, bw, bh, 32); cx.fillStyle = 'rgba(28,15,11,.94)'; cx.fill(); cx.lineWidth = 2; cx.strokeStyle = 'rgba(255,140,90,.7)'; cx.stroke();
    cx.beginPath(); cx.roundRect(bx + 12, by + 12, tagW, bh - 24, 20); cx.fillStyle = OR; cx.fill();
    cx.textBaseline = 'middle'; cx.font = `700 22px ${SANS_LAT}`; cx.fillStyle = '#fff'; cx.fillText(tag, bx + 26, by + bh / 2 + 1);
    cx.font = `600 ${CJK ? 34 : 31}px ${SANS}`; cx.fillStyle = '#fbeee7'; cx.fillText(call, bx + 12 + tagW + 18, by + bh / 2 + 1);
  }
  cx.restore();
}
const wm = document.createElement('canvas'); wm.width = 1400; wm.height = 200; const wmx = wm.getContext('2d');
function drawLockup(t) {
  if (!SB.lockup || t < END) return;
  const a = eout(seg(t, END + .05, END + .8)), b = eout(seg(t, END + .45, END + 1.3)), c = eout(seg(t, END + .9, END + 1.7)), d = eout(seg(t, END + 1.4, END + 2.1));
  const S = 210, name = tr(SB.brand?.product), tag = tr(SB.lockup.tagline);
  cx.save(); cx.font = `600 150px ${SANS_LAT}`; const nameW = cx.measureText(name).width;
  const tagFont = CJK ? `600 46px ${SANS}` : `500 44px ${SANS}`; cx.font = tagFont; const tagW = cx.measureText(tag).width;
  const markW = logoImg ? S * logoImg.width / logoImg.height : S;
  const x0 = (W - (markW + 70 + Math.max(nameW, tagW))) / 2, y0 = H / 2 - S / 2 - 40, tx = x0 + markW + 70;
  cx.globalAlpha = a; cx.translate(x0 + markW / 2, y0 + S / 2); cx.scale(.6 + .4 * eback(a), .6 + .4 * eback(a)); mark(cx, -markW / 2, -S / 2, S); cx.setTransform(1, 0, 0, 1, 0, 0);
  wmx.reset(); wmx.font = `600 150px ${SANS_LAT}`; wmx.fillStyle = '#fbf1ec'; wmx.fillText(name, 20, 150);
  const k = seg(t, END + 1.3, END + 2.3);
  if (k > 0 && k < 1) { wmx.globalCompositeOperation = 'source-atop'; const x = lerp(-250, nameW + 300, ease(k)); const g = wmx.createLinearGradient(x - 120, 0, x + 120, 0);
    g.addColorStop(0, 'rgba(255,140,80,0)'); g.addColorStop(.5, 'rgba(255,150,90,.95)'); g.addColorStop(1, 'rgba(255,140,80,0)'); wmx.fillStyle = g; wmx.fillRect(0, 0, 1400, 200); }
  cx.globalAlpha = b; cx.drawImage(wm, tx + (1 - b) * 40 - 20, y0 - 18);
  cx.globalAlpha = c; cx.font = tagFont; cx.fillStyle = '#f4e6df'; cx.fillText(tag, tx + (1 - c) * 40, y0 + 200);
  cx.globalAlpha = c * .95; cx.font = `500 22px ${SANS_LAT}`; cx.letterSpacing = '7px'; cx.fillStyle = OR2; cx.fillText(tr(SB.lockup.sub), tx + (1 - c) * 40, y0 + 250);
  const by = tr(SB.lockup.by);
  if (by) { cx.globalAlpha = d; cx.letterSpacing = CJK ? '8px' : '3px'; cx.textAlign = 'center'; cx.font = `500 30px ${SANS}`; cx.fillStyle = 'rgba(244,230,223,.85)';
    const bw = cx.measureText(by).width; cx.textAlign = 'left'; mark(cx, W / 2 - bw / 2 - 52, H - 256, 34, d); cx.fillText(by, W / 2 - bw / 2, H - 230); }
  cx.restore();
}
function composite(t, frame) {
  const src = renderer.domElement;
  cx.globalAlpha = 1; cx.globalCompositeOperation = 'source-over'; cx.letterSpacing = '0px'; cx.drawImage(src, 0, 0);
  if (HOOK && t > HT.stamp && t < HT.stamp + .25) { const r = rng(frame * 31 + 5); for (let i = 0; i < 9; i++) { const y = r() * H, h = 8 + r() * 70, dx = (r() - .5) * 90; cx.drawImage(src, 0, y, W, h, dx, y, W, h); }
    cx.globalCompositeOperation = 'screen'; cx.fillStyle = `rgba(255,40,40,${.18 * (1 - seg(t, HT.stamp, HT.stamp + .25))})`; cx.fillRect(0, 0, W, H); cx.globalCompositeOperation = 'source-over'; }
  const s = SHOTS.find(s => t >= s.t0 && t < s.t1);
  if (s) drawSpot(t, s, Math.min(seg(t, s.pan ? s.pan[1] : s.t0 + .7, s.pan ? s.pan[1] + .35 : s.t0 + 1.1), 1 - seg(t, s.t1 - .25, s.t1)) * (1 - seg(t, END - .3, END)));
  cx.drawImage(vign, 0, 0);
  drawHeader(t); drawStepper(t);
  if (SB.note && SHOTS.length && t > SHOTS[0].t0 && t < END) { cx.save(); cx.globalAlpha = .55 * win(t, SHOTS[0].t0 + .2, END, .5, .3); cx.font = `500 20px ${SANS}`; cx.fillStyle = '#d9c3b8'; cx.textAlign = 'right'; cx.fillText('● ' + tr(SB.note), W - 64, 134); cx.restore(); }
  (SB.captions || []).forEach(c => drawCaption(t, c));
  drawLockup(t);
  cx.save(); cx.globalAlpha = .035; cx.globalCompositeOperation = 'overlay'; cx.fillStyle = cx.createPattern(grains[frame % 4], 'repeat'); cx.fillRect(0, 0, W, H); cx.restore();
  let fl = 0; for (const c of CUTS) if (t >= c && t < c + .6) fl = Math.max(fl, .3 * Math.exp(-(t - c) * 8));
  if (fl > 0) { cx.fillStyle = `rgba(255,214,190,${fl})`; cx.fillRect(0, 0, W, H); }
  const black = Math.max(1 - seg(t, 0, .5), seg(t, DUR - .7, DUR)); if (black > 0) { cx.fillStyle = `rgba(0,0,0,${black})`; cx.fillRect(0, 0, W, H); }
}

// ---------- per-frame update ----------
function update(t) {
  dotGrid.material.uniforms.uTime.value = t; dotGrid.material.uniforms.uOp.value = 1 - .5 * win(t, END, DUR + 1, .6, .1);
  const fH = HOOK ? win(t, .2, HOOK_END + .05, .4, .3) : 0; setOpacity(gHook, fH);
  if (fH > 0) { drawHook(t); hookCard.mesh.position.x = t > HT.stamp && t < HT.stamp + .45 ? Math.sin(t * 90) * .07 * (1 - seg(t, HT.stamp, HT.stamp + .45)) : 0; hookCard.mesh.scale.setScalar(lerp(.95, 1, eout(seg(t, .2, .8)))); }
  const fS = SHOTS.length ? win(t, SHOTS[0].t0 - .05, END + .1, .35, .4) : 0; setOpacity(gScreen, fS);
  const i = SHOTS.findIndex(s => t >= s.t0 && t < s.t1);
  if (fS > 0 && i >= 0) {
    const s = SHOTS[i], prev = SHOTS[i - 1];
    planeB.material.map = texFor(s, t); planeB.material.needsUpdate = true;
    const xf = prev ? seg(t, s.t0, s.t0 + .35) : 1;
    planeB.material.opacity = fS * xf; planeA.visible = xf < 1 && !!prev;
    if (prev) { planeA.material.map = texFor(prev, prev.t1 - .01); planeA.material.needsUpdate = true; planeA.material.opacity = fS; }
    const cur = shotCam(s, t), from = prev ? shotCam(prev, prev.t1) : { pos: cur.pos.clone().add(new THREE.Vector3(-2, 1, cur.d * 1.4)), look: cur.look.clone() };
    const k = ease(seg(t, s.t0, s.t0 + (prev ? .9 : 1.2))), push = 1 - .05 * seg(t, s.t0 + .9, s.t1);
    const pos = from.pos.clone().lerp(cur.pos, k), look = from.look.clone().lerp(cur.look, k);
    camera.position.copy(look.clone().add(pos.sub(look).multiplyScalar(push))); camera.lookAt(look);
  } else if (HOOK && t < HOOK_END) { camera.position.set(Math.sin(t * .3) * .3, .35, lerp(9.4, 8.6, ease(seg(t, 0, HOOK_END)))); camera.lookAt(0, .25, 0); }
  else { camera.position.set(0, 0, 12); camera.lookAt(0, 0, 0); }
}

// ---------- load + API ----------
const loader = new THREE.TextureLoader();
const all = [...new Set(SHOTS.flatMap(files))];
await Promise.all(all.map(f => new Promise((res, rej) => loader.load('/' + f, tx => { tx.colorSpace = THREE.SRGBColorSpace; tx.anisotropy = 16; textures[f] = tx; res(); }, undefined, () => rej(new Error('missing image ' + f))))));
await document.fonts.ready;
window.renderFrame = (t, frame = Math.round(t * FPS)) => { update(t); composer.render(); composite(t, frame); return comp.toDataURL('image/jpeg', .93); };
if (location.search.includes('play')) { document.body.innerHTML = ''; document.body.appendChild(comp); comp.style.width = '100vw';
  const t0 = performance.now(); const loop = () => { const t = ((performance.now() - t0) / 1000) % DUR; window.renderFrame(t); requestAnimationFrame(loop); }; loop(); }
window.ready = true;
} catch (e) { window.renderError = String(e && e.stack || e); console.error(e); }
