#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const {performance} = require('node:perf_hooks');
const {spawnSync} = require('node:child_process');

const HELP = `Record an explicitly selected page with an agent-written Playwright scenario.

node record.cjs --scenario /absolute/scenario.cjs --output /absolute/new-run \\
  --url https://example.test [--playwright-module /path/to/playwright] \\
  [--executable /path/to/browser | --channel chrome] [--headed] \\
  [--width 1600 --height 1000] [--timeout-ms 300000]

Scenario: module.exports = async ({page, context, browser, baseUrl, outputDir, mark}) => { ... }
The helper opens --url once. The trusted scenario supplies all further UI actions.
await mark('name', {page, screenshot: true, note: 'optional explanation'});

Environment fallbacks: PRODUCT_DEMO_PLAYWRIGHT_MODULE (or PLAYWRIGHT_MODULE),
PRODUCT_DEMO_BROWSER_EXECUTABLE. Otherwise resolve playwright/playwright-core
from the scenario project, working directory, or this helper's dependencies.

Output: manifest.json, events.jsonl, screenshots/, raw/. Existing recording
artifacts are refused. Use a new output directory for each take. Marks use wall
time, not exact encoded-video timestamps; verify trim points against the video.
Only use this helper when the applicable browser-routing instructions permit
regular Playwright. It does not install browsers, authenticate, or seed an app.
`;

function fail(code) { const error = new Error(code); error.code = code; throw error; }
function options(argv) {
  const values = {}, booleans = new Set(['headed', 'help']);
  const names = new Set(['scenario', 'output', 'url', 'playwright-module', 'executable', 'channel', 'width', 'height', 'timeout-ms']);
  for (let i = 0; i < argv.length; i++) {
    let token = argv[i];
    if (token === '-h') token = '--help';
    const compact = /^--(width|height)(\d+)$/.exec(token);
    if (compact) token = `--${compact[1]}=${compact[2]}`;
    if (!token.startsWith('--')) fail('UNEXPECTED_ARGUMENT');
    const at = token.indexOf('=');
    const name = token.slice(2, at < 0 ? undefined : at);
    if (Object.hasOwn(values, name)) fail('DUPLICATE_OPTION');
    if (booleans.has(name)) {
      if (at >= 0) fail('BOOLEAN_OPTION_TAKES_NO_VALUE');
      values[name] = true; continue;
    }
    if (!names.has(name)) fail('UNKNOWN_OPTION');
    const value = at < 0 ? argv[++i] : token.slice(at + 1);
    if (!value || value.startsWith('--')) fail('OPTION_VALUE_REQUIRED');
    values[name] = value;
  }
  if (values.help) return values;
  for (const name of ['scenario', 'output', 'url']) if (!values[name]) fail(`MISSING_${name.toUpperCase()}`);
  for (const name of ['scenario', 'output']) if (!path.isAbsolute(values[name])) fail('ABSOLUTE_PATH_REQUIRED');
  for (const [name, fallback, min, max] of [['width', 1600, 320, 7680], ['height', 1000, 240, 4320], ['timeout-ms', 300000, 100, 86400000]]) {
    const raw = values[name] ?? String(fallback);
    if (!/^\d+$/.test(raw) || Number(raw) < min || Number(raw) > max) fail('INVALID_NUMERIC_OPTION');
    values[name] = Number(raw);
  }
  if (values.executable && values.channel) fail('CHOOSE_EXECUTABLE_OR_CHANNEL');
  if (!values.channel && !values.executable) values.executable = process.env.PRODUCT_DEMO_BROWSER_EXECUTABLE;
  if (values.executable) {
    values.executable = path.resolve(values.executable);
    if (!fs.statSync(values.executable).isFile()) fail('BROWSER_EXECUTABLE_NOT_A_FILE');
  }
  if (!fs.statSync(values.scenario).isFile()) fail('SCENARIO_NOT_A_FILE');
  const url = new URL(values.url);
  if (!['http:', 'https:', 'file:'].includes(url.protocol)) fail('URL_PROTOCOL_NOT_SUPPORTED');
  if (url.username || url.password) fail('URL_USERINFO_NOT_ALLOWED');
  values.url = url.href;
  return values;
}

function canonicalFuturePath(value) {
  let existing = path.resolve(value); const suffix = [];
  while (!fs.existsSync(existing)) { suffix.unshift(path.basename(existing)); const parent = path.dirname(existing); if (parent === existing) fail('OUTPUT_PARENT_MISSING'); existing = parent; }
  return path.join(fs.realpathSync(existing), ...suffix);
}
function within(parent, candidate) { const relative = path.relative(parent, candidate); return relative === '' || (!relative.startsWith(`..${path.sep}`) && relative !== '..' && !path.isAbsolute(relative)); }
function reserveOutput(value) {
  const skillRoot = fs.realpathSync(path.resolve(__dirname, '..'));
  if (within(skillRoot, canonicalFuturePath(value))) fail('OUTPUT_INSIDE_SKILL_DIRECTORY');
  fs.mkdirSync(value, {recursive: true});
  const output = fs.realpathSync(value);
  if (within(skillRoot, output)) fail('OUTPUT_INSIDE_SKILL_DIRECTORY');
  for (const name of ['manifest.json', 'events.jsonl', 'raw', 'screenshots']) if (fs.existsSync(path.join(output, name))) fail('OUTPUT_RECORDING_ALREADY_EXISTS');
  const lock = path.join(output, '.recording.lock');
  const fd = fs.openSync(lock, 'wx', 0o600); fs.closeSync(fd);
  try {
    for (const name of ['manifest.json', 'events.jsonl', 'raw', 'screenshots']) if (fs.existsSync(path.join(output, name))) fail('OUTPUT_RECORDING_ALREADY_EXISTS');
    fs.mkdirSync(path.join(output, 'raw')); fs.mkdirSync(path.join(output, 'screenshots'));
  } catch (error) { fs.unlinkSync(lock); throw error; }
  return {output, lock};
}
function loadPlaywright(opts) {
  const explicit = opts['playwright-module'] || process.env.PRODUCT_DEMO_PLAYWRIGHT_MODULE || process.env.PLAYWRIGHT_MODULE;
  for (const specifier of explicit ? [explicit] : ['playwright', 'playwright-core']) {
    let resolved;
    try { resolved = require.resolve(specifier, {paths: [path.dirname(opts.scenario), process.cwd(), __dirname]}); }
    catch (error) { if (!explicit && error.code === 'MODULE_NOT_FOUND') continue; fail('PLAYWRIGHT_MODULE_NOT_FOUND'); }
    const loaded = require(resolved); const playwright = loaded.chromium ? loaded : loaded.default;
    if (typeof playwright?.chromium?.launch !== 'function') fail('PLAYWRIGHT_MODULE_INVALID');
    return {playwright, resolved};
  }
  fail('PLAYWRIGHT_NOT_INSTALLED_USE_MODULE_OPTION');
}

function safeUrl(value) {
  try { const url = new URL(value); url.username = ''; url.password = ''; for (const key of [...url.searchParams.keys()]) url.searchParams.set(key, '[redacted]'); if (url.hash.includes('=')) url.hash = '[redacted]'; return url.href; }
  catch { return '[unavailable URL]'; }
}
function safeMessage(value) {
  return String(value).replace(/https?:\/\/[^\s"'<>]+/g, safeUrl)
    .replace(/\bBearer\s+[^\s"']+/gi, 'Bearer [redacted]')
    .replace(/((?:api[_-]?key|access[_-]?token|password|secret)\s*[=:]\s*)[^\s,;]+/gi, '$1[redacted]').slice(0, 1500);
}
function errorInfo(error) { return {name: error?.name || 'Error', code: error?.code || 'RECORDING_ERROR', message: safeMessage(error?.message || error)}; }
async function bounded(promise, milliseconds, code) {
  let timer;
  try { return await Promise.race([promise, new Promise((_, reject) => { timer = setTimeout(() => { const error = new Error(code); error.code = code; reject(error); }, milliseconds); })]); }
  finally { clearTimeout(timer); }
}
function videoProbe(file) {
  const result = spawnSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-show_entries', 'stream=codec_type,width,height', '-of', 'json', file], {encoding: 'utf8', timeout: 10000});
  if (result.error?.code === 'ENOENT') return {status: 'unavailable', reason: 'ffprobe not on PATH'};
  if (result.error || result.status !== 0) return {status: 'failed'};
  try {
    const data = JSON.parse(result.stdout), stream = data.streams.find(item => item.codec_type === 'video');
    const seconds = Number(data.format.duration);
    if (!stream || !Number.isFinite(seconds) || seconds <= 0) return {status: 'failed'};
    return {status: 'inspected', width: stream.width, height: stream.height, durationSeconds: seconds};
  } catch { return {status: 'failed'}; }
}

async function record(opts, reservation) {
  const {output: outputDir, lock} = reservation;
  const origin = performance.now(), elapsed = () => Number(((performance.now() - origin) / 1000).toFixed(3));
  const startedAt = new Date().toISOString(), expected = {width: opts.width, height: opts.height};
  const eventsFile = path.join(outputDir, 'events.jsonl');
  const event = data => fs.appendFileSync(eventsFile, JSON.stringify({elapsedSeconds: elapsed(), ...data}) + '\n', {mode: 0o600});
  const pages = [], marks = [], observations = [], errors = [], warnings = [], pending = new Set();
  const pageMap = new Map(); let browser, context, primary, resolvedModule, scenarioCompleted = false, contextClosed = false, interrupted = false;
  const binding = `__productDemoObserve_${crypto.randomBytes(8).toString('hex')}`;
  const trackPending = promise => { pending.add(promise); promise.finally(() => pending.delete(promise)); };
  const rememberError = (phase, error) => { const item = {phase, ...errorInfo(error)}; errors.push(item); event({type: 'error', ...item}); };
  const observation = (page, data) => {
    const info = pageMap.get(page); if (!info) return;
    const item = {pageId: info.id, elapsedSeconds: elapsed(), ...data};
    item.viewportMatchesExpected = data.viewport?.width === expected.width && data.viewport?.height === expected.height;
    item.screenMatchesExpected = data.screen?.width === expected.width && data.screen?.height === expected.height;
    observations.push(item); event({type: 'geometry', ...item});
    if (!item.viewportMatchesExpected || !item.screenMatchesExpected) {
      if (!warnings.some(old => old.code === 'GEOMETRY_REQUIRES_REVIEW' && old.pageId === info.id)) warnings.push({code: 'GEOMETRY_REQUIRES_REVIEW', pageId: info.id, note: 'Observed dimensions differ from the requested recording. Inspect the actual video, especially fullscreen; no size correction was applied.'});
    }
  };
  async function observe(page, kind, install = false) {
    if (page.isClosed()) return;
    try {
      const data = await page.evaluate(({binding, install, kind}) => {
        const read = label => ({kind: label, viewport: {width: innerWidth, height: innerHeight}, screen: {width: screen.width, height: screen.height}, devicePixelRatio, fullscreen: !!document.fullscreenElement});
        if (install && !window[`${binding}_installed`]) {
          window[`${binding}_installed`] = true;
          const emit = label => { const send = window[binding]; if (typeof send === 'function') void send(read(label)).catch(() => {}); };
          addEventListener('resize', () => emit('resize'), {passive: true});
          document.addEventListener('fullscreenchange', () => emit('fullscreenchange'));
        }
        return read(kind);
      }, {binding, install, kind});
      observation(page, data);
    } catch (error) { event({type: 'geometry-unavailable', pageId: pageMap.get(page)?.id, reason: safeMessage(error.message)}); }
  }
  function trackPage(page) {
    if (pageMap.has(page)) return;
    const info = {id: `page-${String(pages.length + 1).padStart(3, '0')}`, createdElapsedSeconds: elapsed(), navigations: [], videoHandle: page.video()};
    pages.push(info); pageMap.set(page, info);
    page.on('pageerror', error => rememberError(`pageerror:${info.id}`, error));
    page.on('console', message => { if (message.type() === 'error') rememberError(`console:${info.id}`, new Error(message.text())); });
    page.on('framenavigated', frame => { if (frame === page.mainFrame()) { const item = {url: safeUrl(frame.url()), elapsedSeconds: elapsed()}; info.navigations.push(item); event({type: 'navigation', pageId: info.id, ...item}); } });
    page.on('domcontentloaded', () => trackPending(observe(page, 'domcontentloaded', true)));
    page.on('close', () => { info.closedElapsedSeconds = elapsed(); event({type: 'page-closed', pageId: info.id}); });
  }
  async function mark(name, details = {}) {
    if (typeof name !== 'string' || !name.trim()) fail('MARK_NAME_REQUIRED');
    const page = details.page || primary, info = pageMap.get(page);
    if (!info || page.isClosed()) fail('MARK_REQUIRES_OPEN_RECORDED_PAGE');
    const item = {name: name.slice(0, 160), pageId: info.id, elapsedSeconds: elapsed(), approximatePageSeconds: Number((elapsed() - info.createdElapsedSeconds).toFixed(3)), url: safeUrl(page.url())};
    if (details.note) item.note = safeMessage(details.note);
    await observe(page, `mark:${item.name}`);
    if (details.screenshot !== false) {
      const slug = name.replace(/[^a-zA-Z0-9_-]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 60) || 'mark';
      item.screenshot = path.join(outputDir, 'screenshots', `${String(marks.length + 1).padStart(3, '0')}-${slug}.png`);
      await page.screenshot({path: item.screenshot, fullPage: false});
    }
    marks.push(item); event({type: 'mark', ...item}); return item;
  }

  let rejectInterrupt;
  const interruption = new Promise((_, reject) => { rejectInterrupt = reject; });
  // Suppress an early-signal unhandled rejection while Chromium is still launching.
  interruption.catch(() => {});
  const signalHandler = signal => { interrupted = true; const error = new Error(signal); error.code = 'INTERRUPTED'; rejectInterrupt(error); };
  const onSigint = () => signalHandler('SIGINT'), onSigterm = () => signalHandler('SIGTERM');
  process.on('SIGINT', onSigint); process.on('SIGTERM', onSigterm);
  try {
    event({type: 'recording-start', url: safeUrl(opts.url), requestedDimensions: expected});
    const loaded = loadPlaywright(opts); resolvedModule = loaded.resolved;
    const exported = require(opts.scenario), scenario = typeof exported === 'function' ? exported : exported.default;
    if (typeof scenario !== 'function') fail('SCENARIO_MUST_EXPORT_FUNCTION');
    browser = await loaded.playwright.chromium.launch({headless: !opts.headed, timeout: 30000, ...(opts.executable ? {executablePath: opts.executable} : {}), ...(opts.channel ? {channel: opts.channel} : {})});
    context = await browser.newContext({viewport: expected, screen: expected, deviceScaleFactor: 1, acceptDownloads: true, recordVideo: {dir: path.join(outputDir, 'raw'), size: expected}});
    context.on('page', trackPage);
    await context.exposeBinding(binding, ({page}, data) => observation(page, data));
    primary = await context.newPage(); trackPage(primary);
    primary.setDefaultTimeout(30000); primary.setDefaultNavigationTimeout(30000);
    await primary.goto(opts.url, {waitUntil: 'domcontentloaded'});
    await observe(primary, 'entry', true); await mark('entry');
    if (interrupted) fail('INTERRUPTED');
    const execution = Promise.resolve().then(() => scenario({page: primary, context, browser, baseUrl: opts.url, outputDir, mark}));
    await bounded(Promise.race([execution, interruption]), opts['timeout-ms'], 'SCENARIO_TIMEOUT');
    scenarioCompleted = true;
    if (!primary.isClosed()) { await mark('scenario-complete'); await primary.waitForTimeout(250); }
  } catch (error) {
    rememberError('scenario-or-runtime', error);
    if (primary && !primary.isClosed()) { try { await mark('failure'); } catch (captureError) { rememberError('failure-screenshot', captureError); } }
  } finally {
    if (context) {
      for (const page of context.pages()) { try { await bounded(page.close(), 15000, 'PAGE_CLOSE_TIMEOUT'); } catch (error) { rememberError('page-close', error); } }
      try { await bounded(context.close(), 20000, 'CONTEXT_CLOSE_TIMEOUT'); contextClosed = true; } catch (error) { rememberError('context-close', error); }
    }
    if (browser) { try { await bounded(browser.close(), 15000, 'BROWSER_CLOSE_TIMEOUT'); } catch (error) { rememberError('browser-close', error); } }
    await Promise.allSettled([...pending]);
    process.removeListener('SIGINT', onSigint); process.removeListener('SIGTERM', onSigterm);
  }

  for (const info of pages) {
    try {
      if (!info.videoHandle || !contextClosed) fail('VIDEO_NOT_FINALIZED');
      const file = await bounded(info.videoHandle.path(), 10000, 'VIDEO_FINALIZE_TIMEOUT');
      const stat = fs.statSync(file); if (!stat.isFile() || !stat.size) fail('VIDEO_EMPTY');
      const probe = videoProbe(file);
      info.video = {path: file, bytes: stat.size, finalizedAfterContextClose: true, probe};
      if (probe.status === 'failed') fail('VIDEO_PROBE_FAILED');
      if (probe.status === 'inspected' && (probe.width !== expected.width || probe.height !== expected.height)) warnings.push({code: 'ENCODED_DIMENSIONS_DIFFER', pageId: info.id});
    } catch (error) { rememberError(`video:${info.id}`, error); }
    delete info.videoHandle;
  }
  if (!pages.some(info => info.video)) rememberError('video', new Error('NO_FINALIZED_VIDEO'));
  try { fs.unlinkSync(lock); } catch (error) { rememberError('recording-lock-release', error); }
  const failed = !scenarioCompleted || !contextClosed || errors.length > 0;
  const manifest = {
    version: 1, status: failed ? 'failed' : warnings.length ? 'recorded_needs_review' : 'recorded',
    startedAt, completedAt: new Date().toISOString(), durationWallSeconds: elapsed(),
    baseUrl: safeUrl(opts.url), scenarioPath: opts.scenario, outputDir,
    browser: {engine: 'chromium', headed: !!opts.headed, channel: opts.channel || null, executablePath: opts.executable || null, playwrightModule: resolvedModule || null},
    requestedDimensions: {viewport: expected, screen: expected, video: expected},
    scenarioCompleted, contextClosed, pages, marks, observations, errors, warnings,
    fullscreen: {exercised: observations.some(item => item.fullscreen), observationCount: observations.filter(item => item.kind === 'fullscreenchange').length, resizedToForceSuccess: false},
    storageInitialization: 'none; no addInitScript or storage writes by this helper',
    timebase: 'Monotonic wall time since recorder setup; page-relative marks are approximate, not encoded-frame timestamps. Verify edit points in the saved video.',
    visualReview: 'not_performed', eventsFile,
  };
  // This is the only manifest write, after pages/context/browser have closed and video artifacts were read back.
  fs.writeFileSync(path.join(outputDir, 'manifest.json'), JSON.stringify(manifest, null, 2) + '\n', {flag: 'wx', mode: 0o600});
  process.stdout.write(JSON.stringify({status: manifest.status, manifest: path.join(outputDir, 'manifest.json'), pages: pages.length, errors: errors.length, warnings: warnings.length}) + '\n');
  if (failed) process.exitCode = interrupted ? 130 : 1;
}

(async () => {
  const opts = options(process.argv.slice(2));
  if (opts.help) { process.stdout.write(HELP); return; }
  await record(opts, reserveOutput(opts.output));
})().catch(error => { process.stderr.write(JSON.stringify({status: 'failed', ...errorInfo(error)}) + '\n'); process.exitCode = 1; });
