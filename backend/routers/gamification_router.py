from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timedelta

from backend.database import get_supabase

router = APIRouter(prefix="/api", tags=["gamification"])


class UpdateStatsRequest(BaseModel):
    user_id: str
    stat_updates: Dict[str, int]


@router.get("/leaderboard")
async def get_leaderboard(season: str = "eternal", limit: int = 10):
    try:
        supabase = get_supabase()

        result = supabase.table('leaderboard_entries').select(
            'rank, mysterious_score, score_breakdown, user_profiles(username, title, avatar_url)'
        ).eq('season', season).order('rank').limit(limit).execute()

        leaderboard = []
        for entry in result.data:
            profile = entry['user_profiles']
            leaderboard.append({
                'rank': entry['rank'],
                'username': profile['username'],
                'title': profile['title'],
                'avatar_url': profile.get('avatar_url'),
                'mysterious_score': float(entry['mysterious_score']),
                'breakdown': entry.get('score_breakdown', {})
            })

        return leaderboard

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_global_stats():
    try:
        supabase = get_supabase()

        profiles = supabase.table('user_profiles').select('*', count='exact').execute()

        today = datetime.utcnow().date()
        sessions_today = supabase.table('voice_sessions').select('*', count='exact').gte(
            'created_at', today.isoformat()
        ).execute()

        kb_docs = supabase.table('kb_documents').select('*', count='exact').execute()

        insights = supabase.table('insights').select('*', count='exact').execute()

        return {
            'total_users': profiles.count,
            'sessions_today': sessions_today.count,
            'total_kb_documents': kb_docs.count,
            'total_insights': insights.count
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/{user_id}/stats")
async def update_user_stats(user_id: str, request: UpdateStatsRequest):
    try:
        supabase = get_supabase()

        profile = supabase.table('user_profiles').select('stats').eq('id', user_id).maybeSingle().execute()

        if not profile.data:
            raise HTTPException(status_code=404, detail="User profile not found")

        current_stats = profile.data['stats']

        for key, increment in request.stat_updates.items():
            if key in current_stats:
                current_stats[key] = int(current_stats[key]) + increment
            else:
                current_stats[key] = increment

        supabase.table('user_profiles').update({
            'stats': current_stats,
            'last_active': datetime.utcnow().isoformat()
        }).eq('id', user_id).execute()

        await check_achievements(user_id, current_stats)

        supabase.rpc('update_leaderboard').execute()

        return {'success': True, 'stats': current_stats}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/profile")
async def get_user_profile(user_id: str):
    try:
        supabase = get_supabase()

        profile = supabase.table('user_profiles').select('*').eq('id', user_id).maybeSingle().execute()

        if not profile.data:
            raise HTTPException(status_code=404, detail="User profile not found")

        achievements = supabase.table('user_achievements').select(
            'unlocked_at, achievements(name, description, icon, tier, points)'
        ).eq('user_profile_id', user_id).execute()

        quests = supabase.table('quest_completions').select('*').eq('user_profile_id', user_id).order('completed_at', desc=True).limit(10).execute()

        return {
            'profile': profile.data,
            'achievements': achievements.data,
            'recent_quests': quests.data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/achievements")
async def get_achievements(include_hidden: bool = False):
    try:
        supabase = get_supabase()

        query = supabase.table('achievements').select('*')

        if not include_hidden:
            query = query.eq('hidden', False)

        result = query.order('tier').order('points').execute()

        return result.data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quests/{quest_key}/complete")
async def complete_quest(quest_key: str, user_id: str, completion_data: Optional[Dict] = None):
    try:
        supabase = get_supabase()

        quest_definitions = {
            'first_log': {'name': 'First Log Analysis', 'score': 10},
            'voice_session': {'name': 'Voice Session Master', 'score': 50},
            'kb_contributor': {'name': 'Knowledge Contributor', 'score': 25},
            'build_success': {'name': 'Build Master', 'score': 100},
            'speed_run': {'name': 'Speed Run', 'score': 150}
        }

        if quest_key not in quest_definitions:
            raise HTTPException(status_code=404, detail="Quest not found")

        quest = quest_definitions[quest_key]

        existing = supabase.table('quest_completions').select('*').eq('user_profile_id', user_id).eq('quest_key', quest_key).maybeSingle().execute()

        if existing.data:
            return {'message': 'Quest already completed', 'quest': existing.data}

        result = supabase.table('quest_completions').insert({
            'user_profile_id': user_id,
            'quest_key': quest_key,
            'quest_name': quest['name'],
            'completion_data': completion_data or {},
            'score_awarded': quest['score']
        }).execute()

        await update_user_stats(user_id, UpdateStatsRequest(
            user_id=user_id,
            stat_updates={'quests_completed': 1}
        ))

        return {'success': True, 'quest': result.data[0]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def check_achievements(user_id: str, stats: Dict):
    supabase = get_supabase()

    achievements_to_check = [
        ('first_session', stats.get('sessions_completed', 0) >= 1),
        ('log_analyzer', stats.get('sessions_completed', 0) >= 10),
        ('kb_contributor', stats.get('kb_contributions', 0) >= 5),
        ('helpful_feedback', stats.get('helpful_votes', 0) >= 50),
        ('voice_veteran', stats.get('voice_sessions', 0) >= 10),
        ('build_master', stats.get('builds_successful', 0) >= 25),
        ('artifact_master', stats.get('insights_discovered', 0) >= 100),
    ]

    for achievement_key, condition in achievements_to_check:
        if condition:
            achievement = supabase.table('achievements').select('id').eq('achievement_key', achievement_key).maybeSingle().execute()

            if achievement.data:
                existing = supabase.table('user_achievements').select('*').eq('user_profile_id', user_id).eq('achievement_id', achievement.data['id']).maybeSingle().execute()

                if not existing.data:
                    supabase.table('user_achievements').insert({
                        'user_profile_id': user_id,
                        'achievement_id': achievement.data['id']
                    }).execute()
