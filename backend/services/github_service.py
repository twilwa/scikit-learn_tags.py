from typing import Dict, List, Optional
import httpx
from datetime import datetime
import base64
import uuid

from backend.database import get_supabase


class GitHubService:
    def __init__(self):
        self.supabase = get_supabase()
        self.github_api_base = "https://api.github.com"

    async def exchange_code_for_token(
        self,
        code: str,
        client_id: str,
        client_secret: str
    ) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code
                }
            )
            return response.json()

    async def get_github_user(self, access_token: str) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.github_api_base}/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json"
                }
            )
            return response.json()

    async def save_github_connection(
        self,
        user_profile_id: str,
        github_user_data: Dict,
        access_token: str,
        refresh_token: Optional[str] = None
    ) -> Dict:
        result = self.supabase.table('github_connections').upsert({
            'user_profile_id': user_profile_id,
            'github_user_id': str(github_user_data['id']),
            'github_username': github_user_data['login'],
            'access_token': access_token,
            'refresh_token': refresh_token,
            'avatar_url': github_user_data.get('avatar_url'),
            'last_used': datetime.utcnow().isoformat()
        }, on_conflict='user_profile_id').execute()

        return result.data[0]

    async def get_user_repositories(
        self,
        github_connection_id: str,
        access_token: str,
        sync: bool = True
    ) -> List[Dict]:
        if sync:
            await self._sync_repositories(github_connection_id, access_token)

        result = self.supabase.table('github_repositories').select('*').eq(
            'github_connection_id', github_connection_id
        ).order('stars', desc=True).execute()

        return result.data

    async def _sync_repositories(self, github_connection_id: str, access_token: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.github_api_base}/user/repos",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json"
                },
                params={"per_page": 100, "sort": "updated"}
            )

            repos = response.json()

            for repo in repos:
                self.supabase.table('github_repositories').upsert({
                    'github_connection_id': github_connection_id,
                    'repo_full_name': repo['full_name'],
                    'repo_url': repo['html_url'],
                    'default_branch': repo.get('default_branch', 'main'),
                    'primary_language': repo.get('language'),
                    'stars': repo.get('stargazers_count', 0),
                    'forks': repo.get('forks_count', 0),
                    'open_issues': repo.get('open_issues_count', 0),
                    'size_kb': repo.get('size', 0),
                    'metadata': {
                        'description': repo.get('description'),
                        'topics': repo.get('topics', []),
                        'private': repo.get('private', False)
                    },
                    'synced_at': datetime.utcnow().isoformat()
                }, on_conflict='github_connection_id,repo_full_name').execute()

    async def get_repository_tree(
        self,
        access_token: str,
        repo_full_name: str,
        branch: str = 'main'
    ) -> List[Dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.github_api_base}/repos/{repo_full_name}/git/trees/{branch}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json"
                },
                params={"recursive": "1"}
            )

            data = response.json()
            return data.get('tree', [])

    async def get_file_content(
        self,
        access_token: str,
        repo_full_name: str,
        file_path: str,
        branch: str = 'main'
    ) -> Optional[str]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.github_api_base}/repos/{repo_full_name}/contents/{file_path}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json"
                },
                params={"ref": branch}
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('encoding') == 'base64':
                    content = base64.b64decode(data['content']).decode('utf-8')
                    return content

            return None

    async def create_analysis_session(
        self,
        user_profile_id: str,
        github_repository_id: str,
        session_type: str,
        analysis_focus: Optional[List[str]] = None
    ) -> Dict:
        session_url = str(uuid.uuid4())

        result = self.supabase.table('repo_analysis_sessions').insert({
            'user_profile_id': user_profile_id,
            'github_repository_id': github_repository_id,
            'session_url': session_url,
            'session_type': session_type,
            'status': 'initializing',
            'analysis_focus': analysis_focus or []
        }).execute()

        return result.data[0]

    async def analyze_repository_structure(
        self,
        session_id: str,
        repo_full_name: str,
        access_token: str,
        branch: str = 'main'
    ):
        self.supabase.table('repo_analysis_sessions').update({
            'status': 'analyzing'
        }).eq('id', session_id).execute()

        tree = await self.get_repository_tree(access_token, repo_full_name, branch)

        code_files = [
            f for f in tree
            if f['type'] == 'blob' and self._is_code_file(f['path'])
        ]

        languages = {}
        file_count = 0
        total_size = 0

        for file_item in code_files[:100]:
            file_path = file_item['path']
            file_type = self._get_file_type(file_path)

            if file_type:
                languages[file_type] = languages.get(file_type, 0) + 1
                file_count += 1
                total_size += file_item.get('size', 0)

        findings = {
            'total_files': len(tree),
            'code_files': file_count,
            'total_size_bytes': total_size,
            'languages': languages,
            'structure': self._analyze_directory_structure(tree)
        }

        self.supabase.table('repo_analysis_sessions').update({
            'status': 'completed',
            'findings': findings,
            'completed_at': datetime.utcnow().isoformat()
        }).eq('id', session_id).execute()

        return findings

    def _is_code_file(self, path: str) -> bool:
        code_extensions = [
            '.js', '.ts', '.jsx', '.tsx', '.py', '.rb', '.go', '.rs',
            '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.php', '.swift',
            '.kt', '.scala', '.clj', '.ex', '.exs', '.erl', '.hs', '.ml'
        ]
        return any(path.endswith(ext) for ext in code_extensions)

    def _get_file_type(self, path: str) -> Optional[str]:
        ext_map = {
            '.js': 'JavaScript', '.ts': 'TypeScript', '.jsx': 'React',
            '.tsx': 'React/TypeScript', '.py': 'Python', '.rb': 'Ruby',
            '.go': 'Go', '.rs': 'Rust', '.java': 'Java', '.c': 'C',
            '.cpp': 'C++', '.cs': 'C#', '.php': 'PHP', '.swift': 'Swift',
            '.kt': 'Kotlin', '.scala': 'Scala'
        }

        for ext, lang in ext_map.items():
            if path.endswith(ext):
                return lang

        return None

    def _analyze_directory_structure(self, tree: List[Dict]) -> Dict:
        dirs = set()
        for item in tree:
            if '/' in item['path']:
                top_level = item['path'].split('/')[0]
                dirs.add(top_level)

        common_patterns = {
            'src': 'Source code',
            'lib': 'Libraries',
            'test': 'Tests',
            'tests': 'Tests',
            'docs': 'Documentation',
            'examples': 'Examples',
            'scripts': 'Scripts',
            'public': 'Public assets',
            'dist': 'Distribution',
            'build': 'Build output'
        }

        structure = {}
        for dir_name in dirs:
            structure[dir_name] = common_patterns.get(dir_name, 'Unknown')

        return structure

    async def explore_file(
        self,
        session_id: str,
        repo_full_name: str,
        file_path: str,
        access_token: str,
        branch: str = 'main'
    ) -> Dict:
        content = await self.get_file_content(access_token, repo_full_name, file_path, branch)

        if not content:
            return {'error': 'Failed to fetch file content'}

        file_type = self._get_file_type(file_path)
        lines_of_code = len(content.split('\n'))

        result = self.supabase.table('code_explorations').insert({
            'repo_analysis_session_id': session_id,
            'file_path': file_path,
            'file_content': content,
            'file_type': file_path.split('.')[-1],
            'language': file_type,
            'lines_of_code': lines_of_code
        }).execute()

        return result.data[0]
