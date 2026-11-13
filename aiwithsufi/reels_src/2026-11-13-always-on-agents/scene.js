// @aiwithsufi · "The Night Shift: Always-on AI" (13 Nov 2026) · Glow Sketch on explainer-engine. One narrator, no hosts.
X.boot(async (X) => {
  await X.loadVO();
  const C = { BG: '#2c182e', CARD: '#3c243e', CARD2: '#442a46', LINE: '#5c405e', TEXT: '#f8eef2', MUTED: '#cebcca', ACC: '#f0a4b8', MINT: '#9fe3c9', RED: '#ff7a8f', SUN: '#ffd59a' };
  const F = 'Montserrat, sans-serif';
  const GLOW = X.glow('glow', 7, C.ACC, 0.95), GLOW2 = X.glow('glow2', 16, C.ACC, 0.75), SOFT = X.glow('soft', 5, '#ffffff', 0.35), GMINT = X.glow('gmint', 8, C.MINT, 0.9);
  const BLUR = (() => { const f = X.svg('filter', { id: 'blur', x: '-50%', y: '-50%', width: '200%', height: '200%' }, X.defs); X.svg('feGaussianBlur', { stdDeviation: 9 }, f); return 'url(#blur)'; })();
  const L = X.vo.lines, byId = Object.fromEntries(L.map((l) => [l.id, l]));
  const W = (id, w, n = 0) => X.word(id, w, n), S = (id) => byId[id].start, E = (id) => byId[id].end;
  const TOTAL = X.vo.duration;

  // ------------------------------------------------------------ helpers
  const T = (g, x, y, s, size = 34, o = {}) => X.svg('text', { x, y, text: s, fill: o.fill || C.TEXT, 'font-family': F, 'font-size': size,
    'font-weight': o.w || 700, 'text-anchor': o.a || 'start', 'letter-spacing': o.ls || 0, 'dominant-baseline': 'middle', ...(o.attrs || {}) }, g);
  const R = (g, x, y, w, h, r, o = {}) => {
    const at = o.attrs || {};
    if (at.filter && o.fill && o.fill !== 'none') {
      const { filter, ...rest } = at;
      const f = X.svg('rect', { x, y, width: w, height: h, rx: r, fill: o.fill, stroke: 'none', ...rest }, g);
      const st = X.svg('rect', { x, y, width: w, height: h, rx: r, fill: 'none', stroke: o.stroke || C.ACC, 'stroke-width': o.sw ?? 4, filter, ...rest }, g);
      st._fill = f; return st;
    }
    return X.svg('rect', { x, y, width: w, height: h, rx: r, fill: o.fill || 'none', stroke: o.stroke || C.ACC, 'stroke-width': o.sw ?? 4, ...at }, g);
  };
  const P = (g, d, o = {}) => X.svg('path', { d, fill: o.fill || 'none', stroke: o.stroke || C.ACC, 'stroke-width': o.sw ?? 5, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', ...(o.attrs || {}) }, g);
  const draw = (el, t, d = 0.8) => { X.drawOn(el, t, d); if (el._fill) { gsap.set(el._fill, { opacity: 0 }); X.tl.to(el._fill, { opacity: 1, duration: d * 0.8 }, t + d * 0.3); } };
  const fin = (el, t, d = 0.5, dy = 24) => { X.tl.fromTo(el, { opacity: 0, y: dy }, { opacity: 1, y: 0, duration: d, ease: 'power3.out', immediateRender: false }, t); gsap.set(el, { opacity: 0 }); };
  const fout = (el, t, d = 0.4) => X.tl.to(el, { opacity: 0, duration: d, ease: 'power2.in' }, t);
  const slam = (el, t, sfx = 'impact', gain = 0.35) => { X.tl.fromTo(el, { scale: 2.4, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.35, ease: 'power4.out', immediateRender: false }, t); gsap.set(el, { opacity: 0, transformOrigin: '50% 50%' }); if (sfx) X.sfx(t, sfx, { gain }); };
  const whip = (el, t, from = 900) => { X.tl.fromTo(el, { x: from, skewX: -18, opacity: 0 }, { x: 0, skewX: 0, opacity: 1, duration: 0.5, ease: 'expo.out', immediateRender: false }, t); gsap.set(el, { opacity: 0 }); X.sfx(t, 'whoosh', { gain: 0.3 }); };
  const check = (g, x, y, s = 1, col = C.MINT) => P(g, `M${x - 14 * s},${y} L${x - 4 * s},${y + 11 * s} L${x + 16 * s},${y - 12 * s}`, { stroke: col, sw: 6 });
  const flash = (t, op = 0.55) => { const f = X.svg('rect', { x: 0, y: 0, width: 1080, height: 1920, fill: '#fff', opacity: 0 }, flashLayer); X.tl.fromTo(f, { opacity: op }, { opacity: 0, duration: 0.35, ease: 'power2.out', immediateRender: false }, t); };
  const cloudD = 'M300,760 C230,760 220,640 310,630 C300,520 450,480 500,560 C540,470 700,480 720,580 C820,560 870,660 800,720 C860,770 820,860 740,850 L340,850 C270,860 250,780 300,760 Z';
  const laptop = (g, cx, cy, s = 1) => { const lg = X.svg('g', {}, g); const scr = X.svg('g', {}, lg); gsap.set(scr, { svgOrigin: `${cx} ${cy}` });
    R(scr, cx - 145 * s, cy - 190 * s, 290 * s, 190 * s, 14, { fill: C.CARD, sw: 5 }); P(lg, `M${cx - 190 * s},${cy} L${cx + 190 * s},${cy} L${cx + 220 * s},${cy + 35 * s} L${cx - 220 * s},${cy + 35 * s} Z`, { sw: 5, fill: C.CARD }); return { lg, scr }; };
  const padlock = (g, cx, cy, s = 1) => { const pg = X.svg('g', {}, g); const sh = P(pg, `M${cx - 50 * s},${cy} v-50 a50,50 0 0 1 100,0 v50`, { sw: 14 * s });
    R(pg, cx - 85 * s, cy - 5 * s, 170 * s, 140 * s, 22, { fill: C.ACC, sw: 0 }); X.svg('circle', { cx, cy: cy + 55 * s, r: 14 * s, fill: C.BG }, pg); R(pg, cx - 5 * s, cy + 58 * s, 10 * s, 36 * s, 4, { fill: C.BG, sw: 0 }); return { pg, sh }; };

  // scene windows
  const SC = []; L.forEach((l) => { if (!SC.length || SC[SC.length - 1].id !== l.scene) SC.push({ id: l.scene, s: l.start }); });
  SC.forEach((s, i) => { s.t0 = i ? s.s - 0.35 : 0; s.t1 = i + 1 < SC.length ? SC[i + 1].s - 0.35 : TOTAL + 1; });
  const win = Object.fromEntries(SC.map((s) => [s.id, s]));
  const scene = (id, build) => X.scene(id, win[id].t0, win[id].t1, (g, t0, t1) => {
    X.tl.fromTo(g, { opacity: 0 }, { opacity: 1, duration: 0.25, immediateRender: false }, t0);
    if (t1 < TOTAL) X.tl.to(g, { opacity: 0, duration: 0.2 }, t1 - 0.2);
    const cam = X.svg('g', {}, g); X.cam(cam);  // slow push-in on every scene
    X.tl.fromTo(cam, { scale: 1 }, { scale: 1.035, duration: Math.max(0.5, Math.min(t1, TOTAL) - t0), ease: 'none', immediateRender: false }, t0);
    build(cam, t0, t1);
  }, mainLayer);

  // ------------------------------------------------------------ background
  X.svg('rect', { x: 0, y: 0, width: 1080, height: 1920, fill: C.BG });
  X.svg('rect', { x: 0, y: 0, width: 1080, height: 1920, fill: X.radial('bgr', [[0, '#4a2a4c', 1], [1, C.BG, 1]], 0.5, 0.38, 0.75) });
  const dawn = X.svg('rect', { x: 0, y: 0, width: 1080, height: 1920, fill: X.linear('dawn', [[0, '#6b3a5a', 1], [0.6, '#c9787e', 0.55], [1, C.BG, 0]]), opacity: 0 });
  const dots = X.svg('g', { opacity: 0.15 });
  for (let y = 40; y < 1980; y += 60) for (let x = 30; x < 1080; x += 60) X.svg('circle', { cx: x, cy: y, r: 2, fill: C.MUTED }, dots);
  X.every((t) => dots.setAttribute('transform', `translate(0 ${-(t * 6) % 60})`));
  const rs = X.rand(5), sp = Array.from({ length: 22 }, () => [rs() * 1080, rs() * 1250 + 250, 1.5 + rs() * 3, rs() * 6]);
  const spEl = sp.map(([x, y, r]) => X.svg('circle', { cx: x, cy: y, r, fill: C.ACC, filter: SOFT }));
  X.every((t) => spEl.forEach((el, i) => { const [, y, , ph] = sp[i]; el.setAttribute('cy', ((y - t * 14 + 1920) % 1500) + 250); el.setAttribute('opacity', 0.12 + 0.25 * (0.5 + 0.5 * Math.sin(t * 1.3 + ph))); }));
  X.grain(0.05, 12);
  const top = X.svg('g', {});
  R(top, 90, 58, 900, 8, 4, { fill: C.LINE, sw: 0 });
  const prog = R(top, 90, 58, 1, 8, 4, { fill: C.ACC, sw: 0 });
  X.every((t) => prog.setAttribute('width', Math.max(1, 900 * Math.min(1, t / TOTAL))));
  T(top, 540, 118, '@aiwithsufi', 28, { a: 'middle', fill: C.MUTED, w: 600 });
  // "example story" tag while Sara's story runs
  const tag = X.svg('g', {}); R(tag, 400, 168, 280, 46, 23, { fill: C.CARD, sw: 2, stroke: C.MUTED }); T(tag, 540, 192, 'EXAMPLE STORY', 20, { a: 'middle', fill: C.MUTED, w: 800, ls: 3 });
  gsap.set(tag, { opacity: 0 }); X.tl.to(tag, { opacity: 1, duration: 0.4 }, win.sara.t0 + 0.2); X.tl.to(tag, { opacity: 0, duration: 0.3 }, win.real.t0);

  const mainLayer = X.svg('g', {});
  const flashLayer = X.svg('g', {});

  // ------------------------------------------------------------ COLD OPEN
  scene('cold', (g) => {
    // bedroom at night
    const room = X.svg('g', {}, g);
    const winR = R(room, 150, 300, 300, 360, 20, { sw: 4, stroke: C.MUTED }); X.drawOn(winR, 0.05, 1.0);
    P(room, 'M300,300 L300,660 M150,480 L450,480', { sw: 3, stroke: C.MUTED });
    const moon = P(room, 'M380,360 a40,40 0 1 0 30,62 a32,32 0 1 1 -30,-62 Z', { stroke: C.SUN, sw: 4, attrs: { filter: SOFT } }); X.drawOn(moon, 0.4, 0.8);
    const bed = P(room, 'M80,1110 L80,900 M80,1010 L700,1010 L700,1110 M80,1040 L700,1040 M120,1010 C120,960 240,960 250,1010', { sw: 5, stroke: C.MUTED }); X.drawOn(bed, 0.2, 1.2);
    const zz = T(room, 300, 900, 'z z z', 40, { fill: C.MUTED, w: 800 }); fin(zz, 0.9, 0.6); X.tl.to(zz, { y: -50, opacity: 0.2, duration: 4, ease: 'none' }, 1.5);
    const stand = R(room, 760, 960, 230, 150, 14, { sw: 4, stroke: C.MUTED }); X.drawOn(stand, 0.3, 0.9);
    const clk = T(room, 875, 1060, '3:00', 40, { a: 'middle', fill: C.RED, w: 800, attrs: { filter: SOFT } }); fin(clk, W('a1', 'three'), 0.3, 0);
    const ph = X.svg('g', {}, room);
    const phb = R(ph, 820, 880, 110, 70, 12, { fill: C.CARD, sw: 4 });
    const phGlow = X.svg('circle', { cx: 875, cy: 915, r: 120, fill: X.radial('pg', [[0, C.ACC, 0.6], [1, C.ACC, 0]]), opacity: 0 }, room);
    const tw = W('a1', 'working');
    X.tl.to(phGlow, { opacity: 1, duration: 0.3 }, tw); X.tl.to(phb, { attr: { fill: C.ACC }, duration: 0.2 }, tw); X.sfx(tw, 'notif', { gain: 0.45 });
    X.tl.to(ph, { x: 4, duration: 0.05, yoyo: true, repeat: 7 }, tw);
    // camera dives into the phone, a beam shoots to the cloud
    X.tl.to(room, { scale: 3, x: -1500, y: -1700, duration: 0.9, ease: 'power3.in' }, E('a1') - 0.3);
    X.tl.to(room, { opacity: 0, duration: 0.2 }, E('a1') + 0.45);
    flash(E('a1') + 0.5, 0.4);
    // chat box that shuts itself
    const ch = X.svg('g', {}, g); gsap.set(ch, { svgOrigin: '540 760' });
    R(ch, 140, 660, 800, 200, 30, { fill: C.CARD, sw: 4 });
    T(ch, 190, 760, 'Ask anything…', 40, { fill: C.MUTED, w: 600 });
    const cur = R(ch, 520, 730, 5, 60, 2, { fill: C.ACC, sw: 0 });
    X.every((t) => cur.setAttribute('opacity', Math.floor(t * 2.5) % 2));
    fin(ch, S('a2') - 0.1, 0.3, 0);
    const np = W('a2', 'prompt');
    const glitch = (t0) => { for (let k = 0; k < 6; k++) X.tl.set(ch, { x: (k % 2 ? -1 : 1) * (8 + k * 3), skewX: k % 2 ? 6 : -6 }, t0 + k * 0.04); X.tl.set(ch, { x: 0, skewX: 0 }, t0 + 0.26); X.sfx(t0, 'glitch', { gain: 0.35 }); };
    glitch(np - 0.3);
    X.tl.to(ch, { scaleY: 0.02, duration: 0.25, ease: 'power3.in' }, np); X.tl.to(ch, { scaleX: 0, opacity: 0, duration: 0.2 }, np + 0.25);
    const npT = T(g, 540, 760, 'NO PROMPT', 110, { a: 'middle', w: 900, attrs: { filter: GLOW2 } }); slam(npT, np + 0.15);
    const st = W('a2', 'started');
    X.tl.to(npT, { opacity: 0, scale: 0.6, duration: 0.3 }, S('a3') - 0.3);
    const dot = X.svg('circle', { cx: 540, cy: 760, r: 16, fill: '#fff', filter: GLOW2, opacity: 0 }, g);
    X.tl.to(dot, { opacity: 1, duration: 0.1 }, st); X.tl.to(dot, { attr: { cx: 900, cy: 320 }, duration: 0.5, ease: 'power2.in' }, st + 0.1); X.tl.to(dot, { opacity: 0, duration: 0.1 }, st + 0.6);
    X.sfx(st, 'zoom_out', { gain: 0.3 });
    // title + blurred padlock teaser
    const ti = T(g, 540, 560, 'ALWAYS-ON AI', 104, { a: 'middle', w: 900, attrs: { filter: GLOW2 } }); slam(ti, S('a3') - 0.15);
    const pl = padlock(g, 540, 860, 1.2); pl.pg.setAttribute('filter', BLUR); fin(pl.pg, W('a3', 'one'), 0.5, 0);
    const qm = T(g, 540, 1120, 'never allowed', 46, { a: 'middle', fill: C.ACC, w: 800 }); fin(qm, W('a3', 'never'), 0.4);
    X.sfx(W('a3', 'never'), 'heartbeat', { gain: 0.4 });
  });

  // ------------------------------------------------------------ MEET SARA
  scene('sara', (g, t0) => {
    const sg = X.svg('g', {}, g);
    // Sara, line art
    const sara = X.svg('g', {}, sg);
    const head = X.svg('circle', { cx: 290, cy: 560, r: 70, fill: 'none', stroke: C.ACC, 'stroke-width': 6, filter: GLOW }, sara);
    const hair = P(sara, 'M220,560 C210,470 370,470 360,560 C370,620 380,660 350,690 M220,560 C210,620 200,660 230,690', { sw: 6 });
    const bodyP = P(sara, 'M180,880 C190,720 390,720 400,880', { sw: 6 });
    const eyes = [265, 315].map((x) => X.svg('ellipse', { cx: x, cy: 565, rx: 6, ry: 7, fill: C.TEXT }, sara));
    const smile = P(sara, 'M268,600 Q290,618 312,600', { sw: 5, stroke: C.TEXT });
    [head, hair, bodyP].forEach((p, i) => X.drawOn(p, S('b1') + i * 0.15, 0.8));
    fin(smile, S('b1') + 0.6, 0.3, 0); eyes.forEach((e) => fin(e, S('b1') + 0.6, 0.3, 0));
    X.every((t) => { const b = ((t + 0.4) % 3.3) < 0.12; eyes.forEach((e) => e.setAttribute('ry', b ? 1 : 7)); });
    const nm = T(sg, 290, 940, 'SARA', 40, { a: 'middle', fill: C.ACC, w: 900, ls: 4 }); fin(nm, W('b1', 'sara'), 0.4);
    // her shop
    const shop = X.svg('g', {}, sg);
    const sh1 = P(shop, 'M600,560 L960,560 L940,500 L620,500 Z', { sw: 5 });
    const sh2 = P(shop, 'M620,560 L620,840 L940,840 L940,560 M700,840 L700,700 L780,700 L780,840 M820,620 L910,620 L910,690 L820,690 Z', { sw: 5, stroke: C.MUTED });
    const aw = P(shop, 'M600,560 q22,40 45,0 q22,40 45,0 q22,40 45,0 q22,40 45,0 q22,40 45,0 q22,40 45,0 q22,40 45,0 q22,40 45,0', { sw: 4 });
    [sh1, aw, sh2].forEach((p, i) => X.drawOn(p, W('b1', 'shop') - 0.3 + i * 0.12, 0.7));
    X.sfx(W('b1', 'shop') - 0.2, 'scribble', { gain: 0.25 });
    const sl = T(shop, 780, 900, 'online shop', 30, { a: 'middle', fill: C.MUTED, w: 600 }); fin(sl, W('b1', 'shop'), 0.4);
    // goal card
    const gc = X.svg('g', {}, sg);
    R(gc, 120, 1000, 840, 110, 26, { fill: C.CARD, sw: 4, attrs: { filter: GLOW } });
    T(gc, 160, 1055, 'GOAL', 24, { fill: C.ACC, w: 900, ls: 3 });
    const gt = T(gc, 260, 1056, '', 36, { w: 800 });
    fin(gc, W('b2', 'goal') - 0.2, 0.35); X.typeOn(gt, 'Never run out of stock', W('b2', 'never'), 22); X.sfx(W('b2', 'never'), 'type', { dur: 1.0, gain: 0.3 });
    // laptop closes, a dot escapes
    const cl = W('b2', 'closed');
    X.tl.to(sg, { opacity: 0, y: -60, duration: 0.4 }, cl - 0.5);
    const lp = laptop(g, 540, 1150, 1); fin(lp.lg, cl - 0.4, 0.35);
    X.tl.to(lp.scr, { scaleY: 0.05, duration: 0.4, ease: 'power3.in' }, cl + 0.1); X.sfx(cl + 0.45, 'thud', { gain: 0.35 });
    const dot = X.svg('circle', { cx: 540, cy: 1130, r: 15, fill: '#fff', filter: GLOW2, opacity: 0 }, g);
    X.tl.to(dot, { opacity: 1, duration: 0.15 }, E('b2') - 0.2);
    X.tl.to(dot, { attr: { cy: 1060 }, duration: 0.6, yoyo: true, repeat: 1, ease: 'sine.inOut' }, E('b2'));
    // into the cloud
    const tc = W('b3', 'cloud');
    const cloud = P(g, cloudD, { sw: 6, attrs: { filter: GLOW } }); gsap.set(cloud, { attr: { transform: 'translate(540 520) scale(1.3) translate(-540 -680)' } });
    X.drawOn(cloud, tc - 0.4, 0.9); X.sfx(tc - 0.4, 'swoosh', { gain: 0.3 });
    X.tl.to(dot, { attr: { cx: 540, cy: 520 }, duration: 0.8, ease: 'power2.inOut' }, tc - 0.1); X.sfx(tc - 0.1, 'riser', { dur: 0.8, gain: 0.25 });
    const pc = X.svg('g', {}, g); R(pc, 470, 470, 140, 95, 10, { fill: C.CARD2, sw: 5, stroke: C.MINT }); P(pc, 'M520,590 L560,590 M540,565 L540,590', { stroke: C.MINT, sw: 5 });
    const scrn = R(pc, 485, 485, 110, 65, 6, { fill: C.MINT, sw: 0, attrs: { opacity: 0 } });
    X.pop(pc, W('b3', 'computer') - 0.1, { sfx: 'pop' }); X.tl.to(scrn, { attr: { opacity: 0.85 }, duration: 0.3 }, W('b3', 'computer') + 0.2);
    X.tl.to(dot, { opacity: 0, duration: 0.2 }, W('b3', 'computer'));
    const kg = X.svg('g', {}, g); R(kg, 380, 760, 320, 70, 35, { fill: C.CARD2, sw: 3, stroke: C.MINT }); T(kg, 540, 796, 'keeps going', 32, { a: 'middle', fill: C.MINT, w: 800 });
    X.pop(kg, W('b3', 'keeps'), { sfx: 'ding' });
    const orb = X.svg('circle', { cx: 540, cy: 520, r: 9, fill: C.MINT, filter: GMINT, opacity: 0 }, g);
    X.tl.to(orb, { opacity: 1, duration: 0.2 }, W('b3', 'keeps'));
    X.every((t) => { const a = t * 3; orb.setAttribute('cx', 540 + 120 * Math.cos(a)); orb.setAttribute('cy', 520 + 60 * Math.sin(a)); });
  });

  // ------------------------------------------------------------ THE LOOP
  scene('loop', (g, t0) => {
    const cy = X.svg('g', {}, g); gsap.set(cy, { svgOrigin: '540 720' });
    const circ = X.svg('circle', { cx: 540, cy: 720, r: 270, fill: 'none', stroke: C.ACC, 'stroke-width': 5, filter: GLOW }, cy);
    X.drawOn(circ, t0 + 0.1, 1.0);
    const nodes = [['Trigger', 540, 450, 'trigger'], ['Think', 810, 720, 'thinks'], ['Act', 540, 990, 'acts'], ['Check in', 270, 720, 'checks']];
    nodes.forEach(([s, x, y, w]) => { const ng = X.svg('g', {}, cy); const c = X.svg('circle', { cx: x, cy: y, r: 84, fill: C.BG, stroke: C.ACC, 'stroke-width': 4 }, ng);
      const tx = T(ng, x, y + 2, s, s.length > 6 ? 27 : 32, { a: 'middle', w: 800 }); const tw = W('c1', w);
      X.pop(ng, tw - 0.15, { sfx: 'blip_up', gain: 0.3 }); X.tl.to(c, { attr: { fill: C.ACC }, duration: 0.2 }, tw); X.tl.to(tx, { attr: { fill: C.BG }, duration: 0.2 }, tw);
      X.tl.to(c, { attr: { fill: C.BG }, duration: 0.4 }, tw + 0.5); X.tl.to(tx, { attr: { fill: C.TEXT }, duration: 0.4 }, tw + 0.5); });
    const dot = X.svg('circle', { cx: 540, cy: 450, r: 14, fill: '#fff', filter: GLOW2 }, cy);
    const ts = S('c2');
    X.every((t) => { const u = Math.max(0, t - t0), v = Math.max(0, t - ts); const a = -Math.PI / 2 + u * 1.0 + v * v * 2.2;
      dot.setAttribute('cx', 540 + 270 * Math.cos(a)); dot.setAttribute('cy', 720 + 270 * Math.sin(a)); });
    X.tl.to(cy, { rotation: 0, scale: 0.92, duration: 1.5, ease: 'power2.inOut' }, ts);
    // triggers flying past while it "watches"
    ['7:00 AM', 'New email', 'Stock -1', 'New order', 'Price change'].forEach((s, i) => {
      const fg = X.svg('g', {}, g); const y = 300 + (i % 2) * 860; R(fg, -110, y - 32, 220, 64, 32, { fill: C.CARD2, sw: 3 }); T(fg, 0, y + 1, s, 26, { a: 'middle', w: 800 });
      X.tl.fromTo(fg, { x: 1250, opacity: 1 }, { x: -200, duration: 1.4, ease: 'none', immediateRender: false }, ts - 0.4 + i * 0.35); gsap.set(fg, { x: 1250 });
    });
    X.sfx(ts, 'riser', { dur: 1.5, gain: 0.3 });
  });

  // ------------------------------------------------------------ 3:07
  scene('night', (g, t0) => {
    const big = T(g, 540, 720, '3:06', 230, { a: 'middle', w: 300, fill: C.TEXT, attrs: { filter: GLOW2 } });
    fin(big, t0 + 0.1, 0.2, 0);
    const sev = W('d1', 'seven');
    const big2 = T(g, 540, 720, '3:07', 230, { a: 'middle', w: 300, fill: C.RED, attrs: { filter: GLOW2 } }); gsap.set(big2, { opacity: 0, transformOrigin: '50% 50%' });
    X.tl.set(big, { opacity: 0 }, sev); X.tl.fromTo(big2, { scaleY: 0.2, opacity: 1 }, { scaleY: 1, duration: 0.25, immediateRender: false }, sev);
    flash(sev, 0.35); X.sfx(sev, 'heartbeat', { gain: 0.55 }); X.sfx(sev, 'tick', { gain: 0.5 });
    X.tl.to(big2, { scale: 0.6, opacity: 0, duration: 0.4, ease: 'power3.in' }, E('d1') + 0.1);
    // stock bar
    const sb = X.svg('g', {}, g);
    T(sb, 120, 420, 'BEST SELLER · STOCK', 26, { fill: C.MUTED, w: 800, ls: 2 });
    R(sb, 120, 450, 840, 46, 23, { fill: C.CARD, sw: 2, stroke: C.LINE });
    const bar = R(sb, 120, 450, 620, 46, 23, { fill: C.MINT, sw: 0 });
    const cnt = T(sb, 960, 420, '62 left', 30, { a: 'end', w: 900, fill: C.MINT });
    fin(sb, S('d2') - 0.2, 0.4);
    const five = W('d2', 'five');
    const o = { v: 62 };
    X.tl.to(o, { v: 5, duration: 1.0, ease: 'power2.in', onUpdate: () => { cnt.textContent = Math.round(o.v) + ' left'; bar.setAttribute('width', Math.max(20, 620 * o.v / 62)); } }, five - 0.9);
    X.tl.to([bar], { attr: { fill: C.RED }, duration: 0.3 }, five); X.tl.to(cnt, { attr: { fill: C.RED }, duration: 0.3 }, five); X.sfx(five, 'error', { gain: 0.35 });
    // supplier page + cart
    const pg = X.svg('g', {}, g);
    R(pg, 120, 560, 840, 560, 30, { fill: C.CARD, sw: 4, attrs: { filter: GLOW } });
    R(pg, 120, 560, 840, 70, 30, { fill: C.CARD2, sw: 0 }); [160, 190, 220].forEach((x) => X.svg('circle', { cx: x, cy: 595, r: 8, fill: C.LINE }, pg));
    T(pg, 260, 596, 'supplier.example', 24, { fill: C.MUTED, w: 600 });
    T(pg, 170, 680, 'Best seller × 50', 36, { w: 800 });
    const boxes = X.svg('g', {}, pg);
    const cart = P(pg, 'M560,780 L610,780 L650,950 L860,950 L900,820 L630,820', { sw: 6, stroke: C.TEXT });
    X.svg('circle', { cx: 680, cy: 990, r: 16, fill: 'none', stroke: C.TEXT, 'stroke-width': 5 }, pg); X.svg('circle', { cx: 830, cy: 990, r: 16, fill: 'none', stroke: C.TEXT, 'stroke-width': 5 }, pg);
    whip(pg, W('d2', 'supplier') - 0.1);
    const fills = W('d2', 'fills');
    [0, 1, 2].forEach((i) => { const b = R(boxes, 680 + i * 60, 860, 52, 52, 6, { fill: C.ACC, sw: 0 });
      X.tl.fromTo(b, { y: -260, opacity: 0 }, { y: 0, opacity: 1, duration: 0.45, ease: 'bounce.out', immediateRender: false }, fills + i * 0.18); gsap.set(b, { opacity: 0 }); X.sfx(fills + 0.3 + i * 0.18, 'drop', { gain: 0.3 }); });
    const pay = X.svg('g', {}, pg); const payB = R(pay, 170, 1010, 300, 80, 40, { fill: C.ACC, sw: 0 }); T(pay, 320, 1051, 'Pay now', 32, { a: 'middle', w: 900, fill: C.BG });
    fin(pay, W('d2', 'checkout') - 0.3, 0.3);
    // cursor glides to Pay
    const cur = P(g, 'M0,0 L0,46 L12,34 L22,56 L30,52 L20,31 L36,31 Z', { fill: '#fff', stroke: C.BG, sw: 3 });
    gsap.set(cur, { x: 900, y: 1250, opacity: 0 });
    X.tl.to(cur, { opacity: 1, duration: 0.2 }, W('d2', 'checkout') - 0.3);
    X.tl.to(cur, { x: 330, y: 1040, duration: 1.0, ease: 'power2.inOut' }, W('d2', 'checkout') - 0.2);
    // ...and STOPS: freeze
    const stp = S('d3');
    const dim = X.svg('rect', { x: 0, y: 0, width: 1080, height: 1920, fill: '#120a13', opacity: 0 }, g);
    X.tl.to(dim, { opacity: 0.6, duration: 0.15 }, stp + 0.25);
    const pz = X.svg('g', {}, g); R(pz, 450, 640, 60, 200, 12, { fill: C.TEXT, sw: 0 }); R(pz, 570, 640, 60, 200, 12, { fill: C.TEXT, sw: 0 });
    slam(pz, stp + 0.3, 'thud', 0.5);
    const ft = T(g, 540, 930, 'STOPPED', 70, { a: 'middle', w: 900, fill: C.TEXT, ls: 8 }); fin(ft, stp + 0.5, 0.3, 0);
  });

  // ------------------------------------------------------------ QUIZ
  scene('quiz', (g, t0) => {
    const ch = X.svg('g', {}, g); R(ch, 360, 250, 360, 54, 27, { fill: C.CARD, sw: 3 }); T(ch, 540, 278, 'PAUSE & GUESS', 24, { a: 'middle', ls: 3, fill: C.ACC, w: 900 }); slam(ch, t0 + 0.1, 'blip_up', 0.3);
    const qt = T(g, 540, 400, 'Why did the agent stop?', 54, { a: 'middle', w: 900 }); fin(qt, W('q1', 'why'), 0.4);
    const opts = [['It crashed', 'crashed'], ['It needs Sara’s yes', 'needs'], ['It ran out of time', 'ran']];
    const cards = opts.map(([o, w], i) => {
      const cg = X.svg('g', {}, g), y = 520 + i * 160;
      const bx = R(cg, 120, y, 840, 128, 30, { fill: C.CARD, sw: 4 });
      const lc = X.svg('circle', { cx: 196, cy: y + 64, r: 38, fill: C.CARD2, stroke: C.ACC, 'stroke-width': 4 }, cg);
      T(cg, 196, y + 66, 'ABC'[i], 34, { a: 'middle', w: 900, fill: C.ACC }); T(cg, 262, y + 66, o, 38, { w: 700 });
      const tw = W('q1', w) - 0.35; X.tl.fromTo(cg, { opacity: 0, x: 120 }, { opacity: 1, x: 0, duration: 0.35, ease: 'back.out(1.6)', immediateRender: false }, tw); gsap.set(cg, { opacity: 0 }); X.sfx(tw, 'pop', { gain: 0.3, pitch: 1 + i * 0.1 });
      return { cg, bx, lc };
    });
    const cdS = E('q1') + 0.1, cdE = S('q2') - 0.1;
    const cd = X.svg('g', {}, g);
    X.svg('circle', { cx: 540, cy: 1110, r: 66, fill: C.CARD, stroke: C.LINE, 'stroke-width': 8 }, cd);
    const arc = X.svg('circle', { cx: 540, cy: 1110, r: 66, fill: 'none', stroke: C.ACC, 'stroke-width': 8, transform: 'rotate(-90 540 1110)', filter: GLOW }, cd);
    const num = T(cd, 540, 1113, '3', 56, { a: 'middle', w: 900 });
    const Lc = 2 * Math.PI * 66; arc.setAttribute('stroke-dasharray', `${Lc} ${Lc}`);
    fin(cd, E('q1') - 0.2, 0.3, 0);
    X.every((t) => { const k = Math.min(1, Math.max(0, (t - cdS) / (cdE - cdS))); arc.setAttribute('stroke-dashoffset', Lc * k); num.textContent = k >= 1 ? '!' : String(Math.max(1, 3 - Math.floor(k * 3))); });
    [0, 1, 2].forEach((i) => X.sfx(cdS + i * (cdE - cdS) / 3, 'tick', { gain: 0.4 }));
    const rv = S('q2');
    fout(cd, rv, 0.25);
    cards.forEach((c, i) => {
      if (i === 1) { X.tl.to(c.bx, { attr: { fill: C.ACC, stroke: '#fff' }, duration: 0.3 }, rv); X.tl.to(c.cg.querySelectorAll('text'), { attr: { fill: C.BG }, duration: 0.3 }, rv); X.tl.to(c.lc, { attr: { fill: '#fff' }, duration: 0.3 }, rv);
        const ck = check(c.cg, 900, 520 + 160 + 64, 1.5, C.BG); X.drawOn(ck, rv + 0.2, 0.3); }
      else X.tl.to(c.cg, { opacity: 0.25, duration: 0.4 }, rv);
    });
    X.sfx(rv, 'success', { gain: 0.45 });
    const stmp = X.svg('g', {}, g); gsap.set(stmp, { svgOrigin: '540 1110' });
    R(stmp, 210, 1050, 660, 120, 18, { sw: 7, stroke: C.MINT }); T(stmp, 540, 1112, 'WAITING FOR SARA', 50, { a: 'middle', w: 900, fill: C.MINT, ls: 3 });
    X.tl.fromTo(stmp, { scale: 2.2, rotation: -14, opacity: 0 }, { scale: 1, rotation: -6, opacity: 1, duration: 0.3, ease: 'power4.in', immediateRender: false }, W('q2', 'human') - 0.15); gsap.set(stmp, { opacity: 0 });
    X.sfx(W('q2', 'human') + 0.15, 'stamp', { gain: 0.55 });
  });

  // ------------------------------------------------------------ MORNING
  scene('morning', (g, t0) => {
    X.tl.to(dawn, { opacity: 1, duration: 1.5 }, t0); X.tl.to(dawn, { opacity: 0, duration: 0.6 }, win.morning.t1 - 0.4);
    const sun = X.svg('circle', { cx: 540, cy: 1250, r: 120, fill: C.SUN, filter: X.glow('gsun', 30, C.SUN, 0.8), opacity: 0.9 }, g);
    X.tl.fromTo(sun, { attr: { cy: 1300 } }, { attr: { cy: 420 }, duration: 2.2, ease: 'power2.out', immediateRender: false }, t0);
    X.tl.to(sun, { attr: { r: 70 }, opacity: 0.55, duration: 0.8 }, t0 + 2);
    X.tl.to(sun, { attr: { cx: 880, cy: 330 }, duration: 0.8 }, t0 + 2);
    X.sfx(t0, 'chime', { gain: 0.35 });
    const ph = X.svg('g', {}, g);
    R(ph, 300, 400, 480, 820, 54, { fill: 'rgba(60,36,62,.85)', sw: 5, attrs: { filter: GLOW } });
    T(ph, 540, 470, '7:00', 70, { a: 'middle', w: 300 });
    const brief = X.svg('g', {}, ph); R(brief, 330, 530, 420, 300, 26, { fill: C.CARD2, sw: 2, stroke: C.LINE });
    T(brief, 360, 570, 'MORNING BRIEF', 22, { fill: C.ACC, w: 900, ls: 2 }); T(brief, 360, 620, '1 order waiting', 32, { w: 800 }); T(brief, 360, 660, 'for your approval', 32, { w: 800 });
    T(brief, 360, 715, 'Best seller × 50', 24, { fill: C.MUTED, w: 600 });
    const ap = X.svg('g', {}, brief); const apb = R(ap, 360, 750, 360, 60, 30, { fill: C.ACC, sw: 0 }); T(ap, 540, 781, 'Approve', 28, { a: 'middle', w: 900, fill: C.BG });
    X.tl.fromTo(ph, { y: 700, opacity: 0 }, { y: 0, opacity: 1, duration: 0.6, ease: 'power3.out', immediateRender: false }, W('e1', 'sara') - 0.2); gsap.set(ph, { opacity: 0 });
    fin(brief, W('e1', 'brief') - 0.2, 0.4); X.sfx(W('e1', 'brief'), 'notif', { gain: 0.4 });
    // finger tap
    const tap = W('e2', 'tap');
    const fg = X.svg('g', {}, g); const ring = X.svg('circle', { cx: 0, cy: 0, r: 22, fill: 'none', stroke: '#fff', 'stroke-width': 4 }, fg); X.svg('circle', { cx: 0, cy: 0, r: 22, fill: 'rgba(255,255,255,.85)', filter: SOFT }, fg);
    gsap.set(fg, { x: 950, y: 1250, opacity: 0 }); X.tl.to(fg, { opacity: 1, duration: 0.2 }, tap - 0.8); X.tl.to(fg, { x: 560, y: 781, duration: 0.7, ease: 'power2.inOut' }, tap - 0.75);
    X.tl.fromTo(ring, { attr: { r: 22 }, opacity: 0.9 }, { attr: { r: 75 }, opacity: 0, duration: 0.5, immediateRender: false }, tap); X.tl.to(fg, { opacity: 0, duration: 0.3 }, tap + 0.5);
    X.tl.to(apb, { attr: { fill: C.MINT }, duration: 0.2 }, tap); X.sfx(tap, 'click', { gain: 0.5 }); X.sfx(tap + 0.2, 'success', { gain: 0.4 });
    // one-time card flips in
    const one = W('e2', 'one');
    const cdg = X.svg('g', {}, g); gsap.set(cdg, { svgOrigin: '540 1000' });
    R(cdg, 320, 870, 440, 260, 26, { fill: C.CARD2, sw: 4, stroke: C.MINT, attrs: { filter: GMINT } });
    R(cdg, 360, 920, 70, 50, 8, { fill: C.SUN, sw: 0 });
    T(cdg, 360, 1020, '••••  ••••  ••••', 30, { fill: C.MUTED, w: 700 });
    T(cdg, 360, 1080, 'SINGLE USE', 30, { fill: C.MINT, w: 900, ls: 4 });
    X.tl.to(brief, { opacity: 0.25, duration: 0.3 }, one - 0.3);
    X.tl.fromTo(cdg, { scaleX: 0, opacity: 1 }, { scaleX: 1, duration: 0.45, ease: 'back.out(2)', immediateRender: false }, one - 0.1); gsap.set(cdg, { opacity: 0 }); X.sfx(one - 0.1, 'coin', { gain: 0.4 });
  });

  // ------------------------------------------------------------ IT'S REAL
  scene('real', (g, t0) => {
    const sf = T(g, 540, 640, 'SCIENCE FICTION?', 76, { a: 'middle', w: 900, fill: C.MUTED }); fin(sf, t0 + 0.1, 0.3, 0);
    const strike = P(g, 'M150,640 L930,640', { sw: 12, stroke: C.RED }); X.drawOn(strike, W('f1', 'isn') - 0.1, 0.35); X.sfx(W('f1', 'isn'), 'swoosh', { gain: 0.3 });
    const real = T(g, 540, 800, 'IT’S REAL', 120, { a: 'middle', w: 900, attrs: { filter: GLOW2 } }); slam(real, W('f1', 'fiction'));
    X.tl.to([sf, strike, real], { opacity: 0, duration: 0.25 }, S('f2') - 0.1);
    const card = (y, t, title, date, rows, avatar) => { const cg = X.svg('g', {}, g);
      R(cg, 80, y, 920, 400, 34, { fill: 'rgba(60,36,62,.85)', sw: 5, attrs: { filter: GLOW } }); avatar(cg, 160, y + 80);
      T(cg, 225, y + 68, title, 42, { w: 800 }); const dg = X.svg('g', {}, cg); const dw = date.length * 14 + 50; R(dg, 225, y + 100, dw, 42, 21, { fill: C.CARD2, sw: 2 }); T(dg, 225 + dw / 2, y + 122, date, 21, { a: 'middle', fill: C.ACC, w: 800, ls: 1 });
      rows.forEach(([s, w], i) => { const rg = X.svg('g', {}, cg); R(rg, 115, y + 180 + i * 95, 850, 76, 20, { fill: C.CARD2, sw: 0 }); X.svg('circle', { cx: 150, cy: y + 218 + i * 95, r: 10, fill: C.MINT, filter: SOFT }, rg);
        T(rg, 180, y + 219 + i * 95, s, 29, { w: 600 }); fin(rg, w - 0.15, 0.35, 0); X.sfx(w, 'blip', { gain: 0.25 }); });
      whip(cg, t); return cg; };
    card(260, W('f2', 'september') - 0.2, 'OpenAI · dots', 'SEP 29, 2026', [['Always-on agents in ChatGPT', W('f2', 'always')], ['Work on your goals in the background', W('f2', 'background') - 0.5]],
      (cg, x, y) => { const a = X.svg('g', {}, cg); X.svg('circle', { cx: x, cy: y, r: 38, fill: C.ACC, filter: GLOW }, a); X.svg('circle', { cx: x - 11, cy: y - 5, r: 5, fill: C.BG }, a); X.svg('circle', { cx: x + 11, cy: y - 5, r: 5, fill: C.BG }, a);
        P(a, `M${x - 10},${y + 11} Q${x},${y + 19} ${x + 10},${y + 11}`, { stroke: C.BG, sw: 4 }); X.every((t) => a.setAttribute('transform', `translate(0 ${Math.sin(t * 3) * 4})`)); });
    card(720, W('f3', 'october') - 0.2, 'Anthropic · Claude Duet', 'OCT 2026 · PREVIEW', [['Sends a morning brief', W('f3', 'morning')], ['Runs on its own cloud computer', W('f3', 'cloud') - 0.4]],
      (cg, x, y) => { X.svg('circle', { cx: x - 14, cy: y, r: 30, fill: 'none', stroke: C.ACC, 'stroke-width': 5 }, cg); X.svg('circle', { cx: x + 16, cy: y, r: 30, fill: 'none', stroke: C.MINT, 'stroke-width': 5 }, cg); });
  });

  // ------------------------------------------------------------ THE RULE
  scene('rules', (g, t0) => {
    const pl = padlock(g, 540, 560, 1.6); gsap.set(pl.pg, { transformOrigin: '50% 50%' });
    X.tl.fromTo(pl.pg, { scale: 0.4, opacity: 0, filter: 'blur(14px)' }, { scale: 1, opacity: 1, filter: 'blur(0px)', duration: 0.6, ease: 'power3.out', immediateRender: false }, t0 + 0.1); gsap.set(pl.pg, { opacity: 0 });
    X.sfx(t0 + 0.1, 'zoom_in', { gain: 0.35 });
    const bl = W('g1', 'blocked');
    X.tl.fromTo(pl.sh, { y: -40 }, { y: 0, duration: 0.25, ease: 'power4.in', immediateRender: false }, bl - 0.2); gsap.set(pl.sh, { y: -40 });
    X.sfx(bl, 'thud', { gain: 0.6 }); flash(bl, 0.25);
    const mm = T(g, 540, 820, 'MOVING MONEY', 64, { a: 'middle', w: 900, attrs: { filter: GLOW2 } }); fin(mm, W('g1', 'moving') - 0.1, 0.35);
    const yes = X.svg('g', {}, g); R(yes, 400, 880, 280, 80, 40, { fill: C.CARD2, sw: 3, stroke: C.MUTED }); T(yes, 540, 921, 'Yes', 34, { a: 'middle', w: 800, fill: C.MUTED });
    fin(yes, W('g1', 'yes') - 0.3, 0.3); const x1 = P(yes, 'M420,900 L660,940', { stroke: C.RED, sw: 8 }); X.drawOn(x1, W('g1', 'yes'), 0.25); X.sfx(W('g1', 'yes'), 'error', { gain: 0.35 });
    X.tl.to([pl.pg, mm, yes], { y: -230, scale: 0.75, duration: 0.5, ease: 'power3.inOut', transformOrigin: '50% 50%' }, S('g2') - 0.2);
    [['Paying', 'paying'], ['Signing', 'signing'], ['Deleting', 'deleting']].forEach(([s, w], i) => { const x = 210 + i * 330, gg = X.svg('g', {}, g);
      R(gg, x - 120, 980, 240, 70, 35, { fill: C.CARD2, sw: 3 }); T(gg, x, 1016, s, 30, { a: 'middle', w: 800 });
      const arm = R(gg, x - 130, 940, 260, 18, 9, { fill: C.ACC, sw: 0 }); gsap.set(arm, { svgOrigin: `${x - 125} 949` });
      const tw = W('g2', w); fin(gg, tw - 0.15, 0.25, 0); X.tl.fromTo(arm, { rotation: -80 }, { rotation: 0, duration: 0.35, ease: 'bounce.out', immediateRender: false }, tw); X.sfx(tw + 0.2, 'stamp', { gain: 0.35 }); });
    const af = X.svg('g', {}, g); R(af, 340, 1110, 400, 70, 35, { fill: C.MINT, sw: 0 }); T(af, 540, 1146, 'IT ASKS FIRST', 30, { a: 'middle', w: 900, fill: C.BG, ls: 2 });
    X.pop(af, W('g2', 'asks'), { sfx: 'ding' });
  });

  // ------------------------------------------------------------ END
  scene('end', (g, t0) => {
    const warn = (x, y, s, t) => { const wg = X.svg('g', {}, g); P(wg, `M${x},${y - 40} L${x + 46},${y + 40} L${x - 46},${y + 40} Z`, { sw: 6, stroke: C.SUN }); T(wg, x, y + 14, '!', 40, { a: 'middle', w: 900, fill: C.SUN });
      T(wg, x, y + 90, s, 30, { a: 'middle', w: 800 }); X.pop(wg, t, { sfx: 'glitch', gain: 0.2 });
      X.every((tt) => { if (tt > t + 0.4) wg.setAttribute('opacity', (Math.floor(tt * 8) % 11 === 0) ? 0.4 : 1); }); return wg; };
    const w1 = warn(300, 420, 'Misjudged urgency', W('h1', 'misjudge')), w2 = warn(780, 420, 'Sneaky emails', W('h1', 'sneaky'));
    const boss = X.svg('g', {}, g); R(boss, 240, 620, 600, 110, 55, { fill: C.ACC, sw: 0, attrs: { filter: GLOW } }); T(boss, 540, 676, 'YOU’RE THE BOSS', 46, { a: 'middle', w: 900, fill: C.BG, ls: 2 });
    slam(boss, W('h1', 'boss') - 0.1, 'impact', 0.3);
    X.tl.to([w1, w2, boss], { opacity: 0, duration: 0.3 }, S('h2') - 0.1);
    // comment bubble
    const cb = X.svg('g', {}, g); gsap.set(cb, { svgOrigin: '540 640' });
    P(cb, 'M220,440 h640 a40,40 0 0 1 40,40 v240 a40,40 0 0 1 -40,40 h-420 l-80,70 v-70 h-140 a40,40 0 0 1 -40,-40 v-240 a40,40 0 0 1 40,-40 z', { sw: 6, fill: C.CARD, attrs: { filter: GLOW } });
    T(cb, 540, 560, 'Would YOU let AI', 52, { a: 'middle', w: 900 }); T(cb, 540, 630, 'work your night shift?', 52, { a: 'middle', w: 900, fill: C.ACC });
    const dd = [480, 540, 600].map((x) => X.svg('circle', { cx: x, cy: 710, r: 12, fill: C.MUTED }, cb));
    X.every((t) => dd.forEach((d, i) => d.setAttribute('cy', 710 - 8 * Math.max(0, Math.sin(t * 6 - i * 0.8)))));
    X.pop(cb, S('h2'), { sfx: 'bubble', gain: 0.4 });
    const yn = X.svg('g', {}, g); [['YES', 330, C.MINT], ['NO WAY', 750, C.RED]].forEach(([s, x, c]) => { R(yn, x - 140, 880, 280, 80, 40, { fill: 'none', sw: 4, stroke: c }); T(yn, x, 921, s, 32, { a: 'middle', w: 900, fill: c }); });
    fin(yn, W('h2', 'below') - 0.2, 0.35);
    const nx = X.svg('g', {}, g); R(nx, 110, 1010, 860, 150, 30, { fill: C.CARD, sw: 4, attrs: { filter: GLOW } });
    T(nx, 160, 1052, 'NEXT UP', 24, { fill: C.ACC, w: 900, ls: 3 }); T(nx, 160, 1105, 'Get recommended by AI search', 38, { w: 800 });
    whip(nx, W('h3', 'next') - 0.1);
    const fl = X.svg('g', {}, g); R(fl, 340, 1190, 400, 70, 35, { fill: C.ACC, sw: 0 }); T(fl, 540, 1226, 'Follow @aiwithsufi', 28, { a: 'middle', w: 900, fill: C.BG });
    X.pop(fl, W('h3', 'search'), { sfx: 'sparkle', gain: 0.4 });
  });

  // ------------------------------------------------------------ captions (narrator)
  const cap = document.getElementById('cap');
  let shown = null, spans = [];
  const isKey = (w) => { const a = w.replace(/[^A-Za-z]/g, ''); return (a.length >= 2 && a === a.toUpperCase()) || /^[ABC][!.,]?$/.test(w); };
  const curLine = (t) => { let c = null; for (const l of L) if (t >= l.start - 0.15 && t <= l.end + 0.35) c = l; return c; };
  X.every((t) => {
    const l = curLine(t);
    if (!l) { cap.style.opacity = 0; return; }
    if (shown !== l.id) {
      shown = l.id;
      cap.innerHTML = `<div class="b"><div class="t">${l.cap.split(' ').map((w) => `<span class="${isKey(w) ? 'k' : ''}">${w}</span>`).join(' ')}</div></div>`;
      spans = [...cap.querySelectorAll('.t span')];
    }
    const k = Math.min(1, Math.max(0, (t - l.start) / Math.max(0.1, l.end - l.start)));
    const n = Math.ceil(k * spans.length * 1.15);
    spans.forEach((s, i) => { s.style.opacity = i < n ? 1 : 0.35; });
    const fi = Math.min(1, (t - (l.start - 0.15)) / 0.15);
    cap.style.opacity = fi.toFixed(2); cap.style.transform = `translateY(${((1 - fi) * 12).toFixed(1)}px)`;
  });
  X.end(TOTAL);
});
