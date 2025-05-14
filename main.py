from app import app  # noqa: F401
from routes.auth import auth
from routes.dashboard import dashboard
from routes.tenant import tenant
from routes.prospect import prospect
from routes.opportunity import opportunity
from routes.contact import contact
from routes.account import account
from routes.integration import integration

# Register all blueprints
app.register_blueprint(auth)
app.register_blueprint(dashboard)
app.register_blueprint(tenant)
app.register_blueprint(prospect)
app.register_blueprint(opportunity)
app.register_blueprint(contact)
app.register_blueprint(account)
app.register_blueprint(integration)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
