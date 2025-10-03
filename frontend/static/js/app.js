let ws = null;
let sessionUrl = null;

const dropZone = document.getElementById('drop-zone');
const uploadForm = document.getElementById('upload-form');
const logContent = document.getElementById('log-content');
const uploadSection = document.getElementById('upload-section');
const analysisSection = document.getElementById('analysis-section');
const progressFill = document.getElementById('progress-fill');
const statusMessage = document.getElementById('status-message');
const insightsContainer = document.getElementById('insights-container');
const visualizationsContainer = document.getElementById('visualizations-container');

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        const file = files[0];
        if (file.name.endsWith('.codex') || file.name.endsWith('.claude') || file.name.endsWith('.log')) {
            const reader = new FileReader();
            reader.onload = (e) => {
                logContent.value = e.target.result;
            };
            reader.readAsText(file);
        } else {
            alert('please drop a .codex, .claude, or .log file');
        }
    }
});

uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const content = logContent.value.trim();
    if (!content) {
        alert('please paste log content or drop a file');
        return;
    }

    const encryptEnabled = document.getElementById('encrypt-toggle').checked;

    uploadSection.style.display = 'none';
    analysisSection.style.display = 'block';

    try {
        const response = await fetch('/api/sessions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                log_content: content,
                encryption_enabled: encryptEnabled
            })
        });

        if (!response.ok) {
            throw new Error('failed to create session');
        }

        const data = await response.json();
        sessionUrl = data.session_url;

        connectWebSocket(sessionUrl);

    } catch (error) {
        console.error('upload error:', error);
        statusMessage.textContent = `> error: ${error.message}`;
    }
});

function connectWebSocket(sessionUrl) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws/${sessionUrl}`);

    ws.onopen = () => {
        console.log('websocket connected');
    };

    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
    };

    ws.onerror = (error) => {
        console.error('websocket error:', error);
    };

    ws.onclose = () => {
        console.log('websocket closed');
    };
}

function handleWebSocketMessage(message) {
    const { type, data } = message;

    switch (type) {
        case 'status':
            updateProgress(data.progress, data.message);
            break;

        case 'analysis_complete':
            updateProgress(data.progress, `> ${data.type} complete`);
            showVisualization(data.type, data.data);
            break;

        case 'insight':
            addInsight(data);
            break;

        case 'complete':
            updateProgress(100, '> analysis complete. ready.');
            break;

        case 'error':
            statusMessage.textContent = `> error: ${data.message}`;
            statusMessage.style.color = 'var(--text-error)';
            break;
    }
}

function updateProgress(percent, message) {
    progressFill.style.width = `${percent}%`;
    statusMessage.textContent = message;
}

function addInsight(insightData) {
    const card = document.createElement('div');
    card.className = `insight-card ${insightData.type}`;
    card.innerHTML = `
        <div class="insight-header">
            <span class="insight-type">${insightData.type.replace('_', ' ')}</span>
            <span class="insight-score">signal: ${(insightData.signal_score * 100).toFixed(0)}%</span>
        </div>
        <div class="insight-text">${insightData.text}</div>
        <button class="btn-small" onclick="toggleComment('${insightData.id}')">add comment</button>
        <div id="comment-form-${insightData.id}" class="comment-form">
            <input type="text" class="comment-input" placeholder="your thoughts..." />
            <button class="btn-small" onclick="submitComment('${insightData.id}')">send</button>
        </div>
    `;

    insightsContainer.appendChild(card);

    if (insightData.visualization && insightData.visualization.chart_type === 'network') {
        showNetworkGraph(insightData.visualization);
    }
}

function toggleComment(insightId) {
    const form = document.getElementById(`comment-form-${insightId}`);
    form.classList.toggle('active');
}

function submitComment(insightId) {
    const form = document.getElementById(`comment-form-${insightId}`);
    const input = form.querySelector('.comment-input');
    const text = input.value.trim();

    if (text && ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: 'comment',
            data: {
                insight_id: insightId,
                text: text
            }
        }));

        input.value = '';
        form.classList.remove('active');
    }
}

function showVisualization(type, data) {
    if (type === 'tool_calls' && data.tool_usage) {
        showToolUsageChart(data.tool_usage);
    } else if (type === 'dependency_graph' && data.nodes && data.nodes.length > 0) {
        showNetworkGraph(data);
    }
}

function showToolUsageChart(toolUsage) {
    const card = document.createElement('div');
    card.className = 'viz-card';

    const entries = Object.entries(toolUsage).sort((a, b) => b[1] - a[1]).slice(0, 10);
    const maxValue = Math.max(...entries.map(([_, count]) => count));

    const bars = entries.map(([tool, count]) => {
        const width = (count / maxValue) * 100;
        return `
            <div style="margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span style="color: var(--text-secondary); font-size: 11px;">${tool}</span>
                    <span style="color: var(--text-accent); font-size: 11px;">${count}</span>
                </div>
                <div style="width: 100%; height: 6px; background: var(--bg-primary); border-radius: 3px;">
                    <div style="width: ${width}%; height: 100%; background: var(--text-accent); border-radius: 3px;"></div>
                </div>
            </div>
        `;
    }).join('');

    card.innerHTML = `
        <div class="viz-header">╭─ tool usage</div>
        <div style="padding: 10px 0;">${bars}</div>
    `;

    visualizationsContainer.appendChild(card);
}

function showNetworkGraph(graphData) {
    const card = document.createElement('div');
    card.className = 'viz-card';
    card.innerHTML = `
        <div class="viz-header">╭─ dependency graph</div>
        <div id="network-graph"></div>
    `;

    visualizationsContainer.appendChild(card);

    const container = document.getElementById('network-graph');

    const nodes = new vis.DataSet(
        graphData.nodes.map(node => ({
            id: node.id,
            label: node.label,
            color: {
                background: '#11151c',
                border: '#39bae6',
                highlight: {
                    background: '#1a1f29',
                    border: '#4ac7f2'
                }
            },
            font: {
                color: '#b3b9c5',
                size: 12
            }
        }))
    );

    const edges = new vis.DataSet(
        graphData.edges.map(edge => ({
            from: edge.from,
            to: edge.to,
            arrows: 'to',
            color: {
                color: '#2d3543',
                highlight: '#39bae6'
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
