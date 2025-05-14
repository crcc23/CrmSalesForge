import re
import datetime
from flask import session
from models import Tenant

def get_tenant_theme_settings():
    """Get current tenant's theme settings"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        return {
            'primary_color': '#3498db',
            'secondary_color': '#2ecc71',
            'logo_url': None,
            'name': 'CRM System'
        }
    
    tenant = Tenant.query.get(tenant_id)
    if not tenant:
        return {
            'primary_color': '#3498db',
            'secondary_color': '#2ecc71',
            'logo_url': None,
            'name': 'CRM System'
        }
    
    return {
        'primary_color': tenant.primary_color or '#3498db',
        'secondary_color': tenant.secondary_color or '#2ecc71',
        'logo_url': tenant.logo_url,
        'name': tenant.name
    }

def format_currency(amount):
    """Format a number as currency"""
    if amount is None:
        return '$0.00'
    
    return f"${amount:,.2f}"

def format_date(date):
    """Format a date for display"""
    if not date:
        return ''
    
    if isinstance(date, str):
        try:
            date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            return date
    
    return date.strftime('%b %d, %Y')

def format_datetime(dt):
    """Format a datetime for display"""
    if not dt:
        return ''
    
    if isinstance(dt, str):
        try:
            dt = datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return dt
    
    return dt.strftime('%b %d, %Y %I:%M %p')

def sanitize_html(html):
    """Sanitize HTML to prevent XSS attacks"""
    if not html:
        return ''
    
    # Remove script tags
    html = re.sub(r'<script.*?>.*?</script>', '', html, flags=re.DOTALL)
    
    # Remove on* attributes
    html = re.sub(r'\s+on\w+=".*?"', '', html)
    html = re.sub(r"\s+on\w+='.*?'", '', html)
    html = re.sub(r'\s+on\w+=.*?>', '>', html)
    
    # Remove javascript: in URLs
    html = re.sub(r'href="javascript:.*?"', 'href="#"', html)
    html = re.sub(r"href='javascript:.*?'", "href='#'", html)
    
    return html

def get_initials(name):
    """Get initials from a name"""
    if not name:
        return ''
    
    parts = name.split()
    initials = ''
    
    for part in parts:
        if part and len(part) > 0:
            initials += part[0].upper()
    
    return initials[:2]  # Return at most 2 characters
