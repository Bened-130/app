/**
 * Chart helper functions for admin page
 */

// Initialize a vote chart
function initVoteChart(ctx, initialData) {
    const names = initialData.map(d => d.name);
    const votes = initialData.map(d => d.votes);
    
    const colors = [
        'rgba(255, 99, 132, 0.8)',
        'rgba(54, 162, 235, 0.8)',
        'rgba(255, 206, 86, 0.8)',
        'rgba(75, 192, 192, 0.8)',
        'rgba(153, 102, 255, 0.8)',
        'rgba(255, 159, 64, 0.8)',
        'rgba(199, 199, 199, 0.8)',
        'rgba(83, 102, 255, 0.8)'
    ];
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: names,
            datasets: [{
                label: 'Votes',
                data: votes,
                backgroundColor: colors.slice(0, names.length),
                borderColor: colors.slice(0, names.length).map(c => c.replace('0.8', '1')),
                borderWidth: 2,
                borderRadius: 6,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            animation: {
                duration: 500
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    cornerRadius: 8,
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? ((context.raw / total) * 100).toFixed(1) : 0;
                            return `${context.raw} votes (${percentage}%)`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#8892b0',
                        stepSize: 1
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                x: {
                    ticks: {
                        color: '#fff',
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// Update chart data
function updateVoteChart(chart, data) {
    if (!chart) return;
    chart.data.datasets[0].data = data.map(d => d.votes);
    chart.update('none');
}

// Calculate and display statistics
function updateStats(data, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const total = data.reduce((sum, item) => sum + item.votes, 0);
    const leader = data.reduce((max, item) => item.votes > max.votes ? item : max, data[0]);
    
    container.innerHTML = `
        <div class="stat-card">
            <div class="stat-value">${total}</div>
            <div class="stat-label">Total Votes</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${data.length}</div>
            <div class="stat-label">Candidates</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${leader.name}</div>
            <div class="stat-label">Leading (${leader.votes} votes)</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${total > 0 ? (total / data.length).toFixed(1) : 0}</div>
            <div class="stat-label">Avg Votes</div>
        </div>
    `;
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { initVoteChart, updateVoteChart, updateStats };
}