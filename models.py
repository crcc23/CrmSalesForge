from app import db
from flask_login import UserMixin
import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Subscription Plans
class SubscriptionPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)
    features = db.Column(db.Text, nullable=True)
    max_users = db.Column(db.Integer, nullable=False, default=5)
    max_prospects = db.Column(db.Integer, nullable=False, default=100)
    includes_email_campaigns = db.Column(db.Boolean, default=False)
    includes_whatsapp = db.Column(db.Boolean, default=False) 
    includes_ai_content = db.Column(db.Boolean, default=False)
    includes_web_scraping = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    tenants = db.relationship('Tenant', backref='subscription_plan', lazy='dynamic')

# Tenant Organization
class Tenant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subdomain = db.Column(db.String(50), unique=True, nullable=False)
    logo_url = db.Column(db.String(255), nullable=True)
    primary_color = db.Column(db.String(20), nullable=True, default="#3498db")
    secondary_color = db.Column(db.String(20), nullable=True, default="#2ecc71")
    subscription_plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plan.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)  # This is fine as Tenant doesn't extend UserMixin
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    users = db.relationship('User', backref='tenant', lazy='dynamic')
    prospects = db.relationship('Prospect', backref='tenant', lazy='dynamic')
    opportunities = db.relationship('Opportunity', backref='tenant', lazy='dynamic')
    contacts = db.relationship('Contact', backref='tenant', lazy='dynamic')
    accounts = db.relationship('Account', backref='tenant', lazy='dynamic')

# User Role within Tenant
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    users = db.relationship('User', backref='role', lazy='dynamic')

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    _is_active = db.Column(db.Boolean, default=True)  # Internal field
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_active(self):
        # Override UserMixin's is_active property
        return self._is_active
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

# Account/Company Model
class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    website = db.Column(db.String(255), nullable=True)
    industry = db.Column(db.String(100), nullable=True)
    employees = db.Column(db.Integer, nullable=True)
    annual_revenue = db.Column(db.Float, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    postal_code = db.Column(db.String(20), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    contacts = db.relationship('Contact', backref='account', lazy='dynamic')
    opportunities = db.relationship('Opportunity', backref='account', lazy='dynamic')
    owner = db.relationship('User', backref='owned_accounts')

# Contact Model
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    job_title = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    mobile = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    postal_code = db.Column(db.String(20), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    opportunities = db.relationship('Opportunity', backref='contact', lazy='dynamic')
    owner = db.relationship('User', backref='owned_contacts')
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

# Prospect Model (Lead)
class Prospect(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    company = db.Column(db.String(100), nullable=True)
    job_title = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    source = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(50), nullable=False, default='New')
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    owner = db.relationship('User', backref='owned_prospects')
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

# Opportunity Model
class Opportunity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=True)
    close_date = db.Column(db.Date, nullable=True)
    stage = db.Column(db.String(50), nullable=False, default='Qualification')
    probability = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    owner = db.relationship('User', backref='owned_opportunities')

# Activity Model (for tracking interactions)
class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    completed_date = db.Column(db.DateTime, nullable=True)
    related_to_type = db.Column(db.String(50), nullable=True)  # 'contact', 'account', 'opportunity', 'prospect'
    related_to_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    user = db.relationship('User', backref='activities')

# Email Campaign
class EmailCampaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='Draft')
    scheduled_date = db.Column(db.DateTime, nullable=True)
    sent_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    owner = db.relationship('User', backref='email_campaigns')
    recipients = db.relationship('EmailCampaignRecipient', backref='campaign', lazy='dynamic')

# Email Campaign Recipients
class EmailCampaignRecipient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('email_campaign.id'), nullable=False)
    recipient_type = db.Column(db.String(50), nullable=False)  # 'contact', 'prospect'
    recipient_id = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    sent = db.Column(db.Boolean, default=False)
    opened = db.Column(db.Boolean, default=False)
    clicked = db.Column(db.Boolean, default=False)
    bounced = db.Column(db.Boolean, default=False)
    unsubscribed = db.Column(db.Boolean, default=False)
    sent_at = db.Column(db.DateTime, nullable=True)
    opened_at = db.Column(db.DateTime, nullable=True)
    clicked_at = db.Column(db.DateTime, nullable=True)

# WhatsApp Campaign
class WhatsAppCampaign(db.Model):
    __tablename__ = 'whatsapp_campaign'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='Draft')
    scheduled_date = db.Column(db.DateTime, nullable=True)
    sent_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    owner = db.relationship('User', backref='whatsapp_campaigns')
    recipients = db.relationship('WhatsAppCampaignRecipient', backref='campaign', lazy='dynamic')

# WhatsApp Campaign Recipients
class WhatsAppCampaignRecipient(db.Model):
    __tablename__ = 'whatsapp_campaign_recipient'
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('whatsapp_campaign.id'), nullable=False)
    recipient_type = db.Column(db.String(50), nullable=False)  # 'contact', 'prospect'
    recipient_id = db.Column(db.Integer, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    sent = db.Column(db.Boolean, default=False)
    delivered = db.Column(db.Boolean, default=False)
    read = db.Column(db.Boolean, default=False)
    replied = db.Column(db.Boolean, default=False)
    sent_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    read_at = db.Column(db.DateTime, nullable=True)

# AI Generated Content
class AIContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=True)
    content_type = db.Column(db.String(50), nullable=False)  # email, message, blog, etc.
    status = db.Column(db.String(50), default='Pending')
    related_to_type = db.Column(db.String(50), nullable=True)
    related_to_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    user = db.relationship('User', backref='ai_contents')

# Web Scraping Task
class WebScrapingTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    url = db.Column(db.Text, nullable=False)
    frequency = db.Column(db.String(50), nullable=True)  # once, daily, weekly, monthly
    status = db.Column(db.String(50), default='Pending')
    last_run = db.Column(db.DateTime, nullable=True)
    next_run = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    user = db.relationship('User', backref='scraping_tasks')
    results = db.relationship('WebScrapingResult', backref='task', lazy='dynamic')

# Web Scraping Results
class WebScrapingResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('web_scraping_task.id'), nullable=False)
    execution_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    status = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    error = db.Column(db.Text, nullable=True)
