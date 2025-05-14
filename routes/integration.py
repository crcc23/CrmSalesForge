from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_required, current_user
from app import db
from models import (
    Tenant, SubscriptionPlan, EmailCampaign, EmailCampaignRecipient,
    WhatsAppCampaign, WhatsAppCampaignRecipient, AIContent,
    WebScrapingTask, WebScrapingResult, Contact, Prospect
)
from utils.decorators import tenant_required
from integrations.web_scraper import get_website_text
from integrations.email_campaign import send_email_campaign
from integrations.whatsapp import send_whatsapp_message
from integrations.ai_content import generate_ai_content
import datetime

# Create blueprint but DON'T register it here - it will be registered in main.py
integration = Blueprint('integration', __name__)

@integration.route('/integrations')
@login_required
@tenant_required
def index():
    tenant_id = session.get('tenant_id')
    tenant = Tenant.query.get(tenant_id)
    subscription_plan = SubscriptionPlan.query.get(tenant.subscription_plan_id)
    
    # Get counts for different integration types
    email_campaigns_count = EmailCampaign.query.filter_by(tenant_id=tenant_id).count()
    whatsapp_campaigns_count = WhatsAppCampaign.query.filter_by(tenant_id=tenant_id).count()
    ai_contents_count = AIContent.query.filter_by(tenant_id=tenant_id).count()
    scraping_tasks_count = WebScrapingTask.query.filter_by(tenant_id=tenant_id).count()
    
    return render_template('integrations.html',
                          tenant=tenant,
                          subscription_plan=subscription_plan,
                          email_campaigns_count=email_campaigns_count,
                          whatsapp_campaigns_count=whatsapp_campaigns_count,
                          ai_contents_count=ai_contents_count,
                          scraping_tasks_count=scraping_tasks_count)

# Email Campaign routes
@integration.route('/integrations/email')
@login_required
@tenant_required
def email_campaigns():
    tenant_id = session.get('tenant_id')
    tenant = Tenant.query.get(tenant_id)
    subscription_plan = SubscriptionPlan.query.get(tenant.subscription_plan_id)
    
    if not subscription_plan.includes_email_campaigns:
        flash('Email campaigns are not included in your subscription plan. Please upgrade to use this feature.', 'warning')
        return redirect(url_for('integration.index'))
    
    campaigns = EmailCampaign.query.filter_by(tenant_id=tenant_id).order_by(EmailCampaign.created_at.desc()).all()
    
    return render_template('email_campaigns.html',
                          campaigns=campaigns)

@integration.route('/integrations/email/new', methods=['GET', 'POST'])
@login_required
@tenant_required
def new_email_campaign():
    tenant_id = session.get('tenant_id')
    tenant = Tenant.query.get(tenant_id)
    subscription_plan = SubscriptionPlan.query.get(tenant.subscription_plan_id)
    
    if not subscription_plan.includes_email_campaigns:
        flash('Email campaigns are not included in your subscription plan. Please upgrade to use this feature.', 'warning')
        return redirect(url_for('integration.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        subject = request.form.get('subject')
        body = request.form.get('body')
        
        # Create campaign
        campaign = EmailCampaign(
            tenant_id=tenant_id,
            owner_id=current_user.id,
            name=name,
            subject=subject,
            body=body,
            status='Draft'
        )
        db.session.add(campaign)
        db.session.commit()
        
        flash('Email campaign created successfully.', 'success')
        return redirect(url_for('integration.email_campaigns'))
    
    contacts = Contact.query.filter_by(tenant_id=tenant_id).all()
    prospects = Prospect.query.filter_by(tenant_id=tenant_id).all()
    
    return render_template('email_campaign_form.html',
                          campaign=None,
                          contacts=contacts,
                          prospects=prospects,
                          action='new')

@integration.route('/integrations/email/edit/<int:campaign_id>', methods=['GET', 'POST'])
@login_required
@tenant_required
def edit_email_campaign(campaign_id):
    tenant_id = session.get('tenant_id')
    
    campaign = EmailCampaign.query.filter_by(id=campaign_id, tenant_id=tenant_id).first()
    
    if not campaign:
        flash('Campaign not found.', 'danger')
        return redirect(url_for('integration.email_campaigns'))
    
    if campaign.status != 'Draft':
        flash('Cannot edit campaign that is not in draft status.', 'warning')
        return redirect(url_for('integration.email_campaigns'))
    
    if request.method == 'POST':
        campaign.name = request.form.get('name')
        campaign.subject = request.form.get('subject')
        campaign.body = request.form.get('body')
        campaign.updated_at = datetime.datetime.utcnow()
        
        db.session.commit()
        
        flash('Email campaign updated successfully.', 'success')
        return redirect(url_for('integration.email_campaigns'))
    
    contacts = Contact.query.filter_by(tenant_id=tenant_id).all()
    prospects = Prospect.query.filter_by(tenant_id=tenant_id).all()
    
    # Get existing recipients
    recipients = EmailCampaignRecipient.query.filter_by(campaign_id=campaign_id).all()
    
    return render_template('email_campaign_form.html',
                          campaign=campaign,
                          contacts=contacts,
                          prospects=prospects,
                          recipients=recipients,
                          action='edit')

@integration.route('/integrations/email/add_recipient', methods=['POST'])
@login_required
@tenant_required
def add_email_recipient():
    tenant_id = session.get('tenant_id')
    
    campaign_id = request.form.get('campaign_id')
    recipient_type = request.form.get('recipient_type')
    recipient_id = request.form.get('recipient_id')
    
    if not campaign_id or not recipient_type or not recipient_id:
        return jsonify({'success': False, 'message': 'Missing required fields'})
    
    campaign = EmailCampaign.query.filter_by(id=campaign_id, tenant_id=tenant_id).first()
    
    if not campaign:
        return jsonify({'success': False, 'message': 'Campaign not found'})
    
    if campaign.status != 'Draft':
        return jsonify({'success': False, 'message': 'Cannot modify recipients for a campaign that is not in draft status'})
    
    # Check if recipient already exists
    existing_recipient = EmailCampaignRecipient.query.filter_by(
        campaign_id=campaign_id,
        recipient_type=recipient_type,
        recipient_id=recipient_id
    ).first()
    
    if existing_recipient:
        return jsonify({'success': False, 'message': 'Recipient already added to this campaign'})
    
    # Get recipient email
    email = None
    name = None
    
    if recipient_type == 'contact':
        contact = Contact.query.filter_by(id=recipient_id, tenant_id=tenant_id).first()
        if contact:
            email = contact.email
            name = contact.full_name
    elif recipient_type == 'prospect':
        prospect = Prospect.query.filter_by(id=recipient_id, tenant_id=tenant_id).first()
        if prospect:
            email = prospect.email
            name = prospect.full_name
    
    if not email:
        return jsonify({'success': False, 'message': 'Recipient has no email address'})
    
    # Add recipient
    recipient = EmailCampaignRecipient(
        campaign_id=campaign_id,
        recipient_type=recipient_type,
        recipient_id=recipient_id,
        email=email
    )
    
    db.session.add(recipient)
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': 'Recipient added successfully',
        'recipient': {
            'id': recipient.id,
            'name': name,
            'email': email,
            'type': recipient_type
        }
    })

@integration.route('/integrations/email/remove_recipient', methods=['POST'])
@login_required
@tenant_required
def remove_email_recipient():
    tenant_id = session.get('tenant_id')
    
    recipient_id = request.form.get('recipient_id')
    
    if not recipient_id:
        return jsonify({'success': False, 'message': 'Missing recipient ID'})
    
    recipient = EmailCampaignRecipient.query.get(recipient_id)
    
    if not recipient:
        return jsonify({'success': False, 'message': 'Recipient not found'})
    
    campaign = EmailCampaign.query.filter_by(id=recipient.campaign_id, tenant_id=tenant_id).first()
    
    if not campaign:
        return jsonify({'success': False, 'message': 'Campaign not found'})
    
    if campaign.status != 'Draft':
        return jsonify({'success': False, 'message': 'Cannot modify recipients for a campaign that is not in draft status'})
    
    db.session.delete(recipient)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Recipient removed successfully'})

@integration.route('/integrations/email/send/<int:campaign_id>', methods=['POST'])
@login_required
@tenant_required
def send_email_campaign_route(campaign_id):
    tenant_id = session.get('tenant_id')
    
    campaign = EmailCampaign.query.filter_by(id=campaign_id, tenant_id=tenant_id).first()
    
    if not campaign:
        flash('Campaign not found.', 'danger')
        return redirect(url_for('integration.email_campaigns'))
    
    if campaign.status not in ['Draft', 'Scheduled']:
        flash('Campaign already sent or in progress.', 'warning')
        return redirect(url_for('integration.email_campaigns'))
    
    # Count recipients
    recipients_count = EmailCampaignRecipient.query.filter_by(campaign_id=campaign_id).count()
    
    if recipients_count == 0:
        flash('Cannot send campaign with no recipients.', 'warning')
        return redirect(url_for('integration.email_campaigns'))
    
    # Update campaign status
    campaign.status = 'Sending'
    campaign.sent_date = datetime.datetime.utcnow()
    db.session.commit()
    
    # Call the email sending function (this would normally be async)
    try:
        result = send_email_campaign(campaign_id)
        if result['success']:
            campaign.status = 'Sent'
            flash('Campaign sent successfully.', 'success')
        else:
            campaign.status = 'Failed'
            flash(f'Error sending campaign: {result["message"]}', 'danger')
        
        db.session.commit()
    except Exception as e:
        campaign.status = 'Failed'
        db.session.commit()
        flash(f'Error sending campaign: {str(e)}', 'danger')
    
    return redirect(url_for('integration.email_campaigns'))

# WhatsApp Campaign routes
@integration.route('/integrations/whatsapp')
@login_required
@tenant_required
def whatsapp_campaigns():
    tenant_id = session.get('tenant_id')
    tenant = Tenant.query.get(tenant_id)
    subscription_plan = SubscriptionPlan.query.get(tenant.subscription_plan_id)
    
    if not subscription_plan.includes_whatsapp:
        flash('WhatsApp campaigns are not included in your subscription plan. Please upgrade to use this feature.', 'warning')
        return redirect(url_for('integration.index'))
    
    campaigns = WhatsAppCampaign.query.filter_by(tenant_id=tenant_id).order_by(WhatsAppCampaign.created_at.desc()).all()
    
    return render_template('whatsapp_campaigns.html',
                          campaigns=campaigns)

@integration.route('/integrations/whatsapp/new', methods=['GET', 'POST'])
@login_required
@tenant_required
def new_whatsapp_campaign():
    tenant_id = session.get('tenant_id')
    tenant = Tenant.query.get(tenant_id)
    subscription_plan = SubscriptionPlan.query.get(tenant.subscription_plan_id)
    
    if not subscription_plan.includes_whatsapp:
        flash('WhatsApp campaigns are not included in your subscription plan. Please upgrade to use this feature.', 'warning')
        return redirect(url_for('integration.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        message = request.form.get('message')
        
        # Create campaign
        campaign = WhatsAppCampaign(
            tenant_id=tenant_id,
            owner_id=current_user.id,
            name=name,
            message=message,
            status='Draft'
        )
        db.session.add(campaign)
        db.session.commit()
        
        flash('WhatsApp campaign created successfully.', 'success')
        return redirect(url_for('integration.whatsapp_campaigns'))
    
    contacts = Contact.query.filter_by(tenant_id=tenant_id).all()
    prospects = Prospect.query.filter_by(tenant_id=tenant_id).all()
    
    return render_template('whatsapp_campaign_form.html',
                          campaign=None,
                          contacts=contacts,
                          prospects=prospects,
                          action='new')

@integration.route('/integrations/whatsapp/edit/<int:campaign_id>', methods=['GET', 'POST'])
@login_required
@tenant_required
def edit_whatsapp_campaign(campaign_id):
    tenant_id = session.get('tenant_id')
    
    campaign = WhatsAppCampaign.query.filter_by(id=campaign_id, tenant_id=tenant_id).first()
    
    if not campaign:
        flash('Campaign not found.', 'danger')
        return redirect(url_for('integration.whatsapp_campaigns'))
    
    if campaign.status != 'Draft':
        flash('Cannot edit campaign that is not in draft status.', 'warning')
        return redirect(url_for('integration.whatsapp_campaigns'))
    
    if request.method == 'POST':
        campaign.name = request.form.get('name')
        campaign.message = request.form.get('message')
        campaign.updated_at = datetime.datetime.utcnow()
        
        db.session.commit()
        
        flash('WhatsApp campaign updated successfully.', 'success')
        return redirect(url_for('integration.whatsapp_campaigns'))
    
    contacts = Contact.query.filter_by(tenant_id=tenant_id).all()
    prospects = Prospect.query.filter_by(tenant_id=tenant_id).all()
    
    # Get existing recipients
    recipients = WhatsAppCampaignRecipient.query.filter_by(campaign_id=campaign_id).all()
    
    return render_template('whatsapp_campaign_form.html',
                          campaign=campaign,
                          contacts=contacts,
                          prospects=prospects,
                          recipients=recipients,
                          action='edit')

@integration.route('/integrations/whatsapp/add_recipient', methods=['POST'])
@login_required
@tenant_required
def add_whatsapp_recipient():
    tenant_id = session.get('tenant_id')
    
    campaign_id = request.form.get('campaign_id')
    recipient_type = request.form.get('recipient_type')
    recipient_id = request.form.get('recipient_id')
    
    if not campaign_id or not recipient_type or not recipient_id:
        return jsonify({'success': False, 'message': 'Missing required fields'})
    
    campaign = WhatsAppCampaign.query.filter_by(id=campaign_id, tenant_id=tenant_id).first()
    
    if not campaign:
        return jsonify({'success': False, 'message': 'Campaign not found'})
    
    if campaign.status != 'Draft':
        return jsonify({'success': False, 'message': 'Cannot modify recipients for a campaign that is not in draft status'})
    
    # Check if recipient already exists
    existing_recipient = WhatsAppCampaignRecipient.query.filter_by(
        campaign_id=campaign_id,
        recipient_type=recipient_type,
        recipient_id=recipient_id
    ).first()
    
    if existing_recipient:
        return jsonify({'success': False, 'message': 'Recipient already added to this campaign'})
    
    # Get recipient phone
    phone = None
    name = None
    
    if recipient_type == 'contact':
        contact = Contact.query.filter_by(id=recipient_id, tenant_id=tenant_id).first()
        if contact:
            phone = contact.mobile or contact.phone
            name = contact.full_name
    elif recipient_type == 'prospect':
        prospect = Prospect.query.filter_by(id=recipient_id, tenant_id=tenant_id).first()
        if prospect:
            phone = prospect.phone
            name = prospect.full_name
    
    if not phone:
        return jsonify({'success': False, 'message': 'Recipient has no phone number'})
    
    # Add recipient
    recipient = WhatsAppCampaignRecipient(
        campaign_id=campaign_id,
        recipient_type=recipient_type,
        recipient_id=recipient_id,
        phone=phone
    )
    
    db.session.add(recipient)
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': 'Recipient added successfully',
        'recipient': {
            'id': recipient.id,
            'name': name,
            'phone': phone,
            'type': recipient_type
        }
    })

@integration.route('/integrations/whatsapp/remove_recipient', methods=['POST'])
@login_required
@tenant_required
def remove_whatsapp_recipient():
    tenant_id = session.get('tenant_id')
    
    recipient_id = request.form.get('recipient_id')
    
    if not recipient_id:
        return jsonify({'success': False, 'message': 'Missing recipient ID'})
    
    recipient = WhatsAppCampaignRecipient.query.get(recipient_id)
    
    if not recipient:
        return jsonify({'success': False, 'message': 'Recipient not found'})
    
    campaign = WhatsAppCampaign.query.filter_by(id=recipient.campaign_id, tenant_id=tenant_id).first()
    
    if not campaign:
        return jsonify({'success': False, 'message': 'Campaign not found'})
    
    if campaign.status != 'Draft':
        return jsonify({'success': False, 'message': 'Cannot modify recipients for a campaign that is not in draft status'})
    
    db.session.delete(recipient)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Recipient removed successfully'})

@integration.route('/integrations/whatsapp/send/<int:campaign_id>', methods=['POST'])
@login_required
@tenant_required
def send_whatsapp_campaign(campaign_id):
    tenant_id = session.get('tenant_id')
    
    campaign = WhatsAppCampaign.query.filter_by(id=campaign_id, tenant_id=tenant_id).first()
    
    if not campaign:
        flash('Campaign not found.', 'danger')
        return redirect(url_for('integration.whatsapp_campaigns'))
    
    if campaign.status not in ['Draft', 'Scheduled']:
        flash('Campaign already sent or in progress.', 'warning')
        return redirect(url_for('integration.whatsapp_campaigns'))
    
    # Count recipients
    recipients_count = WhatsAppCampaignRecipient.query.filter_by(campaign_id=campaign_id).count()
    
    if recipients_count == 0:
        flash('Cannot send campaign with no recipients.', 'warning')
        return redirect(url_for('integration.whatsapp_campaigns'))
    
    # Update campaign status
    campaign.status = 'Sending'
    campaign.sent_date = datetime.datetime.utcnow()
    db.session.commit()
    
    # Call the WhatsApp sending function (this would normally be async)
    try:
        result = send_whatsapp_message(campaign_id)
        if result['success']:
            campaign.status = 'Sent'
            flash('Campaign sent successfully.', 'success')
        else:
            campaign.status = 'Failed'
            flash(f'Error sending campaign: {result["message"]}', 'danger')
        
        db.session.commit()
    except Exception as e:
        campaign.status = 'Failed'
        db.session.commit()
        flash(f'Error sending campaign: {str(e)}', 'danger')
    
    return redirect(url_for('integration.whatsapp_campaigns'))

# AI Content Generation routes
@integration.route('/integrations/ai')
@login_required
@tenant_required
def ai_contents():
    tenant_id = session.get('tenant_id')
    tenant = Tenant.query.get(tenant_id)
    subscription_plan = SubscriptionPlan.query.get(tenant.subscription_plan_id)
    
    if not subscription_plan.includes_ai_content:
        flash('AI content generation is not included in your subscription plan. Please upgrade to use this feature.', 'warning')
        return redirect(url_for('integration.index'))
    
    contents = AIContent.query.filter_by(tenant_id=tenant_id, user_id=current_user.id).order_by(AIContent.created_at.desc()).all()
    
    return render_template('ai_contents.html', contents=contents)

@integration.route('/integrations/ai/new', methods=['GET', 'POST'])
@login_required
@tenant_required
def new_ai_content():
    tenant_id = session.get('tenant_id')
    tenant = Tenant.query.get(tenant_id)
    subscription_plan = SubscriptionPlan.query.get(tenant.subscription_plan_id)
    
    if not subscription_plan.includes_ai_content:
        flash('AI content generation is not included in your subscription plan. Please upgrade to use this feature.', 'warning')
        return redirect(url_for('integration.index'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        prompt = request.form.get('prompt')
        content_type = request.form.get('content_type')
        
        # Create AI content request
        ai_content = AIContent(
            tenant_id=tenant_id,
            user_id=current_user.id,
            title=title,
            prompt=prompt,
            content_type=content_type,
            status='Pending'
        )
        db.session.add(ai_content)
        db.session.commit()
        
        # Generate content (this would normally be async)
        try:
            result = generate_ai_content(ai_content.id)
            if result['success']:
                ai_content.content = result['content']
                ai_content.status = 'Completed'
                flash('Content generated successfully.', 'success')
            else:
                ai_content.status = 'Failed'
                flash(f'Error generating content: {result["message"]}', 'danger')
            
            db.session.commit()
        except Exception as e:
            ai_content.status = 'Failed'
            db.session.commit()
            flash(f'Error generating content: {str(e)}', 'danger')
        
        return redirect(url_for('integration.ai_contents'))
    
    return render_template('ai_content_form.html')

@integration.route('/integrations/ai/view/<int:content_id>')
@login_required
@tenant_required
def view_ai_content(content_id):
    tenant_id = session.get('tenant_id')
    
    content = AIContent.query.filter_by(id=content_id, tenant_id=tenant_id, user_id=current_user.id).first()
    
    if not content:
        flash('Content not found.', 'danger')
        return redirect(url_for('integration.ai_contents'))
    
    return render_template('ai_content_view.html', content=content)

# Web Scraping routes
@integration.route('/integrations/scraping')
@login_required
@tenant_required
def scraping_tasks():
    tenant_id = session.get('tenant_id')
    tenant = Tenant.query.get(tenant_id)
    subscription_plan = SubscriptionPlan.query.get(tenant.subscription_plan_id)
    
    if not subscription_plan.includes_web_scraping:
        flash('Web scraping is not included in your subscription plan. Please upgrade to use this feature.', 'warning')
        return redirect(url_for('integration.index'))
    
    tasks = WebScrapingTask.query.filter_by(tenant_id=tenant_id, user_id=current_user.id).order_by(WebScrapingTask.created_at.desc()).all()
    
    return render_template('scraping_tasks.html', tasks=tasks)

@integration.route('/integrations/scraping/new', methods=['GET', 'POST'])
@login_required
@tenant_required
def new_scraping_task():
    tenant_id = session.get('tenant_id')
    tenant = Tenant.query.get(tenant_id)
    subscription_plan = SubscriptionPlan.query.get(tenant.subscription_plan_id)
    
    if not subscription_plan.includes_web_scraping:
        flash('Web scraping is not included in your subscription plan. Please upgrade to use this feature.', 'warning')
        return redirect(url_for('integration.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        url = request.form.get('url')
        frequency = request.form.get('frequency')
        
        # Create scraping task
        task = WebScrapingTask(
            tenant_id=tenant_id,
            user_id=current_user.id,
            name=name,
            url=url,
            frequency=frequency,
            status='Pending'
        )
        db.session.add(task)
        db.session.commit()
        
        # Run the task immediately if once-off
        if frequency == 'once':
            try:
                result = get_website_text(task.id)
                if result['success']:
                    task.status = 'Completed'
                    task.last_run = datetime.datetime.utcnow()
                    
                    # Create scraping result
                    scraping_result = WebScrapingResult(
                        task_id=task.id,
                        status='Success',
                        content=result['content'],
                        summary=result['summary']
                    )
                    db.session.add(scraping_result)
                    flash('Website scraped successfully.', 'success')
                else:
                    task.status = 'Failed'
                    # Create error result
                    scraping_result = WebScrapingResult(
                        task_id=task.id,
                        status='Failed',
                        error=result['message']
                    )
                    db.session.add(scraping_result)
                    flash(f'Error scraping website: {result["message"]}', 'danger')
                
                db.session.commit()
            except Exception as e:
                task.status = 'Failed'
                # Create error result
                scraping_result = WebScrapingResult(
                    task_id=task.id,
                    status='Failed',
                    error=str(e)
                )
                db.session.add(scraping_result)
                db.session.commit()
                flash(f'Error scraping website: {str(e)}', 'danger')
        else:
            # Schedule for later based on frequency
            if frequency == 'daily':
                task.next_run = datetime.datetime.utcnow() + datetime.timedelta(days=1)
            elif frequency == 'weekly':
                task.next_run = datetime.datetime.utcnow() + datetime.timedelta(weeks=1)
            elif frequency == 'monthly':
                task.next_run = datetime.datetime.utcnow() + datetime.timedelta(days=30)
            
            task.status = 'Scheduled'
            db.session.commit()
            flash('Scraping task scheduled successfully.', 'success')
        
        return redirect(url_for('integration.scraping_tasks'))
    
    return render_template('scraping_task_form.html')

@integration.route('/integrations/scraping/view/<int:task_id>')
@login_required
@tenant_required
def view_scraping_task(task_id):
    tenant_id = session.get('tenant_id')
    
    task = WebScrapingTask.query.filter_by(id=task_id, tenant_id=tenant_id, user_id=current_user.id).first()
    
    if not task:
        flash('Task not found.', 'danger')
        return redirect(url_for('integration.scraping_tasks'))
    
    # Get results
    results = WebScrapingResult.query.filter_by(task_id=task_id).order_by(WebScrapingResult.execution_date.desc()).all()
    
    return render_template('scraping_task_view.html', task=task, results=results)

@integration.route('/integrations/scraping/run/<int:task_id>', methods=['POST'])
@login_required
@tenant_required
def run_scraping_task(task_id):
    tenant_id = session.get('tenant_id')
    
    task = WebScrapingTask.query.filter_by(id=task_id, tenant_id=tenant_id, user_id=current_user.id).first()
    
    if not task:
        flash('Task not found.', 'danger')
        return redirect(url_for('integration.scraping_tasks'))
    
    # Update task status
    task.status = 'Running'
    db.session.commit()
    
    # Run the scraping task
    try:
        result = get_website_text(task.id)
        if result['success']:
            task.status = 'Completed'
            task.last_run = datetime.datetime.utcnow()
            
            # Update next run time if recurring
            if task.frequency == 'daily':
                task.next_run = datetime.datetime.utcnow() + datetime.timedelta(days=1)
            elif task.frequency == 'weekly':
                task.next_run = datetime.datetime.utcnow() + datetime.timedelta(weeks=1)
            elif task.frequency == 'monthly':
                task.next_run = datetime.datetime.utcnow() + datetime.timedelta(days=30)
            
            # Create scraping result
            scraping_result = WebScrapingResult(
                task_id=task.id,
                status='Success',
                content=result['content'],
                summary=result['summary']
            )
            db.session.add(scraping_result)
            flash('Website scraped successfully.', 'success')
        else:
            task.status = 'Failed'
            # Create error result
            scraping_result = WebScrapingResult(
                task_id=task.id,
                status='Failed',
                error=result['message']
            )
            db.session.add(scraping_result)
            flash(f'Error scraping website: {result["message"]}', 'danger')
        
        db.session.commit()
    except Exception as e:
        task.status = 'Failed'
        # Create error result
        scraping_result = WebScrapingResult(
            task_id=task.id,
            status='Failed',
            error=str(e)
        )
        db.session.add(scraping_result)
        db.session.commit()
        flash(f'Error scraping website: {str(e)}', 'danger')
    
    return redirect(url_for('integration.view_scraping_task', task_id=task_id))
