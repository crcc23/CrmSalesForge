from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from models import User, Role, Tenant, SubscriptionPlan
import datetime

# Create blueprint but DON'T register it here - it will be registered in main.py
auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            flash('Invalid username or password', 'danger')
            return render_template('login.html')
            
        if not user.is_active:
            flash('Your account has been deactivated. Please contact your administrator.', 'danger')
            return render_template('login.html')
            
        # Check if tenant is active
        tenant = Tenant.query.get(user.tenant_id)
        if not tenant or not tenant.is_active:
            flash('Your organization account has been deactivated or suspended.', 'danger')
            return render_template('login.html')
            
        # Update last login time
        user.last_login = datetime.datetime.utcnow()
        db.session.commit()
        
        # Set tenant in session
        session['tenant_id'] = tenant.id
        session['tenant_name'] = tenant.name
        
        login_user(user)
        next_page = request.args.get('next')
        return redirect(next_page or url_for('dashboard.index'))
        
    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('tenant_id', None)
    session.pop('tenant_name', None)
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('auth.login'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        # Get form data
        company_name = request.form.get('company_name')
        subdomain = request.form.get('subdomain').lower()
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate form data
        if not company_name or not subdomain or not first_name or not last_name or not email or not username or not password:
            flash('All fields are required', 'danger')
            return render_template('register.html')
            
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
            
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('register.html')
            
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return render_template('register.html')
            
        # Check if subdomain already exists
        if Tenant.query.filter_by(subdomain=subdomain).first():
            flash('Subdomain already exists', 'danger')
            return render_template('register.html')
            
        # Get default subscription plan
        default_plan = SubscriptionPlan.query.filter_by(name='Free').first()
        if not default_plan:
            # Create default plans if they don't exist
            free_plan = SubscriptionPlan(
                name='Free',
                price=0.0,
                features='Basic CRM functionality',
                max_users=3,
                max_prospects=50,
                includes_email_campaigns=False,
                includes_whatsapp=False,
                includes_ai_content=False,
                includes_web_scraping=False
            )
            
            starter_plan = SubscriptionPlan(
                name='Starter',
                price=29.99,
                features='Email campaigns, Basic CRM',
                max_users=10,
                max_prospects=200,
                includes_email_campaigns=True,
                includes_whatsapp=False,
                includes_ai_content=False,
                includes_web_scraping=False
            )
            
            professional_plan = SubscriptionPlan(
                name='Professional',
                price=79.99,
                features='Email campaigns, WhatsApp, AI content, Basic CRM',
                max_users=25,
                max_prospects=1000,
                includes_email_campaigns=True,
                includes_whatsapp=True,
                includes_ai_content=True,
                includes_web_scraping=False
            )
            
            enterprise_plan = SubscriptionPlan(
                name='Enterprise',
                price=149.99,
                features='All features included, Unlimited prospects',
                max_users=100,
                max_prospects=10000,
                includes_email_campaigns=True,
                includes_whatsapp=True,
                includes_ai_content=True,
                includes_web_scraping=True
            )
            
            db.session.add_all([free_plan, starter_plan, professional_plan, enterprise_plan])
            db.session.commit()
            default_plan = free_plan
        
        # Create tenant
        tenant = Tenant(
            name=company_name,
            subdomain=subdomain,
            subscription_plan_id=default_plan.id
        )
        db.session.add(tenant)
        db.session.flush()  # To get the tenant ID without committing
        
        # Check if admin role exists
        admin_role = Role.query.filter_by(name='Admin').first()
        if not admin_role:
            # Create roles
            admin_role = Role(name='Admin')
            manager_role = Role(name='Manager')
            user_role = Role(name='User')
            db.session.add_all([admin_role, manager_role, user_role])
            db.session.flush()
        
        # Create user
        new_user = User(
            tenant_id=tenant.id,
            role_id=admin_role.id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('register.html')

@auth.route('/register_tenant', methods=['GET', 'POST'])
@login_required
def register_tenant():
    # Only admin users can create new tenants
    if current_user.role.name != 'Admin':
        flash('You do not have permission to create new tenants.', 'danger')
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        # Get form data
        company_name = request.form.get('company_name')
        subdomain = request.form.get('subdomain').lower()
        subscription_plan_id = request.form.get('subscription_plan_id')
        
        # Validate form data
        if not company_name or not subdomain or not subscription_plan_id:
            flash('All fields are required', 'danger')
            return render_template('register_tenant.html')
            
        # Check if subdomain already exists
        if Tenant.query.filter_by(subdomain=subdomain).first():
            flash('Subdomain already exists', 'danger')
            return render_template('register_tenant.html')
            
        # Create tenant
        tenant = Tenant(
            name=company_name,
            subdomain=subdomain,
            subscription_plan_id=subscription_plan_id
        )
        db.session.add(tenant)
        db.session.commit()
        
        flash('Tenant created successfully!', 'success')
        return redirect(url_for('dashboard.index'))
        
    subscription_plans = SubscriptionPlan.query.all()
    return render_template('register_tenant.html', subscription_plans=subscription_plans)
