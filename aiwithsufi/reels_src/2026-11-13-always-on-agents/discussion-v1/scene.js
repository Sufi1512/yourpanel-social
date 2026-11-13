// @aiwithsufi · Always-on AI (13 Nov 2026) · Glow Sketch style on the explainer-engine runtime.
// Plum & Blush (Friday) palette. Riya (B, left) asks, Arjun (A, right) explains.
X.boot(async (X) => {
  await X.loadVO();
  const C = { BG: '#2c182e', CARD: '#3c243e', CARD2: '#442a46', LINE: '#5c405e', TEXT: '#f8eef2', MUTED: '#cebcca', ACC: '#f0a4b8', MINT: '#9fe3c9' };
  const F = 'Montserrat, sans-serif';
  const GLOW = X.glow('glow', 7, C.ACC, 0.95), GLOW2 = X.glow('glow2', 14, C.ACC, 0.7), SOFT = X.glow('soft', 5, '#ffffff', 0.35);
  const L = X.vo.lines, byId = Object.fromEntries(L.map((l) => [l.id, l]));
  const W = (id, w, n = 0) => X.word(id, w, n), S = (id) => byId[id].start, E = (id) => byId[id].end;
  const TOTAL = X.vo.duration;

  // ------------------------------------------------------------ helpers
  const T = (g, x, y, s, size = 34, o = {}) => X.svg('text', { x, y, text: s, fill: o.fill || C.TEXT, 'font-family': F, 'font-size': size,
    'font-weight': o.w || 700, 'text-anchor': o.a || 'start', 'letter-spacing': o.ls || 0, 'dominant-baseline': 'middle', ...(o.attrs || {}) }, g);
  const wrap = (g, x, y, s, size, max, lh, o = {}) => {
    const words = s.split(' '), lines = []; let cur = '';
    for (const w of words) { if ((cur + ' ' + w).trim().length > max) { lines.push(cur); cur = w; } else cur = (cur + ' ' + w).trim(); }
    lines.push(cur);
    const grp = X.svg('g', {}, g);
    lines.forEach((ln, i) => T(grp, x, y + i * lh - ((lines.length - 1) * lh) / 2 * (o.center ? 1 : 0), ln, size, o));
    return grp;
  };
  const R = (g, x, y, w, h, r, o = {}) => {
    const at = o.attrs || {};
    if (at.filter && o.fill && o.fill !== 'none') {  // glow only the outline: fill and stroke as two rects
      const { filter, ...rest } = at;
      const f = X.svg('rect', { x, y, width: w, height: h, rx: r, fill: o.fill, stroke: 'none', ...rest }, g);
      const st = X.svg('rect', { x, y, width: w, height: h, rx: r, fill: 'none', stroke: o.stroke || C.ACC, 'stroke-width': o.sw ?? 4, filter, ...rest }, g);
      st._fill = f; return st;
    }
    return X.svg('rect', { x, y, width: w, height: h, rx: r, fill: o.fill || 'none', stroke: o.stroke || C.ACC, 'stroke-width': o.sw ?? 4, ...at }, g);
  };
  const draw = (el, t, d = 0.8) => { X.drawOn(el, t, d); if (el._fill) { gsap.set(el._fill, { opacity: 0 }); X.tl.to(el._fill, { opacity: 1, duration: d * 0.8 }, t + d * 0.3); } };
  const P = (g, d, o = {}) => X.svg('path', { d, fill: o.fill || 'none', stroke: o.stroke || C.ACC, 'stroke-width': o.sw ?? 5, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, g);
  const fin = (el, t, d = 0.5, dy = 24) => { X.tl.fromTo(el, { opacity: 0, y: dy }, { opacity: 1, y: 0, duration: d, ease: 'power3.out', immediateRender: false }, t); gsap.set(el, { opacity: 0 }); };
  const fout = (el, t, d = 0.4) => X.tl.to(el, { opacity: 0, duration: d, ease: 'power2.in' }, t);
  const check = (g, x, y, s = 1, col = C.MINT) => P(g, `M${x - 14 * s},${y} L${x - 4 * s},${y + 11 * s} L${x + 16 * s},${y - 12 * s}`, { stroke: col, sw: 6 });
  const chip = (g, label, t) => {
    const cg = X.svg('g', {}, g), w = label.length * 17 + 60;
    R(cg, 540 - w / 2, 172, w, 54, 27, { fill: C.CARD, sw: 3 });
    T(cg, 540, 200, label, 24, { a: 'middle', ls: 2, fill: C.ACC, w: 800 });
    fin(cg, t, 0.45, -16); X.sfx(t, 'blip_up', { gain: 0.25 });
    return cg;
  };
  // scene windows from the voice lines
  const SC = []; L.forEach((l) => { if (!SC.length || SC[SC.length - 1].id !== l.scene) SC.push({ id: l.scene, s: l.start }); });
  SC.forEach((s, i) => { s.t0 = i ? s.s - 0.3 : 0; s.t1 = i + 1 < SC.length ? SC[i + 1].s - 0.3 : TOTAL + 1; });
  const win = Object.fromEntries(SC.map((s) => [s.id, s]));
  const scene = (id, build) => X.scene(id, win[id].t0, win[id].t1, (g, t0, t1) => {
    X.tl.fromTo(g, { opacity: 0 }, { opacity: 1, duration: 0.3, immediateRender: false }, t0);
    if (t1 < TOTAL) X.tl.to(g, { opacity: 0, duration: 0.25 }, t1 - 0.25);
    if (win[id].t0 > 0) X.sfx(t0, 'whoosh', { gain: 0.22 });
    build(g, t0, t1);
  }, mainLayer);

  // ------------------------------------------------------------ background (static + slow drift)
  X.svg('rect', { x: 0, y: 0, width: 1080, height: 1920, fill: C.BG });
  X.svg('rect', { x: 0, y: 0, width: 1080, height: 1920, fill: X.radial('bgr', [[0, '#4a2a4c', 1], [1, C.BG, 1]], 0.5, 0.38, 0.75) });
  const dots = X.svg('g', { opacity: 0.16 });
  for (let y = 40; y < 1920; y += 60) for (let x = 30; x < 1080; x += 60) X.svg('circle', { cx: x, cy: y, r: 2, fill: C.MUTED }, dots);
  X.every((t) => dots.setAttribute('transform', `translate(0 ${-(t * 6) % 60})`));
  const sparks = X.svg('g', {}), rs = X.rand(5), sp = Array.from({ length: 18 }, () => [rs() * 1080, rs() * 1250 + 250, 2 + rs() * 3, rs() * 6]);
  const spEl = sp.map(([x, y, r]) => X.svg('circle', { cx: x, cy: y, r, fill: C.ACC, filter: SOFT }, sparks));
  X.every((t) => spEl.forEach((el, i) => { const [x, y, , ph] = sp[i]; el.setAttribute('cy', ((y - t * 14 + 1920) % 1500) + 250); el.setAttribute('opacity', 0.15 + 0.25 * (0.5 + 0.5 * Math.sin(t * 1.3 + ph))); }));
  X.grain(0.05, 12);

  // top bar: progress + handle
  const top = X.svg('g', {});
  R(top, 90, 58, 900, 8, 4, { fill: C.LINE, sw: 0 });
  const prog = R(top, 90, 58, 1, 8, 4, { fill: C.ACC, sw: 0});
  X.every((t) => prog.setAttribute('width', Math.max(1, 900 * Math.min(1, t / TOTAL))));
  T(top, 540, 118, '@aiwithsufi', 28, { a: 'middle', fill: C.MUTED, w: 600 });

  const mainLayer = X.svg('g', {});

  // ------------------------------------------------------------ 1 · HOOK
  scene('hook', (g) => {
    const ph = X.svg('g', {}, g);
    gsap.set(ph, { svgOrigin: '540 680' });
    const body = R(ph, 360, 330, 360, 700, 52, { fill: 'rgba(60,36,62,.55)', sw: 5, attrs: { filter: GLOW } });
    draw(body, 0.05, 1.0);
    const notch = P(ph, 'M500,360 L580,360', { sw: 6 }); X.drawOn(notch, 0.7, 0.3);
    const clock = T(ph, 540, 470, '07:00', 86, { a: 'middle', w: 300 }); fin(clock, 0.7, 0.6);
    const day = T(ph, 540, 528, 'Friday, 13 November', 24, { a: 'middle', fill: C.MUTED, w: 500 }); fin(day, 0.85, 0.6);
    // notification slides in on "texts"
    const tx = W('h1', 'texts');
    const nt = X.svg('g', {}, ph);
    R(nt, 382, 585, 316, 150, 24, { fill: C.CARD2, sw: 3 });
    X.svg('circle', { cx: 425, cy: 628, r: 20, fill: C.ACC, filter: GLOW }, nt);
    T(nt, 425, 629, 'AI', 16, { a: 'middle', fill: C.BG, w: 900 });
    T(nt, 457, 628, 'Agent · now', 22, { fill: C.MUTED, w: 600 });
    T(nt, 404, 676, 'Your morning brief', 27, { w: 800 });
    T(nt, 404, 711, '3 things need you', 23, { fill: C.MUTED, w: 600 });
    X.tl.fromTo(nt, { opacity: 0, y: -60 }, { opacity: 1, y: 0, duration: 0.55, ease: 'back.out(1.6)', immediateRender: false }, tx - 0.1);
    gsap.set(nt, { opacity: 0 });
    X.sfx(tx - 0.1, 'notif', { gain: 0.5 });
    X.tl.to(ph, { rotation: 2.2, duration: 0.05, yoyo: true, repeat: 9, ease: 'none' }, tx - 0.1);
    X.tl.set(ph, { rotation: 0 }, tx + 0.45);
    // second notification on "asking"
    const nt2 = X.svg('g', {}, ph);
    R(nt2, 382, 752, 316, 92, 24, { fill: C.CARD2, sw: 3, attrs: { opacity: 0.85 } });
    T(nt2, 404, 785, 'Agent · just now', 20, { fill: C.MUTED, w: 600 });
    T(nt2, 404, 818, 'Invoice reply drafted', 24, { w: 800 });
    X.tl.fromTo(nt2, { opacity: 0, y: -40 }, { opacity: 1, y: 0, duration: 0.5, ease: 'back.out(1.6)', immediateRender: false }, W('h1', 'asking')); gsap.set(nt2, { opacity: 0 });
    X.sfx(W('h1', 'asking'), 'notif', { gain: 0.35, pitch: 1.2 });
    // always-on pulse rings
    const rings = [0, 1, 2].map(() => X.svg('circle', { cx: 540, cy: 680, r: 200, fill: 'none', stroke: C.ACC, 'stroke-width': 3 }, g));
    X.every((t) => rings.forEach((c, i) => { const k = ((t * 0.45 + i / 3) % 1); const on = t > 1.0 && t < win.hook.t1;
      c.setAttribute('r', 230 + k * 330); c.setAttribute('opacity', on ? (1 - k) * 0.35 : 0); }));
    // title on "always-on"
    const ta = W('h2', 'always');
    const title = T(g, 540, 1130, 'ALWAYS-ON AI', 96, { a: 'middle', w: 900, attrs: { filter: GLOW2 } });
    X.pop(title, ta, { sfx: 'impact', gain: 0.35 });
    const sub = T(g, 540, 1205, 'works while you don’t', 36, { a: 'middle', fill: C.ACC, w: 600 }); fin(sub, W('h2', 'background'), 0.5);
    X.tl.to(ph, { scale: 0.92, y: -20, duration: 1.2, ease: 'power2.inOut' }, ta - 0.2);
  });

  // ------------------------------------------------------------ 2 · CHATBOT VS ALWAYS-ON
  scene('compare', (g, t0) => {
    chip(g, '1 · CHATBOT VS ALWAYS-ON', t0 + 0.1);
    const col = (x, title, rows, t, accent) => {
      const cg = X.svg('g', {}, g);
      const box = R(cg, x, 290, 425, 860, 36, { fill: 'rgba(60,36,62,.5)', sw: accent ? 5 : 4, stroke: accent ? C.ACC : C.MUTED, attrs: accent ? { filter: GLOW } : {} });
      draw(box, t, 0.9);
      const hd = T(cg, x + 212, 470, title, 34, { a: 'middle', w: 900, fill: accent ? C.ACC : C.TEXT }); fin(hd, t + 0.3);
      return cg;
    };
    // left: chatbot
    const lc = col(80, 'CHATBOT', [], S('c1') - 0.1, false);
    const bub = P(lc, 'M222,330 h136 a22,22 0 0 1 22,22 v62 a22,22 0 0 1 -22,22 h-80 l-30,26 v-26 h-26 a22,22 0 0 1 -22,-22 v-62 a22,22 0 0 1 22,-22 z', { stroke: C.MUTED, sw: 5 });
    X.drawOn(bub, S('c1'), 0.8);
    const lrows = [['waits', 'Waits for you'], ['answers', 'Answers once'], ['stops', 'Then stops']];
    lrows.forEach(([w, s], i) => { const rg = X.svg('g', {}, lc); X.svg('circle', { cx: 130, cy: 590 + i * 120, r: 12, fill: C.MUTED }, rg); T(rg, 160, 590 + i * 120, s, 32, { w: 700 }); fin(rg, W('c1', w) - 0.1); X.sfx(W('c1', w), 'tick', { gain: 0.2 }); });
    const lab1 = T(lc, 292, 1080, 'REACTIVE', 30, { a: 'middle', fill: C.MUTED, w: 800, ls: 4 }); fin(lab1, W('c1', 'reactive'));
    const close = W('c2', 'close');
    X.tl.to(lc, { opacity: 0.35, duration: 0.6 }, close);
    const zz = T(g, 410, 380, 'z z z', 34, { fill: C.ACC, w: 800 }); fin(zz, close + 0.2, 0.6);
    X.tl.to(zz, { y: -40, duration: 3, ease: 'none' }, close + 0.4);
    // right: always-on agent
    const rc = col(575, 'ALWAYS-ON', [], S('c3') - 0.2, true);
    const rad = X.svg('g', {}, rc);
    const ring = X.svg('circle', { cx: 787, cy: 385, r: 50, fill: 'none', stroke: C.ACC, 'stroke-width': 5 }, rad); X.drawOn(ring, S('c3'), 0.8);
    const sweep = P(rad, 'M787,385 L787,340', { sw: 5 }); fin(sweep, S('c3') + 0.4, 0.3, 0);
    X.every((t) => sweep.setAttribute('transform', `rotate(${(t * 140) % 360} 787 385)`));
    const rrows = [['goal', 'Goal, set once'], ['watches', 'Watches triggers'], ['acts', 'Acts on its own'], ['checks', 'Checks in']];
    rrows.forEach(([w, s], i) => { const rg = X.svg('g', {}, rc); X.svg('circle', { cx: 625, cy: 570 + i * 105, r: 12, fill: C.ACC, filter: GLOW }, rg); T(rg, 655, 570 + i * 105, s, 31, { w: 700 }); fin(rg, W('c3', w) - 0.1); X.sfx(W('c3', w), 'blip', { gain: 0.25 }); });
    const lab2 = T(rc, 787, 1080, 'PROACTIVE', 30, { a: 'middle', fill: C.ACC, w: 800, ls: 4 }); fin(lab2, W('c3', 'proactive'));
  });

  // ------------------------------------------------------------ 3 · THE LOOP
  scene('loop', (g, t0) => {
    chip(g, '2 · HOW IT WORKS', t0 + 0.1);
    const cy = X.svg('g', {}, g); gsap.set(cy, { svgOrigin: '540 740' });
    const circ = X.svg('circle', { cx: 540, cy: 740, r: 270, fill: 'none', stroke: C.ACC, 'stroke-width': 5, filter: GLOW }, cy);
    X.drawOn(circ, t0 + 0.2, 1.2);
    const nodes = [['Trigger', 540, 470, 'trigger'], ['Think', 810, 740, 'think'], ['Act', 540, 1010, 'act'], ['Check in', 270, 740, 'check']];
    const nEl = nodes.map(([s, x, y], i) => {
      const ng = X.svg('g', {}, cy);
      const c = X.svg('circle', { cx: x, cy: y, r: 82, fill: C.BG, stroke: C.ACC, 'stroke-width': 4 }, ng);
      const tx = T(ng, x, y + 2, s, s.length > 6 ? 27 : 31, { a: 'middle', w: 800 });
      X.pop(ng, t0 + 0.5 + i * 0.15, { gain: 0.2 });
      return { c, tx };
    });
    const dot = X.svg('circle', { cx: 540, cy: 470, r: 13, fill: '#fff', filter: GLOW2 }, cy);
    X.every((t) => { const a = -Math.PI / 2 + Math.max(0, t - t0) * 0.9; dot.setAttribute('cx', 540 + 270 * Math.cos(a)); dot.setAttribute('cy', 740 + 270 * Math.sin(a)); });
    // trigger examples
    const ex = [['7:00 AM', 'schedule'], ['New email', 'email'], ['Data change', 'change']];
    const exg = X.svg('g', {}, g);
    ex.forEach(([s, w], i) => { const x = 200 + i * 340, eg = X.svg('g', {}, exg); R(eg, x - 125, 270, 250, 64, 32, { fill: C.CARD2, sw: 3 }); T(eg, x, 303, s, 28, { a: 'middle', w: 800 }); X.pop(eg, W('l2', w) - 0.05, { sfx: 'pop' }); });
    X.tl.to(nEl[0].c, { attr: { fill: C.CARD2 }, duration: 0.3 }, W('l2', 'schedule'));
    // light the loop step by step
    nodes.forEach(([s, , , w], i) => { const tw = W('l3', w); X.tl.to(nEl[i].c, { attr: { fill: C.ACC }, duration: 0.2 }, tw); X.tl.to(nEl[i].tx, { attr: { fill: C.BG }, duration: 0.2 }, tw);
      X.tl.to(nEl[i].c, { attr: { fill: C.BG }, duration: 0.4 }, tw + 0.55); X.tl.to(nEl[i].tx, { attr: { fill: C.TEXT }, duration: 0.4 }, tw + 0.55); X.sfx(tw, 'blip_up', { gain: 0.3, pitch: 1 + i * 0.12 }); });
    // move it into the cloud, close the laptop
    const tl4 = S('l4');
    fout(exg, tl4 - 0.1);
    X.tl.to(cy, { scale: 0.5, y: -150, duration: 0.9, ease: 'power3.inOut' }, tl4);
    const cloud = P(g, 'M300,760 C230,760 220,640 310,630 C300,520 450,480 500,560 C540,470 700,480 720,580 C820,560 870,660 800,720 C860,770 820,860 740,850 L340,850 C270,860 250,780 300,760 Z', { sw: 6 });
    gsap.set(cloud, { attr: { transform: 'translate(540 600) scale(1.25) translate(-540 -680)' } });
    cloud.setAttribute('filter', GLOW);
    X.drawOn(cloud, W('l5', 'cloud') - 0.3, 1.0);
    X.sfx(W('l5', 'cloud') - 0.3, 'swoosh', { gain: 0.3 });
    const lap = X.svg('g', {}, g);
    const scr = X.svg('g', {}, lap); gsap.set(scr, { svgOrigin: '540 1180' });
    R(scr, 395, 990, 290, 190, 14, { fill: C.CARD, sw: 5 });
    T(scr, 540, 1085, 'your laptop', 24, { a: 'middle', fill: C.MUTED, w: 600 });
    P(lap, 'M350,1180 L730,1180 L760,1215 L320,1215 Z', { sw: 5, fill: C.CARD });
    fin(lap, W('l4', 'laptop') - 0.2, 0.5);
    const cl = W('l5', 'close');
    X.tl.to(scr, { scaleY: 0.05, duration: 0.5, ease: 'power2.in' }, cl);
    X.sfx(cl + 0.45, 'thud', { gain: 0.3 });
    const kg = X.svg('g', {}, g);
    R(kg, 650, 1110, 300, 64, 32, { fill: C.CARD2, sw: 3, stroke: C.MINT });
    T(kg, 800, 1143, 'keeps going', 28, { a: 'middle', fill: C.MINT, w: 800 });
    X.pop(kg, W('l5', 'keeps'), { sfx: 'ding' });
  });

  // ------------------------------------------------------------ quizzes
  const quiz = (id, label, q, opts, ans, qa, qb, qc) => scene(id, (g, t0) => {
    chip(g, label + ' · PAUSE & GUESS', t0 + 0.1);
    const qt = wrap(g, 540, 400, q, 46, 24, 60, { a: 'middle', w: 800, center: true }); fin(qt, S(qa) + 0.1, 0.5);
    const cards = opts.map((o, i) => {
      const cg = X.svg('g', {}, g), y = 600 + i * 160;
      const bx = R(cg, 120, y, 840, 128, 30, { fill: C.CARD, sw: 4 });
      const lc = X.svg('circle', { cx: 196, cy: y + 64, r: 38, fill: C.CARD2, stroke: C.ACC, 'stroke-width': 4 }, cg);
      const lt = T(cg, 196, y + 66, 'ABC'[i], 34, { a: 'middle', w: 900, fill: C.ACC });
      T(cg, 262, y + 66, o, 38, { w: 700 });
      fin(cg, S(qa) + 0.8 + i * 0.35, 0.45, 30); X.sfx(S(qa) + 0.8 + i * 0.35, 'pop', { gain: 0.25, pitch: 1 + i * 0.1 });
      return { cg, bx, lc, lt };
    });
    // countdown in the silent gap
    const cdS = E(qb) + 0.1, cdE = S(qc) - 0.1;
    const cd = X.svg('g', {}, g);
    X.svg('circle', { cx: 540, cy: 1150, r: 62, fill: C.CARD, stroke: C.LINE, 'stroke-width': 8 }, cd);
    const arc = X.svg('circle', { cx: 540, cy: 1150, r: 62, fill: 'none', stroke: C.ACC, 'stroke-width': 8, transform: 'rotate(-90 540 1150)', filter: GLOW }, cd);
    const num = T(cd, 540, 1153, '3', 52, { a: 'middle', w: 900 });
    const Lc = 2 * Math.PI * 62; arc.setAttribute('stroke-dasharray', `${Lc} ${Lc}`);
    fin(cd, S(qb), 0.4, 0);
    X.every((t) => { const k = Math.min(1, Math.max(0, (t - cdS) / (cdE - cdS))); arc.setAttribute('stroke-dashoffset', Lc * k);
      num.textContent = k >= 1 ? '!' : String(Math.max(1, 3 - Math.floor(k * 3))); });
    [0, 1, 2].forEach((i) => X.sfx(cdS + i * (cdE - cdS) / 3, 'tick', { gain: 0.35 }));
    // reveal
    const rv = S(qc);
    fout(cd, rv, 0.3);
    cards.forEach((c, i) => {
      if (i === ans) { X.tl.to(c.bx, { attr: { fill: C.ACC, stroke: '#fff' }, duration: 0.3 }, rv); X.tl.to(c.cg.querySelectorAll('text'), { attr: { fill: C.BG }, duration: 0.3 }, rv);
        X.tl.to(c.lc, { attr: { fill: '#fff' }, duration: 0.3 }, rv); X.tl.fromTo(c.cg, { scale: 1 }, { scale: 1.05, svgOrigin: `540 ${600 + i * 160 + 64}`, duration: 0.35, ease: 'back.out(3)', immediateRender: false }, rv);
        const ck = check(c.cg, 900, 600 + i * 160 + 64, 1.5, C.BG); X.drawOn(ck, rv + 0.2, 0.35); }
      else X.tl.to(c.cg, { opacity: 0.3, duration: 0.4 }, rv);
    });
    X.sfx(rv, 'success', { gain: 0.45 });
  });
  quiz('quiz1', 'QUIZ 1', 'Your laptop is closed. Where does an always-on agent keep working?', ['On your phone', 'In the cloud', 'It pauses'], 1, 'q1', 'q2', 'q3');

  // ------------------------------------------------------------ 4 · LAUNCHES
  scene('launches', (g, t0) => {
    chip(g, "3 · IT'S ALREADY HERE", t0 + 0.1);
    const qm = T(g, 540, 700, '?', 260, { a: 'middle', w: 900, fill: C.ACC, attrs: { filter: GLOW2 } });
    X.pop(qm, S('r1') + 0.1, { sfx: 'boing', gain: 0.25 }); fout(qm, S('r2') - 0.1, 0.3);
    // card A: OpenAI dots
    const a = X.svg('g', {}, g);
    const ab = R(a, 80, 280, 870, 460, 34, { fill: 'rgba(60,36,62,.75)', sw: 5, attrs: { filter: GLOW } }); draw(ab, S('r2') - 0.1, 0.8);
    const av = X.svg('g', {}, a);
    X.svg('circle', { cx: 158, cy: 350, r: 36, fill: C.ACC, filter: GLOW }, av);
    X.svg('circle', { cx: 147, cy: 345, r: 5, fill: C.BG }, av); X.svg('circle', { cx: 169, cy: 345, r: 5, fill: C.BG }, av);
    P(av, 'M148,361 Q158,369 168,361', { stroke: C.BG, sw: 4 });
    X.pop(av, W('r2', 'openai'), { sfx: 'pop' });
    X.every((t) => av.setAttribute('transform', `translate(0 ${Math.sin(t * 3) * 4})`));
    const at = T(a, 215, 337, 'OpenAI · dots', 40, { w: 800 }); fin(at, W('r2', 'launched'), 0.45);
    const ad = X.svg('g', {}, a); R(ad, 215, 365, 190, 40, 20, { fill: C.CARD2, sw: 2 }); T(ad, 310, 386, 'SEP 29, 2026', 20, { a: 'middle', fill: C.ACC, w: 800, ls: 1 }); fin(ad, W('r2', 'september'), 0.4);
    const r1 = X.svg('g', {}, a); R(r1, 115, 440, 800, 70, 20, { fill: C.CARD2, sw: 0 });
    X.svg('circle', { cx: 150, cy: 475, r: 10, fill: C.MINT, filter: SOFT }, r1);
    T(r1, 178, 476, 'Working on your goals in the background', 27, { w: 600 }); fin(r1, W('r2', 'background') - 0.3, 0.45);
    const r3 = S('r3');
    const chips = X.svg('g', {}, a);
    [['Slack', 'slack'], ['Teams', 'teams']].forEach(([s, w], i) => { const cg = X.svg('g', {}, chips); R(cg, 640 + i * 145, 316, 130, 46, 23, { fill: C.CARD, sw: 3 }); T(cg, 705 + i * 145, 340, s, 22, { a: 'middle', w: 800 }); X.pop(cg, W('r3', w), { gain: 0.25 }); });
    const r2 = X.svg('g', {}, a); R(r2, 115, 530, 800, 70, 20, { fill: C.CARD2, sw: 0 });
    const sp2 = X.svg('circle', { cx: 150, cy: 565, r: 12, fill: 'none', stroke: C.ACC, 'stroke-width': 4, 'stroke-dasharray': '40 40' }, r2);
    X.every((t) => sp2.setAttribute('transform', `rotate(${t * 360} 150 565)`));
    const r2t = T(r2, 178, 566, '', 27, { w: 600 }); fin(r2, W('r3', 'example'), 0.4);
    X.typeOn(r2t, 'Watching customer feedback…', W('r3', 'example') + 0.2, 30);
    const r4 = X.svg('g', {}, a); R(r4, 115, 620, 800, 70, 20, { fill: C.CARD2, sw: 0 });
    T(r4, 178, 656, 'Bug fixed', 27, { w: 800, fill: C.MINT }); const ck = check(r4, 150, 656, 1, C.MINT);
    fin(r4, W('r3', 'fixes') - 0.1, 0.4); X.drawOn(ck, W('r3', 'fixes'), 0.35); X.sfx(W('r3', 'fixes'), 'success', { gain: 0.3 });
    const af = T(a, 515, 715, 'ChatGPT Pro & Business Premium', 22, { a: 'middle', fill: C.MUTED, w: 600 }); fin(af, W('r3', 'slack'), 0.4);
    // card B: Claude Duet
    const tb = S('r5');
    X.tl.to(a, { opacity: 0.45, duration: 0.5 }, W('r4', 'anthropic'));
    const b = X.svg('g', {}, g);
    const bb = R(b, 80, 780, 870, 470, 34, { fill: 'rgba(60,36,62,.75)', sw: 5, attrs: { filter: GLOW } }); draw(bb, S('r4'), 0.8);
    const bav = X.svg('g', {}, b);
    X.svg('circle', { cx: 145, cy: 850, r: 28, fill: 'none', stroke: C.ACC, 'stroke-width': 5 }, bav);
    X.svg('circle', { cx: 175, cy: 850, r: 28, fill: 'none', stroke: C.MINT, 'stroke-width': 5 }, bav);
    X.pop(bav, W('r5', 'claude'), { sfx: 'pop' });
    const bt = T(b, 220, 837, 'Anthropic · Claude Duet', 38, { w: 800 }); fin(bt, W('r5', 'claude'), 0.45);
    const bd = X.svg('g', {}, b); R(bd, 220, 865, 220, 40, 20, { fill: C.CARD2, sw: 2 }); T(bd, 330, 886, 'LATE OCT 2026', 20, { a: 'middle', fill: C.ACC, w: 800, ls: 1 }); fin(bd, W('r5', 'late'), 0.4);
    const row = (y, s, t, icon) => { const rg = X.svg('g', {}, b); R(rg, 115, y, 800, 70, 20, { fill: C.CARD2, sw: 0 }); T(rg, 185, y + 36, s, 27, { w: 600 }); icon(rg, 150, y + 35); fin(rg, t - 0.1, 0.45); X.sfx(t, 'blip', { gain: 0.25 }); return rg; };
    row(935, 'Morning brief: email + calendar', W('r5', 'morning'), (rg, x, y) => { X.svg('circle', { cx: x, cy: y, r: 10, fill: C.ACC, filter: SOFT }, rg); for (let k = 0; k < 8; k++) { const an = k * Math.PI / 4; P(rg, `M${x + 15 * Math.cos(an)},${y + 15 * Math.sin(an)} L${x + 21 * Math.cos(an)},${y + 21 * Math.sin(an)}`, { sw: 3 }); } });
    row(1020, 'Checks your accounts every few hours', W('r5', 'checks'), (rg, x, y) => { X.svg('circle', { cx: x, cy: y, r: 17, fill: 'none', stroke: C.ACC, 'stroke-width': 4 }, rg); const hd = P(rg, `M${x},${y} L${x},${y - 11}`, { sw: 4 }); X.every((t) => hd.setAttribute('transform', `rotate(${t * 120} ${x} ${y})`)); });
    row(1105, 'Its own cloud computer + browser', W('r6', 'computer'), (rg, x, y) => { R(rg, x - 18, y - 14, 36, 24, 4, { sw: 3 }); P(rg, `M${x - 8},${y + 17} L${x + 8},${y + 17}`, { sw: 3 }); });
    const bf = T(b, 515, 1222, 'Research preview · Pro & Max · US waitlist', 22, { a: 'middle', fill: C.MUTED, w: 600 }); fin(bf, W('r6', 'preview'), 0.4);
  });

  // ------------------------------------------------------------ 5 · A DAY WITH AN AGENT
  scene('day', (g, t0) => {
    chip(g, '4 · A DAY WITH AN AGENT', t0 + 0.1);
    const ph = X.svg('g', {}, g);
    const body = R(ph, 300, 270, 480, 990, 54, { fill: 'rgba(60,36,62,.6)', sw: 5, attrs: { filter: GLOW } }); draw(body, t0 + 0.1, 0.9);
    const hdr = X.svg('g', {}, ph); X.svg('circle', { cx: 350, cy: 330, r: 16, fill: C.ACC, filter: SOFT }, hdr); T(hdr, 378, 331, 'Your agent', 24, { w: 800 }); fin(hdr, t0 + 0.6);
    const card = (y, h, time, title, sub, t) => { const cg = X.svg('g', {}, ph); R(cg, 325, y, 430, h, 24, { fill: C.CARD2, sw: 2, stroke: C.LINE });
      T(cg, 350, y + 34, time, 22, { fill: C.ACC, w: 800, ls: 1 }); T(cg, 350, y + 72, title, 30, { w: 800 }); if (sub) T(cg, 350, y + 110, sub, 22, { fill: C.MUTED, w: 600 });
      X.tl.fromTo(cg, { opacity: 0, x: 40 }, { opacity: 1, x: 0, duration: 0.5, immediateRender: false }, t); gsap.set(cg, { opacity: 0 }); X.sfx(t, 'notif', { gain: 0.3 }); return cg; };
    card(370, 140, '7:00 AM', 'Morning brief', '3 meetings · 2 urgent emails', W('d2', 'seven') - 0.1);
    const c2 = card(530, 250, '10:00 AM', 'Invoice email', null, W('d3', 'ten') - 0.1);
    const dr = X.svg('g', {}, c2); R(dr, 345, 640, 390, 120, 18, { fill: C.CARD, sw: 2, stroke: C.ACC });
    T(dr, 365, 668, 'DRAFT REPLY', 18, { fill: C.ACC, w: 800, ls: 2 });
    const l1 = T(dr, 365, 704, '', 22, { w: 600 }), l2 = T(dr, 365, 736, '', 22, { w: 600 });
    const td = W('d3', 'drafts'); fin(dr, td - 0.1, 0.4);
    X.typeOn(l1, 'Thanks for the invoice.', td + 0.1, 28); X.typeOn(l2, 'Paying it this week.', td + 1.0, 28); X.sfx(td + 0.1, 'type', { dur: 1.6, gain: 0.25 });
    // approval sheet
    const sh = X.svg('g', {}, ph);
    R(sh, 315, 840, 450, 370, 34, { fill: C.CARD, sw: 4, attrs: { filter: GLOW } });
    const st = T(sh, 540, 900, 'Send this reply?', 32, { a: 'middle', w: 800 });
    const ap = X.svg('g', {}, sh); const apb = R(ap, 345, 950, 390, 86, 43, { fill: C.ACC, sw: 0 }); T(ap, 540, 994, 'Approve', 32, { a: 'middle', w: 900, fill: C.BG });
    const ed = X.svg('g', {}, sh); R(ed, 345, 1055, 390, 86, 43, { fill: 'none', sw: 3, stroke: C.MUTED }); T(ed, 540, 1099, 'Edit', 30, { a: 'middle', w: 800, fill: C.MUTED });
    const tsh = W('d4', 'before');
    X.tl.fromTo(sh, { opacity: 0, y: 160 }, { opacity: 1, y: 0, duration: 0.6, ease: 'power3.out', immediateRender: false }, tsh); gsap.set(sh, { opacity: 0 }); X.sfx(tsh, 'slide', { gain: 0.3 });
    // finger tap
    const fg = X.svg('g', {}, g);
    const ring = X.svg('circle', { cx: 0, cy: 0, r: 34, fill: 'none', stroke: '#fff', 'stroke-width': 4, opacity: 0 }, fg);
    X.svg('circle', { cx: 0, cy: 0, r: 22, fill: 'rgba(255,255,255,.85)', filter: SOFT }, fg);
    const tap = W('d4', 'approve');
    gsap.set(fg, { x: 900, y: 1400, opacity: 0 });
    X.tl.to(fg, { opacity: 1, duration: 0.2 }, tap - 0.9);
    X.tl.to(fg, { x: 560, y: 1000, duration: 0.8, ease: 'power2.inOut' }, tap - 0.85);
    X.tl.fromTo(ring, { attr: { r: 22 }, opacity: 0.9 }, { attr: { r: 70 }, opacity: 0, duration: 0.5, immediateRender: false }, tap);
    X.tl.to(fg, { scale: 0.85, duration: 0.1, yoyo: true, repeat: 1 }, tap - 0.05);
    X.tl.to(fg, { opacity: 0, duration: 0.3 }, tap + 0.6);
    X.sfx(tap, 'click', { gain: 0.5 });
    X.tl.to(apb, { attr: { fill: C.MINT }, duration: 0.2 }, tap);
    X.tl.call(() => {}, [], tap);
    const sent = X.svg('g', {}, sh); T(sent, 560, 900, 'Sent by you', 32, { a: 'middle', w: 800, fill: C.MINT }); const sck = check(sent, 400, 900, 1.1, C.MINT);
    gsap.set(sent, { opacity: 0 });
    X.tl.to(st, { opacity: 0, duration: 0.2 }, tap + 0.3); X.tl.to(sent, { opacity: 1, duration: 0.3 }, tap + 0.35); X.drawOn(sck, tap + 0.4, 0.3);
    X.sfx(tap + 0.35, 'success', { gain: 0.4 });
    // "still the boss": glow pulse on the phone
    const boss = W('d5', 'boss');
    X.tl.fromTo(body, { attr: { 'stroke-width': 5 } }, { attr: { 'stroke-width': 10 }, duration: 0.25, yoyo: true, repeat: 1, immediateRender: false }, boss - 0.1);
  });

  // ------------------------------------------------------------ 6 · TRADE-OFFS
  scene('safety', (g, t0) => {
    chip(g, '5 · THE TRADE-OFFS', t0 + 0.1);
    const h1 = X.svg('g', {}, g);
    R(h1, 80, 270, 920, 470, 34, { fill: 'rgba(60,36,62,.55)', sw: 4, attrs: { filter: GLOW } });
    const pi = X.svg('g', {}, h1); R(pi, 120, 302, 13, 40, 4, { fill: C.ACC, sw: 0 }); R(pi, 143, 302, 13, 40, 4, { fill: C.ACC, sw: 0 });
    T(h1, 180, 323, 'ASKS YOU FIRST', 32, { w: 900, fill: C.ACC, ls: 2 });
    fin(h1, S('t1') - 0.1, 0.5);
    [['Paying', 'payments'], ['Signing', 'signing'], ['Deleting', 'deleting']].forEach(([s, w], i) => { const cg = X.svg('g', {}, g); const x = 230 + i * 280;
      R(cg, x - 120, 380, 240, 76, 38, { fill: C.CARD2, sw: 3 }); T(cg, x, 419, s, 30, { a: 'middle', w: 800 }); X.pop(cg, W('t1', w) - 0.05, { gain: 0.3 }); });
    const rowS = (y, s, t, icon, col = C.TEXT) => { const rg = X.svg('g', {}, g); icon(rg, 150, y); T(rg, 195, y + 2, s, 31, { w: 700, fill: col }); fin(rg, t - 0.1, 0.45); X.sfx(t, 'stamp', { gain: 0.25 }); return rg; };
    rowS(540, 'Moving money: always blocked', W('t2', 'blocked'), (rg, x, y) => { R(rg, x - 18, y - 4, 36, 28, 6, { fill: C.ACC, sw: 0 }); P(rg, `M${x - 11},${y - 4} v-10 a11,11 0 0 1 22,0 v10`, { sw: 5 }); });
    rowS(640, 'Purchases: a one-time card', W('t2', 'one'), (rg, x, y) => { R(rg, x - 22, y - 15, 44, 30, 6, { sw: 4 }); P(rg, `M${x - 22},${y - 4} L${x + 22},${y - 4}`, { sw: 4 }); });
    const h2 = X.svg('g', {}, g);
    R(h2, 80, 780, 920, 440, 34, { fill: 'rgba(60,36,62,.55)', sw: 4, stroke: C.MUTED });
    P(h2, 'M140,808 L162,848 L118,848 Z', { sw: 4, stroke: C.ACC }); T(h2, 140, 838, '!', 20, { a: 'middle', fill: C.ACC, w: 900 });
    T(h2, 180, 832, 'WHAT CAN GO WRONG', 32, { w: 900, fill: C.TEXT, ls: 2 });
    fin(h2, S('t3') - 0.05, 0.5); X.sfx(S('t3'), 'glitch', { gain: 0.2 });
    rowS(930, 'Misjudges what’s urgent', W('t4', 'misjudge'), (rg, x, y) => X.svg('circle', { cx: x, cy: y, r: 10, fill: C.ACC }, rg));
    rowS(1030, 'Trick emails (prompt injection)', W('t4', 'trick'), (rg, x, y) => X.svg('circle', { cx: x, cy: y, r: 10, fill: C.ACC }, rg));
    rowS(1130, 'Background work uses your limits', W('t4', 'limits'), (rg, x, y) => X.svg('circle', { cx: x, cy: y, r: 10, fill: C.ACC }, rg));
  });

  quiz('quiz2', 'QUIZ 2', 'Before signing a document for you, an agent should…', ['Sign it fast', 'Pause and ask you', 'Wait a week'], 1, 'q4', 'q5', 'q6');

  // ------------------------------------------------------------ 7 · OUTRO
  scene('outro', (g, t0) => {
    chip(g, 'RECAP', t0 + 0.1);
    const cg = X.svg('g', {}, g);
    const circ = X.svg('circle', { cx: 540, cy: 600, r: 210, fill: 'none', stroke: C.ACC, 'stroke-width': 5, filter: GLOW }, cg); X.drawOn(circ, t0 + 0.1, 0.9);
    const nodes = [['Goal', 540, 390, 'goal'], ['Trigger', 750, 600, 'trigger'], ['Act', 540, 810, 'action'], ['Check in', 330, 600, 'check']];
    nodes.forEach(([s, x, y, w]) => { const ng = X.svg('g', {}, cg); const c = X.svg('circle', { cx: x, cy: y, r: 74, fill: C.BG, stroke: C.ACC, 'stroke-width': 4 }, ng);
      const tx = T(ng, x, y + 2, s, s.length > 6 ? 25 : 29, { a: 'middle', w: 800 }); const tw = W('o1', w); X.pop(ng, tw - 0.05, { sfx: 'blip_up', gain: 0.3 });
      X.tl.to(c, { attr: { fill: C.ACC }, duration: 0.25 }, tw + 0.05); X.tl.to(tx, { attr: { fill: C.BG }, duration: 0.25 }, tw + 0.05); });
    const nx = X.svg('g', {}, g);
    R(nx, 110, 960, 860, 200, 32, { fill: C.CARD, sw: 4, attrs: { filter: GLOW } });
    T(nx, 160, 1010, 'NEXT UP', 24, { fill: C.ACC, w: 900, ls: 3 });
    T(nx, 160, 1060, 'GEO: get your business', 36, { w: 800 }); T(nx, 160, 1108, 'recommended by AI search', 36, { w: 800 });
    fin(nx, W('o2', 'next') - 0.1, 0.5); X.sfx(W('o2', 'next'), 'swoosh', { gain: 0.3 });
    const fl = X.svg('g', {}, g); R(fl, 340, 1185, 400, 70, 35, { fill: C.ACC, sw: 0, attrs: { filter: GLOW } }); T(fl, 540, 1221, 'Follow @aiwithsufi', 28, { a: 'middle', w: 900, fill: C.BG });
    X.pop(fl, W('o2', 'follow'), { sfx: 'sparkle', gain: 0.4 });
  });

  // ------------------------------------------------------------ hosts + captions (always on top)
  const hosts = X.svg('g', {});
  const mkHost = (who, x, name) => {
    const hg = X.svg('g', {}, hosts);
    const halo = X.svg('circle', { cx: x, cy: 1420, r: 92, fill: 'none', stroke: C.ACC, 'stroke-width': 5, filter: GLOW }, hg);
    X.svg('circle', { cx: x, cy: 1420, r: 84, fill: C.CARD }, hg);
    const clip = X.svg('clipPath', { id: 'cp' + who }, X.defs); X.svg('circle', { cx: x, cy: 1420, r: 84 }, clip);
    const face = X.svg('g', { 'clip-path': `url(#cp${who})` }, hg);
    const skin = who === 'A' ? '#c98f6b' : '#a8735a', hair = who === 'A' ? '#2b1b1e' : '#3a2025', shirt = who === 'A' ? C.ACC : C.MUTED;
    X.svg('path', { d: `M${x - 80},1520 C${x - 70},1462 ${x + 70},1462 ${x + 80},1520 Z`, fill: shirt }, face);
    X.svg('rect', { x: x - 14, y: 1440, width: 28, height: 30, fill: skin }, face);
    if (who === 'B') X.svg('path', { d: `M${x - 46},1408 C${x - 54},1350 ${x + 54},1350 ${x + 46},1408 L${x + 52},1478 L${x + 30},1478 L${x + 34},1410 L${x - 34},1410 L${x - 30},1478 L${x - 52},1478 Z`, fill: hair }, face);
    X.svg('ellipse', { cx: x, cy: 1412, rx: 36, ry: 42, fill: skin }, face);
    if (who === 'A') { X.svg('path', { d: `M${x - 38},1404 C${x - 42},1360 ${x + 42},1360 ${x + 38},1404 C${x + 30},1384 ${x - 30},1384 ${x - 38},1404 Z`, fill: hair }, face);
      X.svg('path', { d: `M${x - 34},1420 C${x - 30},1462 ${x + 30},1462 ${x + 34},1420 C${x + 22},1446 ${x - 22},1446 ${x - 34},1420 Z`, fill: hair, opacity: 0.85 }, face); }
    else X.svg('path', { d: `M${x - 37},1402 C${x - 30},1372 ${x + 30},1372 ${x + 37},1402 C${x + 10},1388 ${x - 20},1388 ${x - 37},1402 Z`, fill: hair }, face);
    const eyes = [x - 13, x + 13].map((ex) => X.svg('ellipse', { cx: ex, cy: 1410, rx: 4.5, ry: 5.5, fill: '#1b1012' }, face));
    const mouth = X.svg('ellipse', { cx: x, cy: 1438, rx: 9, ry: 2, fill: '#5a1f2c' }, face);
    const nm = T(hg, x, 1538, name, 24, { a: 'middle', w: 800, fill: C.MUTED, ls: 2 });
    return { hg, halo, eyes, mouth, nm, x };
  };
  const H = { B: mkHost('B', 130, 'RIYA'), A: mkHost('A', 950, 'ARJUN') };
  const words = { A: [], B: [] }; L.forEach((l) => l.words.forEach((w) => words[l.who].push(w)));
  const speaking = (who, t) => words[who].some((w) => t >= w.start && t <= w.end);
  const curLine = (t) => { let c = null; for (const l of L) if (t >= l.start - 0.15 && t <= l.end + 0.35) c = l; return c; };
  X.every((t) => ['A', 'B'].forEach((who) => {
    const h = H[who], l = curLine(t), on = l && l.who === who, talk = speaking(who, t);
    h.halo.setAttribute('opacity', on ? 1 : 0.25); h.halo.setAttribute('stroke-width', on ? 6 : 3);
    h.nm.setAttribute('fill', on ? C.ACC : C.MUTED);
    const bob = on ? Math.sin(t * 5.5) * 3 : Math.sin(t * 1.4 + (who === 'A' ? 1 : 0)) * 2;
    h.hg.setAttribute('transform', `translate(0 ${bob.toFixed(2)})`);
    h.mouth.setAttribute('ry', talk ? (3 + 6 * Math.abs(Math.sin(t * 17 + (who === 'A' ? 0 : 1.3)))).toFixed(2) : 2);
    const bl = ((t + (who === 'A' ? 0.7 : 0)) % 3.7) < 0.12; h.eyes.forEach((e) => e.setAttribute('ry', bl ? 0.8 : 5.5));
  }));
  gsap.set(hosts, { opacity: 0 }); X.tl.to(hosts, { opacity: 1, duration: 0.4 }, 0.2);

  // caption bubble (HTML for crisp wrapped text)
  const cap = document.getElementById('cap');
  let shown = null, spans = [], bars = [];
  const isKey = (w) => /[A-Z]{2,}/.test(w.replace(/[^A-Za-z]/g, '')) && w.replace(/[^A-Za-z]/g, '') === w.replace(/[^A-Za-z]/g, '').toUpperCase() || /^[ABC][!.,]?$/.test(w);
  X.every((t) => {
    const l = curLine(t);
    if (!l) { cap.style.opacity = 0; return; }
    if (shown !== l.id) {
      shown = l.id;
      const left = l.who === 'B';
      cap.innerHTML = `<div class="b"><div class="n"><span>${l.who === 'A' ? 'ARJUN' : 'RIYA'}</span><span class="w">${'<i></i>'.repeat(9)}</span></div><div class="t">${
        l.cap.split(' ').map((w) => `<span class="${isKey(w) ? 'k' : ''}">${w}</span>`).join(' ')}</div><div class="tail"></div></div>`;
      const tail = cap.querySelector('.tail');
      Object.assign(tail.style, left ? { left: '-18px', borderRight: '18px solid rgba(240,164,184,.75)' } : { right: '-18px', borderLeft: '18px solid rgba(240,164,184,.75)' });
      spans = [...cap.querySelectorAll('.t span')]; bars = [...cap.querySelectorAll('.w i')];
    }
    const k = Math.min(1, Math.max(0, (t - l.start) / Math.max(0.1, l.end - l.start)));
    const n = Math.ceil(k * spans.length * 1.15);
    spans.forEach((s, i) => { s.style.opacity = i < n ? 1 : 0.38; });
    const talk = speaking(l.who, t);
    bars.forEach((b, i) => { b.style.height = (talk ? 5 + 16 * Math.abs(Math.sin(t * 13 + i * 1.7)) : 4).toFixed(1) + 'px'; });
    const fadeIn = Math.min(1, (t - (l.start - 0.15)) / 0.15);
    cap.style.opacity = fadeIn.toFixed(2);
    cap.style.transform = `translateY(${((1 - fadeIn) * 12).toFixed(1)}px)`;
  });

  X.end(TOTAL);
});
