import logging
import os
import requests
from datetime import datetime
from app import db
from models import WhatsAppCampaign, WhatsAppCampaignRecipient

def send_whatsapp_message(campaign_id):
    """
    Send a WhatsApp campaign to all recipients
    
    Args:
        campaign_id: The ID of the WhatsAppCampaign
        
    Returns:
        dict: Result of the operation
    """
    # Get the campaign
    campaign = WhatsAppCampaign.query.get(campaign_id)
    
    if not campaign:
        return {
            'success': False,
            'message': 'Campaign not found'
        }
    
    # Get recipients
    recipients = WhatsAppCampaignRecipient.query.filter_by(campaign_id=campaign_id).all()
    
    if not recipients:
        return {
            'success': False,
            'message': 'No recipients found for this campaign'
        }
    
    try:
        # Get WhatsApp API settings from environment variables
        api_key = os.environ.get('WHATSAPP_API_KEY', '')
        api_url = os.environ.get('WHATSAPP_API_URL', 'https://api.whatsapp.com/v1/messages')
        sender_phone = os.environ.get('WHATSAPP_SENDER_PHONE', '')
        
        if not api_key or not sender_phone:
            return {
                'success': False,
                'message': 'WhatsApp API credentials not configured'
            }
        
        # Send message to each recipient
        success_count = 0
        error_count = 0
        
        for recipient in recipients:
            try:
                # Format phone number (remove spaces, +, etc.)
                phone = ''.join(filter(str.isdigit, recipient.phone))
                
                # Check if phone number is valid
                if len(phone) < 10:
                    recipient.sent = False
                    error_count += 1
                    continue
                
                # Prepare payload
                payload = {
                    'from': sender_phone,
                    'to': phone,
                    'type': 'text',
                    'text': {
                        'body': campaign.message
                    }
                }
                
                # Set headers
                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }
                
                # Send message via API
                response = requests.post(
                    api_url,
                    json=payload,
                    headers=headers
                )
                
                # Check response
                if response.status_code == 200:
                    # Update recipient status
                    recipient.sent = True
                    recipient.sent_at = datetime.utcnow()
                    success_count += 1
                else:
                    error_count += 1
                    logging.error(f"Error sending WhatsApp message to {phone}: {response.text}")
            except Exception as e:
                logging.error(f"Error sending WhatsApp message to {recipient.phone}: {str(e)}")
                error_count += 1
        
        # Update campaign
        campaign.status = 'Sent'
        campaign.sent_date = datetime.utcnow()
        db.session.commit()
        
        return {
            'success': True,
            'message': f'Campaign sent to {success_count} recipients. {error_count} failed.'
        }
    
    except Exception as e:
        logging.error(f"Error sending WhatsApp campaign: {str(e)}")
        return {
            'success': False,
            'message': str(e)
        }
