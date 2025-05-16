from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user
from app import db
from models import User, Tenant
import logging
import os
import json
import datetime
import requests

# Importaciones opcionales
try:
    from openai import OpenAI
    openai_available = True
except ImportError:
    openai_available = False

try:
    import anthropic
    anthropic_available = True
except ImportError:
    anthropic_available = False

try:
    import google.generativeai as genai
    gemini_available = True
except ImportError:
    gemini_available = False

# Blueprint para Content Writer AI
content_writer_bp = Blueprint('content_writer', __name__, url_prefix='/content-writer')

def get_tenant_id():
    """Helper function to get tenant ID from session"""
    if hasattr(current_user, 'tenant_id'):
        return current_user.tenant_id
    return None

@content_writer_bp.route('/')
@login_required
def index():
    """Mostrar la página principal del generador de contenido"""
    tenant_id = get_tenant_id()
    
    # Para desarrollo: usamos mock data para pruebas
    # En una implementación completa, se verificaría realmente las claves API
    openai_configured = True  # Para demostración, simulamos que está configurado
    anthropic_configured = True
    gemini_configured = True
    
    # Tipos de contenido disponibles
    content_types = [
        {"id": "blog_post", "name": "Artículo de blog"},
        {"id": "email", "name": "Email"},
        {"id": "instagram_post", "name": "Post de Instagram"},
        {"id": "facebook_post", "name": "Post de Facebook"},
        {"id": "twitter_post", "name": "Post de Twitter"},
        {"id": "product_short", "name": "Descripción corta de producto"},
        {"id": "product_long", "name": "Descripción larga de producto"}
    ]
    
    # Tonos disponibles
    tones = [
        {"id": "professional", "name": "Profesional"},
        {"id": "conversational", "name": "Conversacional"},
        {"id": "inspirational", "name": "Inspirador"},
        {"id": "technical", "name": "Técnico"},
        {"id": "funny", "name": "Divertido"},
        {"id": "custom", "name": "Otro"}
    ]
    
    # Objetivos
    objectives = [
        {"id": "inform", "name": "Informar"},
        {"id": "persuade", "name": "Persuadir"},
        {"id": "entertain", "name": "Entretener"},
        {"id": "educate", "name": "Educar"},
        {"id": "inspire", "name": "Inspirar"},
        {"id": "sell", "name": "Vender"},
        {"id": "custom", "name": "Otro"}
    ]
    
    # Formatos de salida
    output_formats = [
        {"id": "plain_text", "name": "Texto plano"},
        {"id": "html", "name": "HTML"},
        {"id": "markdown", "name": "Markdown"}
    ]
    
    # APIs disponibles (para desarrollo mostramos todos para pruebas de UI)
    api_providers = [
        {"id": "openai", "name": "OpenAI GPT-4o"},
        {"id": "anthropic", "name": "Anthropic Claude"},
        {"id": "gemini", "name": "Google Gemini"}
    ]
    
    # Historial de contenidos generados (se implementará después)
    content_history = []
    
    return render_template('content_writer/index.html',
                           content_types=content_types,
                           tones=tones,
                           objectives=objectives,
                           output_formats=output_formats,
                           api_providers=api_providers,
                           content_history=content_history)

@content_writer_bp.route('/generate', methods=['POST'])
@login_required
def generate_content():
    """Endpoint para generar contenido"""
    try:
        # Obtener datos del formulario
        content_type = request.form.get('content_type')
        topic = request.form.get('topic')
        tone = request.form.get('tone')
        custom_tone = request.form.get('custom_tone')
        objective = request.form.get('objective')
        custom_objective = request.form.get('custom_objective')
        keywords = request.form.get('keywords')
        output_format = request.form.get('output_format')
        api_provider = request.form.get('api_provider')
        
        # Validar datos
        if not all([content_type, topic, tone, objective, output_format, api_provider]):
            return jsonify({'success': False, 'error': 'Faltan campos obligatorios'}), 400
        
        # Usar tono personalizado si se seleccionó "Otro"
        if tone == 'custom' and custom_tone:
            tone = custom_tone
            
        # Usar objetivo personalizado si se seleccionó "Otro"
        if objective == 'custom' and custom_objective:
            objective = custom_objective
        
        # Crear el prompt para el modelo
        prompt = create_prompt(content_type, topic, tone, objective, keywords)
        
        # Para desarrollo: Generar contenido de ejemplo según el tipo
        result = generate_sample_content(content_type, topic, tone, objective, keywords, output_format, api_provider)
        
        # Simular una pausa para dar sensación de procesamiento
        import time
        time.sleep(1.5)
        
        # En una implementación real, aquí se llamaría a las APIs según el proveedor seleccionado
        # y se guardaría el contenido en el historial
        
        return jsonify({'success': True, 'content': result})
    
    except Exception as e:
        logging.error(f"Error al generar contenido: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
        
def generate_sample_content(content_type, topic, tone, objective, keywords, output_format, api_provider):
    """Generar contenido de ejemplo para demostración"""
    
    # Mapeo de tipos de contenido a ejemplos
    content_examples = {
        'blog_post': f"""<h1>{topic.capitalize()}: Una guía completa</h1>
        
<p>En el mundo actual, {topic} se ha convertido en un tema de gran relevancia. Cada vez más personas buscan información sobre cómo pueden aprovechar al máximo las oportunidades que ofrece.</p>

<h2>¿Por qué es importante {topic}?</h2>

<p>La importancia de {topic} radica en su capacidad para transformar la manera en que interactuamos con nuestro entorno. Ya sea en el ámbito profesional o personal, comprender los principios fundamentales de este tema nos permite tomar decisiones más informadas.</p>

<h2>Aspectos clave a considerar</h2>

<ul>
  <li><strong>Planificación estratégica:</strong> Desarrollar un enfoque sistemático.</li>
  <li><strong>Implementación efectiva:</strong> Pasar de la teoría a la práctica.</li>
  <li><strong>Evaluación continua:</strong> Medir resultados y ajustar según sea necesario.</li>
</ul>

<p>Como se menciona en estudios recientes, la aplicación correcta de {keywords if keywords else 'estrategias adecuadas'} puede mejorar significativamente los resultados.</p>

<h2>Conclusión</h2>

<p>En resumen, {topic} representa una oportunidad invaluable para quienes buscan {objective}. Al adoptar un enfoque {tone}, es posible maximizar los beneficios y minimizar los obstáculos en el camino.</p>""",
        
        'email': f"""<p><strong>Asunto:</strong> Información importante sobre {topic}</p>

<p>Estimado/a [Nombre],</p>

<p>Espero que este mensaje le encuentre bien. Me pongo en contacto con usted para compartir información relevante sobre {topic}.</p>

<p>Recientemente, hemos observado que este tema ha cobrado especial relevancia en nuestro sector, y consideramos fundamental que nuestros {objective == 'vender' and 'clientes potenciales' or 'colaboradores'} estén al tanto de los últimos desarrollos.</p>

<p>Como parte de nuestro compromiso con {keywords if keywords else 'la excelencia y la información actualizada'}, queremos asegurarnos de que cuenta con todos los recursos necesarios para tomar decisiones informadas.</p>

<p>No dude en contactarnos si desea obtener más información o aclarar cualquier duda al respecto.</p>

<p>Un cordial saludo,</p>

<p>[Su nombre]<br>
[Su cargo]<br>
[Datos de contacto]</p>""",
        
        'instagram_post': f"""{topic.capitalize()} 📱✨

¿Sabías que {topic} puede transformar tu día a día? Descubre cómo implementarlo en tu rutina y obtén resultados sorprendentes.

{objective == 'informar' and 'Los expertos coinciden: dedicar tiempo a este tema marca la diferencia.' or '¡No esperes más para probarlo! Los resultados hablan por sí mismos.'}

{keywords and '#' + ' #'.join(keywords.replace(',', ' ').split()) or '#innovación #tendencias #lifestyle'}""",
        
        'facebook_post': f"""<p>🔍 <strong>{topic.upper()}: LO QUE DEBES SABER</strong> 🔍</p>

<p>Hoy queremos compartir contigo información valiosa sobre {topic} que seguramente te resultará útil.</p>

<p>¿Has pensado alguna vez en cómo {topic} afecta tu vida diaria? La mayoría de las personas no son conscientes de su impacto hasta que descubren sus beneficios.</p>

<p>👉 {objective.capitalize()} es nuestro objetivo, y por eso te invitamos a reflexionar: ¿Qué cambiaría en tu vida si implementaras estrategias relacionadas con {topic}?</p>

<p>Déjanos tu opinión en los comentarios. ¿Qué experiencia tienes con este tema?</p>

<p>{keywords and '#' + ' #'.join(keywords.replace(',', ' ').split()) or '#TipDelDía #Información #Comunidad'}</p>""",
        
        'twitter_post': f"""{topic.capitalize()} es fundamental para quienes buscan {objective}.

¿Tú qué opinas? ¿Has explorado este tema en profundidad?

{keywords and '#' + ' #'.join(keywords.replace(',', ' ').split()) or '#consejos #tendencias'}""",
        
        'product_short': f"""<p><strong>{topic.capitalize()}</strong> - La solución ideal para quienes buscan resultados excepcionales. Diseñado con un enfoque {tone}, este producto ofrece {keywords if keywords else 'calidad superior y rendimiento óptimo'}. Perfecto para {objective}.</p>""",
        
        'product_long': f"""<h2>{topic.capitalize()} - Revoluciona tu experiencia</h2>

<p>Presentamos nuestra solución integral diseñada específicamente para aquellos que valoran la excelencia y los resultados consistentes.</p>

<h3>Características principales:</h3>

<ul>
  <li><strong>Diseño innovador:</strong> Creado pensando en la experiencia del usuario.</li>
  <li><strong>Funcionalidad avanzada:</strong> Incorpora las últimas tecnologías del sector.</li>
  <li><strong>Durabilidad garantizada:</strong> Materiales de primera calidad que aseguran una larga vida útil.</li>
  <li><strong>Versatilidad sin igual:</strong> Adaptable a diferentes contextos y necesidades.</li>
</ul>

<p>Este producto ha sido desarrollado con un enfoque {tone}, asegurando que cada detalle contribuya a {objective}.</p>

<p>{keywords and 'Palabras clave que definen este producto: ' + keywords or 'Su rendimiento superior lo convierte en la elección preferida de profesionales y entusiastas por igual.'}</p>

<h3>¿Por qué elegirlo?</h3>

<p>La diferencia está en los detalles. A diferencia de otras opciones en el mercado, nuestro {topic} ofrece una experiencia completa que redefine los estándares del sector.</p>

<p><strong>¡Adquiéralo hoy y descubra la diferencia!</strong></p>"""
    }
    
    # Obtener el contenido de ejemplo según el tipo
    content = content_examples.get(content_type, f"Contenido de ejemplo para {topic}")
    
    # Si el formato es plain_text, eliminar etiquetas HTML
    if output_format == 'plain_text':
        import re
        content = re.sub(r'<[^>]*>', '', content)
    
    # Si el formato es markdown, convertir de HTML a markdown (simulado)
    elif output_format == 'markdown':
        content = content.replace('<h1>', '# ').replace('</h1>', '\n\n')
        content = content.replace('<h2>', '## ').replace('</h2>', '\n\n')
        content = content.replace('<h3>', '### ').replace('</h3>', '\n\n')
        content = content.replace('<p>', '').replace('</p>', '\n\n')
        content = content.replace('<strong>', '**').replace('</strong>', '**')
        content = content.replace('<ul>', '').replace('</ul>', '\n')
        content = content.replace('<li>', '* ').replace('</li>', '\n')
    
    # Añadir un pie indicando el proveedor usado (simulado)
    provider_info = {
        'openai': 'Generado con OpenAI GPT-4o',
        'anthropic': 'Generado con Anthropic Claude',
        'gemini': 'Generado con Google Gemini'
    }
    
    footer = f"\n\n---\n{provider_info.get(api_provider, 'Generado con IA')}"
    
    if output_format == 'html':
        footer = f"<hr><p><em>{provider_info.get(api_provider, 'Generado con IA')}</em></p>"
    
    return content + footer

def create_prompt(content_type, topic, tone, objective, keywords):
    """Crear un prompt optimizado según el tipo de contenido, tono y objetivo"""
    content_type_map = {
        'blog_post': 'artículo de blog',
        'email': 'email',
        'instagram_post': 'publicación para Instagram',
        'facebook_post': 'publicación para Facebook',
        'twitter_post': 'tweet para Twitter',
        'product_short': 'descripción corta de producto',
        'product_long': 'descripción larga de producto'
    }
    
    content_type_name = content_type_map.get(content_type, content_type)
    
    # Keywords section
    keywords_section = ""
    if keywords:
        keywords_section = f"Incluye las siguientes palabras clave: {keywords}. "
    
    # Build the prompt with detailed instructions based on content type
    prompt = f"""Crea un {content_type_name} sobre "{topic}" con un tono {tone} y con el objetivo de {objective}. {keywords_section}

Instrucciones específicas según el tipo de contenido:
"""

    # Add specific instructions based on content type
    if content_type == 'blog_post':
        prompt += """
- Incluye un título atractivo
- Escribe una introducción que enganche al lector
- Desarrolla el tema en secciones con subtítulos
- Incluye una conclusión
- Extensión recomendada: 800-1200 palabras
"""
    elif content_type == 'email':
        prompt += """
- Incluye una línea de asunto efectiva
- Comienza con un saludo personalizado
- Ve directo al punto en el primer párrafo
- Incluye una llamada a la acción clara
- Termina con una despedida profesional
- Extensión recomendada: 150-300 palabras
"""
    elif content_type == 'instagram_post':
        prompt += """
- Escribe un texto atractivo y conciso
- Incluye emojis relevantes
- Añade hashtags efectivos al final
- Incluye una llamada a la acción
- Extensión recomendada: 125-150 caracteres (sin contar hashtags)
"""
    elif content_type == 'facebook_post':
        prompt += """
- Escribe un contenido que genere engagement
- Haz preguntas para fomentar comentarios
- Incluye una imagen sugerida (descríbela)
- Extensión recomendada: 100-250 palabras
"""
    elif content_type == 'twitter_post':
        prompt += """
- Crea un tweet conciso y atractivo
- Incluye hashtags relevantes
- Mantén el conteo bajo 280 caracteres
- Considera incluir una pregunta o llamada a la acción
"""
    elif content_type == 'product_short':
        prompt += """
- Escribe una descripción concisa y atractiva
- Destaca los beneficios principales
- Usa lenguaje persuasivo
- Extensión recomendada: 50-100 palabras
"""
    elif content_type == 'product_long':
        prompt += """
- Comienza con un resumen atractivo del producto
- Describe las características detalladamente
- Explica los beneficios de cada característica
- Incluye especificaciones técnicas si es relevante
- Termina con una llamada a la acción
- Extensión recomendada: 300-500 palabras
"""

    return prompt

def generate_with_openai(prompt, output_format):
    """Generar contenido usando OpenAI API"""
    try:
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
        format_instruction = ""
        if output_format == 'html':
            format_instruction = "Formatea la respuesta en HTML válido, con las etiquetas apropiadas."
        elif output_format == 'markdown':
            format_instruction = "Formatea la respuesta en Markdown válido."
        
        full_prompt = f"{prompt}\n\n{format_instruction}"
        
        # The newest OpenAI model is "gpt-4o" which was released May 13, 2024
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Eres un experto en creación de contenido de alta calidad para marketing y comunicación."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        logging.error(f"Error con OpenAI API: {str(e)}")
        raise Exception(f"Error al generar contenido con OpenAI: {str(e)}")

def generate_with_anthropic(prompt, output_format):
    """Generar contenido usando Anthropic Claude API"""
    try:
        client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        
        format_instruction = ""
        if output_format == 'html':
            format_instruction = "Formatea la respuesta en HTML válido, con las etiquetas apropiadas."
        elif output_format == 'markdown':
            format_instruction = "Formatea la respuesta en Markdown válido."
        
        full_prompt = f"{prompt}\n\n{format_instruction}"
        
        # The newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
        # do not change this unless explicitly requested by the user
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            temperature=0.7,
            system="Eres un experto en creación de contenido de alta calidad para marketing y comunicación.",
            messages=[
                {"role": "user", "content": full_prompt}
            ]
        )
        
        return response.content[0].text
    
    except Exception as e:
        logging.error(f"Error con Anthropic API: {str(e)}")
        raise Exception(f"Error al generar contenido con Claude: {str(e)}")

def generate_with_gemini(prompt, output_format):
    """Generar contenido usando Google Gemini API"""
    try:
        # Configurar API key
        genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))
        
        format_instruction = ""
        if output_format == 'html':
            format_instruction = "Formatea la respuesta en HTML válido, con las etiquetas apropiadas."
        elif output_format == 'markdown':
            format_instruction = "Formatea la respuesta en Markdown válido."
        
        full_prompt = f"{prompt}\n\n{format_instruction}"
        
        # Use the Gemini model
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=2000,
            ),
        )
        
        return response.text
    
    except Exception as e:
        logging.error(f"Error con Gemini API: {str(e)}")
        raise Exception(f"Error al generar contenido con Gemini: {str(e)}")

@content_writer_bp.route('/history')
@login_required
def view_history():
    """Ver historial de contenidos generados"""
    # Implementar después
    return render_template('content_writer/history.html')