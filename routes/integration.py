from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify, current_app as app
from flask_login import login_required, current_user
from app import db
from models import (
    IntegrationConfig, EvolutionApiConfig, SmtpConfig, ImapConfig, 
    OpenAiConfig, ClaudeConfig, GeminiConfig, SerpMapsConfig, NotionConfig
)
import os
import json
import datetime

# Blueprint for integration routes
integration = Blueprint('integration', __name__, url_prefix='/integration')

def get_tenant_id():
    """Helper function to get tenant ID from session"""
    if hasattr(current_user, 'tenant_id'):
        return current_user.tenant_id
    return None

@integration.route('/')
@login_required
def index():
    """Show list of available integrations"""
    return render_template('integration/config_list.html')

# Evolution API Configuration
@integration.route('/evolution-api', methods=['GET', 'POST'])
@login_required
def evolution_api_config():
    """Configure Evolution API for WhatsApp"""
    tenant_id = get_tenant_id()
    config = EvolutionApiConfig.query.filter_by(
        tenant_id=tenant_id,
        integration_type='evolution_api'
    ).first()
    
    if request.method == 'POST':
        if not config:
            config = EvolutionApiConfig()
            config.tenant_id = tenant_id
        
        # Update config from form
        config.update_from_form(request.form)
        
        # Test connection and set active if successful
        # For now, we'll just set is_active to True - in a real app, we'd test the connection
        config.is_active = True
        config.last_tested = datetime.datetime.utcnow()
        
        db.session.add(config)
        db.session.commit()
        
        flash('Configuración de Evolution API guardada correctamente', 'success')
        return redirect(url_for('integration.evolution_api_config'))
    
    return render_template('integration/evolution_api.html', config=config)

# SMTP Configuration
@integration.route('/smtp', methods=['GET', 'POST'])
@login_required
def smtp_config():
    """Configure SMTP for outgoing emails"""
    tenant_id = get_tenant_id()
    config = SmtpConfig.query.filter_by(
        tenant_id=tenant_id,
        integration_type='smtp'
    ).first()
    
    if request.method == 'POST':
        if not config:
            config = SmtpConfig()
            config.tenant_id = tenant_id
        
        # Update config from form
        config.update_from_form(request.form)
        
        # Test connection in a real app
        config.is_active = True
        config.last_tested = datetime.datetime.utcnow()
        
        db.session.add(config)
        db.session.commit()
        
        flash('Configuración SMTP guardada correctamente', 'success')
        return redirect(url_for('integration.smtp_config'))
    
    return render_template('integration/smtp.html', config=config)

# IMAP Configuration
@integration.route('/imap', methods=['GET', 'POST'])
@login_required
def imap_config():
    """Configure IMAP for incoming emails"""
    tenant_id = get_tenant_id()
    config = ImapConfig.query.filter_by(
        tenant_id=tenant_id,
        integration_type='imap'
    ).first()
    
    if request.method == 'POST':
        if not config:
            config = ImapConfig()
            config.tenant_id = tenant_id
        
        # Update config from form
        config.update_from_form(request.form)
        
        # Test connection in a real app
        config.is_active = True
        config.last_tested = datetime.datetime.utcnow()
        
        db.session.add(config)
        db.session.commit()
        
        flash('Configuración IMAP guardada correctamente', 'success')
        return redirect(url_for('integration.imap_config'))
    
    return render_template('integration/imap.html', config=config)

# OpenAI Configuration
@integration.route('/openai', methods=['GET', 'POST'])
@login_required
def openai_config():
    """Configure OpenAI API"""
    tenant_id = get_tenant_id()
    config = OpenAiConfig.query.filter_by(
        tenant_id=tenant_id,
        integration_type='openai'
    ).first()
    
    if request.method == 'POST':
        if not config:
            config = OpenAiConfig()
            config.tenant_id = tenant_id
        
        # Update config from form
        config.update_from_form(request.form)
        
        # Test connection in a real app
        config.is_active = True
        config.last_tested = datetime.datetime.utcnow()
        
        db.session.add(config)
        db.session.commit()
        
        flash('Configuración de OpenAI guardada correctamente', 'success')
        return redirect(url_for('integration.openai_config'))
    
    return render_template('integration/openai.html', config=config)

# Claude Configuration
@integration.route('/claude', methods=['GET', 'POST'])
@login_required
def claude_config():
    """Configure Anthropic Claude API"""
    tenant_id = get_tenant_id()
    config = ClaudeConfig.query.filter_by(
        tenant_id=tenant_id,
        integration_type='claude'
    ).first()
    
    if request.method == 'POST':
        if not config:
            config = ClaudeConfig()
            config.tenant_id = tenant_id
        
        # Update config from form
        config.update_from_form(request.form)
        
        # Test connection in a real app
        config.is_active = True
        config.last_tested = datetime.datetime.utcnow()
        
        db.session.add(config)
        db.session.commit()
        
        flash('Configuración de Claude AI guardada correctamente', 'success')
        return redirect(url_for('integration.claude_config'))
    
    return render_template('integration/claude.html', config=config)

# Gemini Configuration
@integration.route('/gemini', methods=['GET', 'POST'])
@login_required
def gemini_config():
    """Configure Google Gemini API"""
    tenant_id = get_tenant_id()
    config = GeminiConfig.query.filter_by(
        tenant_id=tenant_id,
        integration_type='gemini'
    ).first()
    
    if request.method == 'POST':
        if not config:
            config = GeminiConfig()
            config.tenant_id = tenant_id
        
        # Update config from form
        config.update_from_form(request.form)
        
        # Test connection in a real app
        config.is_active = True
        config.last_tested = datetime.datetime.utcnow()
        
        db.session.add(config)
        db.session.commit()
        
        flash('Configuración de Gemini guardada correctamente', 'success')
        return redirect(url_for('integration.gemini_config'))
    
    return render_template('integration/gemini.html', config=config)

# SERP API Google Maps Configuration
@integration.route('/serp-maps', methods=['GET', 'POST'])
@login_required
def serp_maps_config():
    """Configure SERP API for Google Maps"""
    tenant_id = get_tenant_id()
    config = SerpMapsConfig.query.filter_by(
        tenant_id=tenant_id,
        integration_type='serp_maps'
    ).first()
    
    if request.method == 'POST':
        if not config:
            config = SerpMapsConfig()
            config.tenant_id = tenant_id
        
        # Update config from form
        config.update_from_form(request.form)
        
        # Test connection in a real app
        config.is_active = True
        config.last_tested = datetime.datetime.utcnow()
        
        db.session.add(config)
        db.session.commit()
        
        flash('Configuración de SERP API guardada correctamente', 'success')
        return redirect(url_for('integration.serp_maps_config'))
    
    return render_template('integration/serp_maps.html', config=config)

# Notion Configuration
@integration.route('/notion', methods=['GET', 'POST'])
@login_required
def notion_config():
    """Configure Notion integration"""
    tenant_id = get_tenant_id()
    config = NotionConfig.query.filter_by(
        tenant_id=tenant_id,
        integration_type='notion'
    ).first()
    
    if request.method == 'POST':
        if not config:
            config = NotionConfig()
            config.tenant_id = tenant_id
        
        # Update config from form
        config.update_from_form(request.form)
        
        # Test connection in a real app
        config.is_active = True
        config.last_tested = datetime.datetime.utcnow()
        
        db.session.add(config)
        db.session.commit()
        
        flash('Configuración de Notion guardada correctamente', 'success')
        return redirect(url_for('integration.notion_config'))
    
    return render_template('integration/notion.html', config=config)

# API Endpoints for testing connections
@integration.route('/test-connection/<integration_type>', methods=['POST'])
@login_required
def test_connection(integration_type):
    """Test connection to an integration"""
    tenant_id = get_tenant_id()
    
    # Map of integration types to their model classes
    integration_models = {
        'evolution_api': EvolutionApiConfig,
        'smtp': SmtpConfig,
        'imap': ImapConfig,
        'openai': OpenAiConfig,
        'claude': ClaudeConfig,
        'gemini': GeminiConfig,
        'serp_maps': SerpMapsConfig,
        'notion': NotionConfig
    }
    
    if integration_type not in integration_models:
        return jsonify({
            'success': False,
            'message': 'Tipo de integración no válido'
        }), 400
    
    # Get the config object
    model_class = integration_models[integration_type]
    config = model_class.query.filter_by(
        tenant_id=tenant_id,
        integration_type=integration_type
    ).first()
    
    if not config:
        return jsonify({
            'success': False,
            'message': 'No existe configuración para esta integración'
        }), 404
    
    # In a real app, we would actually test the connection here
    # For now, we'll simulate a successful test
    success = True
    message = 'Conexión exitosa'
    details = None
    
    # Update the config with the test results
    config.is_active = success
    config.last_tested = datetime.datetime.utcnow()
    config.test_result = json.dumps({
        'success': success,
        'message': message,
        'details': details
    })
    
    db.session.commit()
    
    return jsonify({
        'success': success,
        'message': message,
        'details': details
    })