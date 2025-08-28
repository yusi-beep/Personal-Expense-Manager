function toNums(arr) {
  return (arr || []).map(v => {
    const n = typeof v === 'string' ? parseFloat(v) : v;
    return isNaN(n) ? 0 : n;
  });
}

function renderCategoryChart(labels, values) {
  if (!labels || labels.length === 0) return;
  const el = document.getElementById('categoryChart'); if (!el) return;

  const vals = toNums(values);
  if (vals.reduce((a,b)=>a+b,0) === 0) return; // нищо за рисуване

  new Chart(el.getContext('2d'), {
    type: 'pie',
    data: { labels, datasets: [{ data: vals }] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }
  });
}

function renderIncomeCategoryChart(labels, values) {
  if (!labels || labels.length === 0) return;
  const el = document.getElementById('incomeChart'); if (!el) return;

  const vals = toNums(values);
  if (vals.reduce((a,b)=>a+b,0) === 0) return;

  new Chart(el.getContext('2d'), {
    type: 'pie',
    data: { labels, datasets: [{ data: vals }] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }
  });
}

function renderMonthlyChart(months, incomeVals, expenseVals) {
  if (!months || months.length === 0) return;
  const el = document.getElementById('monthlyChart'); if (!el) return;

  const inc = toNums(incomeVals);
  const exp = toNums(expenseVals);

  new Chart(el.getContext('2d'), {
    type: 'bar',
    data: {
      labels: months,
      datasets: [
        { label: 'Income', data: inc },
        { label: 'Expense', data: exp }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'bottom' } },
      scales: { y: { beginAtZero: true } }
    }
  });
}
