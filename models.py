from app import db
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import JSONB
import datetime
import json
import enum
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
    is_superadmin = db.Column(db.Boolean, default=False)  # Indica si este tenant tiene permisos de superadmin
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    users = db.relationship('User', backref='tenant', lazy='dynamic')
    prospects = db.relationship('Prospect', backref='tenant', lazy='dynamic')
    opportunities = db.relationship('Opportunity', backref='tenant', lazy='dynamic')
    contacts = db.relationship('Contact', backref='tenant', lazy='dynamic')
    accounts = db.relationship('Account', backref='tenant', lazy='dynamic')
    
# Cliente Settings - Configuración detallada del cliente
class ClientSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    
    # Información de la empresa
    company_name = db.Column(db.String(100))
    company_logo = db.Column(db.String(255))  # URL o ruta al logo
    industry = db.Column(db.String(100))
    company_size = db.Column(db.String(50))  # Pequeña, Mediana, Grande
    website = db.Column(db.String(255))
    
    # Información de contacto
    primary_contact_name = db.Column(db.String(100))
    primary_contact_email = db.Column(db.String(120))
    primary_contact_phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    state_province = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(100))
    
    # Configuración de facturación
    billing_plan = db.Column(db.String(50))  # Básico, Profesional, Empresarial
    billing_cycle = db.Column(db.String(20))  # Mensual, Anual
    billing_contact_email = db.Column(db.String(120))
    tax_id = db.Column(db.String(50))
    
    # Límites y cuotas
    max_users = db.Column(db.Integer, default=5)
    max_contacts = db.Column(db.Integer, default=1000)
    max_storage_gb = db.Column(db.Float, default=5.0)
    
    # Preferencias
    timezone = db.Column(db.String(50), default='UTC')
    language = db.Column(db.String(10), default='es')
    date_format = db.Column(db.String(20), default='DD/MM/YYYY')
    currency = db.Column(db.String(3), default='EUR')
    
    # Integraciones habilitadas
    enable_email_integration = db.Column(db.Boolean, default=False)
    enable_whatsapp_integration = db.Column(db.Boolean, default=False)
    enable_notion_integration = db.Column(db.Boolean, default=False)
    enable_ai_content_writer = db.Column(db.Boolean, default=False)
    
    # Información de suscripción
    subscription_status = db.Column(db.String(20), default='active')  # active, canceled, suspended
    subscription_start_date = db.Column(db.DateTime)
    subscription_end_date = db.Column(db.DateTime)
    
    # Metadatos
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relaciones
    tenant = db.relationship('Tenant', backref=db.backref('client_settings', uselist=False))

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
    last_interaction_date = db.Column(db.DateTime, nullable=True)
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

# Campaigns
class CampaignStatus(enum.Enum):
    DRAFT = 'Draft'
    SCHEDULED = 'Scheduled'
    SENDING = 'Sending'
    COMPLETED = 'Completed'
    PAUSED = 'Paused'
    CANCELLED = 'Cancelled'
    ERROR = 'Error'

class Campaign(db.Model):
    """Base model for email and WhatsApp campaigns"""
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    campaign_type = db.Column(db.String(20), nullable=False)  # 'email' or 'whatsapp'
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='Draft')
    scheduled_date = db.Column(db.DateTime, nullable=True)
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    target_audience = db.Column(db.String(50))  # 'all_contacts', 'all_prospects', 'filtered'
    audience_filter = db.Column(JSONB)  # Filter criteria in JSON format
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    owner = db.relationship('User', backref='campaigns')
    
    __mapper_args__ = {
        'polymorphic_on': campaign_type,
        'polymorphic_identity': 'campaign'
    }
    
    @property
    def sent_count(self):
        """Count how many messages have been sent"""
        raise NotImplementedError("Subclasses must implement this")
    
    @property
    def total_recipients(self):
        """Count total number of recipients"""
        raise NotImplementedError("Subclasses must implement this")
    
    @property
    def progress(self):
        """Calculate campaign progress as percentage"""
        total = self.total_recipients
        if total == 0:
            return 0
        return int((self.sent_count / total) * 100)

# Email Campaign
class EmailCampaign(Campaign):
    __tablename__ = 'email_campaign'
    id = db.Column(db.Integer, db.ForeignKey('campaign.id'), primary_key=True)
    # Plantilla inicial
    initial_template_id = db.Column(db.Integer, db.ForeignKey('email_template.id'), nullable=True)
    initial_subject = db.Column(db.String(255), nullable=False)
    initial_body_html = db.Column(db.Text, nullable=False)
    initial_body_text = db.Column(db.Text)
    
    # Plantilla de seguimiento 1
    follow_up1_template_id = db.Column(db.Integer, db.ForeignKey('email_template.id'), nullable=True)
    follow_up1_subject = db.Column(db.String(255), nullable=True)
    follow_up1_body_html = db.Column(db.Text, nullable=True)
    follow_up1_body_text = db.Column(db.Text, nullable=True)
    follow_up1_delay_days = db.Column(db.Integer, default=3)  # Días de espera después del inicial
    
    # Plantilla de seguimiento 2
    follow_up2_template_id = db.Column(db.Integer, db.ForeignKey('email_template.id'), nullable=True)
    follow_up2_subject = db.Column(db.String(255), nullable=True)
    follow_up2_body_html = db.Column(db.Text, nullable=True)
    follow_up2_body_text = db.Column(db.Text, nullable=True)
    follow_up2_delay_days = db.Column(db.Integer, default=7)  # Días de espera después del inicial
    
    # Plantilla de seguimiento 3
    follow_up3_template_id = db.Column(db.Integer, db.ForeignKey('email_template.id'), nullable=True)
    follow_up3_subject = db.Column(db.String(255), nullable=True)
    follow_up3_body_html = db.Column(db.Text, nullable=True)
    follow_up3_body_text = db.Column(db.Text, nullable=True)
    follow_up3_delay_days = db.Column(db.Integer, default=14)  # Días de espera después del inicial
    
    # Configuración general
    sender_name = db.Column(db.String(100))
    sender_email = db.Column(db.String(120))
    reply_to = db.Column(db.String(120))
    track_opens = db.Column(db.Boolean, default=True)
    track_clicks = db.Column(db.Boolean, default=True)
    custom_variables = db.Column(JSONB)  # Custom variables for template
    
    # Relaciones
    initial_template = db.relationship('EmailTemplate', foreign_keys=[initial_template_id])
    follow_up1_template = db.relationship('EmailTemplate', foreign_keys=[follow_up1_template_id])
    follow_up2_template = db.relationship('EmailTemplate', foreign_keys=[follow_up2_template_id])
    follow_up3_template = db.relationship('EmailTemplate', foreign_keys=[follow_up3_template_id])
    recipients = db.relationship('EmailCampaignRecipient', backref='campaign', lazy='dynamic', 
                                cascade='all, delete-orphan')
    
    __mapper_args__ = {
        'polymorphic_identity': 'email'
    }
    
    @property
    def sent_count(self):
        return self.recipients.filter_by(sent=True).count()
    
    @property
    def total_recipients(self):
        return self.recipients.count()
    
    @property
    def opened_count(self):
        return self.recipients.filter_by(opened=True).count()
    
    @property
    def clicked_count(self):
        return self.recipients.filter_by(clicked=True).count()
    
    @property
    def bounced_count(self):
        return self.recipients.filter_by(bounced=True).count()

# Email Campaign Recipients
class EmailCampaignRecipient(db.Model):
    __tablename__ = 'email_campaign_recipient'
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('email_campaign.id'), nullable=False)
    recipient_type = db.Column(db.String(50), nullable=False)  # 'contact', 'prospect'
    recipient_id = db.Column(db.Integer, nullable=False)
    recipient_name = db.Column(db.String(100))
    email = db.Column(db.String(120), nullable=False)
    
    # Email inicial
    initial_sent = db.Column(db.Boolean, default=False)
    initial_sent_at = db.Column(db.DateTime, nullable=True)
    initial_opened = db.Column(db.Boolean, default=False)
    initial_opened_at = db.Column(db.DateTime, nullable=True)
    initial_clicked = db.Column(db.Boolean, default=False)
    initial_clicked_at = db.Column(db.DateTime, nullable=True)
    
    # Email de seguimiento 1
    follow_up1_sent = db.Column(db.Boolean, default=False)
    follow_up1_sent_at = db.Column(db.DateTime, nullable=True)
    follow_up1_opened = db.Column(db.Boolean, default=False)
    follow_up1_opened_at = db.Column(db.DateTime, nullable=True)
    follow_up1_clicked = db.Column(db.Boolean, default=False)
    follow_up1_clicked_at = db.Column(db.DateTime, nullable=True)
    
    # Email de seguimiento 2
    follow_up2_sent = db.Column(db.Boolean, default=False)
    follow_up2_sent_at = db.Column(db.DateTime, nullable=True)
    follow_up2_opened = db.Column(db.Boolean, default=False)
    follow_up2_opened_at = db.Column(db.DateTime, nullable=True)
    follow_up2_clicked = db.Column(db.Boolean, default=False)
    follow_up2_clicked_at = db.Column(db.DateTime, nullable=True)
    
    # Email de seguimiento 3
    follow_up3_sent = db.Column(db.Boolean, default=False)
    follow_up3_sent_at = db.Column(db.DateTime, nullable=True)
    follow_up3_opened = db.Column(db.Boolean, default=False)
    follow_up3_opened_at = db.Column(db.DateTime, nullable=True)
    follow_up3_clicked = db.Column(db.Boolean, default=False)
    follow_up3_clicked_at = db.Column(db.DateTime, nullable=True)
    
    # Estado general
    bounced = db.Column(db.Boolean, default=False)
    unsubscribed = db.Column(db.Boolean, default=False)
    responded = db.Column(db.Boolean, default=False)  # Si el usuario respondió a algún email
    responded_at = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.String(255))
    custom_fields = db.Column(JSONB)  # Datos específicos para este destinatario
    
    # Propiedades para compatibilidad
    @property
    def sent(self):
        return self.initial_sent
    
    @property
    def opened(self):
        return self.initial_opened or self.follow_up1_opened or self.follow_up2_opened or self.follow_up3_opened
    
    @property
    def clicked(self):
        return self.initial_clicked or self.follow_up1_clicked or self.follow_up2_clicked or self.follow_up3_clicked
    
    @property
    def sent_at(self):
        return self.initial_sent_at
    
    @property
    def opened_at(self):
        """Devuelve la fecha más reciente de apertura de cualquier email"""
        dates = [d for d in [self.initial_opened_at, self.follow_up1_opened_at, 
                          self.follow_up2_opened_at, self.follow_up3_opened_at] if d]
        return max(dates) if dates else None
    
    @property
    def clicked_at(self):
        """Devuelve la fecha más reciente de clic en cualquier email"""
        dates = [d for d in [self.initial_clicked_at, self.follow_up1_clicked_at, 
                          self.follow_up2_clicked_at, self.follow_up3_clicked_at] if d]
        return max(dates) if dates else None
    
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

# WhatsApp Campaign
class WhatsAppCampaign(Campaign):
    __tablename__ = 'whatsapp_campaign'
    id = db.Column(db.Integer, db.ForeignKey('campaign.id'), primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('message_template.id'), nullable=True)
    message = db.Column(db.Text, nullable=False)
    has_media = db.Column(db.Boolean, default=False)
    media_type = db.Column(db.String(20))  # 'image', 'video', 'document', etc.
    media_url = db.Column(db.String(255))
    custom_variables = db.Column(JSONB)  # Custom variables for template
    
    template = db.relationship('WhatsAppTemplate')
    recipients = db.relationship('WhatsAppCampaignRecipient', backref='campaign', lazy='dynamic',
                                cascade='all, delete-orphan')
    
    __mapper_args__ = {
        'polymorphic_identity': 'whatsapp'
    }
    
    @property
    def sent_count(self):
        return self.recipients.filter_by(sent=True).count()
    
    @property
    def total_recipients(self):
        return self.recipients.count()
    
    @property
    def delivered_count(self):
        return self.recipients.filter_by(delivered=True).count()
    
    @property
    def read_count(self):
        return self.recipients.filter_by(read=True).count()

# WhatsApp Campaign Recipients
class WhatsAppCampaignRecipient(db.Model):
    __tablename__ = 'whatsapp_campaign_recipient'
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('whatsapp_campaign.id'), nullable=False)
    recipient_type = db.Column(db.String(50), nullable=False)  # 'contact', 'prospect'
    recipient_id = db.Column(db.Integer, nullable=False)
    recipient_name = db.Column(db.String(100))
    phone = db.Column(db.String(20), nullable=False)
    sent = db.Column(db.Boolean, default=False)
    delivered = db.Column(db.Boolean, default=False)
    read = db.Column(db.Boolean, default=False)
    replied = db.Column(db.Boolean, default=False)
    error_message = db.Column(db.String(255))
    custom_fields = db.Column(JSONB)  # Specific data for this recipient
    sent_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    read_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

# Message templates
class MessageTemplate(db.Model):
    """Base model for email and WhatsApp message templates"""
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'))
    template_type = db.Column(db.String(20))  # 'email' or 'whatsapp'
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_active = db.Column(db.Boolean, default=True)
    
    __mapper_args__ = {
        'polymorphic_on': template_type,
        'polymorphic_identity': 'message_template'
    }

class EmailTemplate(MessageTemplate):
    """Email message template"""
    id = db.Column(db.Integer, db.ForeignKey('message_template.id'), primary_key=True)
    subject = db.Column(db.String(200), nullable=False)
    body_html = db.Column(db.Text, nullable=False)
    body_text = db.Column(db.Text)
    sender_name = db.Column(db.String(100))
    sender_email = db.Column(db.String(100))
    available_variables = db.Column(JSONB)
    
    __mapper_args__ = {
        'polymorphic_identity': 'email'
    }

class WhatsAppTemplate(MessageTemplate):
    """WhatsApp message template"""
    id = db.Column(db.Integer, db.ForeignKey('message_template.id'), primary_key=True)
    content = db.Column(db.Text, nullable=False)
    has_media = db.Column(db.Boolean, default=False)
    media_type = db.Column(db.String(20))  # 'image', 'video', 'document', etc.
    media_url = db.Column(db.String(255))
    available_variables = db.Column(JSONB)
    
    __mapper_args__ = {
        'polymorphic_identity': 'whatsapp'
    }

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

# Base model for all integration configurations
class IntegrationConfig(db.Model):
    __tablename__ = 'integration_config'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    integration_type = db.Column(db.String(50), nullable=False, default='unknown')  # smtp, imap, openai, claude, etc.
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Config as JSON string
    config_json = db.Column(db.Text, nullable=True)
    
    # Store when it was last tested successfully
    last_tested = db.Column(db.DateTime, nullable=True)
    test_result = db.Column(db.Text, nullable=True)  # JSON with any error or success details
    
    # Store credentials separately since they're sensitive
    credentials_json = db.Column(db.Text, nullable=True)
    
    # Discriminator column for polymorphic identity
    __mapper_args__ = {
        'polymorphic_on': integration_type,
        'polymorphic_identity': 'unknown'
    }
    
    @property
    def config(self):
        """Get configuration as dictionary"""
        if not self.config_json:
            return {}
        return json.loads(self.config_json)
    
    @config.setter
    def config(self, value):
        """Set configuration from dictionary"""
        if value is None:
            self.config_json = None
        else:
            self.config_json = json.dumps(value)
    
    @property
    def credentials(self):
        """Get credentials as dictionary"""
        if not self.credentials_json:
            return {}
        return json.loads(self.credentials_json)
    
    @credentials.setter
    def credentials(self, value):
        """Set credentials from dictionary"""
        if value is None:
            self.credentials_json = None
        else:
            self.credentials_json = json.dumps(value)
    
    def __repr__(self):
        return f'<IntegrationConfig {self.integration_type} for tenant {self.tenant_id}>'

# Evolution API WhatsApp Integration
class EvolutionApiConfig(IntegrationConfig):
    __mapper_args__ = {
        'polymorphic_identity': 'evolution_api',
    }
    
    @property
    def api_url(self):
        return self.config.get('api_url', '')
    
    @property
    def instance_name(self):
        return self.config.get('instance_name', '')
    
    @property
    def api_key(self):
        return self.credentials.get('api_key', '')
    
    def update_from_form(self, form_data):
        """Update config from form data"""
        config = {
            'api_url': form_data.get('api_url', '').strip(),
            'instance_name': form_data.get('instance_name', '').strip(),
        }
        self.config = config
        
        # Only update API key if it was changed (not placeholder)
        api_key = form_data.get('api_key', '').strip()
        if api_key and not api_key.startswith('•'):
            self.credentials = {'api_key': api_key}
        
        return self

# SMTP Email Integration
class SmtpConfig(IntegrationConfig):
    __mapper_args__ = {
        'polymorphic_identity': 'smtp',
    }
    
    @property
    def host(self):
        return self.config.get('host', '')
    
    @property
    def port(self):
        return self.config.get('port', 587)
    
    @property
    def use_tls(self):
        return self.config.get('use_tls', True)
    
    @property
    def username(self):
        return self.credentials.get('username', '')
    
    @property
    def password(self):
        return self.credentials.get('password', '')
    
    @property
    def from_name(self):
        return self.config.get('from_name', '')
    
    @property
    def from_email(self):
        return self.config.get('from_email', '')
    
    def update_from_form(self, form_data):
        """Update config from form data"""
        config = {
            'host': form_data.get('host', '').strip(),
            'port': int(form_data.get('port', 587)),
            'use_tls': form_data.get('use_tls') == 'on',
            'from_name': form_data.get('from_name', '').strip(),
            'from_email': form_data.get('from_email', '').strip(),
        }
        self.config = config
        
        # Only update credentials if they were changed
        username = form_data.get('username', '').strip()
        password = form_data.get('password', '').strip()
        
        if username:
            credentials = self.credentials
            credentials['username'] = username
            
            if password and not password.startswith('•'):
                credentials['password'] = password
                
            self.credentials = credentials
        
        return self

# IMAP Email Integration
class ImapConfig(IntegrationConfig):
    __mapper_args__ = {
        'polymorphic_identity': 'imap',
    }
    
    @property
    def host(self):
        return self.config.get('host', '')
    
    @property
    def port(self):
        return self.config.get('port', 993)
    
    @property
    def use_ssl(self):
        return self.config.get('use_ssl', True)
    
    @property
    def username(self):
        return self.credentials.get('username', '')
    
    @property
    def password(self):
        return self.credentials.get('password', '')
    
    def update_from_form(self, form_data):
        """Update config from form data"""
        config = {
            'host': form_data.get('host', '').strip(),
            'port': int(form_data.get('port', 993)),
            'use_ssl': form_data.get('use_ssl') == 'on',
        }
        self.config = config
        
        # Only update credentials if they were changed
        username = form_data.get('username', '').strip()
        password = form_data.get('password', '').strip()
        
        if username:
            credentials = self.credentials
            credentials['username'] = username
            
            if password and not password.startswith('•'):
                credentials['password'] = password
                
            self.credentials = credentials
        
        return self

# OpenAI API Integration
class OpenAiConfig(IntegrationConfig):
    __mapper_args__ = {
        'polymorphic_identity': 'openai',
    }
    
    @property
    def api_key(self):
        return self.credentials.get('api_key', '')
    
    @property
    def default_model(self):
        return self.config.get('default_model', 'gpt-4o')
    
    @property
    def organization_id(self):
        return self.config.get('organization_id', '')
    
    def update_from_form(self, form_data):
        """Update config from form data"""
        config = {
            'default_model': form_data.get('default_model', 'gpt-4o').strip(),
            'organization_id': form_data.get('organization_id', '').strip(),
        }
        self.config = config
        
        # Only update API key if it was changed
        api_key = form_data.get('api_key', '').strip()
        if api_key and not api_key.startswith('•'):
            self.credentials = {'api_key': api_key}
        
        return self

# Anthropic Claude API Integration
class ClaudeConfig(IntegrationConfig):
    __mapper_args__ = {
        'polymorphic_identity': 'claude',
    }
    
    @property
    def api_key(self):
        return self.credentials.get('api_key', '')
    
    @property
    def default_model(self):
        return self.config.get('default_model', 'claude-3-5-sonnet-20241022')
    
    def update_from_form(self, form_data):
        """Update config from form data"""
        config = {
            'default_model': form_data.get('default_model', 'claude-3-5-sonnet-20241022').strip(),
        }
        self.config = config
        
        # Only update API key if it was changed
        api_key = form_data.get('api_key', '').strip()
        if api_key and not api_key.startswith('•'):
            self.credentials = {'api_key': api_key}
        
        return self

# Google Gemini API Integration
class GeminiConfig(IntegrationConfig):
    __mapper_args__ = {
        'polymorphic_identity': 'gemini',
    }
    
    @property
    def api_key(self):
        return self.credentials.get('api_key', '')
    
    @property
    def default_model(self):
        return self.config.get('default_model', 'gemini-1.5-pro')
    
    def update_from_form(self, form_data):
        """Update config from form data"""
        config = {
            'default_model': form_data.get('default_model', 'gemini-1.5-pro').strip(),
        }
        self.config = config
        
        # Only update API key if it was changed
        api_key = form_data.get('api_key', '').strip()
        if api_key and not api_key.startswith('•'):
            self.credentials = {'api_key': api_key}
        
        return self

# SERP API Google Maps Integration
class SerpMapsConfig(IntegrationConfig):
    __mapper_args__ = {
        'polymorphic_identity': 'serp_maps',
    }
    
    @property
    def api_key(self):
        return self.credentials.get('api_key', '')
    
    @property
    def default_country(self):
        return self.config.get('default_country', 'us')
    
    @property
    def default_language(self):
        return self.config.get('default_language', 'en')
    
    def update_from_form(self, form_data):
        """Update config from form data"""
        config = {
            'default_country': form_data.get('default_country', 'us').strip(),
            'default_language': form_data.get('default_language', 'en').strip(),
        }
        self.config = config
        
        # Only update API key if it was changed
        api_key = form_data.get('api_key', '').strip()
        if api_key and not api_key.startswith('•'):
            self.credentials = {'api_key': api_key}
        
        return self

# Notion API Integration
class NotionConfig(IntegrationConfig):
    __mapper_args__ = {
        'polymorphic_identity': 'notion',
    }
    
    @property
    def integration_token(self):
        return self.credentials.get('integration_token', '')
    
    @property
    def database_id(self):
        return self.config.get('database_id', '')
    
    def update_from_form(self, form_data):
        """Update config from form data"""
        config = {
            'database_id': form_data.get('database_id', '').strip(),
        }
        self.config = config
        
        # Only update token if it was changed
        token = form_data.get('integration_token', '').strip()
        if token and not token.startswith('•'):
            self.credentials = {'integration_token': token}
        
        return self
