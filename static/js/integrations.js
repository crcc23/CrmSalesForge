// Integrations JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tabs if they exist
    const integrationsTabs = document.getElementById('integrationsTabs');
    if (integrationsTabs) {
        const triggerTabList = [].slice.call(integrationsTabs.querySelectorAll('button'));
        triggerTabList.forEach(function (triggerEl) {
            const tabTrigger = new bootstrap.Tab(triggerEl);
            
            triggerEl.addEventListener('click', function (event) {
                event.preventDefault();
                tabTrigger.show();
            });
        });
    }
    
    // Email Campaign Recipients
    initEmailCampaignRecipients();
    
    // WhatsApp Campaign Recipients
    initWhatsAppCampaignRecipients();
    
    // AI Content Generation
    initAIContentGeneration();
    
    // Web Scraping
    initWebScraping();
});

// Initialize Email Campaign Recipients
function initEmailCampaignRecipients() {
    // Add email recipient
    const addEmailRecipientForm = document.getElementById('addEmailRecipientForm');
    if (addEmailRecipientForm) {
        addEmailRecipientForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const campaignId = document.getElementById('campaign_id').value;
            const recipientType = document.getElementById('recipient_type').value;
            const recipientId = document.getElementById('recipient_id').value;
            
            if (!recipientId) {
                showNotification('Please select a recipient', 'warning');
                return;
            }
            
            addEmailRecipient(campaignId, recipientType, recipientId);
        });
    }
    
    // Handle recipient type change to update recipients dropdown
    const recipientTypeSelect = document.getElementById('recipient_type');
    if (recipientTypeSelect) {
        recipientTypeSelect.addEventListener('change', function() {
            updateRecipientDropdown(this.value);
        });
    }
    
    // Remove email recipient
    const removeEmailRecipientBtns = document.querySelectorAll('.remove-email-recipient');
    if (removeEmailRecipientBtns.length > 0) {
        removeEmailRecipientBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const recipientId = this.getAttribute('data-recipient-id');
                removeEmailRecipient(recipientId);
            });
        });
    }
}

// Update recipient dropdown based on selected type
function updateRecipientDropdown(type) {
    const recipientSelect = document.getElementById('recipient_id');
    const contactsContainer = document.getElementById('contacts-container');
    const prospectsContainer = document.getElementById('prospects-container');
    
    if (type === 'contact') {
        if (contactsContainer) contactsContainer.style.display = 'block';
        if (prospectsContainer) prospectsContainer.style.display = 'none';
    } else {
        if (contactsContainer) contactsContainer.style.display = 'none';
        if (prospectsContainer) prospectsContainer.style.display = 'block';
    }
}

// Add email recipient
function addEmailRecipient(campaignId, recipientType, recipientId) {
    ajaxRequest('/integrations/email/add_recipient', 'POST', {
        campaign_id: campaignId,
        recipient_type: recipientType,
        recipient_id: recipientId
    }, 
    function(response) {
        if (response.success) {
            showNotification('Recipient added successfully', 'success');
            
            // Add recipient to the list
            const recipientsList = document.getElementById('emailRecipientsList');
            const newRecipient = document.createElement('li');
            newRecipient.className = 'list-group-item d-flex justify-content-between align-items-center';
            newRecipient.setAttribute('data-recipient-id', response.recipient.id);
            
            newRecipient.innerHTML = `
                <div>
                    <span class="badge rounded-pill bg-${recipientType === 'contact' ? 'primary' : 'secondary'} me-2">
                        ${recipientType === 'contact' ? 'Contact' : 'Prospect'}
                    </span>
                    <strong>${response.recipient.name}</strong>
                    <small class="text-muted ms-2">${response.recipient.email}</small>
                </div>
                <button type="button" class="btn btn-sm btn-outline-danger remove-email-recipient" data-recipient-id="${response.recipient.id}">
                    <i class="fas fa-times"></i>
                </button>
            `;
            
            recipientsList.appendChild(newRecipient);
            
            // Add event listener to new remove button
            const removeBtn = newRecipient.querySelector('.remove-email-recipient');
            removeBtn.addEventListener('click', function() {
                const recipientId = this.getAttribute('data-recipient-id');
                removeEmailRecipient(recipientId);
            });
            
            // Reset select
            document.getElementById('recipient_id').value = '';
        } else {
            showNotification(response.message || 'Error adding recipient', 'danger');
        }
    },
    function(error) {
        showNotification('Error adding recipient: ' + error, 'danger');
    });
}

// Remove email recipient
function removeEmailRecipient(recipientId) {
    ajaxRequest('/integrations/email/remove_recipient', 'POST', {
        recipient_id: recipientId
    }, 
    function(response) {
        if (response.success) {
            showNotification('Recipient removed successfully', 'success');
            
            // Remove recipient from the list
            const recipientItem = document.querySelector(`li[data-recipient-id="${recipientId}"]`);
            if (recipientItem) {
                recipientItem.remove();
            }
        } else {
            showNotification(response.message || 'Error removing recipient', 'danger');
        }
    },
    function(error) {
        showNotification('Error removing recipient: ' + error, 'danger');
    });
}

// Initialize WhatsApp Campaign Recipients
function initWhatsAppCampaignRecipients() {
    // Add WhatsApp recipient
    const addWhatsAppRecipientForm = document.getElementById('addWhatsAppRecipientForm');
    if (addWhatsAppRecipientForm) {
        addWhatsAppRecipientForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const campaignId = document.getElementById('whatsapp_campaign_id').value;
            const recipientType = document.getElementById('whatsapp_recipient_type').value;
            const recipientId = document.getElementById('whatsapp_recipient_id').value;
            
            if (!recipientId) {
                showNotification('Please select a recipient', 'warning');
                return;
            }
            
            addWhatsAppRecipient(campaignId, recipientType, recipientId);
        });
    }
    
    // Handle recipient type change to update recipients dropdown
    const recipientTypeSelect = document.getElementById('whatsapp_recipient_type');
    if (recipientTypeSelect) {
        recipientTypeSelect.addEventListener('change', function() {
            updateWhatsAppRecipientDropdown(this.value);
        });
    }
    
    // Remove WhatsApp recipient
    const removeWhatsAppRecipientBtns = document.querySelectorAll('.remove-whatsapp-recipient');
    if (removeWhatsAppRecipientBtns.length > 0) {
        removeWhatsAppRecipientBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const recipientId = this.getAttribute('data-recipient-id');
                removeWhatsAppRecipient(recipientId);
            });
        });
    }
}

// Update WhatsApp recipient dropdown based on selected type
function updateWhatsAppRecipientDropdown(type) {
    const contactsContainer = document.getElementById('whatsapp-contacts-container');
    const prospectsContainer = document.getElementById('whatsapp-prospects-container');
    
    if (type === 'contact') {
        if (contactsContainer) contactsContainer.style.display = 'block';
        if (prospectsContainer) prospectsContainer.style.display = 'none';
    } else {
        if (contactsContainer) contactsContainer.style.display = 'none';
        if (prospectsContainer) prospectsContainer.style.display = 'block';
    }
}

// Add WhatsApp recipient
function addWhatsAppRecipient(campaignId, recipientType, recipientId) {
    ajaxRequest('/integrations/whatsapp/add_recipient', 'POST', {
        campaign_id: campaignId,
        recipient_type: recipientType,
        recipient_id: recipientId
    }, 
    function(response) {
        if (response.success) {
            showNotification('Recipient added successfully', 'success');
            
            // Add recipient to the list
            const recipientsList = document.getElementById('whatsappRecipientsList');
            const newRecipient = document.createElement('li');
            newRecipient.className = 'list-group-item d-flex justify-content-between align-items-center';
            newRecipient.setAttribute('data-recipient-id', response.recipient.id);
            
            newRecipient.innerHTML = `
                <div>
                    <span class="badge rounded-pill bg-${recipientType === 'contact' ? 'primary' : 'secondary'} me-2">
                        ${recipientType === 'contact' ? 'Contact' : 'Prospect'}
                    </span>
                    <strong>${response.recipient.name}</strong>
                    <small class="text-muted ms-2">${response.recipient.phone}</small>
                </div>
                <button type="button" class="btn btn-sm btn-outline-danger remove-whatsapp-recipient" data-recipient-id="${response.recipient.id}">
                    <i class="fas fa-times"></i>
                </button>
            `;
            
            recipientsList.appendChild(newRecipient);
            
            // Add event listener to new remove button
            const removeBtn = newRecipient.querySelector('.remove-whatsapp-recipient');
            removeBtn.addEventListener('click', function() {
                const recipientId = this.getAttribute('data-recipient-id');
                removeWhatsAppRecipient(recipientId);
            });
            
            // Reset select
            document.getElementById('whatsapp_recipient_id').value = '';
        } else {
            showNotification(response.message || 'Error adding recipient', 'danger');
        }
    },
    function(error) {
        showNotification('Error adding recipient: ' + error, 'danger');
    });
}

// Remove WhatsApp recipient
function removeWhatsAppRecipient(recipientId) {
    ajaxRequest('/integrations/whatsapp/remove_recipient', 'POST', {
        recipient_id: recipientId
    }, 
    function(response) {
        if (response.success) {
            showNotification('Recipient removed successfully', 'success');
            
            // Remove recipient from the list
            const recipientItem = document.querySelector(`li[data-recipient-id="${recipientId}"]`);
            if (recipientItem) {
                recipientItem.remove();
            }
        } else {
            showNotification(response.message || 'Error removing recipient', 'danger');
        }
    },
    function(error) {
        showNotification('Error removing recipient: ' + error, 'danger');
    });
}

// Initialize AI Content Generation
function initAIContentGeneration() {
    // Handle content type change
    const contentTypeSelect = document.getElementById('content_type');
    const promptHelperText = document.getElementById('promptHelperText');
    
    if (contentTypeSelect && promptHelperText) {
        contentTypeSelect.addEventListener('change', function() {
            updatePromptHelper(this.value);
        });
        
        // Initialize with current value
        if (contentTypeSelect.value) {
            updatePromptHelper(contentTypeSelect.value);
        }
    }
}

// Update prompt helper text based on content type
function updatePromptHelper(contentType) {
    const promptHelperText = document.getElementById('promptHelperText');
    if (!promptHelperText) return;
    
    switch(contentType) {
        case 'email':
            promptHelperText.textContent = 'Describe the email you want to generate. Include subject matter, tone, and key points.';
            break;
        case 'blog':
            promptHelperText.textContent = 'Describe the blog post you want to create. Include topic, target audience, and key points.';
            break;
        case 'social':
            promptHelperText.textContent = 'Describe the social media post you want to generate. Include platform, purpose, and tone.';
            break;
        case 'whatsapp':
            promptHelperText.textContent = 'Describe the WhatsApp message you want to create. Keep it concise and direct.';
            break;
        default:
            promptHelperText.textContent = 'Enter your prompt for AI content generation.';
    }
}

// Initialize Web Scraping
function initWebScraping() {
    // Handle frequency change
    const frequencySelect = document.getElementById('frequency');
    const frequencyHelperText = document.getElementById('frequencyHelperText');
    
    if (frequencySelect && frequencyHelperText) {
        frequencySelect.addEventListener('change', function() {
            updateFrequencyHelper(this.value);
        });
        
        // Initialize with current value
        if (frequencySelect.value) {
            updateFrequencyHelper(frequencySelect.value);
        }
    }
    
    // URL validation
    const urlInput = document.getElementById('url');
    if (urlInput) {
        urlInput.addEventListener('blur', function() {
            validateUrl(this);
        });
    }
}

// Update frequency helper text
function updateFrequencyHelper(frequency) {
    const frequencyHelperText = document.getElementById('frequencyHelperText');
    if (!frequencyHelperText) return;
    
    switch(frequency) {
        case 'once':
            frequencyHelperText.textContent = 'The website will be scraped once immediately.';
            break;
        case 'daily':
            frequencyHelperText.textContent = 'The website will be scraped daily.';
            break;
        case 'weekly':
            frequencyHelperText.textContent = 'The website will be scraped once a week.';
            break;
        case 'monthly':
            frequencyHelperText.textContent = 'The website will be scraped once a month.';
            break;
        default:
            frequencyHelperText.textContent = 'Select how often you want the website to be scraped.';
    }
}

// Validate URL
function validateUrl(input) {
    const url = input.value.trim();
    const urlRegex = /^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$/;
    
    if (url !== '' && !urlRegex.test(url)) {
        input.classList.add('is-invalid');
        const feedbackElement = input.nextElementSibling;
        if (feedbackElement && feedbackElement.classList.contains('invalid-feedback')) {
            feedbackElement.textContent = 'Please enter a valid URL';
        } else {
            const feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            feedback.textContent = 'Please enter a valid URL';
            input.parentNode.insertBefore(feedback, input.nextSibling);
        }
    } else {
        input.classList.remove('is-invalid');
        
        // Add https:// if missing
        if (url !== '' && !url.match(/^https?:\/\//)) {
            input.value = 'https://' + url;
        }
    }
}
