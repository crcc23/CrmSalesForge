from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_required, current_user
from app import db
from models import WebScrapingTask, WebScrapingResult, User, Tenant, SubscriptionPlan
from utils.decorators import tenant_required
from integrations.web_scraper import get_website_text_content
import datetime

# Create blueprint
scraping = Blueprint('scraping', __name__)

@scraping.route('/web-scraping')
@login_required
@tenant_required
def list_tasks():
    """Lista todas las tareas de web scraping"""
    tenant_id = session.get('tenant_id')
    
    # Verificar que el tenant tiene acceso a la funcionalidad
    tenant = Tenant.query.get(tenant_id)
    subscription = SubscriptionPlan.query.get(tenant.subscription_plan_id)
    
    if not subscription.includes_web_scraping:
        flash('Tu plan de suscripción no incluye la funcionalidad de web scraping.', 'warning')
        return redirect(url_for('dashboard.home'))
    
    # Obtener tareas
    tasks = WebScrapingTask.query.filter_by(tenant_id=tenant_id).order_by(WebScrapingTask.created_at.desc()).all()
    
    return render_template('scraping/tasks.html', 
                          tasks=tasks)

@scraping.route('/web-scraping/new', methods=['GET', 'POST'])
@login_required
@tenant_required
def new_task():
    """Crear una nueva tarea de web scraping"""
    tenant_id = session.get('tenant_id')
    
    # Verificar que el tenant tiene acceso a la funcionalidad
    tenant = Tenant.query.get(tenant_id)
    subscription = SubscriptionPlan.query.get(tenant.subscription_plan_id)
    
    if not subscription.includes_web_scraping:
        flash('Tu plan de suscripción no incluye la funcionalidad de web scraping.', 'warning')
        return redirect(url_for('dashboard.home'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        url = request.form.get('url')
        frequency = request.form.get('frequency')
        
        if not name or not url:
            flash('Por favor completa todos los campos requeridos.', 'danger')
            return redirect(url_for('scraping.new_task'))
        
        # Crear nueva tarea
        task = WebScrapingTask(
            tenant_id=tenant_id,
            user_id=current_user.id,
            name=name,
            url=url,
            frequency=frequency,
            status='Pending'
        )
        
        db.session.add(task)
        db.session.commit()
        
        flash('Tarea de web scraping creada con éxito.', 'success')
        return redirect(url_for('scraping.list_tasks'))
    
    return render_template('scraping/task_form.html', task=None)

@scraping.route('/web-scraping/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
@tenant_required
def edit_task(task_id):
    """Editar una tarea de web scraping existente"""
    tenant_id = session.get('tenant_id')
    
    task = WebScrapingTask.query.filter_by(id=task_id, tenant_id=tenant_id).first()
    
    if not task:
        flash('Tarea no encontrada.', 'danger')
        return redirect(url_for('scraping.list_tasks'))
    
    if request.method == 'POST':
        task.name = request.form.get('name')
        task.url = request.form.get('url')
        task.frequency = request.form.get('frequency')
        task.updated_at = datetime.datetime.utcnow()
        
        db.session.commit()
        
        flash('Tarea de web scraping actualizada con éxito.', 'success')
        return redirect(url_for('scraping.list_tasks'))
    
    return render_template('scraping/task_form.html', task=task)

@scraping.route('/web-scraping/delete/<int:task_id>', methods=['POST'])
@login_required
@tenant_required
def delete_task(task_id):
    """Eliminar una tarea de web scraping"""
    tenant_id = session.get('tenant_id')
    
    task = WebScrapingTask.query.filter_by(id=task_id, tenant_id=tenant_id).first()
    
    if not task:
        flash('Tarea no encontrada.', 'danger')
        return redirect(url_for('scraping.list_tasks'))
    
    # Eliminar resultados asociados
    WebScrapingResult.query.filter_by(task_id=task.id).delete()
    
    # Eliminar tarea
    db.session.delete(task)
    db.session.commit()
    
    flash('Tarea de web scraping eliminada con éxito.', 'success')
    return redirect(url_for('scraping.list_tasks'))

@scraping.route('/web-scraping/execute/<int:task_id>', methods=['POST'])
@login_required
@tenant_required
def execute_task(task_id):
    """Ejecutar una tarea de web scraping inmediatamente"""
    tenant_id = session.get('tenant_id')
    
    task = WebScrapingTask.query.filter_by(id=task_id, tenant_id=tenant_id).first()
    
    if not task:
        flash('Tarea no encontrada.', 'danger')
        return redirect(url_for('scraping.list_tasks'))
    
    # Actualizar estado
    task.status = 'Running'
    db.session.commit()
    
    try:
        # Ejecutar scraping
        content = get_website_text_content(task.url)
        
        # Crear resumen simple (primeros 200 caracteres)
        summary = content[:200] + '...' if len(content) > 200 else content
        
        # Guardar resultado
        result = WebScrapingResult(
            task_id=task.id,
            status='Completed',
            content=content,
            summary=summary
        )
        
        # Actualizar tarea
        task.status = 'Completed'
        task.last_run = datetime.datetime.utcnow()
        
        db.session.add(result)
        db.session.commit()
        
        flash('Web scraping ejecutado con éxito.', 'success')
    except Exception as e:
        # Guardar error
        result = WebScrapingResult(
            task_id=task.id,
            status='Failed',
            error=str(e)
        )
        
        # Actualizar tarea
        task.status = 'Failed'
        task.last_run = datetime.datetime.utcnow()
        
        db.session.add(result)
        db.session.commit()
        
        flash(f'Error al ejecutar web scraping: {str(e)}', 'danger')
    
    return redirect(url_for('scraping.view_task', task_id=task.id))

@scraping.route('/web-scraping/view/<int:task_id>')
@login_required
@tenant_required
def view_task(task_id):
    """Ver detalles de una tarea y sus resultados"""
    tenant_id = session.get('tenant_id')
    
    task = WebScrapingTask.query.filter_by(id=task_id, tenant_id=tenant_id).first()
    
    if not task:
        flash('Tarea no encontrada.', 'danger')
        return redirect(url_for('scraping.list_tasks'))
    
    # Obtener resultados ordenados por fecha (más recientes primero)
    results = WebScrapingResult.query.filter_by(task_id=task.id).order_by(WebScrapingResult.execution_date.desc()).all()
    
    return render_template('scraping/task_view.html', task=task, results=results)

@scraping.route('/web-scraping/result/<int:result_id>')
@login_required
@tenant_required
def view_result(result_id):
    """Ver un resultado específico de web scraping"""
    tenant_id = session.get('tenant_id')
    
    result = WebScrapingResult.query.join(WebScrapingTask).filter(
        WebScrapingResult.id == result_id,
        WebScrapingTask.tenant_id == tenant_id
    ).first()
    
    if not result:
        flash('Resultado no encontrado.', 'danger')
        return redirect(url_for('scraping.list_tasks'))
    
    return render_template('scraping/result_view.html', result=result)