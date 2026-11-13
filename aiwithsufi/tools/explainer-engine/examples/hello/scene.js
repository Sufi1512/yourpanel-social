X.boot(async (X) => {
  await X.loadVO();
  const tl = X.tl;
  const L0 = X.line('a'), L1 = X.line('b');
  const cam = X.cam(X.svg('g'));
  const c = X.svg('circle', { cx: 960, cy: 540, r: 120, fill: '#ff6b4a' }, cam);
  const cp = MorphSVGPlugin.convertToPath(c)[0];
  X.pop(cp, L0.start);
  const sq = X.svg('path', { d: 'M860,440h200v200h-200z', fill: '#2b59ff', opacity: 0 }, cam);
  tl.to(cp, { morphSVG: sq, fill: '#2b59ff', duration: 0.7, ease: 'power3.inOut' }, X.word('a', 'square'));
  X.sfx(X.word('a', 'square'), 'swoosh', { dur: 0.5 });
  const t = X.svg('text', { x: 960, y: 820, 'text-anchor': 'middle', 'font-size': 64, 'font-weight': 700, 'font-family': 'Poppins', fill: '#1b1b1b' }, cam);
  X.typeOn(t, 'Seekable, deterministic, synced.', L1.start, 30);
  tl.to(cam, { scale: 1.25, duration: 2.5, ease: 'power2.inOut' }, L1.start);
  X.grain(0.06);
  X.end(X.vo.duration || 6);
});
