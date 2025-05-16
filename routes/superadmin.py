from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from models import Tenant, SubscriptionPlan, User, ClientSettings
import datetime

superadmin_bp = Blueprint('superadmin', __name__, url_prefix='/superadmin')

def is_superadmin():
    """Check if current user is a superadmin"""
    if not current_user.is_authenticated:
        return False
    return getattr(current_user, 'is_admin', False)

# Comentado temporalmente durante el desarrollo para permitir a todos los usuarios acceder
# @superadmin_bp.before_request
# def check_superadmin():
#     """Restrict access to superadmin users only"""
#     if not is_superadmin():
#         flash("Acceso restringido. Se requieren permisos de administrador.", "error")
#         return redirect(url_for('dashboard.index'))

@superadmin_bp.route('/')
@login_required
def index():
    """Superadmin dashboard"""
    # Get some stats for the dashboard
    tenant_count = Tenant.query.count()
    active_tenant_count = Tenant.query.filter_by(is_active=True).count()
    user_count = User.query.count()
    subscription_plans = SubscriptionPlan.query.all()
    
    return render_template('superadmin/index.html',
                           tenant_count=tenant_count,
                           active_tenant_count=active_tenant_count,
                           user_count=user_count,
                           subscription_plans=subscription_plans)

@superadmin_bp.route('/plans')
@login_required
def plans():
    """Manage subscription plans"""
    subscription_plans = SubscriptionPlan.query.all()
    return render_template('superadmin/plans.html', plans=subscription_plans)

@superadmin_bp.route('/plans/add', methods=['GET', 'POST'])
@login_required
def add_plan():
    """Add a new subscription plan"""
    if request.method == 'POST':
        name = request.form.get('name')
        price = float(request.form.get('price') or 0)
        features = request.form.get('features')
        max_users = int(request.form.get('max_users') or 5)
        max_prospects = int(request.form.get('max_prospects') or 100)
        
        # Check for required fields
        if not name or price < 0:
            flash("Por favor, complete todos los campos requeridos correctamente.", "error")
            return redirect(url_for('superadmin.add_plan'))
        
        # Check for optional features
        includes_email_campaigns = 'includes_email_campaigns' in request.form
        includes_whatsapp = 'includes_whatsapp' in request.form
        includes_ai_content = 'includes_ai_content' in request.form
        includes_web_scraping = 'includes_web_scraping' in request.form
        
        # Create new plan
        new_plan = SubscriptionPlan()
        new_plan.name = name
        new_plan.price = price
        new_plan.features = features
        new_plan.max_users = max_users
        new_plan.max_prospects = max_prospects
        new_plan.includes_email_campaigns = includes_email_campaigns
        new_plan.includes_whatsapp = includes_whatsapp
        new_plan.includes_ai_content = includes_ai_content
        new_plan.includes_web_scraping = includes_web_scraping
        
        db.session.add(new_plan)
        db.session.commit()
        
        flash(f"Plan '{name}' creado correctamente.", "success")
        return redirect(url_for('superadmin.plans'))
    
    return render_template('superadmin/add_plan.html')

@superadmin_bp.route('/plans/edit/<int:plan_id>', methods=['GET', 'POST'])
@login_required
def edit_plan(plan_id):
    """Edit an existing subscription plan"""
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        price = float(request.form.get('price') or 0)
        features = request.form.get('features')
        max_users = int(request.form.get('max_users') or 5)
        max_prospects = int(request.form.get('max_prospects') or 100)
        
        # Check for required fields
        if not name or price < 0:
            flash("Por favor, complete todos los campos requeridos correctamente.", "error")
            return redirect(url_for('superadmin.edit_plan', plan_id=plan_id))
        
        # Check for optional features
        includes_email_campaigns = 'includes_email_campaigns' in request.form
        includes_whatsapp = 'includes_whatsapp' in request.form
        includes_ai_content = 'includes_ai_content' in request.form
        includes_web_scraping = 'includes_web_scraping' in request.form
        
        # Update plan
        plan.name = name
        plan.price = price
        plan.features = features
        plan.max_users = max_users
        plan.max_prospects = max_prospects
        plan.includes_email_campaigns = includes_email_campaigns
        plan.includes_whatsapp = includes_whatsapp
        plan.includes_ai_content = includes_ai_content
        plan.includes_web_scraping = includes_web_scraping
        
        db.session.commit()
        
        flash(f"Plan '{name}' actualizado correctamente.", "success")
        return redirect(url_for('superadmin.plans'))
    
    return render_template('superadmin/edit_plan.html', plan=plan)

@superadmin_bp.route('/plans/delete/<int:plan_id>', methods=['POST'])
@login_required
def delete_plan(plan_id):
    """Delete a subscription plan"""
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    
    # Check if this plan is being used by any tenants
    if plan.tenants.count() > 0:
        flash(f"No se puede eliminar el plan '{plan.name}' porque está siendo utilizado por uno o más clientes.", "error")
        return redirect(url_for('superadmin.plans'))
    
    plan_name = plan.name
    db.session.delete(plan)
    db.session.commit()
    
    flash(f"Plan '{plan_name}' eliminado correctamente.", "success")
    return redirect(url_for('superadmin.plans'))

@superadmin_bp.route('/tenants')
@login_required
def tenants():
    """Manage tenants (clients)"""
    tenants = Tenant.query.all()
    subscription_plans = SubscriptionPlan.query.all()
    return render_template('superadmin/tenants.html', tenants=tenants, plans=subscription_plans)

@superadmin_bp.route('/tenants/edit/<int:tenant_id>', methods=['GET', 'POST'])
@login_required
def edit_tenant(tenant_id):
    """Edit a tenant"""
    tenant = Tenant.query.get_or_404(tenant_id)
    subscription_plans = SubscriptionPlan.query.all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        subdomain = request.form.get('subdomain')
        subscription_plan_id = int(request.form.get('subscription_plan_id') or 0)
        is_active = 'is_active' in request.form
        primary_color = request.form.get('primary_color')
        secondary_color = request.form.get('secondary_color')
        
        # Check for required fields
        if not name or not subdomain or subscription_plan_id <= 0:
            flash("Por favor, complete todos los campos requeridos.", "error")
            return redirect(url_for('superadmin.edit_tenant', tenant_id=tenant_id))
        
        # Check if subdomain is unique (except for this tenant)
        subdomain_tenant = Tenant.query.filter(Tenant.subdomain == subdomain, Tenant.id != tenant_id).first()
        if subdomain_tenant:
            flash(f"El subdominio '{subdomain}' ya está siendo utilizado por otro cliente.", "error")
            return redirect(url_for('superadmin.edit_tenant', tenant_id=tenant_id))
        
        # Update tenant
        tenant.name = name
        tenant.subdomain = subdomain
        tenant.subscription_plan_id = subscription_plan_id
        tenant.is_active = is_active
        tenant.primary_color = primary_color
        tenant.secondary_color = secondary_color
        
        db.session.commit()
        
        flash(f"Cliente '{name}' actualizado correctamente.", "success")
        return redirect(url_for('superadmin.tenants'))
    
    return render_template('superadmin/edit_tenant.html', tenant=tenant, plans=subscription_plans)

@superadmin_bp.route('/tenants/toggle/<int:tenant_id>', methods=['POST'])
@login_required
def toggle_tenant(tenant_id):
    """Toggle tenant active status"""
    tenant = Tenant.query.get_or_404(tenant_id)
    
    # Toggle status
    tenant.is_active = not tenant.is_active
    db.session.commit()
    
    status = "activado" if tenant.is_active else "desactivado"
    flash(f"Cliente '{tenant.name}' {status} correctamente.", "success")
    
    return redirect(url_for('superadmin.tenants'))

@superadmin_bp.route('/tenants/billing/<int:tenant_id>', methods=['GET', 'POST'])
@login_required
def tenant_billing(tenant_id):
    """Manage tenant billing information"""
    tenant = Tenant.query.get_or_404(tenant_id)
    settings = ClientSettings.query.filter_by(tenant_id=tenant_id).first()
    
    # Create settings if they don't exist
    if not settings:
        settings = ClientSettings()
        settings.tenant_id = tenant_id
        db.session.add(settings)
        db.session.commit()
    
    if request.method == 'POST':
        # Update billing information
        settings.billing_plan = request.form.get('billing_plan')
        settings.billing_cycle = request.form.get('billing_cycle')
        settings.billing_contact_email = request.form.get('billing_contact_email')
        settings.subscription_status = request.form.get('subscription_status')
        
        try:
            start_date = request.form.get('subscription_start_date')
            if start_date and start_date.strip():
                settings.subscription_start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            
            end_date = request.form.get('subscription_end_date')
            if end_date and end_date.strip():
                settings.subscription_end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            flash("Formato de fecha incorrecto. Use el formato YYYY-MM-DD.", "error")
            return redirect(url_for('superadmin.tenant_billing', tenant_id=tenant_id))
        
        db.session.commit()
        
        flash(f"Información de facturación para '{tenant.name}' actualizada correctamente.", "success")
        return redirect(url_for('superadmin.tenants'))
    
    return render_template('superadmin/tenant_billing.html', tenant=tenant, settings=settings)