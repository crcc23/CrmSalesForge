from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from models import Tenant, ClientSettings
import datetime

client_settings_bp = Blueprint('client_settings', __name__, url_prefix='/ajustes')

def get_tenant_id():
    """Helper function to get tenant ID from session"""
    if hasattr(current_user, 'tenant_id'):
        return current_user.tenant_id
    return None

@client_settings_bp.route('/')
@login_required
def index():
    """Mostrar la página principal de ajustes del cliente"""
    tenant_id = get_tenant_id()
    
    # Obtener el tenant actual
    tenant = Tenant.query.get(tenant_id)
    if not tenant:
        flash("No se encontró la información del cliente", "error")
        return redirect(url_for('dashboard.index'))
    
    # Obtener o crear los ajustes del cliente
    settings = ClientSettings.query.filter_by(tenant_id=tenant_id).first()
    if not settings:
        # Crear un registro de ajustes por defecto si no existe
        settings = ClientSettings()
        settings.tenant_id = tenant_id
        settings.company_name = tenant.name
        settings.language = 'es'
        settings.currency = 'EUR'
        settings.timezone = 'Europe/Madrid'
        settings.date_format = 'DD/MM/YYYY'
        db.session.add(settings)
        db.session.commit()
    
    return render_template('client_settings/index.html', 
                          tenant=tenant,
                          settings=settings)

@client_settings_bp.route('/company', methods=['GET', 'POST'])
@login_required
def company_info():
    """Gestionar la información de la empresa"""
    tenant_id = get_tenant_id()
    
    # Obtener los ajustes del cliente
    settings = ClientSettings.query.filter_by(tenant_id=tenant_id).first()
    if not settings:
        flash("No se encontró la información del cliente", "error")
        return redirect(url_for('client_settings.index'))
    
    if request.method == 'POST':
        # Actualizar la información de la empresa
        settings.company_name = request.form.get('company_name')
        settings.company_logo = request.form.get('company_logo')
        settings.industry = request.form.get('industry')
        settings.company_size = request.form.get('company_size')
        settings.website = request.form.get('website')
        
        # Información de contacto
        settings.primary_contact_name = request.form.get('primary_contact_name')
        settings.primary_contact_email = request.form.get('primary_contact_email')
        settings.primary_contact_phone = request.form.get('primary_contact_phone')
        settings.address = request.form.get('address')
        settings.city = request.form.get('city')
        settings.state_province = request.form.get('state_province')
        settings.postal_code = request.form.get('postal_code')
        settings.country = request.form.get('country')
        
        settings.updated_at = datetime.datetime.utcnow()
        
        db.session.commit()
        flash("Información de la empresa actualizada correctamente", "success")
        return redirect(url_for('client_settings.company_info'))
    
    return render_template('client_settings/company_info.html', settings=settings)

@client_settings_bp.route('/billing', methods=['GET', 'POST'])
@login_required
def billing():
    """Gestionar la información de facturación"""
    tenant_id = get_tenant_id()
    
    # Obtener los ajustes del cliente
    settings = ClientSettings.query.filter_by(tenant_id=tenant_id).first()
    if not settings:
        flash("No se encontró la información del cliente", "error")
        return redirect(url_for('client_settings.index'))
    
    # Obtener el tenant y su plan de suscripción
    tenant = Tenant.query.get(tenant_id)
    subscription_plan = tenant.subscription_plan if tenant else None
    
    if request.method == 'POST':
        # Actualizar la información de facturación
        settings.billing_plan = request.form.get('billing_plan')
        settings.billing_cycle = request.form.get('billing_cycle')
        settings.billing_contact_email = request.form.get('billing_contact_email')
        settings.tax_id = request.form.get('tax_id')
        
        settings.updated_at = datetime.datetime.utcnow()
        
        db.session.commit()
        flash("Información de facturación actualizada correctamente", "success")
        return redirect(url_for('client_settings.billing'))
    
    return render_template('client_settings/billing.html', 
                          settings=settings,
                          tenant=tenant,
                          subscription_plan=subscription_plan)

@client_settings_bp.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    """Gestionar las preferencias del cliente"""
    tenant_id = get_tenant_id()
    
    # Obtener los ajustes del cliente
    settings = ClientSettings.query.filter_by(tenant_id=tenant_id).first()
    if not settings:
        flash("No se encontró la información del cliente", "error")
        return redirect(url_for('client_settings.index'))
    
    if request.method == 'POST':
        # Actualizar las preferencias
        settings.timezone = request.form.get('timezone')
        settings.language = request.form.get('language')
        settings.date_format = request.form.get('date_format')
        settings.currency = request.form.get('currency')
        
        # Actualizar colores del tenant
        tenant = Tenant.query.get(tenant_id)
        if tenant:
            tenant.primary_color = request.form.get('primary_color', '#3498db')
            tenant.secondary_color = request.form.get('secondary_color', '#2ecc71')
        
        settings.updated_at = datetime.datetime.utcnow()
        
        db.session.commit()
        flash("Preferencias actualizadas correctamente", "success")
        return redirect(url_for('client_settings.preferences'))
    
    # Lista de zonas horarias comunes
    timezones = [
        {'value': 'Europe/Madrid', 'name': 'Madrid (GMT+1)'},
        {'value': 'Europe/London', 'name': 'Londres (GMT)'},
        {'value': 'America/New_York', 'name': 'Nueva York (GMT-5)'},
        {'value': 'America/Los_Angeles', 'name': 'Los Ángeles (GMT-8)'},
        {'value': 'America/Mexico_City', 'name': 'Ciudad de México (GMT-6)'},
        {'value': 'America/Bogota', 'name': 'Bogotá (GMT-5)'},
        {'value': 'America/Santiago', 'name': 'Santiago de Chile (GMT-4)'},
        {'value': 'America/Buenos_Aires', 'name': 'Buenos Aires (GMT-3)'}
    ]
    
    # Idiomas disponibles
    languages = [
        {'value': 'es', 'name': 'Español'},
        {'value': 'en', 'name': 'Inglés'},
        {'value': 'fr', 'name': 'Francés'},
        {'value': 'de', 'name': 'Alemán'},
        {'value': 'pt', 'name': 'Portugués'}
    ]
    
    # Formatos de fecha
    date_formats = [
        {'value': 'DD/MM/YYYY', 'name': 'DD/MM/YYYY'},
        {'value': 'MM/DD/YYYY', 'name': 'MM/DD/YYYY'},
        {'value': 'YYYY-MM-DD', 'name': 'YYYY-MM-DD'}
    ]
    
    # Monedas
    currencies = [
        {'value': 'EUR', 'name': 'Euro (€)'},
        {'value': 'USD', 'name': 'Dólar estadounidense ($)'},
        {'value': 'GBP', 'name': 'Libra esterlina (£)'},
        {'value': 'MXN', 'name': 'Peso mexicano ($)'},
        {'value': 'COP', 'name': 'Peso colombiano ($)'},
        {'value': 'CLP', 'name': 'Peso chileno ($)'},
        {'value': 'ARS', 'name': 'Peso argentino ($)'}
    ]
    
    # Obtener tenant para los colores
    tenant = Tenant.query.get(tenant_id)
    
    return render_template('client_settings/preferences.html',
                          settings=settings,
                          tenant=tenant,
                          timezones=timezones,
                          languages=languages,
                          date_formats=date_formats,
                          currencies=currencies)

@client_settings_bp.route('/integrations', methods=['GET', 'POST'])
@login_required
def integrations():
    """Gestionar integraciones habilitadas"""
    tenant_id = get_tenant_id()
    
    # Obtener los ajustes del cliente
    settings = ClientSettings.query.filter_by(tenant_id=tenant_id).first()
    if not settings:
        flash("No se encontró la información del cliente", "error")
        return redirect(url_for('client_settings.index'))
    
    if request.method == 'POST':
        # Actualizar integraciones habilitadas
        settings.enable_email_integration = 'enable_email_integration' in request.form
        settings.enable_whatsapp_integration = 'enable_whatsapp_integration' in request.form
        settings.enable_notion_integration = 'enable_notion_integration' in request.form
        settings.enable_ai_content_writer = 'enable_ai_content_writer' in request.form
        
        settings.updated_at = datetime.datetime.utcnow()
        
        db.session.commit()
        flash("Configuración de integraciones actualizada correctamente", "success")
        return redirect(url_for('client_settings.integrations'))
    
    return render_template('client_settings/integrations.html', settings=settings)