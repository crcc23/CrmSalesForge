// Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize pipeline chart if it exists
    const pipelineChartElement = document.getElementById('pipelineChart');
    if (pipelineChartElement) {
        initializePipelineChart();
    }

    // Initialize opportunity timeline chart if it exists
    const opportunityTimelineElement = document.getElementById('opportunityTimeline');
    if (opportunityTimelineElement) {
        initializeOpportunityTimeline();
    }

    // Initialize sales funnel chart if it exists
    const salesFunnelElement = document.getElementById('salesFunnel');
    if (salesFunnelElement) {
        initializeSalesFunnel();
    }
    
    // Initialize activity chart if it exists
    const activityChartElement = document.getElementById('activityChart');
    if (activityChartElement) {
        initializeActivityChart();
    }
});

// Initialize pipeline chart
function initializePipelineChart() {
    // Get data from data attributes
    const pipelineElement = document.getElementById('pipelineChart');
    const labels = JSON.parse(pipelineElement.getAttribute('data-stages') || '[]');
    const counts = JSON.parse(pipelineElement.getAttribute('data-counts') || '[]');
    const amounts = JSON.parse(pipelineElement.getAttribute('data-amounts') || '[]');
    
    const ctx = pipelineElement.getContext('2d');
    
    // Create gradient fills for the bars
    const primaryGradient = ctx.createLinearGradient(0, 0, 0, 400);
    primaryGradient.addColorStop(0, 'rgba(52, 152, 219, 0.8)');
    primaryGradient.addColorStop(1, 'rgba(52, 152, 219, 0.2)');
    
    const secondaryGradient = ctx.createLinearGradient(0, 0, 0, 400);
    secondaryGradient.addColorStop(0, 'rgba(46, 204, 113, 0.8)');
    secondaryGradient.addColorStop(1, 'rgba(46, 204, 113, 0.2)');
    
    // Create chart
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Count',
                    data: counts,
                    backgroundColor: primaryGradient,
                    borderColor: 'rgba(52, 152, 219, 1)',
                    borderWidth: 1,
                    yAxisID: 'y'
                },
                {
                    label: 'Amount ($)',
                    data: amounts,
                    backgroundColor: secondaryGradient,
                    borderColor: 'rgba(46, 204, 113, 1)',
                    borderWidth: 1,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.dataset.yAxisID === 'y1') {
                                label += formatCurrency(context.raw);
                            } else {
                                label += context.raw;
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    grid: {
                        drawOnChartArea: false
                    },
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        },
                        color: 'rgba(255, 255, 255, 0.7)'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    }
                }
            }
        }
    });
}

// Initialize opportunity timeline chart
function initializeOpportunityTimeline() {
    const timelineElement = document.getElementById('opportunityTimeline');
    const opportunities = JSON.parse(timelineElement.getAttribute('data-opportunities') || '[]');
    
    // Organize opportunities by month
    const months = {};
    
    opportunities.forEach(opportunity => {
        const closeDate = new Date(opportunity.close_date);
        const monthKey = closeDate.toLocaleString('default', { month: 'short' }) + ' ' + closeDate.getFullYear();
        
        if (!months[monthKey]) {
            months[monthKey] = 0;
        }
        
        months[monthKey] += parseFloat(opportunity.amount || 0);
    });
    
    // Convert to arrays for chart
    const labels = Object.keys(months);
    const data = Object.values(months);
    
    const ctx = timelineElement.getContext('2d');
    
    // Create gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(52, 152, 219, 0.8)');
    gradient.addColorStop(1, 'rgba(52, 152, 219, 0.2)');
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Opportunity Amount',
                data: data,
                backgroundColor: gradient,
                borderColor: 'rgba(52, 152, 219, 1)',
                borderWidth: 2,
                pointBackgroundColor: 'rgba(52, 152, 219, 1)',
                pointBorderColor: '#fff',
                pointRadius: 5,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return formatCurrency(context.raw);
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        },
                        color: 'rgba(255, 255, 255, 0.7)'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    }
                }
            }
        }
    });
}

// Initialize sales funnel
function initializeSalesFunnel() {
    const funnelElement = document.getElementById('salesFunnel');
    const labels = JSON.parse(funnelElement.getAttribute('data-stages') || '[]');
    const data = JSON.parse(funnelElement.getAttribute('data-counts') || '[]');
    
    const ctx = funnelElement.getContext('2d');
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    'rgba(52, 152, 219, 0.7)',
                    'rgba(46, 204, 113, 0.7)',
                    'rgba(155, 89, 182, 0.7)',
                    'rgba(52, 73, 94, 0.7)',
                    'rgba(22, 160, 133, 0.7)',
                    'rgba(243, 156, 18, 0.7)'
                ],
                borderColor: [
                    'rgba(52, 152, 219, 1)',
                    'rgba(46, 204, 113, 1)',
                    'rgba(155, 89, 182, 1)',
                    'rgba(52, 73, 94, 1)',
                    'rgba(22, 160, 133, 1)',
                    'rgba(243, 156, 18, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    }
                }
            }
        }
    });
}

// Initialize activity chart
function initializeActivityChart() {
    const activityElement = document.getElementById('activityChart');
    const labels = JSON.parse(activityElement.getAttribute('data-labels') || '[]');
    const data = JSON.parse(activityElement.getAttribute('data-values') || '[]');
    
    const ctx = activityElement.getContext('2d');
    
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    'rgba(52, 152, 219, 0.7)',
                    'rgba(46, 204, 113, 0.7)',
                    'rgba(155, 89, 182, 0.7)',
                    'rgba(52, 73, 94, 0.7)'
                ],
                borderColor: [
                    'rgba(52, 152, 219, 1)',
                    'rgba(46, 204, 113, 1)',
                    'rgba(155, 89, 182, 1)',
                    'rgba(52, 73, 94, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    }
                }
            }
        }
    });
}

// Fetch updated dashboard data
function refreshDashboardData() {
    ajaxRequest('/api/dashboard/data', 'GET', null, 
        function(response) {
            // Update metrics
            document.getElementById('prospectCount').textContent = response.prospect_count;
            document.getElementById('opportunityCount').textContent = response.opportunity_count;
            document.getElementById('contactCount').textContent = response.contact_count;
            document.getElementById('accountCount').textContent = response.account_count;
            document.getElementById('totalOpportunityAmount').textContent = formatCurrency(response.total_opportunity_amount);
            
            // Refresh charts
            initializePipelineChart();
            initializeOpportunityTimeline();
            initializeSalesFunnel();
            
            // Update recent prospects list
            const recentProspectsList = document.getElementById('recentProspects');
            if (recentProspectsList && response.recent_prospects) {
                recentProspectsList.innerHTML = '';
                response.recent_prospects.forEach(prospect => {
                    const li = document.createElement('li');
                    li.className = 'list-group-item d-flex justify-content-between align-items-center';
                    li.innerHTML = `
                        <div>
                            <strong>${prospect.first_name} ${prospect.last_name}</strong>
                            <small class="d-block text-muted">${prospect.company || 'No company'}</small>
                        </div>
                        <span class="badge rounded-pill bg-primary">${prospect.status}</span>
                    `;
                    recentProspectsList.appendChild(li);
                });
            }
            
            showNotification('Dashboard data refreshed successfully', 'success');
        },
        function(error) {
            showNotification('Error refreshing dashboard data: ' + error, 'danger');
        }
    );
}
