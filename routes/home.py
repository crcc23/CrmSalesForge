from flask import Blueprint, render_template, redirect, url_for

# Crear blueprint para la página de inicio
home_bp = Blueprint('home', __name__, url_prefix='')

@home_bp.route('/')
def index():
    """Página de inicio pública del SaaS"""
    return render_template('home/index.html')

@home_bp.route('/features')
def features():
    """Página de características del producto"""
    return redirect(url_for('home.index', _anchor='caracteristicas'))

@home_bp.route('/pricing')
def pricing():
    """Página de precios del producto"""
    return redirect(url_for('home.index', _anchor='precios'))

@home_bp.route('/testimonials')
def testimonials():
    """Página de testimonios de clientes"""
    return redirect(url_for('home.index', _anchor='testimonios'))

@home_bp.route('/contact')
def contact():
    """Página de contacto"""
    return redirect(url_for('home.index', _anchor='contacto'))