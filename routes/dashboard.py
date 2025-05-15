from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from app import db
from models import Prospect, Opportunity, Contact, Account, User, Tenant
from sqlalchemy import func
import datetime
from utils.seed_data import create_demo_prospects

# Create blueprint but DON'T register it here - it will be registered in main.py
dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/')
@dashboard.route('/dashboard')
@login_required
def index():
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        flash('Tenant not found. Please log in again.', 'danger')
        return redirect(url_for('auth.logout'))
    
    tenant = Tenant.query.get(tenant_id)
    if not tenant:
        flash('Tenant not found. Please log in again.', 'danger')
        return redirect(url_for('auth.logout'))
    
    # Get counts
    prospect_count = Prospect.query.filter_by(tenant_id=tenant_id).count()
    opportunity_count = Opportunity.query.filter_by(tenant_id=tenant_id).count()
    contact_count = Contact.query.filter_by(tenant_id=tenant_id).count()
    account_count = Account.query.filter_by(tenant_id=tenant_id).count()
    user_count = User.query.filter_by(tenant_id=tenant_id).count()
    
    # Get recent prospects
    recent_prospects = Prospect.query.filter_by(tenant_id=tenant_id) \
        .order_by(Prospect.created_at.desc()).limit(5).all()
    
    # Get opportunities by stage for pipeline visualization
    pipeline_data = db.session.query(
        Opportunity.stage,
        func.count(Opportunity.id).label('count'),
        func.sum(Opportunity.amount).label('amount')
    ).filter(
        Opportunity.tenant_id == tenant_id
    ).group_by(
        Opportunity.stage
    ).all()
    
    pipeline_stages = [p[0] for p in pipeline_data]
    pipeline_counts = [p[1] for p in pipeline_data]
    pipeline_amounts = [float(p[2] or 0) for p in pipeline_data]
    
    # Get opportunities closing this month
    today = datetime.datetime.today()
    month_start = datetime.date(today.year, today.month, 1)
    if today.month == 12:
        next_month = datetime.date(today.year + 1, 1, 1)
    else:
        next_month = datetime.date(today.year, today.month + 1, 1)
    
    closing_opportunities = Opportunity.query.filter(
        Opportunity.tenant_id == tenant_id,
        Opportunity.close_date >= month_start,
        Opportunity.close_date < next_month
    ).order_by(Opportunity.close_date).all()
    
    # Calculate total opportunity amount
    total_opportunity_amount = db.session.query(func.sum(Opportunity.amount)) \
        .filter(Opportunity.tenant_id == tenant_id).scalar() or 0
    
    return render_template('dashboard.html',
                          tenant=tenant,
                          prospect_count=prospect_count,
                          opportunity_count=opportunity_count,
                          contact_count=contact_count,
                          account_count=account_count,
                          user_count=user_count,
                          recent_prospects=recent_prospects,
                          pipeline_stages=pipeline_stages,
                          pipeline_counts=pipeline_counts,
                          pipeline_amounts=pipeline_amounts,
                          closing_opportunities=closing_opportunities,
                          total_opportunity_amount=total_opportunity_amount)

@dashboard.route('/create_demo_data', methods=['POST'])
@login_required
def create_demo_data():
    tenant_id = session.get('tenant_id')
    
    if not tenant_id:
        flash('Tenant no encontrado. Por favor, inicia sesión de nuevo.', 'danger')
        return redirect(url_for('auth.logout'))
    
    result = create_demo_prospects(tenant_id, current_user.id)
    
    if result["success"]:
        flash(f'Se han creado {result["count"]} prospectos de demostración con éxito.', 'success')
    else:
        flash(result["message"], 'warning')
    
    return redirect(url_for('dashboard.index'))
