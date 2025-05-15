from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from models import MessageTemplate, EmailTemplate, WhatsAppTemplate
import datetime
import json

# Blueprint for message templates
templates_bp = Blueprint('templates', __name__, url_prefix='/templates')

def get_tenant_id():
    """Helper function to get tenant ID from session"""
    if hasattr(current_user, 'tenant_id'):
        return current_user.tenant_id
    return None

@templates_bp.route('/')
@login_required
def index():
    """Show list of message templates"""
    tenant_id = get_tenant_id()
    email_templates = EmailTemplate.query.filter_by(tenant_id=tenant_id).all()
    whatsapp_templates = WhatsAppTemplate.query.filter_by(tenant_id=tenant_id).all()
    
    return render_template('templates/index.html', 
                          email_templates=email_templates,
                          whatsapp_templates=whatsapp_templates)

# Email Templates
@templates_bp.route('/email')
@login_required
def email_templates():
    """Show list of email templates"""
    tenant_id = get_tenant_id()
    templates = EmailTemplate.query.filter_by(tenant_id=tenant_id).all()
    return render_template('templates/email/index.html', templates=templates)

@templates_bp.route('/email/create', methods=['GET', 'POST'])
@login_required
def create_email_template():
    """Create new email template"""
    if request.method == 'POST':
        tenant_id = get_tenant_id()
        
        template = EmailTemplate()
        template.tenant_id = tenant_id
        template.name = request.form.get('name')
        template.description = request.form.get('description')
        template.subject = request.form.get('subject')
        template.body_html = request.form.get('body_html')
        template.body_text = request.form.get('body_text') or ''
        template.sender_name = request.form.get('sender_name')
        template.sender_email = request.form.get('sender_email')
        
        # Handle available variables
        variables = request.form.get('available_variables')
        if variables:
            try:
                template.available_variables = json.loads(variables)
            except Exception:
                template.available_variables = {"error": "Invalid JSON format"}
        
        template.created_by = current_user.id
        
        db.session.add(template)
        db.session.commit()
        
        flash('Plantilla de correo electrónico creada correctamente', 'success')
        return redirect(url_for('templates.email_templates'))
    
    return render_template('templates/email/create.html')

@templates_bp.route('/email/<int:template_id>', methods=['GET', 'POST'])
@login_required
def edit_email_template(template_id):
    """Edit email template"""
    tenant_id = get_tenant_id()
    template = EmailTemplate.query.filter_by(id=template_id, tenant_id=tenant_id).first_or_404()
    
    if request.method == 'POST':
        template.name = request.form.get('name')
        template.description = request.form.get('description')
        template.subject = request.form.get('subject')
        template.body_html = request.form.get('body_html')
        template.body_text = request.form.get('body_text') or ''
        template.sender_name = request.form.get('sender_name')
        template.sender_email = request.form.get('sender_email')
        
        # Handle available variables
        variables = request.form.get('available_variables')
        if variables:
            try:
                template.available_variables = json.loads(variables)
            except Exception:
                template.available_variables = {"error": "Invalid JSON format"}
        
        db.session.commit()
        flash('Plantilla de correo electrónico actualizada correctamente', 'success')
        return redirect(url_for('templates.email_templates'))
    
    return render_template('templates/email/edit.html', template=template)

@templates_bp.route('/email/<int:template_id>/delete', methods=['POST'])
@login_required
def delete_email_template(template_id):
    """Delete email template"""
    tenant_id = get_tenant_id()
    template = EmailTemplate.query.filter_by(id=template_id, tenant_id=tenant_id).first_or_404()
    
    db.session.delete(template)
    db.session.commit()
    
    flash('Plantilla de correo electrónico eliminada correctamente', 'success')
    return redirect(url_for('templates.email_templates'))

# WhatsApp Templates
@templates_bp.route('/whatsapp')
@login_required
def whatsapp_templates():
    """Show list of whatsapp templates"""
    tenant_id = get_tenant_id()
    templates = WhatsAppTemplate.query.filter_by(tenant_id=tenant_id).all()
    return render_template('templates/whatsapp/index.html', templates=templates)

@templates_bp.route('/whatsapp/create', methods=['GET', 'POST'])
@login_required
def create_whatsapp_template():
    """Create new whatsapp template"""
    if request.method == 'POST':
        tenant_id = get_tenant_id()
        
        template = WhatsAppTemplate()
        template.tenant_id = tenant_id
        template.name = request.form.get('name')
        template.description = request.form.get('description')
        template.content = request.form.get('content')
        template.has_media = 'has_media' in request.form
        
        if template.has_media:
            template.media_type = request.form.get('media_type')
            template.media_url = request.form.get('media_url')
        
        # Handle available variables
        variables = request.form.get('available_variables')
        if variables:
            try:
                template.available_variables = json.loads(variables)
            except Exception:
                template.available_variables = {"error": "Invalid JSON format"}
        
        template.created_by = current_user.id
        
        db.session.add(template)
        db.session.commit()
        
        flash('Plantilla de WhatsApp creada correctamente', 'success')
        return redirect(url_for('templates.whatsapp_templates'))
    
    return render_template('templates/whatsapp/create.html')

@templates_bp.route('/whatsapp/<int:template_id>', methods=['GET', 'POST'])
@login_required
def edit_whatsapp_template(template_id):
    """Edit whatsapp template"""
    tenant_id = get_tenant_id()
    template = WhatsAppTemplate.query.filter_by(id=template_id, tenant_id=tenant_id).first_or_404()
    
    if request.method == 'POST':
        template.name = request.form.get('name')
        template.description = request.form.get('description')
        template.content = request.form.get('content')
        template.has_media = 'has_media' in request.form
        
        if template.has_media:
            template.media_type = request.form.get('media_type')
            template.media_url = request.form.get('media_url')
        else:
            template.media_type = None
            template.media_url = None
        
        # Handle available variables
        variables = request.form.get('available_variables')
        if variables:
            try:
                template.available_variables = json.loads(variables)
            except Exception:
                template.available_variables = {"error": "Invalid JSON format"}
        
        db.session.commit()
        flash('Plantilla de WhatsApp actualizada correctamente', 'success')
        return redirect(url_for('templates.whatsapp_templates'))
    
    return render_template('templates/whatsapp/edit.html', template=template)

@templates_bp.route('/whatsapp/<int:template_id>/delete', methods=['POST'])
@login_required
def delete_whatsapp_template(template_id):
    """Delete whatsapp template"""
    tenant_id = get_tenant_id()
    template = WhatsAppTemplate.query.filter_by(id=template_id, tenant_id=tenant_id).first_or_404()
    
    db.session.delete(template)
    db.session.commit()
    
    flash('Plantilla de WhatsApp eliminada correctamente', 'success')
    return redirect(url_for('templates.whatsapp_templates'))

# Preview and testing endpoints
@templates_bp.route('/email/<int:template_id>/preview')
@login_required
def preview_email_template(template_id):
    """Preview email template"""
    tenant_id = get_tenant_id()
    template = EmailTemplate.query.filter_by(id=template_id, tenant_id=tenant_id).first_or_404()
    
    # In a real app, we would substitute variables
    # For now, just return the raw HTML
    return template.body_html

@templates_bp.route('/whatsapp/<int:template_id>/preview')
@login_required
def preview_whatsapp_template(template_id):
    """Preview whatsapp template"""
    tenant_id = get_tenant_id()
    template = WhatsAppTemplate.query.filter_by(id=template_id, tenant_id=tenant_id).first_or_404()
    
    # In a real app, we would substitute variables
    # For now, just return the raw content
    return template.content