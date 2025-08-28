// Simple dark-mode toggle that persists in localStorage
document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('themeToggle');
  if (!btn) return;

  const BODY = document.body;

  // възстанови запазения режим
  const saved = localStorage.getItem('theme') || 'light';
  if (saved === 'dark') BODY.classList.add('theme-dark');

  const updateLabel = () => {
    btn.textContent = BODY.classList.contains('theme-dark') ? 'Light' : 'Dark';
  };
  updateLabel();

  btn.addEventListener('click', () => {
    BODY.classList.toggle('theme-dark');
    localStorage.setItem('theme', BODY.classList.contains('theme-dark') ? 'dark' : 'light');
    updateLabel();
  });
});
