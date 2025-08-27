function renderCategoryChart(labels, values) {
    if (labels.length === 0) return;

    const ctx1 = document.getElementById('categoryChart').getContext('2d');
    new Chart(ctx1, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: [
                    '#ff6384','#36a2eb','#ffce56',
                    '#4bc0c0','#9966ff','#ff9f40'
                ]
            }]
        }
    });
}

function renderMonthlyChart(months, incomeVals, expenseVals) {
    if (months.length === 0) return;

    const ctx2 = document.getElementById('monthlyChart').getContext('2d');
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
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}