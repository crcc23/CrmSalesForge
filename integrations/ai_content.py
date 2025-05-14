import logging
import os
import requests
import json
from datetime import datetime
from app import db
from models import AIContent

def generate_ai_content(content_id):
    """
    Generate AI content based on the provided prompt
    
    Args:
        content_id: The ID of the AIContent record
        
    Returns:
        dict: Result of the operation
    """
    # Get the AI content record
    content_record = AIContent.query.get(content_id)
    
    if not content_record:
        return {
            'success': False,
            'message': 'Content record not found'
        }
    
    try:
        # Get AI API settings from environment variables
        api_key = os.environ.get('AI_API_KEY', '')
        api_url = os.environ.get('AI_API_URL', 'https://api.openai.com/v1/completions')
        
        if not api_key:
            return {
                'success': False,
                'message': 'AI API credentials not configured'
            }
        
        # Prepare prompt based on content type
        base_prompt = content_record.prompt
        content_type = content_record.content_type
        
        if content_type == 'email':
            full_prompt = f"Write a professional email with the following information: {base_prompt}"
        elif content_type == 'blog':
            full_prompt = f"Write a blog post about: {base_prompt}"
        elif content_type == 'social':
            full_prompt = f"Write a social media post about: {base_prompt}"
        elif content_type == 'whatsapp':
            full_prompt = f"Write a brief WhatsApp message about: {base_prompt}"
        else:
            full_prompt = base_prompt
        
        # Prepare payload for API
        payload = {
            "model": "gpt-3.5-turbo",  # Can be configured based on needs
            "messages": [
                {"role": "system", "content": f"You are a helpful assistant that generates {content_type} content."},
                {"role": "user", "content": full_prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        # Set headers
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Make API request
        response = requests.post(
            api_url,
            headers=headers,
            json=payload
        )
        
        # Check response
        if response.status_code == 200:
            response_data = response.json()
            generated_content = response_data["choices"][0]["message"]["content"].strip()
            
            # Update content record
            content_record.content = generated_content
            content_record.status = 'Completed'
            content_record.updated_at = datetime.utcnow()
            db.session.commit()
            
            return {
                'success': True,
                'content': generated_content
            }
        else:
            error_message = f"API Error: {response.status_code} - {response.text}"
            logging.error(error_message)
            return {
                'success': False,
                'message': error_message
            }
    
    except Exception as e:
        logging.error(f"Error generating AI content: {str(e)}")
        return {
            'success': False,
            'message': str(e)
        }
