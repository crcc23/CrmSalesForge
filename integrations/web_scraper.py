import trafilatura
import logging
from app import db
from models import WebScrapingTask, WebScrapingResult
from datetime import datetime

def get_website_text(task_id):
    """
    Scrape text content from a website based on the task
    
    Args:
        task_id: The ID of the WebScrapingTask
        
    Returns:
        dict: Result of the operation
    """
    # Get the task
    task = WebScrapingTask.query.get(task_id)
    
    if not task:
        return {
            'success': False,
            'message': 'Task not found'
        }
    
    try:
        # Send a request to the website
        downloaded = trafilatura.fetch_url(task.url)
        if not downloaded:
            return {
                'success': False,
                'message': 'Failed to download content from URL'
            }
        
        # Extract the main content
        text = trafilatura.extract(downloaded)
        if not text:
            return {
                'success': False,
                'message': 'Failed to extract content from the webpage'
            }
        
        # Create a simple summary (first 200 characters)
        summary = text[:200] + '...' if len(text) > 200 else text
        
        # Update task
        task.last_run = datetime.utcnow()
        db.session.commit()
        
        return {
            'success': True,
            'content': text,
            'summary': summary
        }
    
    except Exception as e:
        logging.error(f"Error scraping website: {str(e)}")
        return {
            'success': False,
            'message': str(e)
        }

def get_website_text_content(url: str) -> str:
    """
    This function takes a url and returns the main text content of the website.
    The text content is extracted using trafilatura and easier to understand.
    The results is not directly readable, better to be summarized by LLM before consume
    by the user.

    Some common website to crawl information from:
    MLB scores: https://www.mlb.com/scores/YYYY-MM-DD
    """
    # Send a request to the website
    downloaded = trafilatura.fetch_url(url)
    text = trafilatura.extract(downloaded)
    return text
