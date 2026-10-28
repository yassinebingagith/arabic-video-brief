/* Deterministic, seekable page motion. No wall-clock timers or layout changes. */
(() => {
  const data = window.pageData;
  const tl = gsap.timeline({paused: true});
  for (const p of data.pages) {
    const sel = '#' + p.id;
    tl.set(sel, {visibility: 'visible', opacity: 1}, p.start);
    if (p.start === 0) {
      tl.fromTo(sel + ' .header', {opacity: 0}, {opacity: 1, duration: .3, ease: 'power2.out'}, 0);
    }
    for (const word of p.words) {
      let cursor = word.start;
      const length = word.strokes.reduce((sum, stroke) => sum + stroke.length, 0);
      for (const stroke of word.strokes) {
        const duration = (word.end-word.start) * .95 * stroke.length / length;
        tl.fromTo('#' + stroke.id, {strokeDashoffset: 1},
          {strokeDashoffset: 0, duration, ease: 'none', immediateRender: false}, cursor);
        cursor += duration;
      }
      tl.to('#' + word.id + '-complete', {opacity: 1, duration: .025, ease: 'none'}, word.end-.025);
    }
    for (const mark of p.markers) {
      tl.fromTo('#' + mark.id, {clipPath: 'inset(0 0 0 100% round 10px)'},
        {clipPath: 'inset(0 0 0 0% round 10px)', duration: mark.duration, ease: 'power1.inOut', immediateRender: false}, mark.at);
      tl.to('#' + mark.id + '-text text', {fill: '#FFD700', duration: mark.duration, ease: 'none'}, mark.at);
    }
    tl.to(sel, {opacity: 0, duration: data.outgoing_fade_seconds, ease: 'power1.in'}, p.end - data.outgoing_fade_seconds);
    tl.set(sel, {visibility: 'hidden'}, p.end);
  }
  tl.to({}, {duration: .01}, data.duration - .01);
  window.__timelines = {main: tl};
})();
