from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional, List
import os

from backend.services.github_service import GitHubService
from backend.database import get_supabase

router = APIRouter(prefix="/api/github", tags=["github"])

github_service = GitHubService()


class GitHubAuthRequest(BaseModel):
    code: str


class CreateAnalysisRequest(BaseModel):
    repo_full_name: str
    session_type: str = 'exploration'
    analysis_focus: Optional[List[str]] = None


@router.get("/auth/login")
async def github_login():
    client_id = os.getenv('GITHUB_CLIENT_ID', 'not_configured')
    redirect_uri = os.getenv('GITHUB_REDIRECT_URI', 'http://localhost:8000/api/github/auth/callback')

    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope=repo,read:user"
    )

    return RedirectResponse(url=github_auth_url)


@router.get("/auth/callback")
async def github_callback(code: str):
    try:
        client_id = os.getenv('GITHUB_CLIENT_ID')
        client_secret = os.getenv('GITHUB_CLIENT_SECRET')

        if not client_id or not client_secret:
            raise HTTPException(
                status_code=500,
                detail="GitHub OAuth not configured. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET"
            )

        token_data = await github_service.exchange_code_for_token(
            code=code,
            client_id=client_id,
            client_secret=client_secret
        )

        if 'error' in token_data:
            raise HTTPException(status_code=400, detail=token_data['error_description'])

        access_token = token_data['access_token']

        github_user = await github_service.get_github_user(access_token)

        supabase = get_supabase()
        profile = supabase.table('user_profiles').select('id').eq(
            'username', github_user['login']
        ).maybeSingle().execute()

        if not profile.data:
            new_profile = supabase.table('user_profiles').insert({
                'username': github_user['login'],
                'avatar_url': github_user.get('avatar_url')
            }).execute()
            user_profile_id = new_profile.data[0]['id']
        else:
            user_profile_id = profile.data['id']

        await github_service.save_github_connection(
            user_profile_id=user_profile_id,
            github_user_data=github_user,
            access_token=access_token,
            refresh_token=token_data.get('refresh_token')
        )

        return RedirectResponse(url=f"/?github_connected=true&username={github_user['login']}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connection")
async def get_github_connection(user_profile_id: str):
    try:
        supabase = get_supabase()

        connection = supabase.table('github_connections').select('*').eq(
            'user_profile_id', user_profile_id
        ).maybeSingle().execute()

        if not connection.data:
            return {'connected': False}

        return {
            'connected': True,
            'github_username': connection.data['github_username'],
            'avatar_url': connection.data['avatar_url'],
            'connected_at': connection.data['connected_at']
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repositories")
async def get_repositories(
    user_profile_id: str,
    sync: bool = Query(default=False)
):
    try:
        supabase = get_supabase()

        connection = supabase.table('github_connections').select('*').eq(
            'user_profile_id', user_profile_id
        ).maybeSingle().execute()

        if not connection.data:
            raise HTTPException(status_code=404, detail="GitHub not connected")

        repos = await github_service.get_user_repositories(
            github_connection_id=connection.data['id'],
            access_token=connection.data['access_token'],
            sync=sync
        )

        return repos

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def create_repo_analysis(
    user_profile_id: str,
    request: CreateAnalysisRequest
):
    try:
        supabase = get_supabase()

        connection = supabase.table('github_connections').select('*').eq(
            'user_profile_id', user_profile_id
        ).maybeSingle().execute()

        if not connection.data:
            raise HTTPException(status_code=404, detail="GitHub not connected")

        repo = supabase.table('github_repositories').select('*').eq(
            'github_connection_id', connection.data['id']
        ).eq('repo_full_name', request.repo_full_name).maybeSingle().execute()

        if not repo.data:
            raise HTTPException(status_code=404, detail="Repository not found")

        session = await github_service.create_analysis_session(
            user_profile_id=user_profile_id,
            github_repository_id=repo.data['id'],
            session_type=request.session_type,
            analysis_focus=request.analysis_focus
        )

        await github_service.analyze_repository_structure(
            session_id=session['id'],
            repo_full_name=request.repo_full_name,
            access_token=connection.data['access_token'],
            branch=repo.data['default_branch']
        )

        return {
            'session_url': session['session_url'],
            'session_type': session['session_type'],
            'status': 'analyzing'
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/{session_url}")
async def get_analysis(session_url: str):
    try:
        supabase = get_supabase()

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
    user_profile_id: str
):
    try:
        supabase = get_supabase()

        session = supabase.table('repo_analysis_sessions').select(
            '*, github_repositories(repo_full_name, default_branch, github_connection_id)'
        ).eq('session_url', session_url).maybeSingle().execute()

        if not session.data:
            raise HTTPException(status_code=404, detail="Session not found")

        repo = session.data['github_repositories']

        connection = supabase.table('github_connections').select('access_token').eq(
            'id', repo['github_connection_id']
        ).maybeSingle().execute()

        if not connection.data:
            raise HTTPException(status_code=404, detail="GitHub connection not found")

        exploration = await github_service.explore_file(
            session_id=session.data['id'],
            repo_full_name=repo['repo_full_name'],
            file_path=file_path,
            access_token=connection.data['access_token'],
            branch=repo['default_branch']
        )

        return exploration

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/connection")
async def disconnect_github(user_profile_id: str):
    try:
        supabase = get_supabase()

        supabase.table('github_connections').delete().eq(
            'user_profile_id', user_profile_id
        ).execute()

        return {'success': True, 'message': 'GitHub connection removed'}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
