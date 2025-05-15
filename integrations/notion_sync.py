import os
from notion_client import Client
from models import Prospect, db

def get_notion_client():
    """
    Crea y retorna un cliente para la API de Notion
    
    Returns:
        notion_client: Cliente configurado para la API de Notion
    """
    notion_token = os.environ.get('NOTION_INTEGRATION_SECRET')
    
    if not notion_token:
        raise ValueError("NOTION_INTEGRATION_SECRET no está configurado")
    
    return Client(auth=notion_token)

def sync_prospect_to_notion(prospect_id):
    """
    Sincroniza un prospecto con una base de datos de Notion
    
    Args:
        prospect_id: El ID del prospecto a sincronizar
        
    Returns:
        dict: Resultado de la operación con éxito/error
    """
    try:
        # Obtener el cliente de Notion
        notion = get_notion_client()
        
        # Obtener el ID de la base de datos de Notion
        database_id = os.environ.get('NOTION_DATABASE_ID')
        
        if not database_id:
            return {"success": False, "error": "NOTION_DATABASE_ID no está configurado"}
        
        # Obtener el prospecto de la base de datos
        prospect = Prospect.query.get(prospect_id)
        
        if not prospect:
            return {"success": False, "error": f"No se encontró el prospecto con ID {prospect_id}"}
        
        # Crear las propiedades para la página de Notion
        properties = {
            "Nombre": {
                "title": [
                    {
                        "text": {
                            "content": f"{prospect.first_name} {prospect.last_name}"
                        }
                    }
                ]
            },
            "Empresa": {
                "rich_text": [
                    {
                        "text": {
                            "content": prospect.company or ""
                        }
                    }
                ]
            },
            "Cargo": {
                "rich_text": [
                    {
                        "text": {
                            "content": prospect.job_title or ""
                        }
                    }
                ]
            },
            "Email": {
                "email": prospect.email or ""
            },
            "Teléfono": {
                "phone_number": prospect.phone or ""
            },
            "Estado": {
                "select": {
                    "name": prospect.status
                }
            },
            "Fuente": {
                "select": {
                    "name": prospect.source or "Otro"
                }
            }
        }
        
        # Crear la página en Notion
        response = notion.pages.create(
            parent={"database_id": database_id},
            properties=properties
        )
        
        # Actualizar el prospecto con información adicional si es necesario
        # Por ejemplo, podríamos guardar el ID de Notion en el prospecto
        
        return {"success": True, "notion_page_id": response["id"]}
        
    except Exception as e:
        # Capturar cualquier error que pueda ocurrir
        return {"success": False, "error": str(e)}

def sync_all_prospects_to_notion(tenant_id):
    """
    Sincroniza todos los prospectos de un tenant con Notion
    
    Args:
        tenant_id: El ID del tenant cuyos prospectos se sincronizarán
        
    Returns:
        dict: Resultado de la operación con éxito/error
    """
    try:
        # Obtener todos los prospectos del tenant
        prospects = Prospect.query.filter_by(tenant_id=tenant_id).all()
        
        if not prospects:
            return {"success": False, "error": f"No se encontraron prospectos para el tenant {tenant_id}"}
        
        results = []
        for prospect in prospects:
            result = sync_prospect_to_notion(prospect.id)
            results.append({
                "prospect_id": prospect.id,
                "prospect_name": f"{prospect.first_name} {prospect.last_name}",
                "result": result
            })
        
        return {
            "success": True,
            "total": len(results),
            "details": results
        }
        
    except Exception as e:
        # Capturar cualquier error que pueda ocurrir
        return {"success": False, "error": str(e)}