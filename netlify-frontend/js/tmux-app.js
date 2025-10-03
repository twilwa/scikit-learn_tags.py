const CONFIG_KEY = 'claude_analyzer_api';
// Use empty string for relative URLs (works in all environments)
let API_URL = localStorage.getItem(CONFIG_KEY) || '';
let ws = null;
let sessionUrl = null;
let pollInterval = null;
let currentMode = null;

const elements = {
    dropZone: document.getElementById('drop-zone'),
    logInput: document.getElementById('log-input'),
    encryptCheck: document.getElementById('encrypt-check'),
    analyzeBtn: document.getElementById('analyze-btn'),
    paneUpload: document.getElementById('pane-upload'),
    paneAnalysis: document.getElementById('pane-analysis'),
    paneInsights: document.getElementById('pane-insights'),
    paneViz: document.getElementById('pane-viz'),
    progressFill: document.getElementById('progress-fill'),
    progressText: document.getElementById('progress-text'),
    logOutput: document.getElementById('log-output'),
    insightsList: document.getElementById('insights-list'),
    vizContainer: document.getElementById('viz-container'),
    statusTime: document.getElementById('status-time'),
    connectionStatus: document.getElementById('connection-status'),
    apiEndpoint: document.getElementById('api-endpoint'),
    configModal: document.getElementById('config-modal'),
    apiUrlInput: document.getElementById('api-url-input'),
    saveConfigBtn: document.getElementById('save-config-btn'),
    cancelConfigBtn: document.getElementById('cancel-config-btn'),
    tmuxPanes: document.querySelector('.tmux-panes'),
    githubModeBtn: document.getElementById('github-mode-btn'),
    folderModeBtn: document.getElementById('folder-mode-btn'),
    logModeBtn: document.getElementById('log-mode-btn'),
    githubModeSection: document.getElementById('github-mode-section'),
    folderModeSection: document.getElementById('folder-mode-section'),
    logModeSection: document.getElementById('log-mode-section'),
    githubConnectBtn: document.getElementById('github-connect-btn'),
    folderInput: document.getElementById('folder-input'),
    folderAnalyzeBtn: document.getElementById('folder-analyze-btn')
};

function updateTime() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-US', { hour12: false });
    elements.statusTime.textContent = timeStr;
}

function showConfigModal() {
    elements.apiUrlInput.value = API_URL;
    elements.configModal.classList.remove('hidden');
}

function hideConfigModal() {
    elements.configModal.classList.add('hidden');
}

function saveConfig() {
    API_URL = elements.apiUrlInput.value.trim();
    if (!API_URL) {
        alert('please enter a valid API URL');
        return;
    }
    localStorage.setItem(CONFIG_KEY, API_URL);
    elements.apiEndpoint.textContent = API_URL;
    hideConfigModal();
}

function initConfig() {
    if (!API_URL) {
        API_URL = '';
        localStorage.removeItem(CONFIG_KEY);
    }
    elements.apiEndpoint.textContent = API_URL === '' ? 'integrated' : API_URL;
}

function setMode(mode) {
    currentMode = mode;

    elements.githubModeSection.style.display = 'none';
    elements.folderModeSection.style.display = 'none';
    elements.logModeSection.style.display = 'none';

    const allBtns = [elements.githubModeBtn, elements.folderModeBtn, elements.logModeBtn];
    allBtns.forEach(btn => {
        btn.style.background = 'rgba(255, 255, 255, 0.05)';
        btn.style.borderColor = '#666';
    });

    if (mode === 'github') {
        elements.githubModeSection.style.display = 'block';
        elements.githubModeBtn.style.background = 'rgba(76, 175, 80, 0.2)';
        elements.githubModeBtn.style.borderColor = '#4CAF50';
    } else if (mode === 'folder') {
        elements.folderModeSection.style.display = 'block';
        elements.folderModeBtn.style.background = 'rgba(255, 152, 0, 0.2)';
        elements.folderModeBtn.style.borderColor = '#FF9800';
    } else if (mode === 'log') {
        elements.logModeSection.style.display = 'block';
        elements.logModeBtn.style.background = 'rgba(33, 150, 243, 0.2)';
        elements.logModeBtn.style.borderColor = '#2196F3';
    }
}

elements.githubModeBtn.addEventListener('click', () => setMode('github'));
elements.folderModeBtn.addEventListener('click', () => setMode('folder'));
elements.logModeBtn.addEventListener('click', () => setMode('log'));

const supabaseClient = supabase.createClient(
    'https://0ec90b57d6e95fcbda19832f.supabase.co',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJib2x0IiwicmVmIjoiMGVjOTBiNTdkNmU5NWZjYmRhMTk4MzJmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg4ODE1NzQsImV4cCI6MTc1ODg4MTU3NH0.9I8-U0x86Ak8t2DGaIk0HfvTSLsAyzdnz-Nw00mMkKw'
);

elements.githubConnectBtn.addEventListener('click', async () => {
    const { data, error } = await supabaseClient.auth.signInWithOAuth({
        provider: 'github',
        options: {
            scopes: 'repo read:user',
            redirectTo: window.location.origin + '/netlify-frontend/'
        }
    });

    if (error) {
        alert('GitHub connection failed: ' + error.message);
    }
});

async function checkGitHubConnection() {
    const { data: { session } } = await supabaseClient.auth.getSession();
    const githubStatus = document.getElementById('github-status');

    if (!githubStatus) return;

    if (session) {
        const userName = session.user?.user_metadata?.user_name || session.user?.user_metadata?.preferred_username || 'User';
        const hasProviderToken = !!session.provider_token;

        if (hasProviderToken) {
            githubStatus.innerHTML = `
                <p style="color: #4CAF50;">> connected as: ${userName}</p>
                <p style="color: #888; font-size: 0.9rem;">✓ GitHub API access granted</p>
                <button class="tmux-btn" onclick="syncAndShowRepos()">view repositories [enter]</button>
                <button class="tmux-btn" style="margin-left: 0.5rem; font-size: 0.8rem;" onclick="debugAuth()">debug</button>
            `;
        } else {
            githubStatus.innerHTML = `
                <p style="color: #ff9800;">> signed in as: ${userName}</p>
                <p style="color: #ff5555; font-size: 0.9rem;">⚠ No GitHub API access</p>
                <p style="color: #888; font-size: 0.9rem;">
                    You're signed in, but we don't have permission to access GitHub API.<br>
                    Please sign out and sign in again to grant API access.
                </p>
                <button class="tmux-btn" onclick="signOut()">sign out</button>
                <button class="tmux-btn" style="margin-left: 0.5rem; font-size: 0.8rem;" onclick="debugAuth()">debug</button>
            `;
        }
    } else {
        githubStatus.innerHTML = `
            <p style="color: #888;">> not connected</p>
        `;
    }
}

async function debugAuth() {
    const { data: { session } } = await supabaseClient.auth.getSession();

    if (!session) {
        alert('Not authenticated');
        return;
    }

    try {
        const response = await fetch(API_URL ? `${API_URL}/api/github/auth/debug` : '/api/github/auth/debug', {
            headers: {
                'Authorization': `Bearer ${session.access_token}`
            }
        });

        const data = await response.json();

        console.log('=== AUTH DEBUG ===');
        console.log('Session:', session);
        console.log('Backend sees:', data);
        console.log('================');

        alert(`Debug info (check console):\n\nHas provider_token: ${data.has_provider_token}\nToken length: ${data.provider_token_length}\n\nSee console for details`);

    } catch (error) {
        alert('Debug failed: ' + error.message);
    }
}

async function signOut() {
    await supabaseClient.auth.signOut();
    window.location.reload();
}

window.debugAuth = debugAuth;
window.signOut = signOut;

async function syncAndShowRepos() {
    const { data: { session } } = await supabaseClient.auth.getSession();

    if (!session) {
        alert('not authenticated');
        return;
    }

    try {
        const response = await fetch(API_URL ? `${API_URL}/api/github/repositories?sync=true` : '/api/github/repositories?sync=true', {
            headers: {
                'Authorization': `Bearer ${session.access_token}`
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const repos = await response.json();
        displayRepositories(repos);

    } catch (error) {
        alert('Failed to fetch repos: ' + error.message);
    }
}

function displayRepositories(repos) {
    const githubStatus = document.getElementById('github-status');
    if (!githubStatus) return;

    let html = '<div style="max-height: 400px; overflow-y: auto;">';
    html += '<p style="color: #00ff00;">> repositories:</p>';

    repos.forEach((repo, index) => {
        html += `
            <div style="margin: 0.5rem 0; padding: 0.5rem; background: rgba(0,0,0,0.3); border-left: 2px solid #4CAF50;">
                <div style="font-weight: bold;">${repo.repo_full_name}</div>
                <div style="color: #888; font-size: 0.9rem;">
                    ${repo.primary_language || 'Unknown'} | ⭐ ${repo.stars} | 🍴 ${repo.forks}
                </div>
                <button class="tmux-btn" style="margin-top: 0.5rem; font-size: 0.8rem;"
                        onclick="analyzeRepo('${repo.repo_full_name}')">analyze</button>
            </div>
        `;
    });

    html += '</div>';
    githubStatus.innerHTML = html;
}

async function analyzeRepo(repoFullName) {
    const { data: { session } } = await supabaseClient.auth.getSession();

    if (!session) {
        alert('not authenticated');
        return;
    }

    try {
        showAnalysisPane();
        updateProgress(10, 'starting repository analysis...');

        const response = await fetch(API_URL ? `${API_URL}/api/github/analyze` : '/api/github/analyze', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${session.access_token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                repo_full_name: repoFullName,
                session_type: 'exploration'
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${await response.text()}`);
        }

        const data = await response.json();
        sessionUrl = data.session_url;

        updateProgress(30, 'analyzing repository structure...');
        logMessage(`> analyzing: ${repoFullName}`);

        startPolling();

    } catch (error) {
        logMessage(`> error: ${error.message}`, 'error');
        updateProgress(0, 'failed');
    }
}

window.syncAndShowRepos = syncAndShowRepos;
window.analyzeRepo = analyzeRepo;

checkGitHubConnection();

elements.folderAnalyzeBtn.addEventListener('click', async () => {
    const files = elements.folderInput.files;
    if (!files || files.length === 0) {
        alert('please select a folder');
        return;
    }

    await analyzeFolder(files);
});

async function analyzeFolder(files) {
    const formData = new FormData();

    for (let file of files) {
        formData.append('files', file);
    }
    formData.append('encryption_enabled', elements.encryptCheck.checked);

    try {
        showAnalysisPane();
        updateProgress(10, 'uploading folder...');

        const url = API_URL ? `${API_URL}/api/sessions/folder` : '/api/sessions/folder';
        console.log('[DEBUG] Posting folder to:', url);
        console.log('[DEBUG] Files:', Array.from(files).map(f => f.name));

        const response = await fetch(url, {
            method: 'POST',
            body: formData
        });

        console.log('[DEBUG] Response status:', response.status);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('[DEBUG] Error response:', errorText);
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }

        const data = await response.json();
        sessionUrl = data.session_url;

        updateProgress(30, 'folder uploaded, analyzing...');
        logMessage(`> folder structure detected: ${data.total_logs} logs, ${data.total_entries} entries`);
        logMessage('> → watch this pane for real-time updates');
        logMessage('> → insights will appear automatically');

        if (data.configs_found && data.configs_found.length > 0) {
            logMessage(`> configs found: ${data.configs_found.join(', ')}`);
        }

        if (data.config_insights) {
            if (data.config_insights.mcp) {
                logMessage(`> mcp: ${data.config_insights.mcp.total_servers} servers configured`);
            }
            if (data.config_insights.subagents) {
                logMessage(`> subagents: ${data.config_insights.subagents.total_subagents} configured`);
            }
        }

        startPolling();

    } catch (error) {
        logMessage(`> error: ${error.message}`, 'error');
        updateProgress(0, 'failed');
    }
}

elements.saveConfigBtn.addEventListener('click', saveConfig);
elements.cancelConfigBtn.addEventListener('click', hideConfigModal);
elements.apiEndpoint.addEventListener('click', showConfigModal);

elements.dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    elements.dropZone.classList.add('drag-over');
});

elements.dropZone.addEventListener('dragleave', () => {
    elements.dropZone.classList.remove('drag-over');
});

elements.dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    elements.dropZone.classList.remove('drag-over');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        const file = files[0];
        if (file.name.match(/\.(codex|claude|log|jsonl|json|txt)$/i)) {
            const reader = new FileReader();
            reader.onload = (e) => {
                elements.logInput.value = e.target.result;
            };
            reader.readAsText(file);
        } else {
            addLogLine('error', 'invalid file type. use .jsonl, .json, .log, .txt, .codex, or .claude');
        }
    }
});

elements.logInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && e.ctrlKey) {
        startAnalysis();
    }
});

elements.analyzeBtn.addEventListener('click', startAnalysis);

// Removed global Enter keydown - was causing unwanted session starts

async function startAnalysis() {
    const logContent = elements.logInput.value.trim();

    if (!logContent) {
        addLogLine('error', 'no log content provided');
        return;
    }

    elements.paneUpload.classList.add('hidden');
    elements.paneAnalysis.classList.remove('hidden');
    elements.tmuxPanes.classList.remove('split-horizontal', 'split-vertical', 'split-quad');

    addLogLine('info', 'initializing...');
    addLogLine('info', 'connecting to backend...');

    try {
        const url = API_URL ? `${API_URL}/api/sessions` : '/api/sessions';
        console.log('[DEBUG] Posting to:', url);

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                log_content: logContent,
                encryption_enabled: elements.encryptCheck.checked
            })
        });

        console.log('[DEBUG] Response status:', response.status);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('[DEBUG] Error response:', errorText);
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }

        const data = await response.json();
        sessionUrl = data.session_url;

        addLogLine('success', 'session created: ' + sessionUrl);
        addLogLine('info', '→ watch this pane for real-time updates');
        addLogLine('info', '→ insights will appear automatically');
        connectWebSocket(sessionUrl);

    } catch (error) {
        addLogLine('error', error.message);
        elements.connectionStatus.textContent = '● error';
        elements.connectionStatus.className = 'status-disconnected';
    }
}

function connectWebSocket(sessionUrl) {
    addLogLine('info', 'using polling mode (serverless functions)...');
    elements.connectionStatus.textContent = '● polling';
    elements.connectionStatus.className = 'status-connected';

    startPolling(sessionUrl);
}

function handleMessage(message) {
    const type = message.type;
    const data = message.data;

    switch (type) {
        case 'status':
            updateProgress(data.progress, data.message);
            addLogLine('info', data.message);
            break;

        case 'analysis_complete':
            updateProgress(data.progress, 'completed: ' + data.type);
            addLogLine('success', data.type + ' analysis complete');
            showVisualization(data.type, data.data);
            break;

        case 'insight':
            showInsightPane();
            addInsight(data);
            addLogLine('insight', 'new insight: ' + data.type);
            break;

        case 'complete':
            updateProgress(100, 'analysis complete');
            addLogLine('success', 'all analysis complete. ready.');
            break;

        case 'error':
            addLogLine('error', data.message);
            break;
    }
}

function updateProgress(percent, message) {
    elements.progressFill.style.width = percent + '%';
    elements.progressText.textContent = '> ' + message + ' [' + percent + '%]';
}

function addLogLine(type, message) {
    const line = document.createElement('div');
    line.className = 'log-line';

    const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false });
    const typeColor = {
        info: 'var(--tmux-accent)',
        success: 'var(--tmux-active)',
        error: 'var(--tmux-error)',
        insight: 'var(--tmux-warning)'
    }[type] || 'var(--tmux-fg)';

    line.innerHTML = '<span class="timestamp">' + timestamp + '</span>' +
        '<span class="type" style="color: ' + typeColor + '">[' + type + ']</span>' +
        '<span>' + message + '</span>';

    elements.logOutput.appendChild(line);
    elements.logOutput.scrollTop = elements.logOutput.scrollHeight;
}

function showInsightPane() {
    if (elements.paneInsights.classList.contains('hidden')) {
        elements.paneInsights.classList.remove('hidden');
        elements.tmuxPanes.classList.add('split-horizontal');
    }
}

function showVizPane() {
    if (elements.paneViz.classList.contains('hidden')) {
        elements.paneViz.classList.remove('hidden');

        if (elements.tmuxPanes.classList.contains('split-horizontal')) {
            elements.tmuxPanes.classList.remove('split-horizontal');
            elements.tmuxPanes.classList.add('split-quad');
        } else {
            elements.tmuxPanes.classList.add('split-vertical');
        }
    }
}

function addInsight(insightData) {
    const card = document.createElement('div');
    card.className = 'insight-card ' + insightData.insight_type;

    const typeLabel = insightData.insight_type.replace('_', ' ');
    const signalPercent = (insightData.signal_score * 100).toFixed(0);

    card.innerHTML = '<div class="insight-header">' +
        '<span class="insight-type">' + typeLabel + '</span>' +
        '<span class="insight-score">signal: ' + signalPercent + '%</span>' +
        '</div>' +
        '<div class="insight-text">' + insightData.insight_text + '</div>' +
        '<div class="insight-actions">' +
        '<button class="insight-btn">copy</button>' +
        '<button class="insight-btn">expand</button>' +
        '</div>';

    elements.insightsList.appendChild(card);
}

function showVisualization(type, data) {
    if (type === 'tool_calls' && data.tool_usage) {
        showVizPane();
        renderToolUsageChart(data.tool_usage);
    } else if (type === 'dependency_graph' && data.nodes && data.nodes.length > 0) {
        showVizPane();
        renderNetworkGraph(data);
    }
}

function renderToolUsageChart(toolUsage) {
    const chart = document.createElement('div');
    chart.className = 'viz-chart';

    const entries = Object.entries(toolUsage).sort((a, b) => b[1] - a[1]).slice(0, 10);
    const maxValue = Math.max(...entries.map(([_, count]) => count));

    const bars = entries.map(([tool, count]) => {
        const width = (count / maxValue) * 100;
        return '<div style="margin-bottom: 8px;">' +
            '<div style="display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 11px;">' +
            '<span style="color: var(--tmux-dim);">' + tool + '</span>' +
            '<span style="color: var(--tmux-accent);">' + count + '</span>' +
            '</div>' +
            '<div style="width: 100%; height: 4px; background: var(--tmux-border); border-radius: 2px;">' +
            '<div style="width: ' + width + '%; height: 100%; background: var(--tmux-accent); border-radius: 2px;"></div>' +
            '</div>' +
            '</div>';
    }).join('');

    chart.innerHTML = '<div class="viz-title">tool usage</div>' + bars;
    elements.vizContainer.appendChild(chart);
}

function renderNetworkGraph(graphData) {
    const chart = document.createElement('div');
    chart.className = 'viz-chart';
    chart.innerHTML = '<div class="viz-title">dependency graph</div>' +
        '<div id="network-graph"></div>';

    elements.vizContainer.appendChild(chart);

    const container = document.getElementById('network-graph');

    const nodes = new vis.DataSet(
        graphData.nodes.map(node => ({
            id: node.id,
            label: node.label,
            color: {
                background: 'var(--tmux-bg)',
                border: 'var(--tmux-accent)',
                highlight: {
                    background: 'var(--tmux-border)',
                    border: 'var(--tmux-active)'
                }
            },
            font: {
                color: 'var(--tmux-fg)',
                size: 11
            }
        }))
    );

    const edges = new vis.DataSet(
        graphData.edges.map(edge => ({
            from: edge.from,
            to: edge.to,
            arrows: 'to',
            color: {
                color: 'var(--tmux-border)',
                highlight: 'var(--tmux-accent)'
            }
        }))
    );

    const data = { nodes, edges };

    const options = {
        physics: {
            enabled: true,
            barnesHut: {
                gravitationalConstant: -2000,
                springLength: 150,
                springConstant: 0.01
            },
            stabilization: {
                iterations: 100
            }
        },
        interaction: {
            hover: true,
            zoomView: true,
            dragView: true
        },
        layout: {
            improvedLayout: true
        }
    };

    new vis.Network(container, data, options);
}

function startPolling(sessionUrl) {
    let lastInsightCount = 0;
    let lastAnalysisCount = 0;
    let checksRemaining = 60;

    pollInterval = setInterval(async () => {
        checksRemaining--;

        if (checksRemaining <= 0) {
            clearInterval(pollInterval);
            addLogLine('info', 'polling stopped after timeout');
            return;
        }

        try {
            const sessionResp = await fetch(API_URL + '/api/sessions/' + sessionUrl);
            const session = await sessionResp.json();

            if (session.status === 'completed') {
                updateProgress(100, 'analysis complete');
                addLogLine('success', 'all analysis complete. ready.');
                clearInterval(pollInterval);
            } else if (session.status === 'failed') {
                addLogLine('error', 'analysis failed: ' + (session.metadata?.error || 'unknown error'));
                clearInterval(pollInterval);
            }

            const analysisResp = await fetch(API_URL + '/api/sessions/' + sessionUrl + '/analysis');
            const analysis = await analysisResp.json();

            if (analysis.length > lastAnalysisCount) {
                const newAnalysis = analysis.slice(lastAnalysisCount);
                newAnalysis.forEach(a => {
                    addLogLine('success', a.analysis_type + ' analysis complete');
                    showVisualization(a.analysis_type, a.result_data);
                });
                lastAnalysisCount = analysis.length;
                updateProgress(20 + (lastAnalysisCount * 15), 'processing...');
            }

            const insightsResp = await fetch(API_URL + '/api/sessions/' + sessionUrl + '/insights');
            const insights = await insightsResp.json();

            if (insights.length > lastInsightCount) {
                const newInsights = insights.slice(lastInsightCount);
                newInsights.forEach(insight => {
                    showInsightPane();
                    addInsight(insight);
                    addLogLine('insight', 'new insight: ' + insight.insight_type);
                });
                lastInsightCount = insights.length;
                updateProgress(Math.min(80 + (lastInsightCount * 5), 95), 'generating insights...');
            }

        } catch (error) {
            console.error('Polling error:', error);
        }
    }, 2000);
}

function logMessage(message, type = 'info') {
    if (elements.logOutput) {
        const line = document.createElement('div');
        line.textContent = message;
        line.style.color = type === 'error' ? '#ff5555' : '#00ff00';
        elements.logOutput.appendChild(line);
        elements.logOutput.scrollTop = elements.logOutput.scrollHeight;
    }
}

function showAnalysisPane() {
    elements.paneUpload.style.display = 'none';
    elements.paneAnalysis.classList.remove('hidden');
}

function updateProgress(percent, message) {
    if (elements.progressFill) {
        elements.progressFill.style.width = percent + '%';
    }
    if (elements.progressText) {
        elements.progressText.textContent = '> ' + message;
    }
}

updateTime();
setInterval(updateTime, 1000);
initConfig();
setMode('github');
