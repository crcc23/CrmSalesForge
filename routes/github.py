from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from flask_login import login_required, current_user
from app import db
from models_github import GithubConfig, GithubRepository, GithubBranch, GithubCommit
from integrations.github_service import GitHubService
import os
import requests
import datetime
import json

# Create blueprint
github_bp = Blueprint('github', __name__)

@github_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    """GitHub integration dashboard"""
    # Get tenant ID from session
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        flash("Sesión inválida. Por favor, inicie sesión nuevamente.", "error")
        return redirect(url_for('auth.login'))
    
    # Get GitHub configuration for this tenant
    config = GithubConfig.query.filter_by(tenant_id=tenant_id).first()
    if not config:
        config = GithubConfig()
        config.tenant_id = tenant_id
        config.name = "GitHub Integration"
        db.session.add(config)
        db.session.commit()
    
    # Handle direct connection from index page
    if request.method == 'POST':
        token = request.form.get('github_token', '').strip()
        organization = request.form.get('organization', '').strip()
        
        if token:
            config.github_token = token
            config.organization = organization
            db.session.commit()
            
            # Test connection
            github_service = GitHubService(token=config.github_token)
            try:
                user_info = github_service.get_user_info()
                flash(f"Conexión con GitHub establecida correctamente como: {user_info.get('login')}", "success")
                
                # Sync some repositories automatically
                try:
                    repos = github_service.get_user_repositories()
                    # Only sync the first 3 to not overwhelm
                    for repo in repos[:3]:
                        github_service.sync_repository_to_db(tenant_id, repo['owner']['login'], repo['name'])
                    flash(f"Se sincronizaron {min(3, len(repos))} repositorios automáticamente.", "info")
                except Exception as e:
                    # Non-critical error, just log it
                    print(f"Error syncing repos: {str(e)}")
                    
            except Exception as e:
                flash(f"Error al conectar con GitHub: {str(e)}", "error")
    
    # Get GitHub repositories for this tenant
    repositories = GithubRepository.query.filter_by(tenant_id=tenant_id).all()
    
    return render_template('github/index.html', 
                          config=config, 
                          repositories=repositories,
                          github_connected=bool(config and config.github_token))

@github_bp.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    """Setup GitHub integration"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        flash("Sesión inválida. Por favor, inicie sesión nuevamente.", "error")
        return redirect(url_for('auth.login'))
    
    # Get or create GitHub configuration
    config = GithubConfig.query.filter_by(tenant_id=tenant_id).first()
    if not config:
        config = GithubConfig()
        config.tenant_id = tenant_id
        config.name = "GitHub Integration"
        db.session.add(config)
        db.session.commit()
    
    if request.method == 'POST':
        token = request.form.get('github_token', '').strip()
        organization = request.form.get('organization', '').strip()
        
        # Only update token if provided
        if token and not token.startswith('•'):
            config.github_token = token
        
        config.organization = organization
        config.name = request.form.get('name', 'GitHub Integration').strip()
        
        db.session.commit()
        
        # Test connection
        github_service = GitHubService(token=config.github_token)
        try:
            user_info = github_service.get_user_info()
            flash(f"Conexión con GitHub establecida correctamente como: {user_info.get('login')}", "success")
        except Exception as e:
            flash(f"Error al conectar con GitHub: {str(e)}", "error")
        
        return redirect(url_for('github.index'))
    
    # If GitHub token is already set, mask it for security
    if config.github_token:
        masked_token = '••••••••' + config.github_token[-4:] if len(config.github_token) > 4 else '••••••••'
    else:
        masked_token = ''
    
    return render_template('github/setup.html', 
                          config=config,
                          masked_token=masked_token)

@github_bp.route('/repositories')
@login_required
def repositories():
    """List GitHub repositories"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        flash("Sesión inválida. Por favor, inicie sesión nuevamente.", "error")
        return redirect(url_for('auth.login'))
    
    # Get GitHub configuration
    config = GithubConfig.query.filter_by(tenant_id=tenant_id).first()
    if not config or not config.github_token:
        flash("Configuración de GitHub incompleta. Por favor, configure primero su integración.", "warning")
        return redirect(url_for('github.setup'))
    
    # Get repositories
    github_service = GitHubService(token=config.github_token)
    try:
        user_repos = github_service.get_user_repositories()
        return render_template('github/repositories.html',
                              config=config,
                              repositories=user_repos)
    except Exception as e:
        flash(f"Error al obtener repositorios: {str(e)}", "error")
        return redirect(url_for('github.index'))

@github_bp.route('/repository/<owner>/<repo>')
@login_required
def repository_detail(owner, repo):
    """Show GitHub repository details"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        flash("Sesión inválida. Por favor, inicie sesión nuevamente.", "error")
        return redirect(url_for('auth.login'))
    
    # Get GitHub configuration
    config = GithubConfig.query.filter_by(tenant_id=tenant_id).first()
    if not config or not config.github_token:
        flash("Configuración de GitHub incompleta. Por favor, configure primero su integración.", "warning")
        return redirect(url_for('github.setup'))
    
    # Get repository details
    github_service = GitHubService(token=config.github_token)
    try:
        repo_data = github_service.get_repository(owner, repo)
        branches = github_service.get_branches(owner, repo)
        commits = github_service.get_commits(owner, repo)
        
        # Check if repository is already tracked in our database
        db_repo = GithubRepository.query.filter_by(tenant_id=tenant_id, full_name=f"{owner}/{repo}").first()
        
        return render_template('github/repository_detail.html',
                              config=config,
                              repository=repo_data,
                              branches=branches,
                              commits=commits,
                              is_tracked=bool(db_repo))
    except Exception as e:
        flash(f"Error al obtener detalles del repositorio: {str(e)}", "error")
        return redirect(url_for('github.repositories'))

@github_bp.route('/repository/track/<owner>/<repo>', methods=['POST'])
@login_required
def track_repository(owner, repo):
    """Start tracking a GitHub repository"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        flash("Sesión inválida. Por favor, inicie sesión nuevamente.", "error")
        return redirect(url_for('auth.login'))
    
    # Get GitHub configuration
    config = GithubConfig.query.filter_by(tenant_id=tenant_id).first()
    if not config or not config.github_token:
        flash("Configuración de GitHub incompleta. Por favor, configure primero su integración.", "warning")
        return redirect(url_for('github.setup'))
    
    # Track repository
    github_service = GitHubService(token=config.github_token)
    try:
        repository = github_service.sync_repository_to_db(tenant_id, owner, repo)
        flash(f"Repositorio '{repository.name}' agregado correctamente.", "success")
    except Exception as e:
        flash(f"Error al agregar repositorio: {str(e)}", "error")
    
    return redirect(url_for('github.index'))

@github_bp.route('/repository/untrack/<int:repo_id>', methods=['POST'])
@login_required
def untrack_repository(repo_id):
    """Stop tracking a GitHub repository"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        flash("Sesión inválida. Por favor, inicie sesión nuevamente.", "error")
        return redirect(url_for('auth.login'))
    
    # Get repository
    repository = GithubRepository.query.filter_by(id=repo_id, tenant_id=tenant_id).first()
    if not repository:
        flash("Repositorio no encontrado.", "error")
        return redirect(url_for('github.index'))
    
    # Delete repository (cascade will delete branches and commits)
    repo_name = repository.name
    db.session.delete(repository)
    db.session.commit()
    
    flash(f"Repositorio '{repo_name}' eliminado correctamente.", "success")
    return redirect(url_for('github.index'))

@github_bp.route('/create_repository', methods=['GET', 'POST'])
@login_required
def create_repository():
    """Create a new GitHub repository"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        flash("Sesión inválida. Por favor, inicie sesión nuevamente.", "error")
        return redirect(url_for('auth.login'))
    
    # Get GitHub configuration
    config = GithubConfig.query.filter_by(tenant_id=tenant_id).first()
    if not config or not config.github_token:
        flash("Configuración de GitHub incompleta. Por favor, configure primero su integración.", "warning")
        return redirect(url_for('github.setup'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        private = request.form.get('private') == 'on'
        
        if not name:
            flash("El nombre del repositorio es obligatorio.", "error")
            return redirect(url_for('github.create_repository'))
        
        # Create repository
        github_service = GitHubService(token=config.github_token)
        try:
            repo_data = github_service.create_repository(name, description, private)
            # Sync to database
            repository = github_service.sync_repository_to_db(tenant_id, repo_data['owner']['login'], repo_data['name'])
            flash(f"Repositorio '{repository.name}' creado y agregado correctamente.", "success")
            return redirect(url_for('github.index'))
        except Exception as e:
            flash(f"Error al crear repositorio: {str(e)}", "error")
            return redirect(url_for('github.create_repository'))
    
    return render_template('github/create_repository.html', config=config)

@github_bp.route('/branches/<int:repo_id>')
@login_required
def branches(repo_id):
    """List branches for a repository"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        flash("Sesión inválida. Por favor, inicie sesión nuevamente.", "error")
        return redirect(url_for('auth.login'))
    
    # Get repository
    repository = GithubRepository.query.filter_by(id=repo_id, tenant_id=tenant_id).first()
    if not repository:
        flash("Repositorio no encontrado.", "error")
        return redirect(url_for('github.index'))
    
    # Get branches
    branches = GithubBranch.query.filter_by(repository_id=repo_id).all()
    
    return render_template('github/branches.html', 
                          repository=repository,
                          branches=branches)

@github_bp.route('/commits/<int:repo_id>/<branch>')
@login_required
def commits(repo_id, branch):
    """List commits for a repository branch"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        flash("Sesión inválida. Por favor, inicie sesión nuevamente.", "error")
        return redirect(url_for('auth.login'))
    
    # Get repository
    repository = GithubRepository.query.filter_by(id=repo_id, tenant_id=tenant_id).first()
    if not repository:
        flash("Repositorio no encontrado.", "error")
        return redirect(url_for('github.index'))
    
    # Get GitHub configuration
    config = GithubConfig.query.filter_by(tenant_id=tenant_id).first()
    if not config or not config.github_token:
        flash("Configuración de GitHub incompleta. Por favor, configure primero su integración.", "warning")
        return redirect(url_for('github.setup'))
    
    # Sync commits
    github_service = GitHubService(token=config.github_token)
    try:
        owner, repo = repository.full_name.split('/')
        github_service.sync_commits_to_db(tenant_id, repo_id, owner, repo, branch)
    except Exception as e:
        flash(f"Error al sincronizar commits: {str(e)}", "warning")
    
    # Get commits
    commits = GithubCommit.query.filter_by(repository_id=repo_id).order_by(GithubCommit.commit_date.desc()).all()
    
    return render_template('github/commits.html', 
                          repository=repository,
                          branch=branch,
                          commits=commits)

@github_bp.route('/sync/<int:repo_id>', methods=['POST'])
@login_required
def sync_repository(repo_id):
    """Sync repository data with GitHub"""
    tenant_id = session.get('tenant_id')
    if not tenant_id:
        flash("Sesión inválida. Por favor, inicie sesión nuevamente.", "error")
        return redirect(url_for('auth.login'))
    
    # Get repository
    repository = GithubRepository.query.filter_by(id=repo_id, tenant_id=tenant_id).first()
    if not repository:
        flash("Repositorio no encontrado.", "error")
        return redirect(url_for('github.index'))
    
    # Get GitHub configuration
    config = GithubConfig.query.filter_by(tenant_id=tenant_id).first()
    if not config or not config.github_token:
        flash("Configuración de GitHub incompleta. Por favor, configure primero su integración.", "warning")
        return redirect(url_for('github.setup'))
    
    # Sync repository
    github_service = GitHubService(token=config.github_token)
    try:
        owner, repo = repository.full_name.split('/')
        github_service.sync_repository_to_db(tenant_id, owner, repo)
        flash(f"Repositorio '{repository.name}' sincronizado correctamente.", "success")
    except Exception as e:
        flash(f"Error al sincronizar repositorio: {str(e)}", "error")
    
    return redirect(url_for('github.index'))