import os
import requests
from datetime import datetime
from app import db
from models import GithubRepository, GithubBranch, GithubCommit

class GitHubService:
    """Service to interact with GitHub API"""
    
    def __init__(self, token=None):
        """Initialize with GitHub token"""
        self.token = token or os.environ.get('GITHUB_TOKEN')
        self.api_url = "https://api.github.com"
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
    
    def get_user_info(self):
        """Get authenticated user info"""
        response = requests.get(f"{self.api_url}/user", headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_user_repositories(self):
        """Get repositories for authenticated user"""
        response = requests.get(f"{self.api_url}/user/repos", headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def search_repositories(self, query):
        """Search repositories by query"""
        params = {'q': query}
        response = requests.get(f"{self.api_url}/search/repositories", 
                               headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_repository(self, owner, repo):
        """Get repository details"""
        response = requests.get(f"{self.api_url}/repos/{owner}/{repo}", 
                               headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_branches(self, owner, repo):
        """Get branches for a repository"""
        response = requests.get(f"{self.api_url}/repos/{owner}/{repo}/branches", 
                               headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_commits(self, owner, repo, branch='main', per_page=10):
        """Get commits for a repository branch"""
        params = {'sha': branch, 'per_page': per_page}
        response = requests.get(f"{self.api_url}/repos/{owner}/{repo}/commits", 
                               headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def create_repository(self, name, description=None, private=True):
        """Create a new repository"""
        payload = {
            'name': name,
            'description': description,
            'private': private,
            'auto_init': True
        }
        response = requests.post(f"{self.api_url}/user/repos", 
                                headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def create_file(self, owner, repo, path, content, message, branch='main'):
        """Create a file in a repository"""
        import base64
        content_encoded = base64.b64encode(content.encode()).decode()
        payload = {
            'message': message,
            'content': content_encoded,
            'branch': branch
        }
        response = requests.put(f"{self.api_url}/repos/{owner}/{repo}/contents/{path}", 
                               headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def create_branch(self, owner, repo, branch_name, source_branch='main'):
        """Create a new branch in a repository"""
        # Get the SHA of the source branch
        response = requests.get(f"{self.api_url}/repos/{owner}/{repo}/git/refs/heads/{source_branch}", 
                               headers=self.headers)
        response.raise_for_status()
        sha = response.json()['object']['sha']
        
        # Create the new branch
        payload = {
            'ref': f'refs/heads/{branch_name}',
            'sha': sha
        }
        response = requests.post(f"{self.api_url}/repos/{owner}/{repo}/git/refs", 
                                headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def sync_repository_to_db(self, tenant_id, owner, repo_name):
        """Sync repository data to database"""
        # Get repository info
        repo_data = self.get_repository(owner, repo_name)
        
        # Check if repository exists in database
        repository = GithubRepository.query.filter_by(
            tenant_id=tenant_id,
            full_name=repo_data['full_name']
        ).first()
        
        # If not exists, create new record
        if not repository:
            repository = GithubRepository()
            repository.tenant_id = tenant_id
        
        # Update repository data
        repository.github_id = repo_data['id']
        repository.name = repo_data['name']
        repository.full_name = repo_data['full_name']
        repository.description = repo_data['description']
        repository.private = repo_data['private']
        repository.html_url = repo_data['html_url']
        repository.api_url = repo_data['url']
        repository.default_branch = repo_data['default_branch']
        repository.created_at = datetime.strptime(repo_data['created_at'], "%Y-%m-%dT%H:%M:%SZ")
        repository.updated_at = datetime.strptime(repo_data['updated_at'], "%Y-%m-%dT%H:%M:%SZ")
        
        db.session.add(repository)
        db.session.commit()
        
        # Sync branches
        self.sync_branches_to_db(tenant_id, repository.id, owner, repo_name)
        
        # Sync commits for default branch
        self.sync_commits_to_db(tenant_id, repository.id, owner, repo_name, repository.default_branch)
        
        return repository
    
    def sync_branches_to_db(self, tenant_id, repository_id, owner, repo_name):
        """Sync repository branches to database"""
        # Get branches
        branches_data = self.get_branches(owner, repo_name)
        
        # Create/update branch records
        for branch_data in branches_data:
            branch = GithubBranch.query.filter_by(
                repository_id=repository_id,
                name=branch_data['name']
            ).first()
            
            if not branch:
                branch = GithubBranch()
                branch.repository_id = repository_id
                branch.tenant_id = tenant_id
            
            branch.name = branch_data['name']
            branch.commit_sha = branch_data['commit']['sha']
            
            db.session.add(branch)
        
        db.session.commit()
        
        # Delete branches that no longer exist
        existing_branch_names = [b['name'] for b in branches_data]
        branches_to_delete = GithubBranch.query.filter(
            GithubBranch.repository_id == repository_id,
            ~GithubBranch.name.in_(existing_branch_names)
        ).all()
        
        for branch in branches_to_delete:
            db.session.delete(branch)
        
        db.session.commit()
    
    def sync_commits_to_db(self, tenant_id, repository_id, owner, repo_name, branch='main', limit=20):
        """Sync repository commits to database"""
        # Get commits
        commits_data = self.get_commits(owner, repo_name, branch, per_page=limit)
        
        # Create/update commit records
        for commit_data in commits_data:
            commit = GithubCommit.query.filter_by(
                repository_id=repository_id,
                sha=commit_data['sha']
            ).first()
            
            if not commit:
                commit = GithubCommit()
                commit.repository_id = repository_id
                commit.tenant_id = tenant_id
            
            commit.sha = commit_data['sha']
            commit.message = commit_data['commit']['message']
            commit.author_name = commit_data['commit']['author']['name']
            commit.author_email = commit_data['commit']['author']['email']
            commit.commit_date = datetime.strptime(commit_data['commit']['author']['date'], "%Y-%m-%dT%H:%M:%SZ")
            commit.html_url = commit_data['html_url']
            
            db.session.add(commit)
        
        db.session.commit()