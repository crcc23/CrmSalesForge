from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from app import db
from models import Tenant, SubscriptionPlan, User, Role
from utils.decorators import admin_required

# Create blueprint but DON'T register it here - it will be registered in main.py
tenant = Blueprint('tenant', __name__)

@tenant.route('/tenant/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    tenant_id = session.get('tenant_id')
    tenant = Tenant.query.get(tenant_id)
    
    if not tenant:
        flash('Tenant not found.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        tenant.name = request.form.get('name')
        tenant.primary_color = request.form.get('primary_color')
        tenant.secondary_color = request.form.get('secondary_color')
        
        # Logo URL handling - assuming it's a link
        logo_url = request.form.get('logo_url')
        if logo_url:
            tenant.logo_url = logo_url
        
        db.session.commit()
        flash('Tenant settings updated successfully.', 'success')
        return redirect(url_for('tenant.settings'))
    
    subscription_plans = SubscriptionPlan.query.all()
    current_plan = SubscriptionPlan.query.get(tenant.subscription_plan_id)
    
    return render_template('tenant_settings.html', 
                          tenant=tenant, 
                          subscription_plans=subscription_plans,
                          current_plan=current_plan)

@tenant.route('/tenant/upgrade', methods=['POST'])
@login_required
@admin_required
def upgrade_plan():
    tenant_id = session.get('tenant_id')
    tenant = Tenant.query.get(tenant_id)
    
    if not tenant:
        flash('Tenant not found.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    plan_id = request.form.get('plan_id')
    
    if not plan_id:
        flash('No plan selected.', 'danger')
        return redirect(url_for('tenant.settings'))
    
    plan = SubscriptionPlan.query.get(plan_id)
    
    if not plan:
        flash('Selected plan not found.', 'danger')
        return redirect(url_for('tenant.settings'))
    
    # In a real application, this would involve payment processing
    tenant.subscription_plan_id = plan.id
    db.session.commit()
    
    flash(f'Successfully upgraded to {plan.name} plan.', 'success')
    return redirect(url_for('tenant.settings'))

@tenant.route('/tenant/users')
@login_required
@admin_required
def users():
    tenant_id = session.get('tenant_id')
    users = User.query.filter_by(tenant_id=tenant_id).all()
    roles = Role.query.all()
    
    return render_template('tenant_users.html', users=users, roles=roles)

@tenant.route('/tenant/users/add', methods=['POST'])
@login_required
@admin_required
def add_user():
    tenant_id = session.get('tenant_id')
    tenant = Tenant.query.get(tenant_id)
    
    if not tenant:
        flash('Tenant not found.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # Check if maximum users reached
    user_count = User.query.filter_by(tenant_id=tenant_id).count()
    subscription_plan = SubscriptionPlan.query.get(tenant.subscription_plan_id)
    
    if user_count >= subscription_plan.max_users:
        flash(f'Maximum users ({subscription_plan.max_users}) reached for your plan. Please upgrade to add more users.', 'danger')
        return redirect(url_for('tenant.users'))
    
    # Get form data
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    username = request.form.get('username')
    password = request.form.get('password')
    role_id = request.form.get('role_id')
    
    # Validate form data
    if not first_name or not last_name or not email or not username or not password or not role_id:
        flash('All fields are required', 'danger')
        return redirect(url_for('tenant.users'))
    
    # Check if username already exists
    if User.query.filter_by(username=username).first():
        flash('Username already exists', 'danger')
        return redirect(url_for('tenant.users'))
    
    # Check if email already exists
    if User.query.filter_by(email=email).first():
        flash('Email already exists', 'danger')
        return redirect(url_for('tenant.users'))
    
    # Create user
    new_user = User(
        tenant_id=tenant_id,
        role_id=role_id,
        first_name=first_name,
        last_name=last_name,
        username=username,
        email=email
    )
    new_user.set_password(password)
    
    db.session.add(new_user)
    db.session.commit()
    
    flash('User added successfully.', 'success')
    return redirect(url_for('tenant.users'))

@tenant.route('/tenant/users/edit/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def edit_user(user_id):
    tenant_id = session.get('tenant_id')
    
    user = User.query.filter_by(id=user_id, tenant_id=tenant_id).first()
    
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('tenant.users'))
    
    # Get form data
    user.first_name = request.form.get('first_name')
    user.last_name = request.form.get('last_name')
    user.email = request.form.get('email')
    user.role_id = request.form.get('role_id')
    user.is_active = request.form.get('is_active') == 'on'
    
    password = request.form.get('password')
    if password:
        user.set_password(password)
    
    db.session.commit()
    
    flash('User updated successfully.', 'success')
    return redirect(url_for('tenant.users'))

@tenant.route('/tenant/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    tenant_id = session.get('tenant_id')
    
    user = User.query.filter_by(id=user_id, tenant_id=tenant_id).first()
    
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('tenant.users'))
    
    # Prevent deleting the last admin
    if user.role.name == 'Admin':
        admin_count = User.query.join(Role).filter(
            User.tenant_id == tenant_id,
            Role.name == 'Admin',
            User.is_active == True
        ).count()
        
        if admin_count <= 1:
            flash('Cannot delete the last admin user.', 'danger')
            return redirect(url_for('tenant.users'))
    
    # In a real application, you might want to deactivate users instead of deleting them
    user.is_active = False
    db.session.commit()
    
    flash('User deleted successfully.', 'success')
    return redirect(url_for('tenant.users'))
