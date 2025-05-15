document.addEventListener('DOMContentLoaded', function() {
    // Function to create and append a modal to the document
    function createModal(id, title, content) {
        const modalHTML = `
        <div class="modal fade" id="${id}" tabindex="-1" aria-labelledby="${id}Label" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="${id}Label">${title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        ${content}
                    </div>
                </div>
            </div>
        </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }
    
    // Create modals for each integration
    
    // OpenAI API Modal
    const openaiContent = `
        <form id="openaiForm" method="post" action="/integration/openai">
            <div class="mb-3">
                <p>Configura los ajustes de conexión para OpenAI API</p>
                <label for="openai_api_key" class="form-label">API Key</label>
                <input type="password" class="form-control" id="openai_api_key" name="api_key" required>
            </div>
            <div class="d-flex justify-content-between">
                <button type="submit" class="btn btn-primary">GUARDAR CONFIGURACIÓN</button>
                <button type="button" class="btn btn-outline-success" id="testOpenAI">PROBAR CONEXIÓN</button>
            </div>
        </form>
    `;
    createModal('openaiModal', 'Configuración de OpenAI API', openaiContent);
    
    // Claude API Modal
    const claudeContent = `
        <form id="claudeForm" method="post" action="/integration/claude">
            <div class="mb-3">
                <p>Configura los ajustes de conexión para Claude API</p>
                <label for="claude_api_key" class="form-label">API Key</label>
                <input type="password" class="form-control" id="claude_api_key" name="api_key" required>
            </div>
            <div class="d-flex justify-content-between">
                <button type="submit" class="btn btn-primary">GUARDAR CONFIGURACIÓN</button>
                <button type="button" class="btn btn-outline-success" id="testClaude">PROBAR CONEXIÓN</button>
            </div>
        </form>
    `;
    createModal('claudeModal', 'Configuración de Claude API', claudeContent);
    
    // Gemini API Modal
    const geminiContent = `
        <form id="geminiForm" method="post" action="/integration/gemini">
            <div class="mb-3">
                <p>Configura los ajustes de conexión para Gemini API</p>
                <label for="gemini_api_key" class="form-label">API Key</label>
                <input type="password" class="form-control" id="gemini_api_key" name="api_key" required>
            </div>
            <div class="d-flex justify-content-between">
                <button type="submit" class="btn btn-primary">GUARDAR CONFIGURACIÓN</button>
                <button type="button" class="btn btn-outline-success" id="testGemini">PROBAR CONEXIÓN</button>
            </div>
        </form>
    `;
    createModal('geminiModal', 'Configuración de Gemini API', geminiContent);
    
    // Evolution API Modal
    const evolutionContent = `
        <form id="evolutionForm" method="post" action="/integration/evolution">
            <div class="mb-3">
                <p>Configura los ajustes de conexión para Evolution API (WhatsApp)</p>
                <label for="evolution_base_url" class="form-label">URL Base de Evolution API</label>
                <input type="text" class="form-control mb-3" id="evolution_base_url" name="base_url" required>
                
                <label for="evolution_instance" class="form-label">Nombre de Instancia</label>
                <input type="text" class="form-control mb-3" id="evolution_instance" name="instance_name" required>
                
                <label for="evolution_api_key" class="form-label">API Key</label>
                <input type="password" class="form-control" id="evolution_api_key" name="api_key" required>
            </div>
            <div class="d-flex justify-content-between">
                <button type="submit" class="btn btn-primary">GUARDAR CONFIGURACIÓN</button>
                <button type="button" class="btn btn-outline-success" id="testEvolution">PROBAR CONEXIÓN</button>
            </div>
        </form>
    `;
    createModal('evolutionModal', 'Configuración de API Evolution', evolutionContent);
    
    // SMTP/IMAP Modal
    const smtpImapContent = `
        <form id="emailForm" method="post" action="/integration/smtp">
            <div class="mb-3">
                <p>Configura los ajustes de conexión para envío y recepción de correos (SMTP/IMAP)</p>
                <label for="email_username" class="form-label">Nombre de Usuario</label>
                <input type="text" class="form-control mb-3" id="email_username" name="username" required>
                
                <label for="email_password" class="form-label">Contraseña</label>
                <input type="password" class="form-control mb-3" id="email_password" name="password" required>
                
                <label for="smtp_server" class="form-label">Servidor Saliente (SMTP)</label>
                <input type="text" class="form-control mb-3" id="smtp_server" name="smtp_server" required>
                
                <label for="smtp_port" class="form-label">Puerto SMTP</label>
                <input type="number" class="form-control mb-3" id="smtp_port" name="smtp_port" value="587" required>
                
                <label for="imap_server" class="form-label">Servidor Entrante (IMAP)</label>
                <input type="text" class="form-control mb-3" id="imap_server" name="imap_server" required>
                
                <label for="imap_port" class="form-label">Puerto IMAP</label>
                <input type="number" class="form-control mb-3" id="imap_port" name="imap_port" value="993" required>
                
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="requires_auth" name="requires_auth" checked>
                    <label class="form-check-label" for="requires_auth">
                        Requiere Autenticación
                    </label>
                </div>
            </div>
            <div class="d-flex justify-content-between">
                <button type="submit" class="btn btn-primary">GUARDAR CONFIGURACIÓN</button>
                <button type="button" class="btn btn-outline-success" id="testEmail">PROBAR CONEXIÓN</button>
            </div>
        </form>
    `;
    createModal('smtpImapModal', 'Configuración de Envío de Emails (SMTP/IMAP)', smtpImapContent);
    
    // SERP API Modal
    const serpContent = `
        <form id="serpForm" method="post" action="/integration/serp">
            <div class="mb-3">
                <p>Ingresa tu API Key de SERP para habilitar funcionalidades de búsqueda avanzada.</p>
                <label for="serp_api_key" class="form-label">API Key</label>
                <input type="password" class="form-control" id="serp_api_key" name="api_key" required>
            </div>
            <div class="d-flex justify-content-between">
                <button type="submit" class="btn btn-primary">GUARDAR CONFIGURACIÓN</button>
                <button type="button" class="btn btn-outline-success" id="testSerp">PROBAR CONEXIÓN</button>
            </div>
        </form>
    `;
    createModal('serpModal', 'Configuración de SERP API Key', serpContent);
    
    // Google Maps API Modal
    const mapsContent = `
        <form id="mapsForm" method="post" action="/integration/maps">
            <div class="mb-3">
                <p>Ingresa tu API Key de Google Maps para habilitar funcionalidades de mapas y geolocalización.</p>
                <label for="maps_api_key" class="form-label">API Key</label>
                <input type="password" class="form-control" id="maps_api_key" name="api_key" required>
            </div>
            <div class="d-flex justify-content-between">
                <button type="submit" class="btn btn-primary">GUARDAR CONFIGURACIÓN</button>
                <button type="button" class="btn btn-outline-success" id="testMaps">PROBAR CONEXIÓN</button>
            </div>
        </form>
    `;
    createModal('mapsModal', 'Configuración de Google Maps API Key', mapsContent);
    
    // Add event listeners for test buttons
    const testButtons = {
        'testOpenAI': '/integration/test-connection/openai',
        'testClaude': '/integration/test-connection/claude',
        'testGemini': '/integration/test-connection/gemini',
        'testEvolution': '/integration/test-connection/evolution',
        'testEmail': '/integration/test-connection/smtp',
        'testSerp': '/integration/test-connection/serp',
        'testMaps': '/integration/test-connection/maps'
    };
    
    for (const [btnId, endpoint] of Object.entries(testButtons)) {
        const btn = document.getElementById(btnId);
        if (btn) {
            btn.addEventListener('click', function() {
                // Show loading state
                const originalText = this.innerHTML;
                this.disabled = true;
                this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Probando...';
                
                // Perform AJAX request to test connection
                fetch(endpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({ test: true })
                })
                .then(response => response.json())
                .then(data => {
                    // Reset button state
                    this.disabled = false;
                    this.innerHTML = originalText;
                    
                    // Show notification
                    if (data.success) {
                        showNotification('Conexión exitosa', 'success');
                    } else {
                        showNotification('Error de conexión: ' + data.message, 'danger');
                    }
                })
                .catch(error => {
                    // Reset button state
                    this.disabled = false;
                    this.innerHTML = originalText;
                    
                    // Show error notification
                    showNotification('Error al probar la conexión', 'danger');
                    console.error('Error:', error);
                });
            });
        }
    }
    
    // Helper function to show notifications
    window.showNotification = function(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed notification`;
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '9999';
        notification.style.minWidth = '300px';
        
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(notification);
            bsAlert.close();
        }, 5000);
    };
});