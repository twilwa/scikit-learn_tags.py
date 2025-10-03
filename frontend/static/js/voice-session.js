class VoiceSession {
    constructor(sessionUrl, mode = 'text_only') {
        this.sessionUrl = sessionUrl;
        this.mode = mode;
        this.ws = null;
        this.mediaRecorder = null;
        this.audioStream = null;
        this.isRecording = false;
        this.sessionData = null;
    }

    async initialize() {
        await this.loadSessionData();
        await this.connectWebSocket();

        if (this.mode === 'voice_browser') {
            await this.setupMicrophone();
        }
    }

    async loadSessionData() {
        const response = await fetch(`/api/voice-sessions/${this.sessionUrl}`);
        this.sessionData = await response.json();
        return this.sessionData;
    }

    async connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/voice/${this.sessionUrl}`;

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.onConnect();
        };

        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.onError(error);
        };

        this.ws.onclose = () => {
            console.log('WebSocket closed');
            this.onDisconnect();
        };
    }

    async setupMicrophone() {
        try {
            this.audioStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 16000
                }
            });

            this.mediaRecorder = new MediaRecorder(this.audioStream, {
                mimeType: 'audio/webm',
                audioBitsPerSecond: 16000
            });

            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0 && this.ws.readyState === WebSocket.OPEN) {
                    this.ws.send(event.data);
                }
            };

            this.onMicrophoneReady();
        } catch (error) {
            console.error('Microphone setup failed:', error);
            this.onMicrophoneError(error);
        }
    }

    startRecording() {
        if (this.mediaRecorder && !this.isRecording) {
            this.mediaRecorder.start(100);
            this.isRecording = true;
            this.onRecordingStart();
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.onRecordingStop();
        }
    }

    async executeCode(code) {
        const response = await fetch(`/api/voice-sessions/${this.sessionUrl}/execute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ code })
        });

        return await response.json();
    }

    async sendMessage(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'message',
                data: { text: message }
            }));
        }
    }

    handleMessage(message) {
        switch (message.type) {
            case 'transcription':
                this.onTranscription(message.data);
                break;
            case 'ai_response':
                this.onAIResponse(message.data);
                break;
            case 'code_execution':
                this.onCodeExecution(message.data);
                break;
            case 'visualization':
                this.onVisualization(message.data);
                break;
            case 'time_update':
                this.onTimeUpdate(message.data);
                break;
            case 'session_expired':
                this.onSessionExpired();
                break;
            default:
                console.log('Unknown message type:', message.type);
        }
    }

    async loadREPLHistory() {
        const response = await fetch(`/api/voice-sessions/${this.sessionUrl}/history`);
        return await response.json();
    }

    disconnect() {
        if (this.mediaRecorder && this.isRecording) {
            this.stopRecording();
        }

        if (this.audioStream) {
            this.audioStream.getTracks().forEach(track => track.stop());
        }

        if (this.ws) {
            this.ws.close();
        }
    }

    onConnect() {}
    onDisconnect() {}
    onError(error) {}
    onMicrophoneReady() {}
    onMicrophoneError(error) {}
    onRecordingStart() {}
    onRecordingStop() {}
    onTranscription(data) {}
    onAIResponse(data) {}
    onCodeExecution(data) {}
    onVisualization(data) {}
    onTimeUpdate(data) {}
    onSessionExpired() {}
}


class KBManager {
    constructor() {
        this.supabase = window.supabase;
    }

    async uploadDocument(file, visibility = 'private') {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('visibility', visibility);

        const response = await fetch('/api/kb/upload', {
            method: 'POST',
            body: formData
        });

        return await response.json();
    }

    async setVisibility(documentId, visibility) {
        const response = await fetch(`/api/kb/documents/${documentId}/visibility`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ visibility })
        });

        return await response.json();
    }

    async searchSharedKB(query, category = null) {
        const params = new URLSearchParams({ query });
        if (category) params.append('category', category);

        const response = await fetch(`/api/kb/shared/search?${params}`);
        return await response.json();
    }

    async submitFeedback(chunkId, isHelpful, comment = null) {
        const response = await fetch('/api/kb/feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                chunk_id: chunkId,
                is_helpful: isHelpful,
                correction_text: comment,
                feedback_type: 'helpful'
            })
        });

        return await response.json();
    }

    async getMyContributions() {
        const response = await fetch('/api/kb/my-contributions');
        return await response.json();
    }

    async getSharedKBStats() {
        const response = await fetch('/api/kb/shared/stats');
        return await response.json();
    }
}


if (typeof module !== 'undefined' && module.exports) {
    module.exports = { VoiceSession, KBManager };
}
