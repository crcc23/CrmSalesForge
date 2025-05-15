from app import app, db
from models import Prospect, User, Tenant
from flask import session
import datetime

def create_demo_prospects(tenant_id, user_id):
    """
    Crea 5 prospectos de demostración para un tenant específico
    
    Args:
        tenant_id: ID del tenant al que pertenecerán los prospectos
        user_id: ID del usuario propietario de los prospectos
    """
    
    # Lista de prospectos demo
    prospects_data = [
        {
            "first_name": "Carlos",
            "last_name": "Rodríguez",
            "company": "Innovatech S.A.",
            "job_title": "Director de Tecnología",
            "email": "carlos.rodriguez@innovatech.com",
            "phone": "+34 612 345 678",
            "source": "Website",
            "status": "New",
            "notes": "Interesado en nuestras soluciones de CRM para su empresa tecnológica."
        },
        {
            "first_name": "María",
            "last_name": "González",
            "company": "Consultoría Global",
            "job_title": "Gerente de Proyectos",
            "email": "maria.gonzalez@consultoria.com",
            "phone": "+34 623 456 789",
            "source": "Referral",
            "status": "Contacted",
            "notes": "Referida por Juan Pérez. Busca mejorar la gestión de clientes en su consultora."
        },
        {
            "first_name": "Javier",
            "last_name": "Fernández",
            "company": "Constructora Ibérica",
            "job_title": "Director Comercial",
            "email": "javier.fernandez@constructora.es",
            "phone": "+34 634 567 890",
            "source": "Trade Show",
            "status": "Qualified",
            "notes": "Conocido en la feria de construcción. Tiene un presupuesto asignado para este trimestre."
        },
        {
            "first_name": "Laura",
            "last_name": "Martínez",
            "company": "Edu-Solutions",
            "job_title": "Directora de Marketing",
            "email": "laura.martinez@edusolutions.edu",
            "phone": "+34 645 678 901",
            "source": "Email Campaign",
            "status": "Disqualified",
            "notes": "Respondió a nuestra campaña de email pero actualmente no tiene presupuesto disponible."
        },
        {
            "first_name": "Antonio",
            "last_name": "López",
            "company": "Logística Rápida",
            "job_title": "CEO",
            "email": "antonio.lopez@logisticarapida.com",
            "phone": "+34 656 789 012",
            "source": "Social Media",
            "status": "Qualified",
            "notes": "Contactado a través de LinkedIn. Muy interesado en implementar nuestro CRM en toda su empresa."
        }
    ]
    
    # Verificar si ya existen prospectos para no duplicar
    existing_count = Prospect.query.filter_by(tenant_id=tenant_id).count()
    
    if existing_count == 0:
        # Crear los prospectos
        for data in prospects_data:
            prospect = Prospect(
                tenant_id=tenant_id,
                owner_id=user_id,
                first_name=data["first_name"],
                last_name=data["last_name"],
                company=data["company"],
                job_title=data["job_title"],
                email=data["email"],
                phone=data["phone"],
                source=data["source"],
                status=data["status"],
                notes=data["notes"],
                created_at=datetime.datetime.utcnow()
            )
            db.session.add(prospect)
        
        # Guardar cambios en la base de datos
        db.session.commit()
        return {"success": True, "count": len(prospects_data)}
    else:
        # Ya existen prospectos
        return {"success": False, "message": "Ya existen prospectos para este tenant"}

# Función para ejecutar la creación de prospectos manualmente
def run_seed():
    with app.app_context():
        # Obtener el primer tenant
        tenant = Tenant.query.first()
        if not tenant:
            print("No se encontró ningún tenant. Asegúrate de tener al menos un tenant creado.")
            return
        
        # Obtener el primer usuario del tenant
        user = User.query.filter_by(tenant_id=tenant.id).first()
        if not user:
            print("No se encontró ningún usuario para el tenant. Asegúrate de tener al menos un usuario creado.")
            return
        
        # Crear los prospectos
        result = create_demo_prospects(tenant.id, user.id)
        
        if result["success"]:
            print(f"Se han creado {result['count']} prospectos de demostración con éxito.")
        else:
            print(result["message"])

if __name__ == "__main__":
    run_seed()