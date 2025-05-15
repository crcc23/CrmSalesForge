"""
Script para generar plantillas de muestra en la base de datos.
Ejecutar este script para crear ejemplos de plantillas de correo y WhatsApp
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import EmailTemplate, WhatsAppTemplate, User
from datetime import datetime

def create_sample_templates():
    """Crear plantillas de muestra para correo y WhatsApp"""
    with app.app_context():
        # Verificar si ya hay plantillas
        email_count = EmailTemplate.query.count()
        whatsapp_count = WhatsAppTemplate.query.count()
        
        if email_count > 0 or whatsapp_count > 0:
            print(f"Ya existen plantillas en la base de datos (Email: {email_count}, WhatsApp: {whatsapp_count})")
            if input("¿Desea crear plantillas adicionales? (s/n): ").lower() != 's':
                return
        
        # Obtener el primer usuario (preferiblemente administrador) para asignar tenant_id
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User.query.first()
        
        if not admin:
            print("No se encontraron usuarios en la base de datos. Cree un usuario primero.")
            return
        
        tenant_id = admin.tenant_id if hasattr(admin, 'tenant_id') else 1
        created_by = admin.id
        
        # Crear plantillas de correo electrónico
        email_templates = [
            {
                'name': 'Bienvenida a Nuevos Clientes',
                'description': 'Mensaje de bienvenida para nuevos clientes registrados',
                'subject': 'Bienvenido a nuestra plataforma, {{nombre}}',
                'body_html': """
                <div style="text-align: center; color: #3498db; font-size: 20px; margin-bottom: 20px;">¡Bienvenido a nuestra plataforma!</div>
                <div>
                    <p>Hola <strong>{{nombre}} {{apellido}}</strong>,</p>
                    <p>Estamos encantados de que te hayas unido a nosotros. Tu cuenta ha sido creada exitosamente y ya puedes comenzar a utilizar todos nuestros servicios.</p>
                    <p>Información de tu cuenta:</p>
                    <ul>
                        <li>Email: {{email}}</li>
                        <li>Fecha de registro: {{fecha}}</li>
                    </ul>
                    <p>Para confirmar tu cuenta, por favor haz clic en el siguiente enlace:</p>
                    <p><a href="{{url_confirmacion}}" style="background-color: #3498db; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px;">Confirmar mi cuenta</a></p>
                    <p>Si tienes alguna pregunta, no dudes en contactarnos.</p>
                    <p>Saludos cordiales,<br>El equipo de soporte</p>
                </div>
                """,
                'body_text': """
                ¡Bienvenido a nuestra plataforma!
                
                Hola {{nombre}} {{apellido}},
                
                Estamos encantados de que te hayas unido a nosotros. Tu cuenta ha sido creada exitosamente y ya puedes comenzar a utilizar todos nuestros servicios.
                
                Información de tu cuenta:
                - Email: {{email}}
                - Fecha de registro: {{fecha}}
                
                Para confirmar tu cuenta, por favor visita el siguiente enlace:
                {{url_confirmacion}}
                
                Si tienes alguna pregunta, no dudes en contactarnos.
                
                Saludos cordiales,
                El equipo de soporte
                """,
                'sender_name': 'Equipo de Soporte',
                'sender_email': 'soporte@ejemplo.com',
                'available_variables': {
                    'nombre': 'Nombre del contacto',
                    'apellido': 'Apellido del contacto',
                    'email': 'Email del contacto',
                    'fecha': 'Fecha actual',
                    'url_confirmacion': 'URL de confirmación'
                }
            },
            {
                'name': 'Recordatorio de Cita',
                'description': 'Recordatorio de cita programada',
                'subject': 'Recordatorio: Tu cita del {{fecha_cita}}',
                'body_html': """
                <div style="text-align: center; color: #2ecc71; font-size: 18px; margin-bottom: 15px;">Recordatorio de Cita</div>
                <div>
                    <p>Estimado/a <strong>{{nombre}}</strong>,</p>
                    <p>Te recordamos que tienes una cita programada para el <strong>{{fecha_cita}}</strong> a las <strong>{{hora_cita}}</strong>.</p>
                    <p>Detalles de la cita:</p>
                    <ul>
                        <li>Tipo: {{tipo_cita}}</li>
                        <li>Ubicación: {{ubicacion}}</li>
                        <li>Duración estimada: {{duracion}} minutos</li>
                    </ul>
                    <p>Si necesitas reprogramar, por favor hazlo con al menos 24 horas de anticipación:</p>
                    <p><a href="{{url_reprogramar}}" style="background-color: #2ecc71; color: white; padding: 8px 12px; text-decoration: none; border-radius: 4px;">Reprogramar cita</a></p>
                    <p>Gracias por confiar en nosotros.</p>
                    <p>Saludos,<br>{{empresa}}</p>
                </div>
                """,
                'body_text': """
                Recordatorio de Cita
                
                Estimado/a {{nombre}},
                
                Te recordamos que tienes una cita programada para el {{fecha_cita}} a las {{hora_cita}}.
                
                Detalles de la cita:
                - Tipo: {{tipo_cita}}
                - Ubicación: {{ubicacion}}
                - Duración estimada: {{duracion}} minutos
                
                Si necesitas reprogramar, por favor hazlo con al menos 24 horas de anticipación:
                {{url_reprogramar}}
                
                Gracias por confiar en nosotros.
                
                Saludos,
                {{empresa}}
                """,
                'sender_name': 'Sistema de Citas',
                'sender_email': 'citas@ejemplo.com',
                'available_variables': {
                    'nombre': 'Nombre del contacto',
                    'fecha_cita': 'Fecha de la cita',
                    'hora_cita': 'Hora de la cita',
                    'tipo_cita': 'Tipo de cita',
                    'ubicacion': 'Ubicación de la cita',
                    'duracion': 'Duración en minutos',
                    'url_reprogramar': 'URL para reprogramar',
                    'empresa': 'Nombre de la empresa'
                }
            },
            {
                'name': 'Oferta Especial',
                'description': 'Notificación de oferta especial para clientes',
                'subject': 'Oferta exclusiva para ti: ¡{{porcentaje_descuento}}% de descuento!',
                'body_html': """
                <div style="text-align: center; color: #e74c3c; font-size: 22px; margin-bottom: 20px; font-weight: bold;">OFERTA ESPECIAL</div>
                <div>
                    <p>Hola <strong>{{nombre}}</strong>,</p>
                    <p>Como cliente valioso, queremos ofrecerte una <strong>oferta exclusiva</strong> con {{porcentaje_descuento}}% de descuento en todos nuestros productos.</p>
                    <div style="background-color: #f8f9fa; border-left: 4px solid #e74c3c; padding: 15px; margin: 15px 0;">
                        <p style="font-size: 16px; margin: 0;"><strong>Código de descuento:</strong> {{codigo_descuento}}</p>
                        <p style="font-size: 12px; margin: 5px 0 0 0; color: #7f8c8d;">Válido hasta: {{fecha_expiracion}}</p>
                    </div>
                    <p>Esta oferta incluye:</p>
                    <ul>
                        <li>{{beneficio_1}}</li>
                        <li>{{beneficio_2}}</li>
                        <li>{{beneficio_3}}</li>
                    </ul>
                    <p style="text-align: center; margin: 25px 0;"><a href="{{url_oferta}}" style="background-color: #e74c3c; color: white; padding: 12px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">APROVECHAR OFERTA</a></p>
                    <p style="font-size: 12px; color: #7f8c8d;">Esta oferta es personal y no transferible. Se aplican términos y condiciones.</p>
                </div>
                """,
                'body_text': """
                OFERTA ESPECIAL
                
                Hola {{nombre}},
                
                Como cliente valioso, queremos ofrecerte una oferta exclusiva con {{porcentaje_descuento}}% de descuento en todos nuestros productos.
                
                Código de descuento: {{codigo_descuento}}
                Válido hasta: {{fecha_expiracion}}
                
                Esta oferta incluye:
                - {{beneficio_1}}
                - {{beneficio_2}}
                - {{beneficio_3}}
                
                Para aprovechar esta oferta, visita:
                {{url_oferta}}
                
                Esta oferta es personal y no transferible. Se aplican términos y condiciones.
                """,
                'sender_name': 'Equipo de Marketing',
                'sender_email': 'marketing@ejemplo.com',
                'available_variables': {
                    'nombre': 'Nombre del contacto',
                    'porcentaje_descuento': 'Porcentaje de descuento',
                    'codigo_descuento': 'Código de descuento',
                    'fecha_expiracion': 'Fecha de expiración',
                    'beneficio_1': 'Primer beneficio',
                    'beneficio_2': 'Segundo beneficio',
                    'beneficio_3': 'Tercer beneficio',
                    'url_oferta': 'URL de la oferta'
                }
            }
        ]
        
        # Crear plantillas de WhatsApp
        whatsapp_templates = [
            {
                'name': 'Confirmación de Pedido',
                'description': 'Mensaje de confirmación cuando un cliente realiza un pedido',
                'content': """¡Hola {{nombre}}!

Gracias por tu pedido #{{numero_pedido}}. Hemos recibido tu compra por un total de ${{total}}.

Detalles:
{{detalles_pedido}}

Tu pedido será entregado aproximadamente el {{fecha_entrega}}.

Puedes hacer seguimiento con este enlace: {{url_seguimiento}}

¡Gracias por tu compra!""",
                'has_media': False,
                'media_type': None, 
                'media_url': None,
                'available_variables': {
                    'nombre': 'Nombre del contacto',
                    'numero_pedido': 'Número del pedido',
                    'total': 'Total del pedido',
                    'detalles_pedido': 'Listado de productos',
                    'fecha_entrega': 'Fecha estimada de entrega',
                    'url_seguimiento': 'URL para seguimiento'
                }
            },
            {
                'name': 'Recordatorio de Pago',
                'description': 'Recordatorio amistoso para pagos pendientes',
                'content': """Estimado/a {{nombre}},

Este es un recordatorio amistoso de que tiene un pago pendiente de ${{monto}} correspondiente a la factura #{{numero_factura}}, con vencimiento el {{fecha_vencimiento}}.

Si ya realizó el pago, por favor ignore este mensaje.

Para pagar ahora, use este enlace: {{url_pago}}

Si tiene alguna consulta, contáctenos al {{telefono}}.

Saludos cordiales,
{{empresa}}""",
                'has_media': True,
                'media_type': 'image',
                'media_url': 'https://via.placeholder.com/600x400?text=Factura+Pendiente',
                'available_variables': {
                    'nombre': 'Nombre del contacto',
                    'monto': 'Monto pendiente',
                    'numero_factura': 'Número de factura',
                    'fecha_vencimiento': 'Fecha de vencimiento',
                    'url_pago': 'URL para realizar el pago',
                    'telefono': 'Teléfono de contacto',
                    'empresa': 'Nombre de la empresa'
                }
            },
            {
                'name': 'Agradecimiento post-compra',
                'description': 'Mensaje de agradecimiento después de una compra',
                'content': """¡Gracias por tu compra, {{nombre}}!

Esperamos que estés disfrutando de {{producto}}. Nos encantaría saber tu opinión.

¿Podrías tomarte un momento para dejarnos una reseña? {{url}}

Como agradecimiento, aquí tienes un cupón de descuento del 10% para tu próxima compra: {{codigo_descuento}}

¡Gracias por elegirnos!""",
                'has_media': False,
                'media_type': None,
                'media_url': None,
                'available_variables': {
                    'nombre': 'Nombre del contacto',
                    'producto': 'Producto comprado',
                    'url': 'URL para dejar reseña',
                    'codigo_descuento': 'Código de descuento'
                }
            }
        ]
        
        # Guardar plantillas de correo
        for template_data in email_templates:
            template = EmailTemplate(
                tenant_id=tenant_id,
                created_by=created_by,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                **template_data
            )
            db.session.add(template)
        
        # Guardar plantillas de WhatsApp
        for template_data in whatsapp_templates:
            template = WhatsAppTemplate(
                tenant_id=tenant_id,
                created_by=created_by,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                **template_data
            )
            db.session.add(template)
        
        db.session.commit()
        
        print(f"Se han creado correctamente {len(email_templates)} plantillas de correo y {len(whatsapp_templates)} plantillas de WhatsApp")

if __name__ == "__main__":
    create_sample_templates()