document.addEventListener('DOMContentLoaded', () => {
  const alerts = document.querySelectorAll('.alert');

  alerts.forEach((el) => {
    // for different periods per element: <div class="alert ..." data-autohide="6000">
    const delay = parseInt(el.dataset.autohide || '4000', 10);
    if (isNaN(delay) || delay <= 0) return;

    setTimeout(() => {
      // 1) try Bootstrap API (if exists)
      try {
        if (typeof window.bootstrap !== 'undefined' && window.bootstrap.Alert) {
          const inst = window.bootstrap.Alert.getOrCreateInstance(el);
          inst.close();
          return;
        }
      } catch (_) {}

      // 2) Fallback: ръчен fade-out + remove
      el.classList.remove('show'); // при .fade това ще анимира opacity
      // по-сигурен manual transition за всички случаи
      el.style.transition = 'opacity 180ms ease, max-height 220ms ease, margin 220ms ease, padding 220ms ease';
      el.style.overflow = 'hidden';
      el.style.maxHeight = el.scrollHeight + 'px';

      // start animation for next frame
      requestAnimationFrame(() => {
        el.style.opacity = '0';
        el.style.maxHeight = '0';
        el.style.marginTop = '0';
        el.style.marginBottom = '0';
        el.style.paddingTop = '0';
        el.style.paddingBottom = '0';
      });

      // getout DOM few time latter
      setTimeout(() => {
        if (el && el.parentNode) el.parentNode.removeChild(el);
      }, 260);
    }, delay);
  });
});

