// Prospects JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize status chart if it exists
    const statusChartElement = document.getElementById('statusChart');
    if (statusChartElement) {
        initializeStatusChart();
    }

    // Handle prospect status changes
    const statusSelects = document.querySelectorAll('.prospect-status-select');
    if (statusSelects.length > 0) {
        statusSelects.forEach(select => {
            select.addEventListener('change', function() {
                const prospectId = this.getAttribute('data-prospect-id');
                updateProspectStatus(prospectId, this.value);
            });
        });
    }

    // Handle search form
    const searchForm = document.getElementById('prospectSearchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const searchInput = document.getElementById('prospectSearchInput');
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
            const selectedProspects = Array.from(document.querySelectorAll('.prospect-checkbox:checked')).map(cb => cb.value);
            
            if (selectedProspects.length === 0) {
                showNotification('No prospects selected', 'warning');
                return;
            }
            
            const action = bulkActionSelect.value;
            
            if (action === 'delete') {
                if (confirm('Are you sure you want to delete the selected prospects?')) {
                    bulkDeleteProspects(selectedProspects);
                }
            } else if (action === 'change_status') {
                // Show status change modal
                const modal = new bootstrap.Modal(document.getElementById('changeStatusModal'));
                modal.show();
                
                // Set selected IDs in hidden field
                document.getElementById('selectedProspectsIds').value = selectedProspects.join(',');
            }
        });
    }

    // Handle bulk status change form submission
    const changeStatusForm = document.getElementById('changeStatusForm');
    if (changeStatusForm) {
        changeStatusForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const selectedProspects = document.getElementById('selectedProspectsIds').value.split(',');
            const newStatus = document.getElementById('newStatusSelect').value;
            
            bulkUpdateProspectStatus(selectedProspects, newStatus);
            
            // Hide modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('changeStatusModal'));
            modal.hide();
        });
    }

    // Handle "Select All" checkbox
    const selectAllCheckbox = document.getElementById('selectAllProspects');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const isChecked = this.checked;
            const checkboxes = document.querySelectorAll('.prospect-checkbox');
            
            checkboxes.forEach(checkbox => {
                checkbox.checked = isChecked;
            });
        });
    }

    // Attach event listeners to prospect form (if it exists)
    const prospectForm = document.getElementById('prospectForm');
    if (prospectForm) {
        // Validate email
        const emailInput = document.getElementById('email');
        if (emailInput) {
            emailInput.addEventListener('blur', function() {
                validateEmail(this);
            });
        }
        
        // Format phone number
        const phoneInput = document.getElementById('phone');
        if (phoneInput) {
            phoneInput.addEventListener('input', function() {
                formatPhoneNumber(this);
            });
        }
    }
});

// Initialize status chart
function initializeStatusChart() {
    // Fetch status counts
    ajaxRequest('/api/prospects/status_counts', 'GET', null, 
        function(response) {
            const statusChartElement = document.getElementById('statusChart');
            const ctx = statusChartElement.getContext('2d');
            
            // Convert the response to arrays for the chart
            const labels = Object.keys(response);
            const data = Object.values(response);
            
            const backgroundColors = [
                'rgba(52, 152, 219, 0.7)',
                'rgba(46, 204, 113, 0.7)',
                'rgba(155, 89, 182, 0.7)',
                'rgba(52, 73, 94, 0.7)',
                'rgba(241, 196, 15, 0.7)',
                'rgba(230, 126, 34, 0.7)',
                'rgba(231, 76, 60, 0.7)'
            ];
            
            const borderColors = [
                'rgba(52, 152, 219, 1)',
                'rgba(46, 204, 113, 1)',
                'rgba(155, 89, 182, 1)',
                'rgba(52, 73, 94, 1)',
                'rgba(241, 196, 15, 1)',
                'rgba(230, 126, 34, 1)',
                'rgba(231, 76, 60, 1)'
            ];
            
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
                        backgroundColor: backgroundColors.slice(0, labels.length),
                        borderColor: borderColors.slice(0, labels.length),
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
        },
        function(error) {
            console.error('Error fetching status counts:', error);
        }
    );
}

// Update prospect status
function updateProspectStatus(prospectId, newStatus) {
    ajaxRequest('/prospects/update_status', 'POST', {
        prospect_id: prospectId,
        status: newStatus
    }, 
    function(response) {
        if (response.success) {
            showNotification('Status updated successfully', 'success');
            
            // Refresh the status chart
            initializeStatusChart();
            
            // Update status badge in table
            const statusBadge = document.querySelector(`.prospect-status-badge[data-prospect-id="${prospectId}"]`);
            if (statusBadge) {
                statusBadge.textContent = newStatus;
                
                // Update badge color based on status
                statusBadge.className = 'badge rounded-pill prospect-status-badge';
                
                switch(newStatus) {
                    case 'New':
                        statusBadge.classList.add('bg-primary');
                        break;
                    case 'Contacted':
                        statusBadge.classList.add('bg-info');
                        break;
                    case 'Qualified':
                        statusBadge.classList.add('bg-success');
                        break;
                    case 'Disqualified':
                        statusBadge.classList.add('bg-danger');
                        break;
                    default:
                        statusBadge.classList.add('bg-secondary');
                }
            }
        } else {
            showNotification(response.message || 'Error updating status', 'danger');
        }
    },
    function(error) {
        showNotification('Error updating status: ' + error, 'danger');
    });
}

// Bulk delete prospects
function bulkDeleteProspects(prospectIds) {
    ajaxRequest('/prospects/bulk_delete', 'POST', {
        prospect_ids: prospectIds.join(',')
    }, 
    function(response) {
        if (response.success) {
            showNotification('Prospects deleted successfully', 'success');
            
            // Remove rows from table
            prospectIds.forEach(id => {
                const row = document.querySelector(`tr[data-prospect-id="${id}"]`);
                if (row) row.remove();
            });
            
            // Refresh the status chart
            initializeStatusChart();
            
            // Uncheck "Select All" checkbox
            const selectAllCheckbox = document.getElementById('selectAllProspects');
            if (selectAllCheckbox) selectAllCheckbox.checked = false;
        } else {
            showNotification(response.message || 'Error deleting prospects', 'danger');
        }
    },
    function(error) {
        showNotification('Error deleting prospects: ' + error, 'danger');
    });
}

// Bulk update prospect status
function bulkUpdateProspectStatus(prospectIds, newStatus) {
    ajaxRequest('/prospects/bulk_update_status', 'POST', {
        prospect_ids: prospectIds.join(','),
        status: newStatus
    }, 
    function(response) {
        if (response.success) {
            showNotification('Status updated successfully for ' + prospectIds.length + ' prospects', 'success');
            
            // Update status badges in table
            prospectIds.forEach(id => {
                const statusBadge = document.querySelector(`.prospect-status-badge[data-prospect-id="${id}"]`);
                if (statusBadge) {
                    statusBadge.textContent = newStatus;
                    
                    // Update badge color based on status
                    statusBadge.className = 'badge rounded-pill prospect-status-badge';
                    
                    switch(newStatus) {
                        case 'New':
                            statusBadge.classList.add('bg-primary');
                            break;
                        case 'Contacted':
                            statusBadge.classList.add('bg-info');
                            break;
                        case 'Qualified':
                            statusBadge.classList.add('bg-success');
                            break;
                        case 'Disqualified':
                            statusBadge.classList.add('bg-danger');
                            break;
                        default:
                            statusBadge.classList.add('bg-secondary');
                    }
                }
                
                // Update status select
                const statusSelect = document.querySelector(`.prospect-status-select[data-prospect-id="${id}"]`);
                if (statusSelect) {
                    statusSelect.value = newStatus;
                }
            });
            
            // Refresh the status chart
            initializeStatusChart();
            
            // Uncheck all checkboxes
            const checkboxes = document.querySelectorAll('.prospect-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = false;
            });
            
            const selectAllCheckbox = document.getElementById('selectAllProspects');
            if (selectAllCheckbox) selectAllCheckbox.checked = false;
        } else {
            showNotification(response.message || 'Error updating statuses', 'danger');
        }
    },
    function(error) {
        showNotification('Error updating statuses: ' + error, 'danger');
    });
}

// Validate email format
function validateEmail(input) {
    const email = input.value.trim();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    if (email !== '' && !emailRegex.test(email)) {
        input.classList.add('is-invalid');
        const feedbackElement = input.nextElementSibling;
        if (feedbackElement && feedbackElement.classList.contains('invalid-feedback')) {
            feedbackElement.textContent = 'Please enter a valid email address';
        } else {
            const feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            feedback.textContent = 'Please enter a valid email address';
            input.parentNode.insertBefore(feedback, input.nextSibling);
        }
    } else {
        input.classList.remove('is-invalid');
    }
}

// Format phone number
function formatPhoneNumber(input) {
    let value = input.value.replace(/\D/g, '');
    
    if (value.length > 10) {
        value = value.substring(0, 10);
    }
    
    if (value.length >= 7) {
        input.value = `(${value.substring(0, 3)}) ${value.substring(3, 6)}-${value.substring(6)}`;
    } else if (value.length >= 4) {
        input.value = `(${value.substring(0, 3)}) ${value.substring(3)}`;
    } else if (value.length > 0) {
        input.value = `(${value}`;
    } else {
        input.value = '';
    }
}
