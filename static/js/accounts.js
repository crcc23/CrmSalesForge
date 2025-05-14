// Accounts JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize industry chart if it exists
    const industryChartElement = document.getElementById('industryChart');
    if (industryChartElement) {
        initializeIndustryChart();
    }

    // Handle account industry changes
    const industrySelects = document.querySelectorAll('.account-industry-select');
    if (industrySelects.length > 0) {
        industrySelects.forEach(select => {
            select.addEventListener('change', function() {
                const accountId = this.getAttribute('data-account-id');
                updateAccountIndustry(accountId, this.value);
            });
        });
    }

    // Handle search form
    const searchForm = document.getElementById('accountSearchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const searchInput = document.getElementById('accountSearchInput');
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
            const selectedAccounts = Array.from(document.querySelectorAll('.account-checkbox:checked')).map(cb => cb.value);
            
            if (selectedAccounts.length === 0) {
                showNotification('No accounts selected', 'warning');
                return;
            }
            
            const action = bulkActionSelect.value;
            
            if (action === 'delete') {
                if (confirm('Are you sure you want to delete the selected accounts?')) {
                    bulkDeleteAccounts(selectedAccounts);
                }
            } else if (action === 'change_industry') {
                // Show industry change modal
                const modal = new bootstrap.Modal(document.getElementById('changeIndustryModal'));
                modal.show();
                
                // Set selected IDs in hidden field
                document.getElementById('selectedAccountsIds').value = selectedAccounts.join(',');
            } else if (action === 'export') {
                exportAccounts(selectedAccounts);
            }
        });
    }

    // Handle bulk industry change form submission
    const changeIndustryForm = document.getElementById('changeIndustryForm');
    if (changeIndustryForm) {
        changeIndustryForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const selectedAccounts = document.getElementById('selectedAccountsIds').value.split(',');
            const newIndustry = document.getElementById('newIndustrySelect').value;
            
            bulkUpdateAccountIndustry(selectedAccounts, newIndustry);
            
            // Hide modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('changeIndustryModal'));
            modal.hide();
        });
    }

    // Handle "Select All" checkbox
    const selectAllCheckbox = document.getElementById('selectAllAccounts');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const isChecked = this.checked;
            const checkboxes = document.querySelectorAll('.account-checkbox');
            
            checkboxes.forEach(checkbox => {
                checkbox.checked = isChecked;
            });
        });
    }

    // Attach event listeners to account form (if it exists)
    const accountForm = document.getElementById('accountForm');
    if (accountForm) {
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
        
        // Format website URL
        const websiteInput = document.getElementById('website');
        if (websiteInput) {
            websiteInput.addEventListener('blur', function() {
                formatWebsiteUrl(this);
            });
        }
        
        // Format revenue and employees inputs
        const revenueInput = document.getElementById('annual_revenue');
        const employeesInput = document.getElementById('employees');
        
        if (revenueInput) {
            revenueInput.addEventListener('blur', function() {
                formatRevenueInput(this);
            });
        }
        
        if (employeesInput) {
            employeesInput.addEventListener('blur', function() {
                formatEmployeesInput(this);
            });
        }
    }
});

// Initialize industry chart
function initializeIndustryChart() {
    // Get data from data attribute
    const industryChartElement = document.getElementById('industryChart');
    const ctx = industryChartElement.getContext('2d');
    
    // Get data from HTML data attributes
    const industries = JSON.parse(industryChartElement.getAttribute('data-industries') || '[]');
    const counts = JSON.parse(industryChartElement.getAttribute('data-counts') || '[]');
    
    // Generate colors
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
    
    // Limit to top 7 industries for better visualization
    let chartData = [];
    let chartLabels = [];
    let otherCount = 0;
    
    if (industries.length > 7) {
        // Sort by count
        const combinedData = industries.map((industry, index) => {
            return { industry, count: counts[index] };
        });
        
        combinedData.sort((a, b) => b.count - a.count);
        
        // Take top 6 + "Other"
        for (let i = 0; i < combinedData.length; i++) {
            if (i < 6) {
                chartLabels.push(combinedData[i].industry);
                chartData.push(combinedData[i].count);
            } else {
                otherCount += combinedData[i].count;
            }
        }
        
        if (otherCount > 0) {
            chartLabels.push('Other');
            chartData.push(otherCount);
        }
    } else {
        chartLabels = industries;
        chartData = counts;
    }
    
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: chartLabels,
            datasets: [{
                data: chartData,
                backgroundColor: backgroundColors.slice(0, chartLabels.length),
                borderColor: borderColors.slice(0, chartLabels.length),
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

// Update account industry
function updateAccountIndustry(accountId, newIndustry) {
    ajaxRequest('/accounts/update_industry', 'POST', {
        account_id: accountId,
        industry: newIndustry
    }, 
    function(response) {
        if (response.success) {
            showNotification('Industry updated successfully', 'success');
            
            // Update industry in table
            const industryCell = document.querySelector(`.account-industry[data-account-id="${accountId}"]`);
            if (industryCell) {
                industryCell.textContent = newIndustry || 'Not specified';
            }
        } else {
            showNotification(response.message || 'Error updating industry', 'danger');
        }
    },
    function(error) {
        showNotification('Error updating industry: ' + error, 'danger');
    });
}

// Bulk delete accounts
function bulkDeleteAccounts(accountIds) {
    ajaxRequest('/accounts/bulk_delete', 'POST', {
        account_ids: accountIds.join(',')
    }, 
    function(response) {
        if (response.success) {
            showNotification('Accounts deleted successfully', 'success');
            
            // Remove rows from table
            accountIds.forEach(id => {
                const row = document.querySelector(`tr[data-account-id="${id}"]`);
                if (row) row.remove();
            });
            
            // Uncheck "Select All" checkbox
            const selectAllCheckbox = document.getElementById('selectAllAccounts');
            if (selectAllCheckbox) selectAllCheckbox.checked = false;
        } else {
            showNotification(response.message || 'Error deleting accounts', 'danger');
        }
    },
    function(error) {
        showNotification('Error deleting accounts: ' + error, 'danger');
    });
}

// Bulk update account industry
function bulkUpdateAccountIndustry(accountIds, newIndustry) {
    ajaxRequest('/accounts/bulk_update_industry', 'POST', {
        account_ids: accountIds.join(','),
        industry: newIndustry
    }, 
    function(response) {
        if (response.success) {
            showNotification('Industry updated successfully for ' + accountIds.length + ' accounts', 'success');
            
            // Update industry in table
            accountIds.forEach(id => {
                const industryCell = document.querySelector(`.account-industry[data-account-id="${id}"]`);
                if (industryCell) {
                    industryCell.textContent = newIndustry || 'Not specified';
                }
                
                // Update industry select
                const industrySelect = document.querySelector(`.account-industry-select[data-account-id="${id}"]`);
                if (industrySelect) {
                    industrySelect.value = newIndustry;
                }
            });
            
            // Uncheck all checkboxes
            const checkboxes = document.querySelectorAll('.account-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = false;
            });
            
            const selectAllCheckbox = document.getElementById('selectAllAccounts');
            if (selectAllCheckbox) selectAllCheckbox.checked = false;
        } else {
            showNotification(response.message || 'Error updating industries', 'danger');
        }
    },
    function(error) {
        showNotification('Error updating industries: ' + error, 'danger');
    });
}

// Export accounts
function exportAccounts(accountIds) {
    // Create a form and submit it to get the CSV download
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/accounts/export';
    
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'account_ids';
    input.value = accountIds.join(',');
    
    form.appendChild(input);
    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);
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

// Format website URL
function formatWebsiteUrl(input) {
    let url = input.value.trim();
    
    if (url !== '' && !url.match(/^https?:\/\//)) {
        url = 'https://' + url;
    }
    
    input.value = url;
}

// Format revenue input
function formatRevenueInput(input) {
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

// Format employees input
function formatEmployeesInput(input) {
    let value = input.value.replace(/\D/g, '');
    
    if (value) {
        input.value = parseInt(value);
    } else {
        input.value = '';
    }
}
