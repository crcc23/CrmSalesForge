from app import db
import datetime

# GitHub Integration Models
class GithubConfig(db.Model):
    """Configuration for GitHub API integration"""
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    name = db.Column(db.String(100), default='GitHub Integration')
    is_active = db.Column(db.Boolean, default=True)
    github_token = db.Column(db.String(255))
    organization = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    tenant = db.relationship('Tenant', backref='github_configs')
    
    def connect(self):
        """Connect to GitHub API"""
        if not self.github_token:
            return False, "Missing GitHub token"
        
        try:
            import requests
            
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get('https://api.github.com/user', headers=headers)
            response.raise_for_status()
            user_data = response.json()
            
            return True, f"Connected to GitHub as: {user_data.get('login')}"
        except Exception as e:
            return False, f"Failed to connect to GitHub: {str(e)}"
    
    def to_dict(self):
        """Convert to dictionary for API"""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'name': self.name,
            'is_active': self.is_active,
            'organization': self.organization,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class GithubRepository(db.Model):
    """GitHub Repository model"""
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    github_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    private = db.Column(db.Boolean, default=True)
    html_url = db.Column(db.String(255))
    api_url = db.Column(db.String(255))
    default_branch = db.Column(db.String(100), default='main')
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    local_created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    local_updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    tenant = db.relationship('Tenant', backref='github_repositories')
    branches = db.relationship('GithubBranch', backref='repository', cascade='all, delete-orphan')
    commits = db.relationship('GithubCommit', backref='repository', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert to dictionary for API"""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'github_id': self.github_id,
            'name': self.name,
            'full_name': self.full_name,
            'description': self.description,
            'private': self.private,
            'html_url': self.html_url,
            'default_branch': self.default_branch,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class GithubBranch(db.Model):
    """GitHub Branch model"""
    id = db.Column(db.Integer, primary_key=True)
    repository_id = db.Column(db.Integer, db.ForeignKey('github_repository.id'), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    commit_sha = db.Column(db.String(40))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    tenant = db.relationship('Tenant', backref='github_branches')
    
    def to_dict(self):
        """Convert to dictionary for API"""
        return {
            'id': self.id,
            'repository_id': self.repository_id,
            'tenant_id': self.tenant_id,
            'name': self.name,
            'commit_sha': self.commit_sha,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class GithubCommit(db.Model):
    """GitHub Commit model"""
    id = db.Column(db.Integer, primary_key=True)
    repository_id = db.Column(db.Integer, db.ForeignKey('github_repository.id'), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    sha = db.Column(db.String(40), nullable=False)
    message = db.Column(db.Text)
    author_name = db.Column(db.String(100))
    author_email = db.Column(db.String(120))
    commit_date = db.Column(db.DateTime)
    html_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    tenant = db.relationship('Tenant', backref='github_commits')
    
    def to_dict(self):
        """Convert to dictionary for API"""
        return {
            'id': self.id,
            'repository_id': self.repository_id,
            'tenant_id': self.tenant_id,
            'sha': self.sha,
            'message': self.message,
            'author_name': self.author_name,
            'author_email': self.author_email,
            'commit_date': self.commit_date.isoformat() if self.commit_date else None,
            'html_url': self.html_url,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }