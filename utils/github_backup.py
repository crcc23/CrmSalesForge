import os
import requests
import base64
import json
import datetime
import logging
from models_github import GithubConfig
from app import db

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitHubBackup:
    """Clase para gestionar backups del código en GitHub"""
    
    def __init__(self, tenant_id, repo_name=None):
        """Inicializar con ID del tenant y nombre del repositorio opcional"""
        self.tenant_id = tenant_id
        self.repo_name = repo_name or f"crm-backup-{datetime.datetime.now().strftime('%Y%m%d')}"
        
        # Obtener configuración de GitHub
        self.config = GithubConfig.query.filter_by(tenant_id=tenant_id).first()
        if not self.config or not self.config.github_token:
            raise ValueError("No se ha encontrado una configuración válida de GitHub para este tenant")
        
        self.token = self.config.github_token
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.api_url = "https://api.github.com"
        
    def get_or_create_repository(self):
        """Obtener o crear un repositorio para el backup"""
        # Buscar si ya existe el repositorio
        repos_url = f"{self.api_url}/user/repos"
        response = requests.get(repos_url, headers=self.headers)
        response.raise_for_status()
        
        repos = response.json()
        for repo in repos:
            if repo['name'] == self.repo_name:
                logger.info(f"Repositorio encontrado: {repo['full_name']}")
                return repo
        
        # Si no existe, crear uno nuevo
        payload = {
            'name': self.repo_name,
            'description': f"Backup automático del CRM - {datetime.datetime.now().strftime('%Y-%m-%d')}",
            'private': True,
            'auto_init': True
        }
        
        response = requests.post(repos_url, headers=self.headers, json=payload)
        response.raise_for_status()
        
        repo = response.json()
        logger.info(f"Repositorio creado: {repo['full_name']}")
        return repo
    
    def list_project_files(self, ignore_dirs=None, ignore_files=None):
        """Listar archivos del proyecto para backup"""
        ignore_dirs = ignore_dirs or ['.git', '__pycache__', 'venv', 'env', 'node_modules', 'instance']
        ignore_files = ignore_files or ['.pyc', '.pyo', '.pyd', '.env', '.gitignore']
        
        project_files = []
        
        for root, dirs, files in os.walk('.'):
            # Excluir directorios ignorados
            dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith('.')]
            
            for file in files:
                # Comprobar si debemos ignorar este archivo
                if any(file.endswith(ext) for ext in ignore_files) or file.startswith('.'):
                    continue
                
                file_path = os.path.join(root, file)
                # Normalizar la ruta para GitHub (usar slash en vez de backslash)
                file_path = file_path.replace('\\', '/')
                # Quitar el ./ inicial si existe
                if file_path.startswith('./'):
                    file_path = file_path[2:]
                
                project_files.append(file_path)
        
        return project_files
    
    def get_file_content(self, repo, path, branch='main'):
        """Obtener contenido de un archivo en GitHub"""
        url = f"{self.api_url}/repos/{repo['full_name']}/contents/{path}?ref={branch}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        return None
    
    def create_or_update_file(self, repo, path, content, message=None, branch='main'):
        """Crear o actualizar un archivo en GitHub"""
        url = f"{self.api_url}/repos/{repo['full_name']}/contents/{path}"
        
        # Comprobar si el archivo ya existe
        file_data = self.get_file_content(repo, path, branch)
        
        # Codificar el contenido en base64
        content_bytes = content.encode('utf-8')
        encoded_content = base64.b64encode(content_bytes).decode('utf-8')
        
        commit_message = message or f"Actualización automática: {path}"
        
        if file_data:
            # Actualizar archivo existente
            payload = {
                'message': commit_message,
                'content': encoded_content,
                'sha': file_data['sha'],
                'branch': branch
            }
        else:
            # Crear nuevo archivo
            payload = {
                'message': commit_message,
                'content': encoded_content,
                'branch': branch
            }
        
        response = requests.put(url, headers=self.headers, json=payload)
        
        try:
            response.raise_for_status()
            logger.info(f"Archivo {path} {'actualizado' if file_data else 'creado'}")
            return True
        except Exception as e:
            logger.error(f"Error al {'actualizar' if file_data else 'crear'} {path}: {str(e)}")
            return False
    
    def backup_project(self):
        """Realizar backup completo del proyecto"""
        try:
            # Obtener o crear repositorio
            repo = self.get_or_create_repository()
            
            # Listar archivos del proyecto
            files = self.list_project_files()
            logger.info(f"Se encontraron {len(files)} archivos para backup")
            
            # Recorrer archivos y subirlos al repositorio
            success_count = 0
            for file_path in files:
                try:
                    # Leer contenido del archivo
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Crear o actualizar archivo en GitHub
                    if self.create_or_update_file(repo, file_path, content):
                        success_count += 1
                except Exception as e:
                    logger.error(f"Error procesando archivo {file_path}: {str(e)}")
            
            logger.info(f"Backup completado: {success_count}/{len(files)} archivos procesados correctamente")
            return {
                'status': 'success',
                'repository': repo['full_name'],
                'total_files': len(files),
                'successful_files': success_count,
                'url': repo['html_url']
            }
            
        except Exception as e:
            logger.error(f"Error durante el backup: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }

def create_backup(tenant_id, repo_name=None):
    """Función para crear un backup del proyecto en GitHub"""
    backup = GitHubBackup(tenant_id, repo_name)
    return backup.backup_project()