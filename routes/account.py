from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from app import db
from models import Account, User, Contact, Opportunity
from utils.decorators import tenant_required
import datetime

# Create blueprint but DON'T register it here - it will be registered in main.py
account = Blueprint('account', __name__)

@account.route('/accounts')
@login_required
@tenant_required
def list_accounts():
    tenant_id = session.get('tenant_id')
    
    # Handle sorting
    sort_by = request.args.get('sort', 'name')
    sort_order = request.args.get('order', 'asc')
    
    # Handle filtering
    industry_filter = request.args.get('industry')
    search_query = request.args.get('q')
    
    # Base query
    query = Account.query.filter_by(tenant_id=tenant_id)
    
    # Apply filters
    if industry_filter:
        query = query.filter_by(industry=industry_filter)
    
    if search_query:
        query = query.filter(
            (Account.name.ilike(f'%{search_query}%')) |
            (Account.website.ilike(f'%{search_query}%')) |
            (Account.industry.ilike(f'%{search_query}%'))
        )
    
    # Apply sorting
    if sort_order == 'asc':
        query = query.order_by(getattr(Account, sort_by).asc())
    else:
        query = query.order_by(getattr(Account, sort_by).desc())
    
    accounts = query.all()
    
    # Get users for owner selection
    users = User.query.filter_by(tenant_id=tenant_id, is_active=True).all()
    
    # Get distinct industry values for filtering
    industries = db.session.query(Account.industry.distinct()).filter(
        Account.tenant_id == tenant_id,
        Account.industry.isnot(None),
        Account.industry != ''
    ).all()
    industry_options = [industry[0] for industry in industries]
    
    return render_template('accounts.html', 
                          accounts=accounts, 
                          users=users, 
                          industries=industry_options,
                          current_industry=industry_filter,
                          search_query=search_query)

@account.route('/accounts/new', methods=['GET', 'POST'])
@login_required
@tenant_required
def new_account():
    tenant_id = session.get('tenant_id')
    
    if request.method == 'POST':
        # Create new account
        new_account = Account(
            tenant_id=tenant_id,
            owner_id=request.form.get('owner_id', current_user.id),
            name=request.form.get('name'),
            website=request.form.get('website'),
            industry=request.form.get('industry'),
            employees=request.form.get('employees') or None,
            annual_revenue=request.form.get('annual_revenue') or None,
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            address=request.form.get('address'),
            city=request.form.get('city'),
            state=request.form.get('state'),
            postal_code=request.form.get('postal_code'),
            country=request.form.get('country'),
            description=request.form.get('description')
        )
        
        db.session.add(new_account)
        db.session.commit()
        
        flash('Account created successfully.', 'success')
        return redirect(url_for('account.list_accounts'))
    
    # Get users for owner selection
    users = User.query.filter_by(tenant_id=tenant_id, is_active=True).all()
    
    # Default industry options
    default_industries = [
        'Agriculture', 'Banking', 'Construction', 'Education', 'Energy', 'Entertainment',
        'Finance', 'Food & Beverage', 'Government', 'Healthcare', 'Hospitality',
        'Insurance', 'Manufacturing', 'Media', 'Non-profit', 'Retail', 'Technology',
        'Telecommunications', 'Transportation', 'Utilities', 'Other'
    ]
    
    # Get existing industry values
    existing_industries = db.session.query(Account.industry.distinct()).filter(
        Account.tenant_id == tenant_id,
        Account.industry.isnot(None),
        Account.industry != ''
    ).all()
    industry_options = [industry[0] for industry in existing_industries]
    
    # Combine and deduplicate
    all_industries = list(set(default_industries + industry_options))
    all_industries.sort()
    
    return render_template('accounts_form.html', 
                          account=None, 
                          users=users, 
                          industries=all_industries,
                          action='new')

@account.route('/accounts/view/<int:account_id>')
@login_required
@tenant_required
def view_account(account_id):
    tenant_id = session.get('tenant_id')
    
    account = Account.query.filter_by(id=account_id, tenant_id=tenant_id).first()
    
    if not account:
        flash('Account not found.', 'danger')
        return redirect(url_for('account.list_accounts'))
    
    # Get related contacts
    contacts = Contact.query.filter_by(account_id=account_id, tenant_id=tenant_id).all()
    
    # Get related opportunities
    opportunities = Opportunity.query.filter_by(account_id=account_id, tenant_id=tenant_id).all()
    
    return render_template('account_view.html', 
                          account=account,
                          contacts=contacts,
                          opportunities=opportunities)

@account.route('/accounts/edit/<int:account_id>', methods=['GET', 'POST'])
@login_required
@tenant_required
def edit_account(account_id):
    tenant_id = session.get('tenant_id')
    
    account = Account.query.filter_by(id=account_id, tenant_id=tenant_id).first()
    
    if not account:
        flash('Account not found.', 'danger')
        return redirect(url_for('account.list_accounts'))
    
    if request.method == 'POST':
        # Update account
        account.owner_id = request.form.get('owner_id')
        account.name = request.form.get('name')
        account.website = request.form.get('website')
        account.industry = request.form.get('industry')
        account.employees = request.form.get('employees') or None
        account.annual_revenue = request.form.get('annual_revenue') or None
        account.phone = request.form.get('phone')
        account.email = request.form.get('email')
        account.address = request.form.get('address')
        account.city = request.form.get('city')
        account.state = request.form.get('state')
        account.postal_code = request.form.get('postal_code')
        account.country = request.form.get('country')
        account.description = request.form.get('description')
        account.updated_at = datetime.datetime.utcnow()
        
        db.session.commit()
        
        flash('Account updated successfully.', 'success')
        return redirect(url_for('account.list_accounts'))
    
    # Get users for owner selection
    users = User.query.filter_by(tenant_id=tenant_id, is_active=True).all()
    
    # Default industry options
    default_industries = [
        'Agriculture', 'Banking', 'Construction', 'Education', 'Energy', 'Entertainment',
        'Finance', 'Food & Beverage', 'Government', 'Healthcare', 'Hospitality',
        'Insurance', 'Manufacturing', 'Media', 'Non-profit', 'Retail', 'Technology',
        'Telecommunications', 'Transportation', 'Utilities', 'Other'
    ]
    
    # Get existing industry values
    existing_industries = db.session.query(Account.industry.distinct()).filter(
        Account.tenant_id == tenant_id,
        Account.industry.isnot(None),
        Account.industry != ''
    ).all()
    industry_options = [industry[0] for industry in existing_industries]
    
    # Combine and deduplicate
    all_industries = list(set(default_industries + industry_options))
    all_industries.sort()
    
    return render_template('accounts_form.html', 
                          account=account, 
                          users=users, 
                          industries=all_industries,
                          action='edit')

@account.route('/accounts/delete/<int:account_id>', methods=['POST'])
@login_required
@tenant_required
def delete_account(account_id):
    tenant_id = session.get('tenant_id')
    
    account = Account.query.filter_by(id=account_id, tenant_id=tenant_id).first()
    
    if not account:
        flash('Account not found.', 'danger')
        return redirect(url_for('account.list_accounts'))
    
    # Check for related records
    contacts_count = Contact.query.filter_by(account_id=account_id).count()
    opportunities_count = Opportunity.query.filter_by(account_id=account_id).count()
    
    if contacts_count > 0 or opportunities_count > 0:
        flash(f'Cannot delete account. It has {contacts_count} contacts and {opportunities_count} opportunities associated with it.', 'danger')
        return redirect(url_for('account.list_accounts'))
    
    db.session.delete(account)
    db.session.commit()
    
    flash('Account deleted successfully.', 'success')
    return redirect(url_for('account.list_accounts'))
