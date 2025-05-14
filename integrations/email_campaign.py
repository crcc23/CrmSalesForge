import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from app import db
from models import EmailCampaign, EmailCampaignRecipient

def send_email_campaign(campaign_id):
    """
    Send an email campaign to all recipients
    
    Args:
        campaign_id: The ID of the EmailCampaign
        
    Returns:
        dict: Result of the operation
    """
    # Get the campaign
    campaign = EmailCampaign.query.get(campaign_id)
    
    if not campaign:
        return {
            'success': False,
            'message': 'Campaign not found'
        }
    
    # Get recipients
    recipients = EmailCampaignRecipient.query.filter_by(campaign_id=campaign_id).all()
    
    if not recipients:
        return {
            'success': False,
            'message': 'No recipients found for this campaign'
        }
    
    try:
        # Get SMTP settings from environment variables
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        smtp_username = os.environ.get('SMTP_USERNAME', '')
        smtp_password = os.environ.get('SMTP_PASSWORD', '')
        sender_email = os.environ.get('SENDER_EMAIL', smtp_username)
        
        if not smtp_username or not smtp_password:
            return {
                'success': False,
                'message': 'SMTP credentials not configured'
            }
        
        # Connect to SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        
        # Send email to each recipient
        success_count = 0
        error_count = 0
        
        for recipient in recipients:
            try:
                # Create message
                msg = MIMEMultipart()
                msg['From'] = sender_email
                msg['To'] = recipient.email
                msg['Subject'] = campaign.subject
                
                # Attach HTML body
                msg.attach(MIMEText(campaign.body, 'html'))
                
                # Send the message
                server.send_message(msg)
                
                # Update recipient status
                recipient.sent = True
                recipient.sent_at = datetime.utcnow()
                
                success_count += 1
            except Exception as e:
                logging.error(f"Error sending email to {recipient.email}: {str(e)}")
                error_count += 1
        
        # Close the connection
        server.quit()
        
        # Update campaign
        campaign.status = 'Sent'
        campaign.sent_date = datetime.utcnow()
        db.session.commit()
        
        return {
            'success': True,
            'message': f'Campaign sent to {success_count} recipients. {error_count} failed.'
        }
    
    except Exception as e:
        logging.error(f"Error sending email campaign: {str(e)}")
        return {
            'success': False,
            'message': str(e)
        }
