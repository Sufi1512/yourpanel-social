// Explainer engine renderer: serves a project, opens it in headless Edge/Chrome, seeks its GSAP timeline
// frame by frame (window.__seek(t)), screenshots each frame and pipes it to ffmpeg.
//
//   node render.mjs <project> [--fps 30] [--scale 1] [--workers 4] [--from s] [--to s] [--out out/video.mp4]
//   node render.mjs <project> --cues                 write data/cues.json (sfx cue list + duration) and exit
//   node render.mjs <project> --stills 1.5,4,9       PNG stills into out/stills/
//   node render.mjs <project> --sheet 24             evenly spaced stills tiled into out/sheet.jpg
//   node render.mjs <project> --serve [--port 8123]  just serve it (open http://127.0.0.1:8123/?play to preview)
//
// The project folder holds index.html (loads /engine/lib/*.js and GSAP from /engine/node_modules/gsap/dist/),
// data/vo.json (from audio/tts.py) and audio/final.wav (from audio/sound.py) when they exist.
// Browser: EXPLAINER_BROWSER=msedge|chrome|chromium (default msedge, then chrome), or EXPLAINER_BROWSER_PATH=<exe>.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { spawn, spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const ENGINE = path.dirname(fileURLToPath(import.meta.url));
const argv = process.argv.slice(2);
const PROJECT = path.resolve(argv[0] || '.');
const opt = (k, d) => { const i = argv.indexOf('--' + k); return i >= 0 && argv[i + 1] && !argv[i + 1].startsWith('--') ? argv[i + 1] : d; };
const flag = (k) => argv.includes('--' + k);
const FPS = +opt('fps', 30), SCALE = +opt('scale', 1), WORKERS = +opt('workers', 4);
const FF = process.env.FFMPEG_PATH || require('ffmpeg-static');
// frame size: <html data-size="1080x1920"> in the project's index.html (vertical reels), else 1920×1080
const SIZE = (() => { try { const m = fs.readFileSync(path.join(PROJECT, 'index.html'), 'utf8').match(/data-size="(\d+)x(\d+)"/);
  if (m) return [+m[1], +m[2]]; } catch {} return [1920, 1080]; })();

const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.css': 'text/css',
  '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp',
  '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf', '.otf': 'font/otf', '.wav': 'audio/wav', '.mp3': 'audio/mpeg', '.mp4': 'video/mp4' };

function serve(port = 0) {
  const srv = http.createServer((req, res) => {
    let u = decodeURIComponent(req.url.split('?')[0]);
    let file = u.startsWith('/engine/') ? path.join(ENGINE, u.slice(8)) : path.join(PROJECT, u === '/' ? 'index.html' : u);
    if (!file.startsWith(ENGINE) && !file.startsWith(PROJECT)) { res.writeHead(403); return res.end(); }
    fs.readFile(file, (err, buf) => {
      if (err) { res.writeHead(404); return res.end('not found'); }
      res.writeHead(200, { 'Content-Type': MIME[path.extname(file).toLowerCase()] || 'application/octet-stream', 'Cache-Control': 'no-store' });
      res.end(buf);
    });
  });
  return new Promise((ok) => srv.listen(port, '127.0.0.1', () => ok(srv)));
}

async function launch() {
  const { chromium } = await import('playwright-core');
  const args = ['--hide-scrollbars', '--force-color-profile=srgb', '--font-render-hinting=none', '--disable-lcd-text', '--autoplay-policy=no-user-gesture-required'];
  if (process.env.EXPLAINER_BROWSER_PATH) return chromium.launch({ executablePath: process.env.EXPLAINER_BROWSER_PATH, headless: true, args });
  let last;
  for (const ch of (process.env.EXPLAINER_BROWSER || 'msedge,chrome,chromium').split(',')) {
    try { return await chromium.launch({ channel: ch === 'chromium' ? undefined : ch, headless: true, args }); } catch (e) { last = e; }
  }
  throw last;
}

async function openPage(browser, url) {
  const page = await browser.newPage({ viewport: { width: Math.round(SIZE[0] * SCALE), height: Math.round(SIZE[1] * SCALE) } });
  const errs = [];
  page.on('pageerror', (e) => errs.push(String(e)));
  page.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') console.log('[page]', m.text()); });
  await page.goto(url);
  await page.waitForFunction(() => window.__ready === true || window.__error, null, { timeout: 120000 }).catch(() => {});
  const e = await page.evaluate(() => window.__error);
  if (e || errs.length) throw new Error('page failed: ' + (e || errs.join('\n')));
  return page;
}

const seek = (page, t) => page.evaluate((t) => window.__seek(t), t);
const shot = (page, type = 'jpeg') => page.screenshot(type === 'jpeg' ? { type, quality: 93 } : { type });

function ffmpegChunk(out, fps) {
  const args = ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-c:v', 'mjpeg', '-framerate', String(fps), '-i', 'pipe:0',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', opt('crf', '17'), '-pix_fmt', 'yuv420p', '-r', String(fps), out];
  return spawn(FF, args, { stdio: ['pipe', 'inherit', 'inherit'] });
}

async function renderVideo(browser, url, dur) {
  const from = +opt('from', 0), to = Math.min(+opt('to', dur), dur);
  const n = Math.round((to - from) * FPS);
  const outFile = path.resolve(PROJECT, opt('out', 'out/video.mp4'));
  const tmp = path.join(PROJECT, 'out', '.chunks');
  fs.mkdirSync(tmp, { recursive: true });
  const W = Math.max(1, Math.min(WORKERS, Math.ceil(n / 30)));
  const per = Math.ceil(n / W);
  const t0 = Date.now();
  let done = 0;
  const chunks = await Promise.all(Array.from({ length: W }, async (_, w) => {
    const a = w * per, b = Math.min(n, a + per);
    const file = path.join(tmp, `chunk_${String(w).padStart(2, '0')}.mp4`);
    if (a >= b) return null;
    const page = await openPage(browser, url);
    const ff = ffmpegChunk(file, FPS);
    for (let i = a; i < b; i++) {
      await seek(page, from + i / FPS);
      const buf = await shot(page);
      if (!ff.stdin.write(buf)) await new Promise((ok) => ff.stdin.once('drain', ok));
      if (++done % 60 === 0) {
        const el = (Date.now() - t0) / 1000;
        process.stdout.write(`\r${done}/${n} frames  ${(done / el).toFixed(1)} fps  eta ${((n - done) / (done / el)).toFixed(0)} s   `);
      }
    }
    ff.stdin.end();
    await new Promise((ok) => ff.on('close', ok));
    await page.close();
    return file;
  }));
  const list = path.join(tmp, 'list.txt');
  fs.writeFileSync(list, chunks.filter(Boolean).map((f) => `file '${f.replace(/\\/g, '/')}'`).join('\n'));
  const audio = path.join(PROJECT, 'audio', 'final.wav');
  const args = ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list];
  const withAudio = fs.existsSync(audio) && !flag('noaudio');
  if (withAudio) args.push('-ss', String(from), '-t', String(to - from), '-i', audio, '-map', '0:v:0', '-map', '1:a:0', '-c:a', 'aac', '-b:a', '192k');
  args.push('-c:v', 'copy', '-movflags', '+faststart', outFile);
  fs.mkdirSync(path.dirname(outFile), { recursive: true });
  const r = spawnSync(FF, args, { stdio: 'inherit' });
  if (r.status !== 0) throw new Error('ffmpeg concat/mux failed');
  fs.rmSync(tmp, { recursive: true, force: true });
  console.log(`\n${outFile}  ${n} frames @${FPS} in ${((Date.now() - t0) / 1000).toFixed(0)} s${withAudio ? ' + audio' : ' (no audio)'}`);
}

async function main() {
  const srv = await serve(+opt('port', 0));
  const url = `http://127.0.0.1:${srv.address().port}/`;
  if (flag('serve')) { console.log(`serving ${PROJECT} at ${url}  (preview: ${url}?play)`); return; }
  const browser = await launch();
  try {
    const page = await openPage(browser, url);
    const dur = await page.evaluate(() => window.__duration);
    if (flag('cues')) {
      const cues = await page.evaluate(() => window.__cues());
      fs.mkdirSync(path.join(PROJECT, 'data'), { recursive: true });
      fs.writeFileSync(path.join(PROJECT, 'data', 'cues.json'), JSON.stringify(cues, null, 1));
      console.log(`data/cues.json: ${cues.sfx.length} sfx cues, duration ${cues.duration.toFixed(2)} s`);
    } else if (opt('stills') || opt('sheet')) {
      const dir = path.join(PROJECT, 'out', 'stills');
      fs.mkdirSync(dir, { recursive: true });
      const ts = opt('stills') ? opt('stills').split(',').map(Number)
        : Array.from({ length: +opt('sheet') }, (_, i) => (dur - 0.05) * i / (+opt('sheet') - 1));
      const files = [];
      for (const [i, t] of ts.entries()) {
        await seek(page, t);
        const f = path.join(dir, opt('sheet') ? `sheet_${String(i).padStart(3, '0')}.png` : `still_${t.toFixed(2)}.png`);
        fs.writeFileSync(f, await shot(page, 'png'));
        files.push(f);
      }
      if (opt('sheet')) {
        const cols = 6, rows = Math.ceil(ts.length / cols);
        spawnSync(FF, ['-y', '-loglevel', 'error', '-framerate', '1', '-i', path.join(dir, 'sheet_%03d.png'), '-vf', `scale=320:-1,tile=${cols}x${rows}:padding=4:color=0x181818`, '-frames:v', '1', path.join(PROJECT, 'out', 'sheet.jpg')], { stdio: 'inherit' });
        files.forEach((f) => fs.rmSync(f));
        console.log('out/sheet.jpg  times: ' + ts.map((t) => t.toFixed(1)).join(' '));
      } else console.log(files.join('\n'));
    } else {
      await page.close();
      await renderVideo(browser, url, dur);
    }
  } finally {
    await browser.close();
    srv.close();
  }
}

main().catch((e) => { console.error(e); process.exit(1); });
