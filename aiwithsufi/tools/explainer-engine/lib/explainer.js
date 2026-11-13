/* Explainer runtime — a deterministic, seekable GSAP timeline on a 1920×1080 stage (or <html data-size="WxH">).
 *
 * index.html loads, in order: /engine/node_modules/gsap/dist/gsap.min.js (+ any plugins), this file, then the
 * project's scene script, which calls X.boot(async (X) => { ...build the timeline... }).
 * The renderer calls window.__seek(t) for every frame; nothing may depend on wall-clock time or Math.random.
 *
 * Core:   X.tl (paused timeline)  X.root (<svg>)  X.stage (<div>)  X.W / X.H
 * VO:     await X.loadVO() · X.line(id) → {start,end,words} · X.word(id, 'word', nth) → time the word starts
 * Sound:  X.sfx(t, type, {dur, gain, pitch}) — cue list consumed by audio/sound.py (via render.mjs --cues)
 * Build:  X.svg(tag, attrs, parent) · X.html(tag, attrs, parent) · X.scene(name, t0, t1, build) · X.every(fn(t))
 * Looks:  X.grain(opacity) · X.paper(color) → data URL · X.boil(id, scale, fps) · X.glow(id, std, color)
 *         X.shadow(id, dx, dy, blur, color, opacity) · X.torn(w, h, jag, seed) → path d · X.rand(seed)
 * Motion: X.countUp(el, from, to, t, dur, fmt) · X.typeOn(el, text, t, cps) · X.drawOn(path, t, dur)
 *         X.pop(el, t, opts) · X.cam(el) (centre-origin camera group helper)
 * Preview in a browser: ?play (real-time with audio/final.wav) · ?t=12.5 (freeze on a time)
 */
(function () {
  const X = (window.X = {});
  // stage size: 1920×1080 unless the page declares another, e.g. <html data-size="1080x1920"> for vertical reels
  [X.W, X.H] = (document.documentElement.dataset.size || '1920x1080').split('x').map(Number); X.FPS = 30;
  X._every = []; X._sfx = []; X._end = null; X.vo = { lines: [], duration: 0 };
  const NS = 'http://www.w3.org/2000/svg';

  window.addEventListener('error', (e) => { window.__error = String(e.message || e); });
  window.addEventListener('unhandledrejection', (e) => { window.__error = String(e.reason && (e.reason.stack || e.reason)); });

  for (const p of ['MorphSVGPlugin', 'DrawSVGPlugin', 'SplitText', 'CustomEase', 'MotionPathPlugin', 'CustomWiggle', 'CustomBounce', 'EasePack'])
    if (window[p]) gsap.registerPlugin(window[p]);
  gsap.ticker.lagSmoothing(0);
  gsap.config({ force3D: false });
  X.tl = gsap.timeline({ paused: true, defaults: { ease: 'power3.out', duration: 0.6 } });

  // ---------------------------------------------------------------- stage
  X.stage = document.getElementById('stage');
  X.root = document.getElementById('svg');
  X.defs = X.root.querySelector('defs') || X.root.insertBefore(document.createElementNS(NS, 'defs'), X.root.firstChild);
  function fit() {
    const s = Math.min(innerWidth / X.W, innerHeight / X.H);
    X.stage.style.transform = `scale(${s})`;
  }

  // ---------------------------------------------------------------- elements
  X.svg = (tag, attrs = {}, parent = X.root) => {
    const el = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === 'text') el.textContent = v;
      else if (k === 'style' && typeof v === 'object') Object.assign(el.style, v);
      else el.setAttribute(k, v);
    }
    if (parent) parent.appendChild(el);
    return el;
  };
  X.html = (tag, attrs = {}, parent = X.stage) => {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === 'text') el.textContent = v;
      else if (k === 'html') el.innerHTML = v;
      else if (k === 'style' && typeof v === 'object') Object.assign(el.style, v);
      else el.setAttribute(k, v);
    }
    if (parent) parent.appendChild(el);
    return el;
  };
  /** A group that exists only between t0 and t1 (hidden outside). build(g, t0, t1) adds its tweens to X.tl. */
  X.scene = (name, t0, t1, build, parent = X.root) => {
    const g = X.svg('g', { id: name }, parent);
    gsap.set(g, { autoAlpha: 0 });
    X.tl.set(g, { autoAlpha: 1 }, t0);
    if (t1 != null) X.tl.set(g, { autoAlpha: 0 }, t1);
    if (build) build(g, t0, t1);
    return g;
  };
  X.every = (fn) => X._every.push(fn);
  X.end = (t) => { X._end = t; };

  // ---------------------------------------------------------------- voiceover timing
  X.loadVO = async (p = 'data/vo.json') => {
    try { const r = await fetch(p); if (r.ok) X.vo = await r.json(); } catch (e) { /* no VO yet: silent animatic */ }
    return X.vo;
  };
  X.line = (id) => (typeof id === 'number' ? X.vo.lines[id] : X.vo.lines.find((l) => l.id === id)) || { start: 0, end: 0, words: [] };
  const norm = (s) => s.toLowerCase().replace(/[^\p{L}\p{M}\p{N}%$']/gu, '');  // Unicode-aware: CJK words match; \p{M} keeps Devanagari vowel signs
  /** Find the nth occurrence of a word or phrase ("cell wall", "债务") → [firstWord, lastWord]. Phrases may span
   *  several timed words (CJK lines are timed per character); matching ignores spaces and punctuation. */
  const findSpan = (l, w, nth) => {
    const target = norm(w);
    let k = 0;
    for (const x of l.words) if (norm(x.w).startsWith(target) && k++ === nth) return [x, x];  // single word (prefix)
    const parts = l.words.map((x) => norm(x.w));
    k = 0;
    for (let i = 0; i < parts.length; i++) {
      let acc = '';
      for (let j = i; j < parts.length && acc.length < target.length; j++) {
        acc += parts[j];
        if (acc.startsWith(target) && k++ === nth) return [l.words[i], l.words[j]];
        if (!target.startsWith(acc)) break;
      }
    }
    return null;
  };
  X.word = (id, w, nth = 0) => {
    const l = X.line(id), s = findSpan(l, w, nth);
    if (s) return s[0].start;
    console.warn(`X.word: "${w}" not found in line ${id}`);
    return l.start;
  };
  X.wordEnd = (id, w, nth = 0) => {
    const l = X.line(id), s = findSpan(l, w, nth);
    return s ? s[1].end : l.end;
  };

  // ---------------------------------------------------------------- sound cues
  X.sfx = (t, type, o = {}) => {
    X._sfx.push({ t: Math.max(0, +(+t).toFixed(3)), type, dur: o.dur ?? 0.35, gain: o.gain ?? 0.6, pitch: o.pitch ?? 1, ...o });
  };

  // ---------------------------------------------------------------- seeded randomness
  X.rand = (seed = 1) => {
    let a = seed >>> 0;
    return () => { a |= 0; a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  };

  // ---------------------------------------------------------------- looks
  /** Film grain overlay that re-rolls at `fps` (12 = filmic). */
  X.grain = (opacity = 0.08, fps = 12, blend = 'overlay') => {
    const c = document.createElement('canvas'); c.width = c.height = 256;
    const g = c.getContext('2d'), img = g.createImageData(256, 256), r = X.rand(99);
    for (let i = 0; i < img.data.length; i += 4) { const v = 128 + (r() - 0.5) * 255; img.data[i] = img.data[i + 1] = img.data[i + 2] = v; img.data[i + 3] = 255; }
    g.putImageData(img, 0, 0);
    const d = X.html('div', { style: { position: 'absolute', inset: '0', pointerEvents: 'none', backgroundImage: `url(${c.toDataURL()})`, opacity, mixBlendMode: blend, zIndex: 50 } });
    const rr = X.rand(7), offs = Array.from({ length: 64 }, () => [Math.floor(rr() * 256), Math.floor(rr() * 256)]);
    X.every((t) => { const o = offs[Math.floor(t * fps) % 64]; d.style.backgroundPosition = `${o[0]}px ${o[1]}px`; });
    return d;
  };
  /** Paper texture as a data URL (use as an <image href> or CSS background). */
  X.paper = (color = '#efe6d2', w = 960, h = 540, strength = 0.07, seed = 3) => {
    const c = document.createElement('canvas'); c.width = w; c.height = h;
    const g = c.getContext('2d'); g.fillStyle = color; g.fillRect(0, 0, w, h);
    const img = g.getImageData(0, 0, w, h), r = X.rand(seed);
    // two octaves of value noise: fibres + blotches
    const big = Array.from({ length: (w / 24 + 2) * (h / 24 + 2) }, () => r());
    const bw = Math.floor(w / 24) + 2;
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const bx = x / 24, by = y / 24, ix = Math.floor(bx), iy = Math.floor(by), fx = bx - ix, fy = by - iy;
      const b = big[iy * bw + ix] * (1 - fx) * (1 - fy) + big[iy * bw + ix + 1] * fx * (1 - fy) + big[(iy + 1) * bw + ix] * (1 - fx) * fy + big[(iy + 1) * bw + ix + 1] * fx * fy;
      const n = (r() - 0.5) * 0.6 + (b - 0.5) * 0.9;
      const i = (y * w + x) * 4, k = 1 + n * strength;
      img.data[i] *= k; img.data[i + 1] *= k; img.data[i + 2] *= k;
    }
    g.putImageData(img, 0, 0);
    return c.toDataURL('image/jpeg', 0.92);
  };
  /** Hand-drawn "line boil": displacement filter whose seed steps at `fps` (8–12 = drawn on twos/threes). */
  X.boil = (id = 'boil', scale = 3, fps = 8, freq = 0.025) => {
    const f = X.svg('filter', { id, x: '-5%', y: '-5%', width: '110%', height: '110%' }, X.defs);
    const tb = X.svg('feTurbulence', { type: 'fractalNoise', baseFrequency: freq, numOctaves: 2, seed: 1, result: 'n' }, f);
    X.svg('feDisplacementMap', { in: 'SourceGraphic', in2: 'n', scale, xChannelSelector: 'R', yChannelSelector: 'G' }, f);
    X.every((t) => tb.setAttribute('seed', 1 + (Math.floor(t * fps) % 4)));
    return `url(#${id})`;
  };
  X.glow = (id = 'glow', std = 12, color = '#ffffff', strength = 1) => {
    const f = X.svg('filter', { id, x: '-50%', y: '-50%', width: '200%', height: '200%' }, X.defs);
    X.svg('feGaussianBlur', { in: 'SourceGraphic', stdDeviation: std, result: 'b' }, f);
    X.svg('feFlood', { 'flood-color': color, 'flood-opacity': strength, result: 'c' }, f);
    X.svg('feComposite', { in: 'c', in2: 'b', operator: 'in', result: 'g' }, f);
    const m = X.svg('feMerge', {}, f);
    X.svg('feMergeNode', { in: 'g' }, m); X.svg('feMergeNode', { in: 'SourceGraphic' }, m);
    return `url(#${id})`;
  };
  X.shadow = (id = 'shadow', dx = 0, dy = 8, blur = 12, color = '#000', opacity = 0.25) => {
    const f = X.svg('filter', { id, x: '-30%', y: '-30%', width: '160%', height: '160%' }, X.defs);
    X.svg('feDropShadow', { dx, dy, stdDeviation: blur, 'flood-color': color, 'flood-opacity': opacity }, f);
    return `url(#${id})`;
  };
  X.linear = (id, stops, x1 = 0, y1 = 0, x2 = 0, y2 = 1) => {
    const g = X.svg('linearGradient', { id, x1, y1, x2, y2 }, X.defs);
    stops.forEach(([o, c, a = 1]) => X.svg('stop', { offset: o, 'stop-color': c, 'stop-opacity': a }, g));
    return `url(#${id})`;
  };
  X.radial = (id, stops, cx = 0.5, cy = 0.5, r = 0.5) => {
    const g = X.svg('radialGradient', { id, cx, cy, r }, X.defs);
    stops.forEach(([o, c, a = 1]) => X.svg('stop', { offset: o, 'stop-color': c, 'stop-opacity': a }, g));
    return `url(#${id})`;
  };
  /** Torn-paper rectangle path (cut-out collage edges). */
  X.torn = (w, h, jag = 6, seed = 1, step = 14) => {
    const r = X.rand(seed), pts = [];
    const edge = (x0, y0, x1, y1) => {
      const L = Math.hypot(x1 - x0, y1 - y0), n = Math.max(2, Math.round(L / step)), nx = -(y1 - y0) / L, ny = (x1 - x0) / L;
      for (let i = 0; i < n; i++) { const k = i / n, j = (r() - 0.5) * jag; pts.push([x0 + (x1 - x0) * k + nx * j, y0 + (y1 - y0) * k + ny * j]); }
    };
    edge(0, 0, w, 0); edge(w, 0, w, h); edge(w, h, 0, h); edge(0, h, 0, 0);
    return 'M' + pts.map((p) => p[0].toFixed(1) + ',' + p[1].toFixed(1)).join('L') + 'Z';
  };

  // ---------------------------------------------------------------- motion helpers
  X.countUp = (el, from, to, t, dur = 1.2, fmt = (v) => Math.round(v).toLocaleString('en-US'), ease = 'power2.out') => {
    const o = { v: from };
    el.textContent = fmt(from);
    X.tl.to(o, { v: to, duration: dur, ease, onUpdate: () => { el.textContent = fmt(o.v); } }, t);
  };
  X.typeOn = (el, text, t, cps = 24) => {
    const o = { n: 0 };
    el.textContent = '';
    X.tl.to(o, { n: text.length, duration: text.length / cps, ease: 'none', onUpdate: () => { el.textContent = text.slice(0, Math.round(o.n)); } }, t);
  };
  /** Stroke draw-on for a path/line/circle (no plugin needed). */
  X.drawOn = (el, t, dur = 0.8, ease = 'power2.inOut') => {
    const L = el.getTotalLength ? el.getTotalLength() : 1000;
    // start the dash a stroke-width before the path start so round/square caps don't show a dot before drawing
    const sw = parseFloat(el.getAttribute('stroke-width') || getComputedStyle(el).strokeWidth) || 0;
    gsap.set(el, { strokeDasharray: `${L} ${L + 2 * sw + 2}`, strokeDashoffset: L + sw + 1 });
    X.tl.to(el, { strokeDashoffset: 0, duration: dur, ease }, t);
  };
  /** Scale-pop entrance with overshoot, centred on the element's own box. */
  X.pop = (el, t, o = {}) => {
    gsap.set(el, { transformOrigin: o.origin || '50% 50%', scale: 0, opacity: 1 });
    X.tl.to(el, { scale: o.scale ?? 1, duration: o.dur ?? 0.45, ease: o.ease || 'back.out(2.2)' }, t);
    if (o.sfx !== false) X.sfx(t, o.sfx || 'pop', { gain: o.gain ?? 0.35, pitch: o.pitch ?? 1 });
  };
  /** Camera group: tween {x, y, scale, rotation} about the frame centre. */
  X.cam = (el) => { gsap.set(el, { svgOrigin: `${X.W / 2} ${X.H / 2}` }); return el; };

  // ---------------------------------------------------------------- boot
  X.boot = async (build) => {
    try {
      // load every declared face BEFORE building: SVG <text> may not trigger a load by itself, and text measured
      // during the build (getBBox / getComputedTextLength) must use the real font
      // the 40 MB CJK faces load only on pages that declare <html lang="zh"> (or ja)
      const cjk = /^(zh|ja)/i.test(document.documentElement.lang || '');
      await Promise.all([...document.fonts].filter((f) => cjk || !/ SC$|Noto/.test(f.family.replace(/"/g, ''))).map((f) => f.load().catch(() => {})));
      await document.fonts.ready;
      await build(X);
      await document.fonts.ready;
      fit(); addEventListener('resize', fit);
      const dur = X._end ?? Math.max(X.tl.duration(), X.vo.duration || 0);
      X.duration = dur;
      window.__duration = dur;
      // GSAP does not render zero-duration sets placed exactly at 0 on seek(0): use a hair above zero
      window.__seek = (t) => { X.tl.seek(Math.max(t, 1e-4), false); for (const f of X._every) f(t); };
      window.__cues = () => ({ duration: dur, sfx: X._sfx.slice().sort((a, b) => a.t - b.t) });
      window.__seek(0);
      const q = new URLSearchParams(location.search);
      if (q.has('t')) window.__seek(+q.get('t'));
      if (q.has('play')) preview(dur);
      window.__ready = true;
    } catch (e) {
      console.error(e);
      window.__error = String(e && (e.stack || e));
    }
  };

  function preview(dur) {
    const a = new Audio('audio/final.wav');
    let t0 = null;
    const btn = X.html('button', { text: '▶ play', style: { position: 'fixed', left: '12px', top: '12px', zIndex: 99, font: '16px sans-serif' } }, document.body);
    btn.onclick = () => { a.currentTime = 0; a.play().catch(() => {}); t0 = performance.now(); btn.remove(); };
    const loop = () => {
      if (t0 != null) { const t = a.duration && !a.paused ? a.currentTime : (performance.now() - t0) / 1000; window.__seek(Math.min(t, dur)); }
      requestAnimationFrame(loop);
    };
    loop();
  }
})();
