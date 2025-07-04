from app import app  # noqa: F401
from routes.auth import auth
from routes.dashboard import dashboard
from routes.tenant import tenant
from routes.prospect import prospect
from routes.opportunity import opportunity
from routes.contact import contact
from routes.account import account
from routes.integration import integration
from routes.scraping import scraping
from routes.templates import templates_bp
from routes.campaigns import campaigns_bp
from routes.content_writer import content_writer_bp
from routes.client_settings import client_settings_bp
from routes.superadmin import superadmin_bp
from routes.github import github_bp
from routes.plans import plans_bp
from routes.home import home_bp

# Register all blueprints
app.register_blueprint(home_bp)  # La página de inicio debe registrarse primero
app.register_blueprint(auth)
app.register_blueprint(dashboard)
app.register_blueprint(tenant)
app.register_blueprint(prospect)
app.register_blueprint(opportunity)
app.register_blueprint(contact)
app.register_blueprint(account)
app.register_blueprint(integration)
app.register_blueprint(scraping)
app.register_blueprint(templates_bp)
app.register_blueprint(campaigns_bp)
app.register_blueprint(content_writer_bp)
app.register_blueprint(client_settings_bp)
app.register_blueprint(superadmin_bp)
app.register_blueprint(github_bp, url_prefix='/github')
app.register_blueprint(plans_bp, url_prefix='/plans')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
