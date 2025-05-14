from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from app import db
from models import Contact, User, Account
from utils.decorators import tenant_required
import datetime

# Create blueprint but DON'T register it here - it will be registered in main.py
contact = Blueprint('contact', __name__)

@contact.route('/contacts')
@login_required
@tenant_required
def list_contacts():
    tenant_id = session.get('tenant_id')
    
    # Handle sorting
    sort_by = request.args.get('sort', 'last_name')
    sort_order = request.args.get('order', 'asc')
    
    # Handle filtering
    account_filter = request.args.get('account_id')
    search_query = request.args.get('q')
    
    # Base query
    query = Contact.query.filter_by(tenant_id=tenant_id)
    
    # Apply filters
    if account_filter:
        query = query.filter_by(account_id=account_filter)
    
    if search_query:
        query = query.filter(
            (Contact.first_name.ilike(f'%{search_query}%')) |
            (Contact.last_name.ilike(f'%{search_query}%')) |
            (Contact.email.ilike(f'%{search_query}%')) |
            (Contact.job_title.ilike(f'%{search_query}%'))
        )
    
    # Apply sorting
    if sort_order == 'asc':
        query = query.order_by(getattr(Contact, sort_by).asc())
    else:
        query = query.order_by(getattr(Contact, sort_by).desc())
    
    contacts = query.all()
    
    # Get users for owner selection
    users = User.query.filter_by(tenant_id=tenant_id, is_active=True).all()
    
    # Get accounts for filtering
    accounts = Account.query.filter_by(tenant_id=tenant_id).all()
    
    return render_template('contacts.html', 
                          contacts=contacts, 
                          users=users, 
                          accounts=accounts,
                          current_account=account_filter,
                          search_query=search_query)

@contact.route('/contacts/new', methods=['GET', 'POST'])
@login_required
@tenant_required
def new_contact():
    tenant_id = session.get('tenant_id')
    
    if request.method == 'POST':
        # Create new contact
        new_contact = Contact(
            tenant_id=tenant_id,
            owner_id=request.form.get('owner_id', current_user.id),
            account_id=request.form.get('account_id') or None,
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name'),
            job_title=request.form.get('job_title'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            mobile=request.form.get('mobile'),
            address=request.form.get('address'),
            city=request.form.get('city'),
            state=request.form.get('state'),
            postal_code=request.form.get('postal_code'),
            country=request.form.get('country'),
            notes=request.form.get('notes')
        )
        
        db.session.add(new_contact)
        db.session.commit()
        
        flash('Contact created successfully.', 'success')
        return redirect(url_for('contact.list_contacts'))
    
    # Get users for owner selection
    users = User.query.filter_by(tenant_id=tenant_id, is_active=True).all()
    
    # Get accounts for selection
    accounts = Account.query.filter_by(tenant_id=tenant_id).all()
    
    return render_template('contacts_form.html', 
                          contact=None, 
                          users=users, 
                          accounts=accounts,
                          action='new')

@contact.route('/contacts/edit/<int:contact_id>', methods=['GET', 'POST'])
@login_required
@tenant_required
def edit_contact(contact_id):
    tenant_id = session.get('tenant_id')
    
    contact = Contact.query.filter_by(id=contact_id, tenant_id=tenant_id).first()
    
    if not contact:
        flash('Contact not found.', 'danger')
        return redirect(url_for('contact.list_contacts'))
    
    if request.method == 'POST':
        # Update contact
        contact.owner_id = request.form.get('owner_id')
        contact.account_id = request.form.get('account_id') or None
        contact.first_name = request.form.get('first_name')
        contact.last_name = request.form.get('last_name')
        contact.job_title = request.form.get('job_title')
        contact.email = request.form.get('email')
        contact.phone = request.form.get('phone')
        contact.mobile = request.form.get('mobile')
        contact.address = request.form.get('address')
        contact.city = request.form.get('city')
        contact.state = request.form.get('state')
        contact.postal_code = request.form.get('postal_code')
        contact.country = request.form.get('country')
        contact.notes = request.form.get('notes')
        contact.updated_at = datetime.datetime.utcnow()
        
        db.session.commit()
        
        flash('Contact updated successfully.', 'success')
        return redirect(url_for('contact.list_contacts'))
    
    # Get users for owner selection
    users = User.query.filter_by(tenant_id=tenant_id, is_active=True).all()
    
    # Get accounts for selection
    accounts = Account.query.filter_by(tenant_id=tenant_id).all()
    
    return render_template('contacts_form.html', 
                          contact=contact, 
                          users=users, 
                          accounts=accounts,
                          action='edit')

@contact.route('/contacts/delete/<int:contact_id>', methods=['POST'])
@login_required
@tenant_required
def delete_contact(contact_id):
    tenant_id = session.get('tenant_id')
    
    contact = Contact.query.filter_by(id=contact_id, tenant_id=tenant_id).first()
    
    if not contact:
        flash('Contact not found.', 'danger')
        return redirect(url_for('contact.list_contacts'))
    
    db.session.delete(contact)
    db.session.commit()
    
    flash('Contact deleted successfully.', 'success')
    return redirect(url_for('contact.list_contacts'))
