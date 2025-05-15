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
    tenant_id = get_tenant_id()
    
    if request.method == 'POST':
        try:
            # Datos básicos de la campaña
            name = request.form.get('name')
            description = request.form.get('description')
            
            # Crear la campaña con el email inicial
            campaign = EmailCampaign(
                tenant_id=tenant_id,
                owner_id=current_user.id,
                campaign_type='email',
                name=name,
                description=description,
                
                # Email inicial
                initial_subject=request.form.get('initial_subject', ''),
                initial_template_id=request.form.get('initial_template_id') or None
            )
            
            # Si se usó una plantilla, copiar su contenido
            if campaign.initial_template_id:
                template = EmailTemplate.query.get(campaign.initial_template_id)
                if template:
                    campaign.initial_body_html = template.body_html
                    campaign.initial_body_text = template.body_text
            else:
                # Usar contenido personalizado
                campaign.initial_body_html = request.form.get('initial_body_html', '')
                campaign.initial_body_text = request.form.get('initial_body_text', '')
            
            # Procesar email de seguimiento 1
            if 'enable_followup1' in request.form:
                campaign.follow_up1_subject = request.form.get('follow_up1_subject', '')
                campaign.follow_up1_delay_days = int(request.form.get('follow_up1_delay_days', 3))
                campaign.follow_up1_template_id = request.form.get('follow_up1_template_id') or None
                
                if campaign.follow_up1_template_id:
                    template = EmailTemplate.query.get(campaign.follow_up1_template_id)
                    if template:
                        campaign.follow_up1_body_html = template.body_html
                        campaign.follow_up1_body_text = template.body_text
                else:
                    campaign.follow_up1_body_html = request.form.get('follow_up1_body_html', '')
                    campaign.follow_up1_body_text = request.form.get('follow_up1_body_text', '')
            
            # Seguimientos 2 y 3 tendrían código similar cuando se implementen
            
            # Guardar la campaña
            db.session.add(campaign)
            db.session.commit()
            
            flash('Campaña de email creada exitosamente', 'success')
            return redirect(url_for('campaigns.manage_email_recipients', campaign_id=campaign.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear la campaña: {str(e)}', 'danger')
            # Registrar el error
            logging.error(f"Error creating campaign: {str(e)}")
            return redirect(url_for('campaigns.index'))
    
    # Buscar plantillas disponibles
    templates = EmailTemplate.query.filter_by(tenant_id=tenant_id, is_active=True).all()
    
    return render_template('campaigns/email/create.html', templates=templates)

@campaigns_bp.route('/email/<int:campaign_id>')
@login_required
def view_email_campaign(campaign_id):
    """Ver detalles de una campaña de email"""
    tenant_id = get_tenant_id()
    
    campaign = EmailCampaign.query.filter_by(id=campaign_id, tenant_id=tenant_id).first_or_404()
    recipients = EmailCampaignRecipient.query.filter_by(campaign_id=campaign_id).all()
    
    # Calcular estadísticas generales
    total_recipients = len(recipients)
    
    # Estadísticas del email inicial
    initial_sent = sum(1 for r in recipients if r.initial_sent)
    initial_opened = sum(1 for r in recipients if r.initial_opened)
    initial_clicked = sum(1 for r in recipients if r.initial_clicked)
    
    # Estadísticas del email de seguimiento 1
    followup1_sent = sum(1 for r in recipients if r.follow_up1_sent)
    followup1_opened = sum(1 for r in recipients if r.follow_up1_opened)
    followup1_clicked = sum(1 for r in recipients if r.follow_up1_clicked)
    
    # Estadísticas del email de seguimiento 2
    followup2_sent = sum(1 for r in recipients if r.follow_up2_sent)
    followup2_opened = sum(1 for r in recipients if r.follow_up2_opened)
    followup2_clicked = sum(1 for r in recipients if r.follow_up2_clicked)
    
    # Estadísticas del email de seguimiento 3
    followup3_sent = sum(1 for r in recipients if r.follow_up3_sent)
    followup3_opened = sum(1 for r in recipients if r.follow_up3_opened)
    followup3_clicked = sum(1 for r in recipients if r.follow_up3_clicked)
    
    # Estadísticas generales
    bounce_count = sum(1 for r in recipients if r.bounced)
    response_count = sum(1 for r in recipients if r.responded)
    
    # Preparar objetos de estadísticas para cada email
    initial_stats = {
        'sent': initial_sent,
        'sent_pct': (initial_sent / total_recipients * 100) if total_recipients > 0 else 0,
        'opened': initial_opened,
        'opened_pct': (initial_opened / initial_sent * 100) if initial_sent > 0 else 0,
        'clicked': initial_clicked,
        'clicked_pct': (initial_clicked / initial_opened * 100) if initial_opened > 0 else 0
    }
    
    followup1_stats = {
        'sent': followup1_sent,
        'sent_pct': (followup1_sent / total_recipients * 100) if total_recipients > 0 else 0,
        'opened': followup1_opened,
        'opened_pct': (followup1_opened / followup1_sent * 100) if followup1_sent > 0 else 0,
        'clicked': followup1_clicked,
        'clicked_pct': (followup1_clicked / followup1_opened * 100) if followup1_opened > 0 else 0
    }
    
    followup2_stats = {
        'sent': followup2_sent,
        'sent_pct': (followup2_sent / total_recipients * 100) if total_recipients > 0 else 0,
        'opened': followup2_opened,
        'opened_pct': (followup2_opened / followup2_sent * 100) if followup2_sent > 0 else 0,
        'clicked': followup2_clicked,
        'clicked_pct': (followup2_clicked / followup2_opened * 100) if followup2_opened > 0 else 0
    }
    
    followup3_stats = {
        'sent': followup3_sent,
        'sent_pct': (followup3_sent / total_recipients * 100) if total_recipients > 0 else 0,
        'opened': followup3_opened,
        'opened_pct': (followup3_opened / followup3_sent * 100) if followup3_sent > 0 else 0,
        'clicked': followup3_clicked,
        'clicked_pct': (followup3_clicked / followup3_opened * 100) if followup3_opened > 0 else 0
    }
    
    # Estadísticas generales
    overall_stats = {
        'total': total_recipients,
        'responses': response_count,
        'response_rate': (response_count / total_recipients * 100) if total_recipients > 0 else 0,
        'bounce': bounce_count,
        'bounce_rate': (bounce_count / total_recipients * 100) if total_recipients > 0 else 0
    }
    
    return render_template('campaigns/email/view.html', 
                          campaign=campaign, 
                          recipients=recipients, 
                          initial_stats=initial_stats,
                          followup1_stats=followup1_stats,
                          followup2_stats=followup2_stats,
                          followup3_stats=followup3_stats,
                          overall_stats=overall_stats)

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