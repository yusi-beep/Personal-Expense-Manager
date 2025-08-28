function renderCategoryChart(labels, values) {
  if (!labels || labels.length === 0) return;

  const el = document.getElementById('categoryChart');
  if (!el) return;
  const ctx1 = el.getContext('2d');

  new Chart(ctx1, {
    type: 'pie',
    data: {
      labels: labels,
      datasets: [{
        data: values,
        backgroundColor: [
          '#ff6384', '#36a2eb', '#ffce56',
          '#4bc0c0', '#9966ff', '#ff9f40'
        ]
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false   // <— IMPORTANT: .chart-box 
    }
  });
}

function renderMonthlyChart(months, incomeVals, expenseVals) {
  if (!months || months.length === 0) return;

  const el = document.getElementById('monthlyChart');
  if (!el) return;
  const ctx2 = el.getContext('2d');

  new Chart(ctx2, {
    type: 'bar',
    data: {
      labels: months,
      datasets: [
        {
          label: 'Income',
          data: incomeVals,
          backgroundColor: '#36a2eb'
        },
        {
          label: 'Expense',
          data: expenseVals,
          backgroundColor: '#ff6384'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,  // <— IMPORTANT: .chart-box 
      scales: {
        y: { beginAtZero: true }
      }
    }
  });
}
