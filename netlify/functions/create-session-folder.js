const { createClient } = require('@supabase/supabase-js');
const multipart = require('parse-multipart-data');

const supabaseUrl = process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_ANON_KEY || process.env.VITE_SUPABASE_ANON_KEY;

const supabase = createClient(supabaseUrl, supabaseKey);

exports.handler = async (event, context) => {
  // Handle CORS preflight
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
      },
      body: ''
    };
  }

  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      headers: { 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({ error: 'Method not allowed' })
    };
  }

  try {
    console.log('[FOLDER UPLOAD] Processing request');

    // Parse multipart form data
    const contentType = event.headers['content-type'] || event.headers['Content-Type'];
    const boundary = contentType.split('boundary=')[1];
    const parts = multipart.parse(Buffer.from(event.body, 'base64'), boundary);

    console.log(`[FOLDER UPLOAD] Received ${parts.length} parts`);

    const files = parts.filter(part => part.filename);
    const encryptionField = parts.find(part => part.name === 'encryption_enabled');
    const encryptionEnabled = encryptionField ? encryptionField.data.toString() === 'true' : false;

    console.log(`[FOLDER UPLOAD] Files: ${files.length}, Encryption: ${encryptionEnabled}`);

    // Limit file processing to avoid timeout
    const MAX_FILES = 30;
    const filesToProcess = files.slice(0, MAX_FILES);

    if (files.length > MAX_FILES) {
      console.log(`[FOLDER UPLOAD] Warning: ${files.length} files uploaded, processing first ${MAX_FILES}`);
    }

    // Process files
    let combinedLogs = '';
    let totalEntries = 0;
    const configs = {};
    const logFiles = [];

    for (const file of filesToProcess) {
      const filename = file.filename;
      const content = file.data.toString('utf8');

      console.log(`[FOLDER UPLOAD]   - ${filename} (${content.length} bytes)`);

      // Check file type
      if (filename.endsWith('.jsonl')) {
        const lines = content.split('\n').filter(l => l.trim());
        totalEntries += lines.length;
        combinedLogs += content + '\n';
        logFiles.push({ filename, format: 'jsonl', entries: lines.length });
      } else if (filename.endsWith('.json')) {
        if (filename === 'config.json' || filename === 'mcp.json' || filename === 'subagents.json') {
          configs[filename] = JSON.parse(content);
        } else {
          combinedLogs += content + '\n';
          totalEntries += 1;
          logFiles.push({ filename, format: 'json' });
        }
      } else if (filename.endsWith('.log') || filename.endsWith('.txt')) {
        combinedLogs += content + '\n';
        const lines = content.split('\n').filter(l => l.trim());
        totalEntries += lines.length;
        logFiles.push({ filename, format: 'text', lines: lines.length });
      }
    }

    console.log(`[FOLDER UPLOAD] Processed: ${logFiles.length} logs, ${totalEntries} entries, ${Object.keys(configs).length} configs`);

    // Analyze configs
    const configInsights = {};

    if (configs['mcp.json']) {
      const mcpServers = Object.keys(configs['mcp.json'].mcpServers || {});
      configInsights.mcp = {
        servers_configured: mcpServers.length,
        servers: mcpServers,
        has_environment_vars: mcpServers.some(s => {
          const server = configs['mcp.json'].mcpServers[s];
          return server.env && Object.keys(server.env).length > 0;
        })
      };
    }

    if (configs['subagents.json']) {
      configInsights.subagents = {
        count: configs['subagents.json'].subagents?.length || 0,
        names: configs['subagents.json'].subagents?.map(s => s.name) || []
      };
    }

    if (configs['config.json']) {
      configInsights.interaction_style = {
        cline_mode: configs['config.json'].clineMode || 'unknown',
        custom_instructions: !!configs['config.json'].customInstructions,
        always_allow_read: configs['config.json'].alwaysAllowReadOnly || false
      };
    }

    // Generate session URL
    const sessionUrl = `folder-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    // Insert into database
    const { data, error } = await supabase
      .from('sessions')
      .insert({
        session_url: sessionUrl,
        log_content: combinedLogs,
        redacted_log: combinedLogs, // TODO: Implement secret redaction
        encryption_enabled: encryptionEnabled,
        status: 'analyzing',
        metadata: {
          folder_type: Object.keys(configs).length > 0 ? '.codex' : 'logs',
          total_logs: logFiles.length,
          total_entries: totalEntries,
          configs_found: Object.keys(configs),
          config_insights: configInsights,
          log_files: logFiles
        }
      })
      .select()
      .single();

    if (error) {
      console.error('[FOLDER UPLOAD] Database error:', error);
      throw error;
    }

    console.log(`[FOLDER UPLOAD] Success! Session: ${sessionUrl}`);

    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        session_url: sessionUrl,
        status: 'analyzing',
        total_logs: logFiles.length,
        total_entries: totalEntries,
        configs_found: Object.keys(configs),
        config_insights: configInsights
      })
    };

  } catch (error) {
    console.error('[FOLDER UPLOAD] Error:', error);
    return {
      statusCode: 500,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        error: 'Failed to process folder upload',
        message: error.message
      })
    };
  }
};
