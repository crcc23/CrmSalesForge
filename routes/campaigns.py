from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from models import Campaign, EmailCampaign, WhatsAppCampaign, EmailCampaignRecipient, WhatsAppCampaignRecipient, EmailTemplate, WhatsAppTemplate, Contact, Prospect
from sqlalchemy import desc
import datetime
import json

# Blueprint para campañas
campaigns_bp = Blueprint('campaigns', __name__, url_prefix='/campaigns')

def get_tenant_id():
    """Helper function to get tenant ID from session"""
    if hasattr(current_user, 'tenant_id'):
        return current_user.tenant_id
    return None

@campaigns_bp.route('/')
@login_required
def index():
    """Mostrar lista de campañas"""
    # Versión temporal que muestra página sin datos mientras corregimos la base de datos
    return render_template('campaigns/index.html',
                        email_campaigns=[],
                        whatsapp_campaigns=[])

@campaigns_bp.route('/email')
@login_required
def email_campaigns():
    """Mostrar lista de campañas de email"""
    # Versión temporal
    return render_template('campaigns/email/index.html', campaigns=[])

@campaigns_bp.route('/email/create', methods=['GET', 'POST'])
@login_required
def create_email_campaign():
    """Crear nueva campaña de email"""
    # Versión temporal
    if request.method == 'POST':
        flash('Funcionalidad de creación de campañas en desarrollo', 'info')
        return redirect(url_for('campaigns.index'))
    
    # Mostrar formulario sin plantillas por ahora
    return render_template('campaigns/email/create.html', templates=[])

@campaigns_bp.route('/email/<int:campaign_id>')
@login_required
def view_email_campaign(campaign_id):
    """Ver detalles de una campaña de email"""
    # Versión temporal
    flash('Funcionalidad en desarrollo: ver detalles de campaña', 'info')
    return redirect(url_for('campaigns.index'))

@campaigns_bp.route('/email/<int:campaign_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_email_campaign(campaign_id):
    """Editar campaña de email"""
    # Versión temporal
    flash('Funcionalidad en desarrollo: editar campaña', 'info')
    return redirect(url_for('campaigns.index'))

@campaigns_bp.route('/email/<int:campaign_id>/recipients', methods=['GET', 'POST'])
@login_required
def manage_email_recipients(campaign_id):
    """Gestionar destinatarios de campaña de email"""
    # Versión temporal
    flash('Funcionalidad en desarrollo: gestionar destinatarios', 'info')
    return redirect(url_for('campaigns.index'))

@campaigns_bp.route('/email/<int:campaign_id>/schedule', methods=['GET', 'POST'])
@login_required
def schedule_email_campaign(campaign_id):
    """Programar envío de campaña de email"""
    # Versión temporal
    flash('Funcionalidad en desarrollo: programar campaña', 'info')
    return redirect(url_for('campaigns.index'))

@campaigns_bp.route('/whatsapp')
@login_required
def whatsapp_campaigns():
    """Mostrar lista de campañas de WhatsApp"""
    # Versión temporal
    return render_template('campaigns/whatsapp/index.html', campaigns=[])

@campaigns_bp.route('/whatsapp/create', methods=['GET', 'POST'])
@login_required
def create_whatsapp_campaign():
    """Crear nueva campaña de WhatsApp"""
    # Versión temporal
    if request.method == 'POST':
        flash('Funcionalidad en desarrollo: crear campaña de WhatsApp', 'info')
        return redirect(url_for('campaigns.index'))
    
    return render_template('campaigns/whatsapp/create.html', templates=[])

@campaigns_bp.route('/whatsapp/<int:campaign_id>')
@login_required
def view_whatsapp_campaign(campaign_id):
    """Ver detalles de una campaña de WhatsApp"""
    # Versión temporal
    flash('Funcionalidad en desarrollo: ver campaña de WhatsApp', 'info')
    return redirect(url_for('campaigns.index'))

@campaigns_bp.route('/whatsapp/<int:campaign_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_whatsapp_campaign(campaign_id):
    """Editar campaña de WhatsApp"""
    # Versión temporal
    flash('Funcionalidad en desarrollo: editar campaña de WhatsApp', 'info')
    return redirect(url_for('campaigns.index'))

@campaigns_bp.route('/whatsapp/<int:campaign_id>/recipients', methods=['GET', 'POST'])
@login_required
def manage_whatsapp_recipients(campaign_id):
    """Gestionar destinatarios de campaña de WhatsApp"""
    tenant_id = get_tenant_id()
    
    campaign = WhatsAppCampaign.query.filter_by(id=campaign_id, tenant_id=tenant_id).first_or_404()
    
    if request.method == 'POST':
        # Solo se pueden editar campañas en estado borrador
        if campaign.status != 'Draft':
            flash('No se puede modificar los destinatarios de una campaña que ya ha sido enviada o programada', 'danger')
            return redirect(url_for('campaigns.view_whatsapp_campaign', campaign_id=campaign_id))
        
        # Gestionar selección de destinatarios
        target_type = request.form.get('target_audience')
        campaign.target_audience = target_type
        
        # Primero eliminar destinatarios actuales
        WhatsAppCampaignRecipient.query.filter_by(campaign_id=campaign_id).delete()
        
        if target_type == 'all_contacts':
            # Añadir todos los contactos
            contacts = Contact.query.filter_by(tenant_id=tenant_id).all()
            for contact in contacts:
                if contact.mobile:  # Solo si tiene teléfono móvil
                    recipient = WhatsAppCampaignRecipient(
                        campaign_id=campaign_id,
                        recipient_type='contact',
                        recipient_id=contact.id,
                        recipient_name=contact.full_name,
                        phone=contact.mobile
                    )
                    db.session.add(recipient)
        
        elif target_type == 'all_prospects':
            # Añadir todos los prospectos
            prospects = Prospect.query.filter_by(tenant_id=tenant_id).all()
            for prospect in prospects:
                if prospect.phone:  # Solo si tiene teléfono
                    recipient = WhatsAppCampaignRecipient(
                        campaign_id=campaign_id,
                        recipient_type='prospect',
                        recipient_id=prospect.id,
                        recipient_name=prospect.full_name,
                        phone=prospect.phone
                    )
                    db.session.add(recipient)
        
        elif target_type == 'selected':
            # Añadir destinatarios seleccionados manualmente
            selected_contacts = request.form.getlist('contacts')
            for contact_id in selected_contacts:
                contact = Contact.query.get(contact_id)
                if contact and contact.mobile:
                    recipient = WhatsAppCampaignRecipient(
                        campaign_id=campaign_id,
                        recipient_type='contact',
                        recipient_id=contact.id,
                        recipient_name=contact.full_name,
                        phone=contact.mobile
                    )
                    db.session.add(recipient)
            
            selected_prospects = request.form.getlist('prospects')
            for prospect_id in selected_prospects:
                prospect = Prospect.query.get(prospect_id)
                if prospect and prospect.phone:
                    recipient = WhatsAppCampaignRecipient(
                        campaign_id=campaign_id,
                        recipient_type='prospect',
                        recipient_id=prospect.id,
                        recipient_name=prospect.full_name,
                        phone=prospect.phone
                    )
                    db.session.add(recipient)
        
        campaign.updated_at = datetime.datetime.now()
        db.session.commit()
        
        flash('Destinatarios actualizados exitosamente', 'success')
        return redirect(url_for('campaigns.view_whatsapp_campaign', campaign_id=campaign_id))
    
    # Obtener destinatarios actuales
    recipients = WhatsAppCampaignRecipient.query.filter_by(campaign_id=campaign_id).all()
    
    # Obtener contactos y prospectos para selección manual
    contacts = Contact.query.filter_by(tenant_id=tenant_id).filter(Contact.mobile != None).all()
    prospects = Prospect.query.filter_by(tenant_id=tenant_id).filter(Prospect.phone != None).all()
    
    # Verificar qué contactos/prospectos ya están seleccionados
    selected_contact_ids = [r.recipient_id for r in recipients if r.recipient_type == 'contact']
    selected_prospect_ids = [r.recipient_id for r in recipients if r.recipient_type == 'prospect']
    
    return render_template('campaigns/whatsapp/recipients.html',
                          campaign=campaign,
                          recipients=recipients,
                          contacts=contacts,
                          prospects=prospects,
                          selected_contact_ids=selected_contact_ids,
                          selected_prospect_ids=selected_prospect_ids)

@campaigns_bp.route('/whatsapp/<int:campaign_id>/schedule', methods=['GET', 'POST'])
@login_required
def schedule_whatsapp_campaign(campaign_id):
    """Programar envío de campaña de WhatsApp"""
    tenant_id = get_tenant_id()
    
    campaign = WhatsAppCampaign.query.filter_by(id=campaign_id, tenant_id=tenant_id).first_or_404()
    
    if request.method == 'POST':
        # Verificar que la campaña tenga destinatarios
        recipient_count = WhatsAppCampaignRecipient.query.filter_by(campaign_id=campaign_id).count()
        if recipient_count == 0:
            flash('No se puede programar una campaña sin destinatarios', 'danger')
            return redirect(url_for('campaigns.manage_whatsapp_recipients', campaign_id=campaign_id))
        
        # Obtener datos de programación
        send_type = request.form.get('send_type')
        
        if send_type == 'now':
            # Enviar ahora (en realidad, marcar para envío inmediato)
            campaign.status = 'Sending'
            campaign.scheduled_date = datetime.datetime.now()
            campaign.start_date = datetime.datetime.now()
            
            flash('La campaña ha sido programada para envío inmediato', 'success')
        
        elif send_type == 'later':
            # Programar para más tarde
            scheduled_date_str = request.form.get('scheduled_date')
            scheduled_time_str = request.form.get('scheduled_time')
            
            try:
                # Combinar fecha y hora
                scheduled_datetime = datetime.datetime.strptime(
                    f"{scheduled_date_str} {scheduled_time_str}", 
                    "%Y-%m-%d %H:%M"
                )
                
                # Verificar que la fecha sea en el futuro
                if scheduled_datetime <= datetime.datetime.now():
                    flash('La fecha de programación debe ser en el futuro', 'danger')
                    return redirect(url_for('campaigns.schedule_whatsapp_campaign', campaign_id=campaign_id))
                
                campaign.status = 'Scheduled'
                campaign.scheduled_date = scheduled_datetime
                
                flash(f'La campaña ha sido programada para el {scheduled_date_str} a las {scheduled_time_str}', 'success')
                
            except ValueError:
                flash('Formato de fecha u hora inválido', 'danger')
                return redirect(url_for('campaigns.schedule_whatsapp_campaign', campaign_id=campaign_id))
        
        campaign.updated_at = datetime.datetime.now()
        db.session.commit()
        
        return redirect(url_for('campaigns.view_whatsapp_campaign', campaign_id=campaign_id))
    
    return render_template('campaigns/whatsapp/schedule.html', campaign=campaign)