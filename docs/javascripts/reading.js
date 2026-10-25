/* 阅读进度条：只做一件事，别抢焦点 */
(function () {
  if (window.matchMedia && window.matchMedia('print').matches) return;

  var bar = document.createElement('div');
  bar.id = 'kb-progress';
  document.body.appendChild(bar);

  var ticking = false;
  function update() {
    var doc = document.documentElement;
    var max = doc.scrollHeight - doc.clientHeight;
    bar.style.width = max > 0 ? (doc.scrollTop / max) * 100 + '%' : '0%';
    ticking = false;
  }
  window.addEventListener('scroll', function () {
    if (!ticking) {
      ticking = true;
      window.requestAnimationFrame(update);
    }
  }, { passive: true });
  window.addEventListener('resize', update);
  update();

  /* Material 的 instant navigation 换页后要重算 */
  if (window.document$) {
    window.document$.subscribe(function () { update(); });
  }
})();
