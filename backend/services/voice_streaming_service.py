import asyncio
import json
from typing import Dict, Optional
from datetime import datetime


class VoiceStreamingService:
    def __init__(self):
        self.active_streams = {}

    async def start_voice_stream(
        self,
        session_id: str,
        websocket,
        mode: str = 'browser'
    ):
        stream_id = f"{session_id}_{mode}"
        self.active_streams[stream_id] = {
            'session_id': session_id,
            'websocket': websocket,
            'mode': mode,
            'started_at': datetime.utcnow(),
            'is_active': True
        }

        return stream_id

    async def handle_audio_chunk(
        self,
        stream_id: str,
        audio_data: bytes
    ) -> Optional[str]:
        if stream_id not in self.active_streams:
            return None

        stream = self.active_streams[stream_id]

        transcription = await self._transcribe_audio(audio_data)

        return transcription

    async def _transcribe_audio(self, audio_data: bytes) -> str:
        return "[Transcription would go here - integrate Deepgram SDK]"

    async def send_to_stream(
        self,
        stream_id: str,
        message_type: str,
        data: Dict
    ):
        if stream_id not in self.active_streams:
            return

        stream = self.active_streams[stream_id]
        websocket = stream['websocket']

        try:
            await websocket.send_json({
                'type': message_type,
                'data': data,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            print(f"Error sending to stream {stream_id}: {e}")
            await self.stop_voice_stream(stream_id)

    async def stop_voice_stream(self, stream_id: str):
        if stream_id in self.active_streams:
            self.active_streams[stream_id]['is_active'] = False
            del self.active_streams[stream_id]

    def get_active_streams(self, session_id: str) -> list:
        return [
            stream_id
            for stream_id, stream in self.active_streams.items()
            if stream['session_id'] == session_id and stream['is_active']
        ]
