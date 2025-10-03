from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List
import httpx

from backend.database import get_supabase

router = APIRouter(prefix="/api/github", tags=["github"])


class CreateAnalysisRequest(BaseModel):
    repo_full_name: str
    session_type: str = 'exploration'
    analysis_focus: Optional[List[str]] = None


@router.get("/repositories")
async def get_repositories(
    authorization: str = Header(...),
    sync: bool = False
):
    """
    Get user's GitHub repositories
    Authorization header should contain: Bearer <supabase_access_token>
    """
    try:
        supabase = get_supabase()

        auth_header = authorization.replace('Bearer ', '')
        user_response = supabase.auth.get_user(auth_header)

        if not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid token")

        user_id = user_response.user.id
        user_metadata = user_response.user.user_metadata or {}
        provider_token = user_metadata.get('provider_token')

        if not provider_token:
            raise HTTPException(
                status_code=400,
                detail="No GitHub token found. Please sign in with GitHub."
            )

        if sync:
            await sync_repositories(user_id, provider_token)

        repos = supabase.table('github_repositories').select('*').eq(
            'auth_user_id', user_id
        ).order('stars', desc=True).execute()

        return repos.data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def sync_repositories(user_id: str, github_token: str):
    """Fetch repos from GitHub API and cache in database"""
    supabase = get_supabase()

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/user/repos",
            headers={
                "Authorization": f"Bearer {github_token}",
                "Accept": "application/vnd.github+json"
            },
            params={"per_page": 100, "sort": "updated"}
        )

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch repos")

        repos = response.json()

        for repo in repos:
            supabase.table('github_repositories').upsert({
                'auth_user_id': user_id,
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
                }
            }, on_conflict='auth_user_id,repo_full_name').execute()


@router.post("/analyze")
async def create_repo_analysis(
    request: CreateAnalysisRequest,
    authorization: str = Header(...)
):
    """Create a repository analysis session"""
    try:
        supabase = get_supabase()

        auth_header = authorization.replace('Bearer ', '')
        user_response = supabase.auth.get_user(auth_header)

        if not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid token")

        user_id = user_response.user.id
        user_metadata = user_response.user.user_metadata or {}
        provider_token = user_metadata.get('provider_token')

        if not provider_token:
            raise HTTPException(
                status_code=400,
                detail="No GitHub token found"
            )

        repo = supabase.table('github_repositories').select('*').eq(
            'auth_user_id', user_id
        ).eq('repo_full_name', request.repo_full_name).maybeSingle().execute()

        if not repo.data:
            raise HTTPException(status_code=404, detail="Repository not found. Sync repos first.")

        import uuid
        session_url = str(uuid.uuid4())

        session = supabase.table('repo_analysis_sessions').insert({
            'auth_user_id': user_id,
            'github_repository_id': repo.data['id'],
            'session_url': session_url,
            'session_type': request.session_type,
            'status': 'initializing',
            'analysis_focus': request.analysis_focus or []
        }).execute()

        from backend.services.github_service import GitHubService
        github_service = GitHubService()

        await github_service.analyze_repository_structure(
            session_id=session.data[0]['id'],
            repo_full_name=request.repo_full_name,
            access_token=provider_token,
            branch=repo.data['default_branch']
        )

        return {
            'session_url': session_url,
            'session_type': request.session_type,
            'status': 'analyzing'
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/{session_url}")
async def get_analysis(
    session_url: str,
    authorization: str = Header(...)
):
    """Get analysis results"""
    try:
        supabase = get_supabase()

        auth_header = authorization.replace('Bearer ', '')
        user_response = supabase.auth.get_user(auth_header)

        if not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid token")

        session = supabase.table('repo_analysis_sessions').select(
            '*, github_repositories(repo_full_name, primary_language)'
        ).eq('session_url', session_url).maybeSingle().execute()

        if not session.data:
            raise HTTPException(status_code=404, detail="Analysis session not found")

        explorations = supabase.table('code_explorations').select('*').eq(
            'repo_analysis_session_id', session.data['id']
        ).order('explored_at', desc=True).execute()

        return {
            'session': session.data,
            'explorations': explorations.data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explore/{session_url}")
async def explore_file(
    session_url: str,
    file_path: str,
    authorization: str = Header(...)
):
    """Explore a specific file in the repository"""
    try:
        supabase = get_supabase()

        auth_header = authorization.replace('Bearer ', '')
        user_response = supabase.auth.get_user(auth_header)

        if not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid token")

        user_metadata = user_response.user.user_metadata or {}
        provider_token = user_metadata.get('provider_token')

        session = supabase.table('repo_analysis_sessions').select(
            '*, github_repositories(repo_full_name, default_branch)'
        ).eq('session_url', session_url).maybeSingle().execute()

        if not session.data:
            raise HTTPException(status_code=404, detail="Session not found")

        repo = session.data['github_repositories']

        from backend.services.github_service import GitHubService
        github_service = GitHubService()

        exploration = await github_service.explore_file(
            session_id=session.data['id'],
            repo_full_name=repo['repo_full_name'],
            file_path=file_path,
            access_token=provider_token,
            branch=repo['default_branch']
        )

        return exploration

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
