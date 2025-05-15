from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_required, current_user
from app import db
from models import Prospect, User
from utils.decorators import tenant_required
import datetime

# Create blueprint but DON'T register it here - it will be registered in main.py
prospect = Blueprint('prospect', __name__)

@prospect.route('/prospects')
@login_required
@tenant_required
def list_prospects():
    tenant_id = session.get('tenant_id')
    
    # Handle sorting
    sort_by = request.args.get('sort', 'created_at')
    sort_order = request.args.get('order', 'desc')
    
    # Handle filtering
    status_filter = request.args.get('status')
    search_query = request.args.get('q')
    
    # Base query
    query = Prospect.query.filter_by(tenant_id=tenant_id)
    
    # Apply filters
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    if search_query:
        query = query.filter(
            (Prospect.first_name.ilike(f'%{search_query}%')) |
            (Prospect.last_name.ilike(f'%{search_query}%')) |
            (Prospect.email.ilike(f'%{search_query}%')) |
            (Prospect.company.ilike(f'%{search_query}%'))
        )
    
    # Apply sorting
    if sort_order == 'asc':
        query = query.order_by(getattr(Prospect, sort_by).asc())
    else:
        query = query.order_by(getattr(Prospect, sort_by).desc())
    
    prospects = query.all()
    
    # Get distinct status values for filtering
    statuses = db.session.query(Prospect.status.distinct()).filter_by(tenant_id=tenant_id).all()
    status_options = [status[0] for status in statuses]
    
    return render_template('prospects.html', 
                          prospects=prospects, 
                          statuses=status_options,
                          current_status=status_filter,
                          search_query=search_query)

@prospect.route('/prospects/new', methods=['GET', 'POST'])
@login_required
@tenant_required
def new_prospect():
    tenant_id = session.get('tenant_id')
    
    if request.method == 'POST':
        # Create new prospect
        new_prospect = Prospect(
            tenant_id=tenant_id,
            owner_id=current_user.id,
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name'),
            company=request.form.get('company'),
            job_title=request.form.get('job_title'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            source=request.form.get('source'),
            status=request.form.get('status', 'New'),
            notes=request.form.get('notes')
        )
        
        db.session.add(new_prospect)
        db.session.commit()
        
        flash('Prospect created successfully.', 'success')
        return redirect(url_for('prospect.list_prospects'))
    
    # Default prospect status values if none exist yet
    default_statuses = ['New', 'Contacted', 'Qualified', 'Disqualified']
    
    # Get existing status values
    existing_statuses = db.session.query(Prospect.status.distinct()).filter_by(tenant_id=tenant_id).all()
    status_options = [status[0] for status in existing_statuses]
    
    # Use default statuses if none exist
    if not status_options:
        status_options = default_statuses
    
    return render_template('prospects_form.html', 
                          prospect=None, 
                          statuses=status_options,
                          action='new')

@prospect.route('/prospects/edit/<int:prospect_id>', methods=['GET', 'POST'])
@login_required
@tenant_required
def edit_prospect(prospect_id):
    tenant_id = session.get('tenant_id')
    
    prospect = Prospect.query.filter_by(id=prospect_id, tenant_id=tenant_id).first()
    
    if not prospect:
        flash('Prospect not found.', 'danger')
        return redirect(url_for('prospect.list_prospects'))
    
    if request.method == 'POST':
        # Update prospect
        prospect.first_name = request.form.get('first_name')
        prospect.last_name = request.form.get('last_name')
        prospect.company = request.form.get('company')
        prospect.job_title = request.form.get('job_title')
        prospect.email = request.form.get('email')
        prospect.phone = request.form.get('phone')
        prospect.source = request.form.get('source')
        prospect.status = request.form.get('status')
        prospect.notes = request.form.get('notes')
        prospect.updated_at = datetime.datetime.utcnow()
        
        # Check if interaction should be updated
        update_interaction = request.form.get('update_interaction')
        if update_interaction:
            interaction_notes = request.form.get('interaction_notes', '')
            prospect.last_interaction_date = datetime.datetime.utcnow()
            
            # Optionally log this interaction in Activity model if needed
            # activity = Activity(
            #     tenant_id=tenant_id,
            #     user_id=current_user.id,
            #     activity_type='Interaction',
            #     subject=f"Interaction with {prospect.full_name}",
            #     description=interaction_notes,
            #     related_to_type='prospect',
            #     related_to_id=prospect.id,
            #     completed=True,
            #     completed_date=datetime.datetime.utcnow()
            # )
            # db.session.add(activity)
            
            flash('Interaction registered successfully.', 'info')
        
        db.session.commit()
        
        flash('Prospect updated successfully.', 'success')
        return redirect(url_for('prospect.list_prospects'))
    
    # Default prospect status values if none exist yet
    default_statuses = ['New', 'Contacted', 'Qualified', 'Disqualified']
    
    # Get existing status values
    existing_statuses = db.session.query(Prospect.status.distinct()).filter_by(tenant_id=tenant_id).all()
    status_options = [status[0] for status in existing_statuses]
    
    # Use default statuses if none exist
    if not status_options:
        status_options = default_statuses
    
    return render_template('prospects_form.html', 
                          prospect=prospect, 
                          statuses=status_options,
                          action='edit')

@prospect.route('/prospects/delete/<int:prospect_id>', methods=['POST'])
@login_required
@tenant_required
def delete_prospect(prospect_id):
    tenant_id = session.get('tenant_id')
    
    prospect = Prospect.query.filter_by(id=prospect_id, tenant_id=tenant_id).first()
    
    if not prospect:
        flash('Prospect not found.', 'danger')
        return redirect(url_for('prospect.list_prospects'))
    
    db.session.delete(prospect)
    db.session.commit()
    
    flash('Prospect deleted successfully.', 'success')
    return redirect(url_for('prospect.list_prospects'))

@prospect.route('/api/prospects/status_counts')
@login_required
@tenant_required
def prospect_status_counts():
    tenant_id = session.get('tenant_id')
    
    # Get counts by status
    status_counts = db.session.query(
        Prospect.status, 
        db.func.count(Prospect.id)
    ).filter_by(
        tenant_id=tenant_id
    ).group_by(
        Prospect.status
    ).all()
    
    results = {status: count for status, count in status_counts}
    
    return jsonify(results)
