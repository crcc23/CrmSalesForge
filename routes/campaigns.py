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
    tenant_id = get_tenant_id()
    
    # Obtener campañas ordenadas por fecha de creación (más recientes primero)
    email_campaigns = EmailCampaign.query.filter_by(tenant_id=tenant_id).order_by(desc(EmailCampaign.created_at)).all()
    whatsapp_campaigns = WhatsAppCampaign.query.filter_by(tenant_id=tenant_id).order_by(desc(WhatsAppCampaign.created_at)).all()
    
    return render_template('campaigns/index.html',
                         email_campaigns=email_campaigns,
                         whatsapp_campaigns=whatsapp_campaigns)

@campaigns_bp.route('/email')
@login_required
def email_campaigns():
    """Mostrar lista de campañas de email"""
    tenant_id = get_tenant_id()
    
    campaigns = EmailCampaign.query.filter_by(tenant_id=tenant_id).order_by(desc(EmailCampaign.created_at)).all()
    
    return render_template('campaigns/email/index.html', campaigns=campaigns)

@campaigns_bp.route('/email/create', methods=['GET', 'POST'])
@login_required
def create_email_campaign():
    """Crear nueva campaña de email"""
    tenant_id = get_tenant_id()
    
    if request.method == 'POST':
        # Obtener datos del formulario
        name = request.form.get('name')
        description = request.form.get('description')
        subject = request.form.get('subject')
        
        # Verificar si se seleccionó una plantilla existente
        template_id = request.form.get('template_id')
        
        if template_id:
            # Usar plantilla existente
            template = EmailTemplate.query.get(template_id)
            body_html = template.body_html
            body_text = template.body_text
            subject = subject or template.subject
        else:
            # Usar contenido personalizado
            body_html = request.form.get('body_html')
            body_text = request.form.get('body_text')
        
        # Crear nueva campaña
        campaign = EmailCampaign(
            tenant_id=tenant_id,
            owner_id=current_user.id,
            name=name,
            description=description,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            template_id=template_id if template_id else None,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now()
        )
        
        db.session.add(campaign)
        db.session.commit()
        
        flash('Campaña de email creada exitosamente', 'success')
        return redirect(url_for('campaigns.edit_email_campaign', campaign_id=campaign.id))
    
    # Obtener plantillas disponibles para el formulario
    templates = EmailTemplate.query.filter_by(tenant_id=tenant_id, is_active=True).all()
    
    return render_template('campaigns/email/create.html', templates=templates)

@campaigns_bp.route('/email/<int:campaign_id>')
@login_required
def view_email_campaign(campaign_id):
    """Ver detalles de una campaña de email"""
    tenant_id = get_tenant_id()
    
    campaign = EmailCampaign.query.filter_by(id=campaign_id, tenant_id=tenant_id).first_or_404()
    recipients = EmailCampaignRecipient.query.filter_by(campaign_id=campaign_id).all()
    
    # Calcular estadísticas
    total_recipients = len(recipients)
    sent_count = sum(1 for r in recipients if r.sent)
    open_count = sum(1 for r in recipients if r.opened)
    click_count = sum(1 for r in recipients if r.clicked)
    bounce_count = sum(1 for r in recipients if r.bounced)
    
    stats = {
        'total': total_recipients,
        'sent': sent_count,
        'sent_pct': (sent_count / total_recipients * 100) if total_recipients > 0 else 0,
        'open': open_count,
        'open_pct': (open_count / sent_count * 100) if sent_count > 0 else 0,
        'click': click_count,
        'click_pct': (click_count / open_count * 100) if open_count > 0 else 0,
        'bounce': bounce_count,
        'bounce_pct': (bounce_count / sent_count * 100) if sent_count > 0 else 0
    }
    
    return render_template('campaigns/email/view.html', 
                          campaign=campaign, 
                          recipients=recipients, 
                          stats=stats)

@campaigns_bp.route('/email/<int:campaign_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_email_campaign(campaign_id):
    """Editar campaña de email"""
    tenant_id = get_tenant_id()
    
    campaign = EmailCampaign.query.filter_by(id=campaign_id, tenant_id=tenant_id).first_or_404()
    
    if request.method == 'POST':
        # Solo se pueden editar campañas en estado borrador
        if campaign.status != 'Draft':
            flash('No se puede editar una campaña que ya ha sido enviada o programada', 'danger')
            return redirect(url_for('campaigns.view_email_campaign', campaign_id=campaign_id))
        
        # Actualizar datos de la campaña
        campaign.name = request.form.get('name')
        campaign.description = request.form.get('description')
        campaign.subject = request.form.get('subject')
        
        # Verificar si se cambió la plantilla
        template_id = request.form.get('template_id')
        if template_id and str(template_id) != str(campaign.template_id):
            template = EmailTemplate.query.get(template_id)
            campaign.template_id = template_id
            campaign.body_html = template.body_html
            campaign.body_text = template.body_text
        elif not template_id:
            # Usar contenido personalizado
            campaign.template_id = None
            campaign.body_html = request.form.get('body_html')
            campaign.body_text = request.form.get('body_text')
        
        campaign.updated_at = datetime.datetime.now()
        
        db.session.commit()
        
        flash('Campaña actualizada exitosamente', 'success')
        return redirect(url_for('campaigns.view_email_campaign', campaign_id=campaign_id))
    
    # Obtener plantillas disponibles para el formulario
    templates = EmailTemplate.query.filter_by(tenant_id=tenant_id, is_active=True).all()
    
    return render_template('campaigns/email/edit.html', 
                          campaign=campaign, 
                          templates=templates)

@campaigns_bp.route('/email/<int:campaign_id>/recipients', methods=['GET', 'POST'])
@login_required
def manage_email_recipients(campaign_id):
    """Gestionar destinatarios de campaña de email"""
    tenant_id = get_tenant_id()
    
    campaign = EmailCampaign.query.filter_by(id=campaign_id, tenant_id=tenant_id).first_or_404()
    
    if request.method == 'POST':
        # Solo se pueden editar campañas en estado borrador
        if campaign.status != 'Draft':
            flash('No se puede modificar los destinatarios de una campaña que ya ha sido enviada o programada', 'danger')
            return redirect(url_for('campaigns.view_email_campaign', campaign_id=campaign_id))
        
        # Gestionar selección de destinatarios
        target_type = request.form.get('target_audience')
        campaign.target_audience = target_type
        
        # Primero eliminar destinatarios actuales
        EmailCampaignRecipient.query.filter_by(campaign_id=campaign_id).delete()
        
        if target_type == 'all_contacts':
            # Añadir todos los contactos
            contacts = Contact.query.filter_by(tenant_id=tenant_id).all()
            for contact in contacts:
                if contact.email:  # Solo si tiene email
                    recipient = EmailCampaignRecipient(
                        campaign_id=campaign_id,
                        recipient_type='contact',
                        recipient_id=contact.id,
                        recipient_name=contact.full_name,
                        email=contact.email
                    )
                    db.session.add(recipient)
        
        elif target_type == 'all_prospects':
            # Añadir todos los prospectos
            prospects = Prospect.query.filter_by(tenant_id=tenant_id).all()
            for prospect in prospects:
                if prospect.email:  # Solo si tiene email
                    recipient = EmailCampaignRecipient(
                        campaign_id=campaign_id,
                        recipient_type='prospect',
                        recipient_id=prospect.id,
                        recipient_name=prospect.full_name,
                        email=prospect.email
                    )
                    db.session.add(recipient)
        
        elif target_type == 'selected':
            # Añadir destinatarios seleccionados manualmente
            selected_contacts = request.form.getlist('contacts')
            for contact_id in selected_contacts:
                contact = Contact.query.get(contact_id)
                if contact and contact.email:
                    recipient = EmailCampaignRecipient(
                        campaign_id=campaign_id,
                        recipient_type='contact',
                        recipient_id=contact.id,
                        recipient_name=contact.full_name,
                        email=contact.email
                    )
                    db.session.add(recipient)
            
            selected_prospects = request.form.getlist('prospects')
            for prospect_id in selected_prospects:
                prospect = Prospect.query.get(prospect_id)
                if prospect and prospect.email:
                    recipient = EmailCampaignRecipient(
                        campaign_id=campaign_id,
                        recipient_type='prospect',
                        recipient_id=prospect.id,
                        recipient_name=prospect.full_name,
                        email=prospect.email
                    )
                    db.session.add(recipient)
        
        campaign.updated_at = datetime.datetime.now()
        db.session.commit()
        
        flash('Destinatarios actualizados exitosamente', 'success')
        return redirect(url_for('campaigns.view_email_campaign', campaign_id=campaign_id))
    
    # Obtener destinatarios actuales
    recipients = EmailCampaignRecipient.query.filter_by(campaign_id=campaign_id).all()
    
    # Obtener contactos y prospectos para selección manual
    contacts = Contact.query.filter_by(tenant_id=tenant_id).filter(Contact.email != None).all()
    prospects = Prospect.query.filter_by(tenant_id=tenant_id).filter(Prospect.email != None).all()
    
    # Verificar qué contactos/prospectos ya están seleccionados
    selected_contact_ids = [r.recipient_id for r in recipients if r.recipient_type == 'contact']
    selected_prospect_ids = [r.recipient_id for r in recipients if r.recipient_type == 'prospect']
    
    return render_template('campaigns/email/recipients.html',
                          campaign=campaign,
                          recipients=recipients,
                          contacts=contacts,
                          prospects=prospects,
                          selected_contact_ids=selected_contact_ids,
                          selected_prospect_ids=selected_prospect_ids)

@campaigns_bp.route('/email/<int:campaign_id>/schedule', methods=['GET', 'POST'])
@login_required
def schedule_email_campaign(campaign_id):
    """Programar envío de campaña de email"""
    tenant_id = get_tenant_id()
    
    campaign = EmailCampaign.query.filter_by(id=campaign_id, tenant_id=tenant_id).first_or_404()
    
    if request.method == 'POST':
        # Verificar que la campaña tenga destinatarios
        recipient_count = EmailCampaignRecipient.query.filter_by(campaign_id=campaign_id).count()
        if recipient_count == 0:
            flash('No se puede programar una campaña sin destinatarios', 'danger')
            return redirect(url_for('campaigns.manage_email_recipients', campaign_id=campaign_id))
        
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
                    return redirect(url_for('campaigns.schedule_email_campaign', campaign_id=campaign_id))
                
                campaign.status = 'Scheduled'
                campaign.scheduled_date = scheduled_datetime
                
                flash(f'La campaña ha sido programada para el {scheduled_date_str} a las {scheduled_time_str}', 'success')
                
            except ValueError:
                flash('Formato de fecha u hora inválido', 'danger')
                return redirect(url_for('campaigns.schedule_email_campaign', campaign_id=campaign_id))
        
        campaign.updated_at = datetime.datetime.now()
        db.session.commit()
        
        return redirect(url_for('campaigns.view_email_campaign', campaign_id=campaign_id))
    
    return render_template('campaigns/email/schedule.html', campaign=campaign)

@campaigns_bp.route('/whatsapp')
@login_required
def whatsapp_campaigns():
    """Mostrar lista de campañas de WhatsApp"""
    tenant_id = get_tenant_id()
    
    campaigns = WhatsAppCampaign.query.filter_by(tenant_id=tenant_id).order_by(desc(WhatsAppCampaign.created_at)).all()
    
    return render_template('campaigns/whatsapp/index.html', campaigns=campaigns)

@campaigns_bp.route('/whatsapp/create', methods=['GET', 'POST'])
@login_required
def create_whatsapp_campaign():
    """Crear nueva campaña de WhatsApp"""
    tenant_id = get_tenant_id()
    
    if request.method == 'POST':
        # Obtener datos del formulario
        name = request.form.get('name')
        description = request.form.get('description')
        
        # Verificar si se seleccionó una plantilla existente
        template_id = request.form.get('template_id')
        
        if template_id:
            # Usar plantilla existente
            template = WhatsAppTemplate.query.get(template_id)
            message = template.content
            has_media = template.has_media
            media_type = template.media_type
            media_url = template.media_url
        else:
            # Usar contenido personalizado
            message = request.form.get('message')
            has_media = 'has_media' in request.form
            media_type = request.form.get('media_type') if has_media else None
            media_url = request.form.get('media_url') if has_media else None
        
        # Crear nueva campaña
        campaign = WhatsAppCampaign(
            tenant_id=tenant_id,
            owner_id=current_user.id,
            name=name,
            description=description,
            message=message,
            has_media=has_media,
            media_type=media_type,
            media_url=media_url,
            template_id=template_id if template_id else None,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now()
        )
        
        db.session.add(campaign)
        db.session.commit()
        
        flash('Campaña de WhatsApp creada exitosamente', 'success')
        return redirect(url_for('campaigns.edit_whatsapp_campaign', campaign_id=campaign.id))
    
    # Obtener plantillas disponibles para el formulario
    templates = WhatsAppTemplate.query.filter_by(tenant_id=tenant_id, is_active=True).all()
    
    return render_template('campaigns/whatsapp/create.html', templates=templates)

@campaigns_bp.route('/whatsapp/<int:campaign_id>')
@login_required
def view_whatsapp_campaign(campaign_id):
    """Ver detalles de una campaña de WhatsApp"""
    tenant_id = get_tenant_id()
    
    campaign = WhatsAppCampaign.query.filter_by(id=campaign_id, tenant_id=tenant_id).first_or_404()
    recipients = WhatsAppCampaignRecipient.query.filter_by(campaign_id=campaign_id).all()
    
    # Calcular estadísticas
    total_recipients = len(recipients)
    sent_count = sum(1 for r in recipients if r.sent)
    delivered_count = sum(1 for r in recipients if r.delivered)
    read_count = sum(1 for r in recipients if r.read)
    
    stats = {
        'total': total_recipients,
        'sent': sent_count,
        'sent_pct': (sent_count / total_recipients * 100) if total_recipients > 0 else 0,
        'delivered': delivered_count,
        'delivered_pct': (delivered_count / sent_count * 100) if sent_count > 0 else 0,
        'read': read_count,
        'read_pct': (read_count / delivered_count * 100) if delivered_count > 0 else 0
    }
    
    return render_template('campaigns/whatsapp/view.html', 
                          campaign=campaign, 
                          recipients=recipients, 
                          stats=stats)

@campaigns_bp.route('/whatsapp/<int:campaign_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_whatsapp_campaign(campaign_id):
    """Editar campaña de WhatsApp"""
    tenant_id = get_tenant_id()
    
    campaign = WhatsAppCampaign.query.filter_by(id=campaign_id, tenant_id=tenant_id).first_or_404()
    
    if request.method == 'POST':
        # Solo se pueden editar campañas en estado borrador
        if campaign.status != 'Draft':
            flash('No se puede editar una campaña que ya ha sido enviada o programada', 'danger')
            return redirect(url_for('campaigns.view_whatsapp_campaign', campaign_id=campaign_id))
        
        # Actualizar datos de la campaña
        campaign.name = request.form.get('name')
        campaign.description = request.form.get('description')
        
        # Verificar si se cambió la plantilla
        template_id = request.form.get('template_id')
        if template_id and str(template_id) != str(campaign.template_id):
            template = WhatsAppTemplate.query.get(template_id)
            campaign.template_id = template_id
            campaign.message = template.content
            campaign.has_media = template.has_media
            campaign.media_type = template.media_type
            campaign.media_url = template.media_url
        elif not template_id:
            # Usar contenido personalizado
            campaign.template_id = None
            campaign.message = request.form.get('message')
            campaign.has_media = 'has_media' in request.form
            campaign.media_type = request.form.get('media_type') if campaign.has_media else None
            campaign.media_url = request.form.get('media_url') if campaign.has_media else None
        
        campaign.updated_at = datetime.datetime.now()
        
        db.session.commit()
        
        flash('Campaña actualizada exitosamente', 'success')
        return redirect(url_for('campaigns.view_whatsapp_campaign', campaign_id=campaign_id))
    
    # Obtener plantillas disponibles para el formulario
    templates = WhatsAppTemplate.query.filter_by(tenant_id=tenant_id, is_active=True).all()
    
    return render_template('campaigns/whatsapp/edit.html', 
                          campaign=campaign, 
                          templates=templates)

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