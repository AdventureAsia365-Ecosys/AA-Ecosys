// UAT video overlay (skill aa-uat-video): a visible cursor dot that follows Playwright mouse moves,
// and a ripple on every click. Injected with context.addInitScript, so it survives navigations.
// It draws only; it never changes the page's own DOM outside its own fixed layer.
(() => {
  if (window.__uatOverlay) return;
  window.__uatOverlay = true;
  const install = () => {
    const layer = document.createElement('div');
    layer.id = '__uat_layer';
    layer.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:2147483647;';
    const dot = document.createElement('div');
    dot.style.cssText =
      'position:fixed;width:22px;height:22px;margin:-11px 0 0 -11px;border-radius:50%;' +
      'background:rgba(255,196,0,.55);border:2px solid rgba(20,20,20,.85);box-shadow:0 0 0 3px rgba(255,255,255,.7);' +
      'left:-100px;top:-100px;transition:transform .08s ease-out;';
    layer.appendChild(dot);
    document.documentElement.appendChild(layer);
    const pos = window.__uatPos || { x: -100, y: -100 };
    dot.style.left = pos.x + 'px';
    dot.style.top = pos.y + 'px';
    window.addEventListener('mousemove', (e) => {
      window.__uatPos = { x: e.clientX, y: e.clientY };
      dot.style.left = e.clientX + 'px';
      dot.style.top = e.clientY + 'px';
    }, true);
    window.addEventListener('mousedown', (e) => {
      dot.style.transform = 'scale(.7)';
      const r = document.createElement('div');
      r.style.cssText =
        'position:fixed;width:16px;height:16px;margin:-8px 0 0 -8px;border-radius:50%;' +
        'border:3px solid rgba(255,120,0,.95);left:' + e.clientX + 'px;top:' + e.clientY + 'px;' +
        'transition:all .6s ease-out;opacity:1;';
      layer.appendChild(r);
      requestAnimationFrame(() => {
        r.style.width = r.style.height = '64px';
        r.style.margin = '-32px 0 0 -32px';
        r.style.opacity = '0';
      });
      setTimeout(() => r.remove(), 700);
    }, true);
    window.addEventListener('mouseup', () => { dot.style.transform = 'scale(1)'; }, true);
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install);
  else install();
})();
