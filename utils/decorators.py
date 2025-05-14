from functools import wraps
from flask import session, redirect, url_for, flash, request
from flask_login import current_user
from models import Role

def tenant_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if tenant_id is in session
        if 'tenant_id' not in session:
            flash('You must be part of a tenant to access this page.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user has Admin role
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        
        role = Role.query.get(current_user.role_id)
        if not role or role.name != 'Admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user has Manager role or higher
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        
        role = Role.query.get(current_user.role_id)
        if not role or role.name not in ['Admin', 'Manager']:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function
