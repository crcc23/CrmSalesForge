// Contacts JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Handle search form
    const searchForm = document.getElementById('contactSearchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const searchInput = document.getElementById('contactSearchInput');
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
            const selectedContacts = Array.from(document.querySelectorAll('.contact-checkbox:checked')).map(cb => cb.value);
            
            if (selectedContacts.length === 0) {
                showNotification('No contacts selected', 'warning');
                return;
            }
            
            const action = bulkActionSelect.value;
            
            if (action === 'delete') {
                if (confirm('Are you sure you want to delete the selected contacts?')) {
                    bulkDeleteContacts(selectedContacts);
                }
            } else if (action === 'change_account') {
                // Show account change modal
                const modal = new bootstrap.Modal(document.getElementById('changeAccountModal'));
                modal.show();
                
                // Set selected IDs in hidden field
                document.getElementById('selectedContactsIds').value = selectedContacts.join(',');
            } else if (action === 'export') {
                exportContacts(selectedContacts);
            }
        });
    }

    // Handle bulk account change form submission
    const changeAccountForm = document.getElementById('changeAccountForm');
    if (changeAccountForm) {
        changeAccountForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const selectedContacts = document.getElementById('selectedContactsIds').value.split(',');
            const newAccountId = document.getElementById('newAccountSelect').value;
            
            bulkUpdateContactAccount(selectedContacts, newAccountId);
            
            // Hide modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('changeAccountModal'));
            modal.hide();
        });
    }

    // Handle "Select All" checkbox
    const selectAllCheckbox = document.getElementById('selectAllContacts');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const isChecked = this.checked;
            const checkboxes = document.querySelectorAll('.contact-checkbox');
            
            checkboxes.forEach(checkbox => {
                checkbox.checked = isChecked;
            });
        });
    }

    // Attach event listeners to contact form (if it exists)
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        // Validate email
        const emailInput = document.getElementById('email');
        if (emailInput) {
            emailInput.addEventListener('blur', function() {
                validateEmail(this);
            });
        }
        
        // Format phone numbers
        const phoneInput = document.getElementById('phone');
        const mobileInput = document.getElementById('mobile');
        
        if (phoneInput) {
            phoneInput.addEventListener('input', function() {
                formatPhoneNumber(this);
            });
        }
        
        if (mobileInput) {
            mobileInput.addEventListener('input', function() {
                formatPhoneNumber(this);
            });
        }
    }
});

// Bulk delete contacts
function bulkDeleteContacts(contactIds) {
    ajaxRequest('/contacts/bulk_delete', 'POST', {
        contact_ids: contactIds.join(',')
    }, 
    function(response) {
        if (response.success) {
            showNotification('Contacts deleted successfully', 'success');
            
            // Remove rows from table
            contactIds.forEach(id => {
                const row = document.querySelector(`tr[data-contact-id="${id}"]`);
                if (row) row.remove();
            });
            
            // Uncheck "Select All" checkbox
            const selectAllCheckbox = document.getElementById('selectAllContacts');
            if (selectAllCheckbox) selectAllCheckbox.checked = false;
        } else {
            showNotification(response.message || 'Error deleting contacts', 'danger');
        }
    },
    function(error) {
        showNotification('Error deleting contacts: ' + error, 'danger');
    });
}

// Bulk update contact account
function bulkUpdateContactAccount(contactIds, newAccountId) {
    ajaxRequest('/contacts/bulk_update_account', 'POST', {
        contact_ids: contactIds.join(','),
        account_id: newAccountId
    }, 
    function(response) {
        if (response.success) {
            showNotification('Account updated successfully for ' + contactIds.length + ' contacts', 'success');
            
            // Get new account name
            const accountSelect = document.getElementById('newAccountSelect');
            const accountName = accountSelect.options[accountSelect.selectedIndex].text;
            
            // Update account name in table
            contactIds.forEach(id => {
                const accountCell = document.querySelector(`.contact-account[data-contact-id="${id}"]`);
                if (accountCell) {
                    if (newAccountId && newAccountId !== '') {
                        accountCell.textContent = accountName;
                    } else {
                        accountCell.textContent = 'No Account';
                    }
                }
            });
            
            // Uncheck all checkboxes
            const checkboxes = document.querySelectorAll('.contact-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = false;
            });
            
            const selectAllCheckbox = document.getElementById('selectAllContacts');
            if (selectAllCheckbox) selectAllCheckbox.checked = false;
        } else {
            showNotification(response.message || 'Error updating accounts', 'danger');
        }
    },
    function(error) {
        showNotification('Error updating accounts: ' + error, 'danger');
    });
}

// Export contacts
function exportContacts(contactIds) {
    // Create a form and submit it to get the CSV download
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/contacts/export';
    
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'contact_ids';
    input.value = contactIds.join(',');
    
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
