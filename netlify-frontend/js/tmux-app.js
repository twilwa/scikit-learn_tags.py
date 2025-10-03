const CONFIG_KEY = 'claude_analyzer_api';
let API_URL = localStorage.getItem(CONFIG_KEY) || '';
let ws = null;
let sessionUrl = null;

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
    tmuxPanes: document.querySelector('.tmux-panes')
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
        showConfigModal();
    } else {
        elements.apiEndpoint.textContent = API_URL;
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
        if (file.name.match(/\.(codex|claude|log)$/)) {
            const reader = new FileReader();
            reader.onload = (e) => {
                elements.logInput.value = e.target.result;
            };
            reader.readAsText(file);
        } else {
            addLogLine('error', 'invalid file type. use .codex, .claude, or .log');
        }
    }
});

elements.logInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && e.ctrlKey) {
        startAnalysis();
    }
});

elements.analyzeBtn.addEventListener('click', startAnalysis);

document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.ctrlKey && document.activeElement !== elements.logInput) {
        startAnalysis();
    }
});

async function startAnalysis() {
    const logContent = elements.logInput.value.trim();

    if (!logContent) {
        addLogLine('error', 'no log content provided');
        return;
    }

    if (!API_URL) {
        showConfigModal();
        return;
    }

    elements.paneUpload.classList.add('hidden');
    elements.paneAnalysis.classList.remove('hidden');
    elements.tmuxPanes.classList.remove('split-horizontal', 'split-vertical', 'split-quad');

    addLogLine('info', 'connecting to backend...');

    try {
        const response = await fetch(API_URL + '/api/sessions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                log_content: logContent,
                encryption_enabled: elements.encryptCheck.checked
            })
        });

        if (!response.ok) {
            throw new Error('failed to create session: ' + response.statusText);
        }

        const data = await response.json();
        sessionUrl = data.session_url;

        addLogLine('success', 'session created: ' + sessionUrl);
        connectWebSocket(sessionUrl);

    } catch (error) {
        addLogLine('error', error.message);
        elements.connectionStatus.textContent = '● error';
        elements.connectionStatus.className = 'status-disconnected';
    }
}

function connectWebSocket(sessionUrl) {
    const wsProtocol = API_URL.startsWith('https') ? 'wss:' : 'ws:';
    const wsUrl = API_URL.replace(/^https?:/, wsProtocol) + '/ws/' + sessionUrl;

    addLogLine('info', 'establishing websocket connection...');

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        addLogLine('success', 'websocket connected');
        elements.connectionStatus.textContent = '● connected';
        elements.connectionStatus.className = 'status-connected';
    };

    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleMessage(message);
    };

    ws.onerror = (error) => {
        addLogLine('error', 'websocket error');
        elements.connectionStatus.textContent = '● error';
        elements.connectionStatus.className = 'status-disconnected';
    };

    ws.onclose = () => {
        addLogLine('info', 'websocket disconnected');
        elements.connectionStatus.textContent = '● disconnected';
        elements.connectionStatus.className = 'status-disconnected';
    };
}

function handleMessage(message) {
    const { type, data } = message;

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
    card.className = 'insight-card ' + insightData.type;

    const typeLabel = insightData.type.replace('_', ' ');
    const signalPercent = (insightData.signal_score * 100).toFixed(0);

    card.innerHTML = '<div class="insight-header">' +
        '<span class="insight-type">' + typeLabel + '</span>' +
        '<span class="insight-score">signal: ' + signalPercent + '%</span>' +
        '</div>' +
        '<div class="insight-text">' + insightData.text + '</div>' +
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

updateTime();
setInterval(updateTime, 1000);
initConfig();
