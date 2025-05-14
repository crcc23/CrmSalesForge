from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_required, current_user
from app import db
from models import Opportunity, User, Account, Contact
from utils.decorators import tenant_required
import datetime

# Create blueprint but DON'T register it here - it will be registered in main.py
opportunity = Blueprint('opportunity', __name__)

@opportunity.route('/opportunities')
@login_required
@tenant_required
def list_opportunities():
    tenant_id = session.get('tenant_id')
    
    # Handle sorting
    sort_by = request.args.get('sort', 'close_date')
    sort_order = request.args.get('order', 'asc')
    
    # Handle filtering
    stage_filter = request.args.get('stage')
    search_query = request.args.get('q')
    
    # Base query
    query = Opportunity.query.filter_by(tenant_id=tenant_id)
    
    # Apply filters
    if stage_filter:
        query = query.filter_by(stage=stage_filter)
    
    if search_query:
        query = query.filter(
            (Opportunity.name.ilike(f'%{search_query}%'))
        )
    
    # Apply sorting
    if sort_order == 'asc':
        query = query.order_by(getattr(Opportunity, sort_by).asc())
    else:
        query = query.order_by(getattr(Opportunity, sort_by).desc())
    
    opportunities = query.all()
    
    # Get users for owner selection
    users = User.query.filter_by(tenant_id=tenant_id, is_active=True).all()
    
    # Get distinct stage values for filtering
    stages = db.session.query(Opportunity.stage.distinct()).filter_by(tenant_id=tenant_id).all()
    stage_options = [stage[0] for stage in stages]
    
    return render_template('opportunities.html', 
                          opportunities=opportunities, 
                          users=users, 
                          stages=stage_options,
                          current_stage=stage_filter,
                          search_query=search_query)

@opportunity.route('/opportunities/new', methods=['GET', 'POST'])
@login_required
@tenant_required
def new_opportunity():
    tenant_id = session.get('tenant_id')
    
    if request.method == 'POST':
        # Parse date
        close_date_str = request.form.get('close_date')
        close_date = None
        if close_date_str:
            try:
                close_date = datetime.datetime.strptime(close_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format for close date.', 'danger')
                return redirect(url_for('opportunity.new_opportunity'))
        
        # Create new opportunity
        new_opportunity = Opportunity(
            tenant_id=tenant_id,
            owner_id=request.form.get('owner_id', current_user.id),
            account_id=request.form.get('account_id') or None,
            contact_id=request.form.get('contact_id') or None,
            name=request.form.get('name'),
            amount=request.form.get('amount') or None,
            close_date=close_date,
            stage=request.form.get('stage', 'Qualification'),
            probability=request.form.get('probability') or None,
            description=request.form.get('description')
        )
        
        db.session.add(new_opportunity)
        db.session.commit()
        
        flash('Opportunity created successfully.', 'success')
        return redirect(url_for('opportunity.list_opportunities'))
    
    # Get users for owner selection
    users = User.query.filter_by(tenant_id=tenant_id, is_active=True).all()
    
    # Get accounts and contacts for selection
    accounts = Account.query.filter_by(tenant_id=tenant_id).all()
    contacts = Contact.query.filter_by(tenant_id=tenant_id).all()
    
    # Default opportunity stage values if none exist yet
    default_stages = ['Qualification', 'Needs Analysis', 'Proposal', 'Negotiation', 'Closed Won', 'Closed Lost']
    
    # Get existing stage values
    existing_stages = db.session.query(Opportunity.stage.distinct()).filter_by(tenant_id=tenant_id).all()
    stage_options = [stage[0] for stage in existing_stages]
    
    # Use default stages if none exist
    if not stage_options:
        stage_options = default_stages
    
    return render_template('opportunities_form.html', 
                          opportunity=None, 
                          users=users, 
                          accounts=accounts,
                          contacts=contacts,
                          stages=stage_options,
                          action='new')

@opportunity.route('/opportunities/edit/<int:opportunity_id>', methods=['GET', 'POST'])
@login_required
@tenant_required
def edit_opportunity(opportunity_id):
    tenant_id = session.get('tenant_id')
    
    opportunity = Opportunity.query.filter_by(id=opportunity_id, tenant_id=tenant_id).first()
    
    if not opportunity:
        flash('Opportunity not found.', 'danger')
        return redirect(url_for('opportunity.list_opportunities'))
    
    if request.method == 'POST':
        # Parse date
        close_date_str = request.form.get('close_date')
        close_date = None
        if close_date_str:
            try:
                close_date = datetime.datetime.strptime(close_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format for close date.', 'danger')
                return redirect(url_for('opportunity.edit_opportunity', opportunity_id=opportunity_id))
        
        # Update opportunity
        opportunity.owner_id = request.form.get('owner_id')
        opportunity.account_id = request.form.get('account_id') or None
        opportunity.contact_id = request.form.get('contact_id') or None
        opportunity.name = request.form.get('name')
        opportunity.amount = request.form.get('amount') or None
        opportunity.close_date = close_date
        opportunity.stage = request.form.get('stage')
        opportunity.probability = request.form.get('probability') or None
        opportunity.description = request.form.get('description')
        opportunity.updated_at = datetime.datetime.utcnow()
        
        db.session.commit()
        
        flash('Opportunity updated successfully.', 'success')
        return redirect(url_for('opportunity.list_opportunities'))
    
    # Get users for owner selection
    users = User.query.filter_by(tenant_id=tenant_id, is_active=True).all()
    
    # Get accounts and contacts for selection
    accounts = Account.query.filter_by(tenant_id=tenant_id).all()
    contacts = Contact.query.filter_by(tenant_id=tenant_id).all()
    
    # Default opportunity stage values if none exist yet
    default_stages = ['Qualification', 'Needs Analysis', 'Proposal', 'Negotiation', 'Closed Won', 'Closed Lost']
    
    # Get existing stage values
    existing_stages = db.session.query(Opportunity.stage.distinct()).filter_by(tenant_id=tenant_id).all()
    stage_options = [stage[0] for stage in existing_stages]
    
    # Use default stages if none exist
    if not stage_options:
        stage_options = default_stages
    
    return render_template('opportunities_form.html', 
                          opportunity=opportunity, 
                          users=users, 
                          accounts=accounts,
                          contacts=contacts,
                          stages=stage_options,
                          action='edit')

@opportunity.route('/opportunities/delete/<int:opportunity_id>', methods=['POST'])
@login_required
@tenant_required
def delete_opportunity(opportunity_id):
    tenant_id = session.get('tenant_id')
    
    opportunity = Opportunity.query.filter_by(id=opportunity_id, tenant_id=tenant_id).first()
    
    if not opportunity:
        flash('Opportunity not found.', 'danger')
        return redirect(url_for('opportunity.list_opportunities'))
    
    db.session.delete(opportunity)
    db.session.commit()
    
    flash('Opportunity deleted successfully.', 'success')
    return redirect(url_for('opportunity.list_opportunities'))

@opportunity.route('/api/opportunities/stage_counts')
@login_required
@tenant_required
def opportunity_stage_counts():
    tenant_id = session.get('tenant_id')
    
    # Get counts and sum by stage
    stage_data = db.session.query(
        Opportunity.stage, 
        db.func.count(Opportunity.id).label('count'),
        db.func.sum(Opportunity.amount).label('amount')
    ).filter_by(
        tenant_id=tenant_id
    ).group_by(
        Opportunity.stage
    ).all()
    
    results = {
        'stages': [data[0] for data in stage_data],
        'counts': [data[1] for data in stage_data],
        'amounts': [float(data[2] or 0) for data in stage_data]
    }
    
    return jsonify(results)
