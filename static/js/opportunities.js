// Opportunities JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize pipeline chart if it exists
    const pipelineChartElement = document.getElementById('pipelineChart');
    if (pipelineChartElement) {
        initializePipelineChart();
    }

    // Handle opportunity stage changes
    const stageSelects = document.querySelectorAll('.opportunity-stage-select');
    if (stageSelects.length > 0) {
        stageSelects.forEach(select => {
            select.addEventListener('change', function() {
                const opportunityId = this.getAttribute('data-opportunity-id');
                updateOpportunityStage(opportunityId, this.value);
            });
        });
    }

    // Handle search form
    const searchForm = document.getElementById('opportunitySearchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const searchInput = document.getElementById('opportunitySearchInput');
            if (!searchInput.value.trim()) {
                e.preventDefault();
            }
        });
    }

    // Handle bulk actions
    const bulkActionSelect = document.getElementById('bulkActionSelect');
    const bulkActionBtn = document.getElementById('bulkActionBtn');
    
    if (bulkActionBtn && bulkActionSelect) {
        bulkActionBtn.addEventListener('click', function() {
            const selectedOpportunities = Array.from(document.querySelectorAll('.opportunity-checkbox:checked')).map(cb => cb.value);
            
            if (selectedOpportunities.length === 0) {
                showNotification('No opportunities selected', 'warning');
                return;
            }
            
            const action = bulkActionSelect.value;
            
            if (action === 'delete') {
                if (confirm('Are you sure you want to delete the selected opportunities?')) {
                    bulkDeleteOpportunities(selectedOpportunities);
                }
            } else if (action === 'change_stage') {
                // Show stage change modal
                const modal = new bootstrap.Modal(document.getElementById('changeStageModal'));
                modal.show();
                
                // Set selected IDs in hidden field
                document.getElementById('selectedOpportunitiesIds').value = selectedOpportunities.join(',');
            }
        });
    }

    // Handle bulk stage change form submission
    const changeStageForm = document.getElementById('changeStageForm');
    if (changeStageForm) {
        changeStageForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const selectedOpportunities = document.getElementById('selectedOpportunitiesIds').value.split(',');
            const newStage = document.getElementById('newStageSelect').value;
            
            bulkUpdateOpportunityStage(selectedOpportunities, newStage);
            
            // Hide modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('changeStageModal'));
            modal.hide();
        });
    }

    // Handle "Select All" checkbox
    const selectAllCheckbox = document.getElementById('selectAllOpportunities');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const isChecked = this.checked;
            const checkboxes = document.querySelectorAll('.opportunity-checkbox');
            
            checkboxes.forEach(checkbox => {
                checkbox.checked = isChecked;
            });
        });
    }

    // Attach event listeners to opportunity form (if it exists)
    const opportunityForm = document.getElementById('opportunityForm');
    if (opportunityForm) {
        // Format amount
        const amountInput = document.getElementById('amount');
        if (amountInput) {
            amountInput.addEventListener('blur', function() {
                formatAmountInput(this);
            });
        }
        
        // Update probability based on stage
        const stageSelect = document.getElementById('stage');
        const probabilityInput = document.getElementById('probability');
        
        if (stageSelect && probabilityInput) {
            stageSelect.addEventListener('change', function() {
                updateProbabilityFromStage(this.value, probabilityInput);
            });
        }
        
        // Set current date as default for close date if empty
        const closeDateInput = document.getElementById('close_date');
        if (closeDateInput && !closeDateInput.value) {
            const today = new Date();
            closeDateInput.value = today.toISOString().substr(0, 10);
        }
    }
});

// Initialize pipeline chart
function initializePipelineChart() {
    // Fetch stage data
    ajaxRequest('/api/opportunities/stage_counts', 'GET', null, 
        function(response) {
            const pipelineChartElement = document.getElementById('pipelineChart');
            const ctx = pipelineChartElement.getContext('2d');
            
            // Get data from response
            const stages = response.stages;
            const counts = response.counts;
            const amounts = response.amounts;
            
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
                    labels: stages,
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
        },
        function(error) {
            console.error('Error fetching stage data:', error);
        }
    );
}

// Update opportunity stage
function updateOpportunityStage(opportunityId, newStage) {
    ajaxRequest('/opportunities/update_stage', 'POST', {
        opportunity_id: opportunityId,
        stage: newStage
    }, 
    function(response) {
        if (response.success) {
            showNotification('Stage updated successfully', 'success');
            
            // Refresh the pipeline chart
            initializePipelineChart();
            
            // Update stage badge in table
            const stageBadge = document.querySelector(`.opportunity-stage-badge[data-opportunity-id="${opportunityId}"]`);
            if (stageBadge) {
                stageBadge.textContent = newStage;
                
                // Update badge color based on stage
                stageBadge.className = 'badge rounded-pill opportunity-stage-badge';
                
                switch(newStage) {
                    case 'Qualification':
                        stageBadge.classList.add('bg-primary');
                        break;
                    case 'Needs Analysis':
                        stageBadge.classList.add('bg-info');
                        break;
                    case 'Proposal':
                        stageBadge.classList.add('bg-warning');
                        break;
                    case 'Negotiation':
                        stageBadge.classList.add('bg-secondary');
                        break;
                    case 'Closed Won':
                        stageBadge.classList.add('bg-success');
                        break;
                    case 'Closed Lost':
                        stageBadge.classList.add('bg-danger');
                        break;
                    default:
                        stageBadge.classList.add('bg-secondary');
                }
            }
            
            // Update probability if displayed
            const probabilityElement = document.querySelector(`.opportunity-probability[data-opportunity-id="${opportunityId}"]`);
            if (probabilityElement) {
                const newProbability = getProbabilityFromStage(newStage);
                probabilityElement.textContent = newProbability + '%';
            }
        } else {
            showNotification(response.message || 'Error updating stage', 'danger');
        }
    },
    function(error) {
        showNotification('Error updating stage: ' + error, 'danger');
    });
}

// Bulk delete opportunities
function bulkDeleteOpportunities(opportunityIds) {
    ajaxRequest('/opportunities/bulk_delete', 'POST', {
        opportunity_ids: opportunityIds.join(',')
    }, 
    function(response) {
        if (response.success) {
            showNotification('Opportunities deleted successfully', 'success');
            
            // Remove rows from table
            opportunityIds.forEach(id => {
                const row = document.querySelector(`tr[data-opportunity-id="${id}"]`);
                if (row) row.remove();
            });
            
            // Refresh the pipeline chart
            initializePipelineChart();
            
            // Uncheck "Select All" checkbox
            const selectAllCheckbox = document.getElementById('selectAllOpportunities');
            if (selectAllCheckbox) selectAllCheckbox.checked = false;
        } else {
            showNotification(response.message || 'Error deleting opportunities', 'danger');
        }
    },
    function(error) {
        showNotification('Error deleting opportunities: ' + error, 'danger');
    });
}

// Bulk update opportunity stage
function bulkUpdateOpportunityStage(opportunityIds, newStage) {
    ajaxRequest('/opportunities/bulk_update_stage', 'POST', {
        opportunity_ids: opportunityIds.join(','),
        stage: newStage
    }, 
    function(response) {
        if (response.success) {
            showNotification('Stage updated successfully for ' + opportunityIds.length + ' opportunities', 'success');
            
            // Update stage badges in table
            opportunityIds.forEach(id => {
                const stageBadge = document.querySelector(`.opportunity-stage-badge[data-opportunity-id="${id}"]`);
                if (stageBadge) {
                    stageBadge.textContent = newStage;
                    
                    // Update badge color based on stage
                    stageBadge.className = 'badge rounded-pill opportunity-stage-badge';
                    
                    switch(newStage) {
                        case 'Qualification':
                            stageBadge.classList.add('bg-primary');
                            break;
                        case 'Needs Analysis':
                            stageBadge.classList.add('bg-info');
                            break;
                        case 'Proposal':
                            stageBadge.classList.add('bg-warning');
                            break;
                        case 'Negotiation':
                            stageBadge.classList.add('bg-secondary');
                            break;
                        case 'Closed Won':
                            stageBadge.classList.add('bg-success');
                            break;
                        case 'Closed Lost':
                            stageBadge.classList.add('bg-danger');
                            break;
                        default:
                            stageBadge.classList.add('bg-secondary');
                    }
                }
                
                // Update stage select
                const stageSelect = document.querySelector(`.opportunity-stage-select[data-opportunity-id="${id}"]`);
                if (stageSelect) {
                    stageSelect.value = newStage;
                }
                
                // Update probability if displayed
                const probabilityElement = document.querySelector(`.opportunity-probability[data-opportunity-id="${id}"]`);
                if (probabilityElement) {
                    const newProbability = getProbabilityFromStage(newStage);
                    probabilityElement.textContent = newProbability + '%';
                }
            });
            
            // Refresh the pipeline chart
            initializePipelineChart();
            
            // Uncheck all checkboxes
            const checkboxes = document.querySelectorAll('.opportunity-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = false;
            });
            
            const selectAllCheckbox = document.getElementById('selectAllOpportunities');
            if (selectAllCheckbox) selectAllCheckbox.checked = false;
        } else {
            showNotification(response.message || 'Error updating stages', 'danger');
        }
    },
    function(error) {
        showNotification('Error updating stages: ' + error, 'danger');
    });
}

// Format amount input
function formatAmountInput(input) {
    let value = input.value.replace(/[^\d.]/g, '');
    
    // Ensure it's a valid number
    if (value && !isNaN(parseFloat(value))) {
        input.value = parseFloat(value).toFixed(2);
    } else if (value === '') {
        input.value = '';
    } else {
        input.value = '0.00';
    }
}

// Get default probability based on stage
function getProbabilityFromStage(stage) {
    switch(stage) {
        case 'Qualification':
            return 10;
        case 'Needs Analysis':
            return 30;
        case 'Proposal':
            return 50;
        case 'Negotiation':
            return 70;
        case 'Closed Won':
            return 100;
        case 'Closed Lost':
            return 0;
        default:
            return 10;
    }
}

// Update probability input based on stage
function updateProbabilityFromStage(stage, probabilityInput) {
    const probability = getProbabilityFromStage(stage);
    probabilityInput.value = probability;
}
