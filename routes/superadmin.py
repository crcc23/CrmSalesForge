from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
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

@superadmin_bp.route('/tenants/add', methods=['GET', 'POST'])
@login_required
def add_tenant():
    """Add a new tenant (client)"""
    subscription_plans = SubscriptionPlan.query.all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        subdomain = request.form.get('subdomain')
        subscription_plan_id = int(request.form.get('subscription_plan_id') or 0)
        primary_color = request.form.get('primary_color', '#3498db')
        secondary_color = request.form.get('secondary_color', '#2ecc71')
        logo_url = request.form.get('logo_url')
        
        # Validar datos
        if not name or not subdomain:
            flash("Nombre y subdominio son campos obligatorios.", "error")
            return redirect(url_for('superadmin.add_tenant'))
        
        # Verificar que el subdominio sea único
        existing_tenant = Tenant.query.filter_by(subdomain=subdomain).first()
        if existing_tenant:
            flash(f"El subdominio '{subdomain}' ya está en uso. Por favor, elija otro.", "error")
            return redirect(url_for('superadmin.add_tenant'))
        
        # Verificar que exista el plan seleccionado
        if subscription_plan_id <= 0:
            flash("Debe seleccionar un plan de suscripción válido.", "error")
            return redirect(url_for('superadmin.add_tenant'))
        
        # Crear nuevo tenant
        new_tenant = Tenant()
        new_tenant.name = name
        new_tenant.subdomain = subdomain
        new_tenant.subscription_plan_id = subscription_plan_id
        new_tenant.primary_color = primary_color
        new_tenant.secondary_color = secondary_color
        new_tenant.logo_url = logo_url
        new_tenant.is_active = True
        
        db.session.add(new_tenant)
        db.session.commit()
        
        # Crear configuración inicial para el cliente
        client_settings = ClientSettings()
        client_settings.tenant_id = new_tenant.id
        client_settings.company_name = name
        client_settings.billing_plan = new_tenant.subscription_plan.name
        client_settings.billing_cycle = 'monthly'
        client_settings.subscription_status = 'active'
        client_settings.subscription_start_date = datetime.datetime.now()
        client_settings.subscription_end_date = datetime.datetime.now() + datetime.timedelta(days=30)
        
        db.session.add(client_settings)
        db.session.commit()
        
        # Obtener los datos del administrador
        admin_email = request.form.get('admin_email')
        admin_password = request.form.get('admin_password')
        admin_password_confirm = request.form.get('admin_password_confirm')
        
        # Validar los datos del administrador
        if not admin_email or not admin_password or not admin_password_confirm:
            flash("El email y la contraseña del administrador son campos obligatorios.", "error")
            return redirect(url_for('superadmin.add_tenant'))
        
        if admin_password != admin_password_confirm:
            flash("Las contraseñas no coinciden. Por favor, inténtelo de nuevo.", "error")
            return redirect(url_for('superadmin.add_tenant'))
            
        # Crear un usuario administrador para el nuevo tenant
        admin_user = User()
        admin_user.tenant_id = new_tenant.id
        admin_user.role_id = 1  # Asumimos que 1 es el rol de administrador
        admin_user.first_name = "Admin"
        admin_user.last_name = name
        admin_user.username = f"admin_{subdomain}"
        admin_user.email = admin_email
        admin_user.set_password(admin_password)
        
        db.session.add(admin_user)
        db.session.commit()
        
        flash(f"""Cliente '{name}' creado correctamente. 
              Usuario administrador creado con email: {admin_email}
              Por favor, utilice este email y la contraseña establecida para iniciar sesión.""", "success")
        
        return redirect(url_for('superadmin.tenants'))
    
    return render_template('superadmin/add_tenant.html', plans=subscription_plans)

def generate_random_password(length=10):
    """Generate a random password"""
    import random
    import string
    
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for i in range(length))
    return password

@superadmin_bp.route('/tenants/edit/<int:tenant_id>', methods=['GET', 'POST'])
@login_required
def edit_tenant(tenant_id):
    """Edit a tenant"""
    tenant = Tenant.query.get_or_404(tenant_id)
    subscription_plans = SubscriptionPlan.query.all()
    
    # Obtener el usuario administrador del tenant
    admin_user = User.query.filter_by(tenant_id=tenant_id, role_id=1).first()
    
    if request.method == 'POST':
        name = request.form.get('name')
        subdomain = request.form.get('subdomain')
        subscription_plan_id = int(request.form.get('subscription_plan_id') or 0)
        is_active = 'is_active' in request.form
        primary_color = request.form.get('primary_color')
        secondary_color = request.form.get('secondary_color')
        
        # Datos de la contraseña del administrador
        admin_password = request.form.get('admin_password')
        admin_password_confirm = request.form.get('admin_password_confirm')
        
        # Check for required fields
        if not name or not subdomain or subscription_plan_id <= 0:
            flash("Por favor, complete todos los campos requeridos.", "error")
            return redirect(url_for('superadmin.edit_tenant', tenant_id=tenant_id))
        
        # Check if subdomain is unique (except for this tenant)
        subdomain_tenant = Tenant.query.filter(Tenant.subdomain == subdomain, Tenant.id != tenant_id).first()
        if subdomain_tenant:
            flash(f"El subdominio '{subdomain}' ya está siendo utilizado por otro cliente.", "error")
            return redirect(url_for('superadmin.edit_tenant', tenant_id=tenant_id))
        
        # Validar la contraseña si se ha especificado
        if admin_password:
            if admin_password != admin_password_confirm:
                flash("Las contraseñas no coinciden. Por favor, inténtelo de nuevo.", "error")
                return redirect(url_for('superadmin.edit_tenant', tenant_id=tenant_id))
            
            # Actualizar la contraseña del administrador
            if admin_user:
                admin_user.set_password(admin_password)
                db.session.add(admin_user)
                flash("Contraseña del administrador actualizada correctamente.", "success")
        
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
    
    return render_template('superadmin/edit_tenant.html', tenant=tenant, plans=subscription_plans, admin_user=admin_user)

@superadmin_bp.route('/tenants/admins/<int:tenant_id>', methods=['GET', 'POST'])
@login_required
def tenant_admins(tenant_id):
    """Manage tenant administrators"""
    tenant = Tenant.query.get_or_404(tenant_id)
    admin_users = User.query.filter_by(tenant_id=tenant_id, role_id=1).all()
    
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validar datos
        if not first_name or not last_name or not email or not username or not password:
            flash("Todos los campos son obligatorios.", "error")
            return redirect(url_for('superadmin.tenant_admins', tenant_id=tenant_id))
        
        if password != confirm_password:
            flash("Las contraseñas no coinciden.", "error")
            return redirect(url_for('superadmin.tenant_admins', tenant_id=tenant_id))
        
        # Verificar que el username sea único
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash(f"El nombre de usuario '{username}' ya está en uso.", "error")
            return redirect(url_for('superadmin.tenant_admins', tenant_id=tenant_id))
        
        # Verificar que el email sea único
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash(f"El email '{email}' ya está en uso.", "error")
            return redirect(url_for('superadmin.tenant_admins', tenant_id=tenant_id))
        
        # Crear nuevo administrador
        new_admin = User()
        new_admin.tenant_id = tenant_id
        new_admin.role_id = 1  # Admin role
        new_admin.first_name = first_name
        new_admin.last_name = last_name
        new_admin.email = email
        new_admin.username = username
        new_admin.is_active = True
        new_admin.set_password(password)
        
        db.session.add(new_admin)
        db.session.commit()
        
        flash(f"Administrador '{first_name} {last_name}' añadido correctamente.", "success")
        return redirect(url_for('superadmin.tenant_admins', tenant_id=tenant_id))
    
    return render_template('superadmin/tenant_admins.html', tenant=tenant, admins=admin_users)

@superadmin_bp.route('/tenants/admins/<int:tenant_id>/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_tenant_admin(tenant_id, user_id):
    """Delete tenant administrator"""
    tenant = Tenant.query.get_or_404(tenant_id)
    admin_user = User.query.get_or_404(user_id)
    
    # Verificar que el usuario pertenece al tenant
    if admin_user.tenant_id != tenant_id:
        flash("El usuario no pertenece a este cliente.", "error")
        return redirect(url_for('superadmin.tenant_admins', tenant_id=tenant_id))
    
    # Verificar que no es el último administrador
    admin_count = User.query.filter_by(tenant_id=tenant_id, role_id=1).count()
    if admin_count <= 1:
        flash("No se puede eliminar el último administrador del cliente.", "error")
        return redirect(url_for('superadmin.tenant_admins', tenant_id=tenant_id))
    
    # Eliminar el administrador
    db.session.delete(admin_user)
    db.session.commit()
    
    flash(f"Administrador '{admin_user.first_name} {admin_user.last_name}' eliminado correctamente.", "success")
    return redirect(url_for('superadmin.tenant_admins', tenant_id=tenant_id))

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
    
@superadmin_bp.route('/tenants/toggle-superadmin/<int:tenant_id>', methods=['POST'])
@login_required
def toggle_tenant_superadmin(tenant_id):
    """Toggle tenant superadmin status"""
    tenant = Tenant.query.get_or_404(tenant_id)
    
    # Toggle superadmin status
    tenant.is_superadmin = not tenant.is_superadmin
    db.session.commit()
    
    status = "establecido como superadmin" if tenant.is_superadmin else "removido como superadmin"
    flash(f"Cliente '{tenant.name}' {status} correctamente.", "success")
    return redirect(url_for('superadmin.tenants'))

@superadmin_bp.route('/tenants/delete/<int:tenant_id>', methods=['POST'])
@login_required
def delete_tenant(tenant_id):
    """Delete tenant and all associated data"""
    tenant = Tenant.query.get_or_404(tenant_id)
    
    # No permitir eliminar el propio tenant del superadmin principal
    current_tenant_id = int(session.get('tenant_id', 0))
    if current_tenant_id == tenant_id:
        flash("No puedes eliminar tu propio tenant.", "error")
        return redirect(url_for('superadmin.tenants'))
    
    tenant_name = tenant.name
    
    try:
        # Eliminar todas las relaciones y datos asociados a este tenant
        # Nota: Esto podría eliminarse si se configura CASCADE en la base de datos
        User.query.filter_by(tenant_id=tenant_id).delete()
        
        # Eliminar las configuraciones de cliente
        client_settings = ClientSettings.query.filter_by(tenant_id=tenant_id).first()
        if client_settings:
            db.session.delete(client_settings)
            
        # Finalmente, eliminar el tenant
        db.session.delete(tenant)
        db.session.commit()
        
        flash(f"Cliente '{tenant_name}' y todos sus datos asociados han sido eliminados correctamente.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar cliente: {str(e)}", "error")
    
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