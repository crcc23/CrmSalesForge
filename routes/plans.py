from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_required, current_user
from app import db
from models import Tenant, SubscriptionPlan, User, ClientSettings
import datetime

# Crear blueprint para planes de suscripción
plans_bp = Blueprint('plans', __name__)

@plans_bp.route('/')
@login_required
def index():
    """Página de planes de suscripción"""
    # Obtener todos los planes disponibles
    plans = SubscriptionPlan.query.order_by(SubscriptionPlan.price).all()
    
    # Obtener el tenant actual
    tenant_id = session.get('tenant_id')
    tenant = Tenant.query.get(tenant_id)
    
    # Obtener el plan actual del cliente
    current_plan = None
    if tenant and tenant.subscription_plan_id:
        current_plan = SubscriptionPlan.query.get(tenant.subscription_plan_id)
    
    return render_template('plans/index.html', 
                          plans=plans, 
                          current_plan=current_plan,
                          tenant=tenant)

@plans_bp.route('/select/<int:plan_id>', methods=['POST'])
@login_required
def select_plan(plan_id):
    """Seleccionar un plan de suscripción"""
    # Verificar que el plan existe
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    
    # Obtener el tenant actual
    tenant_id = session.get('tenant_id')
    tenant = Tenant.query.get(tenant_id)
    
    if not tenant:
        flash("Error: No se pudo encontrar la información de su cuenta.", "error")
        return redirect(url_for('plans.index'))
    
    # Actualizar el plan del tenant
    tenant.subscription_plan_id = plan_id
    
    # Actualizar la configuración del cliente
    client_settings = ClientSettings.query.filter_by(tenant_id=tenant_id).first()
    if client_settings:
        client_settings.billing_plan = plan.name
        # Establecer fechas de suscripción
        client_settings.subscription_start_date = datetime.datetime.now()
        client_settings.subscription_end_date = datetime.datetime.now() + datetime.timedelta(days=30)
        client_settings.subscription_status = 'active'
    
    db.session.commit()
    
    flash(f"¡Felicidades! Has seleccionado el plan {plan.name}.", "success")
    return redirect(url_for('dashboard.index'))