const { createClient } = require('@supabase/supabase-js');

const supabaseUrl = process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_ANON_KEY || process.env.VITE_SUPABASE_ANON_KEY;

function redactSecrets(text) {
  const patterns = [
    [/sk-[a-zA-Z0-9]{20,}/g, 'OPENAI_API_KEY'],
    [/sk-ant-[a-zA-Z0-9\-_]{20,}/g, 'ANTHROPIC_API_KEY'],
    [/ghp_[a-zA-Z0-9]{36}/g, 'GITHUB_TOKEN'],
    [/Bearer\s+[a-zA-Z0-9\-_\.]{20,}/gi, 'BEARER_TOKEN'],
    [/ey[A-Za-z0-9\-_]+\.ey[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+/g, 'JWT_TOKEN'],
  ];

  let redacted = text;
  patterns.forEach(([pattern, name]) => {
    redacted = redacted.replace(pattern, `[REDACTED_${name}]`);
  });

  return redacted;
}

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

exports.handler = async (event) => {
  // Handle CORS preflight
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers: corsHeaders,
      body: ''
    };
  }

  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      headers: corsHeaders,
      body: JSON.stringify({ error: 'Method not allowed' })
    };
  }

  try {
    const { log_content, encryption_enabled } = JSON.parse(event.body);

    if (!log_content) {
      return {
        statusCode: 400,
        headers: corsHeaders,
        body: JSON.stringify({ error: 'log_content is required' })
      };
    }

    const supabase = createClient(supabaseUrl, supabaseKey);

    const redactedLog = redactSecrets(log_content);
    const sessionUrl = crypto.randomUUID();

    const { data, error } = await supabase
      .from('sessions')
      .insert({
        session_url: sessionUrl,
        log_content: log_content,
        redacted_log: redactedLog,
        encryption_enabled: encryption_enabled || false,
        status: 'uploading',
        expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
        metadata: {
          secrets_found: (log_content.match(/sk-|ghp_|Bearer/gi) || []).length,
          log_size: log_content.length
        }
      })
      .select()
      .single();

    if (error) throw error;

    await supabase
      .from('sessions')
      .update({ status: 'analyzing' })
      .eq('id', data.id);

    setTimeout(() => {
      processAnalysis(data.id, sessionUrl, redactedLog);
    }, 0);

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify({
        id: data.id,
        session_url: sessionUrl,
        status: 'analyzing',
        created_at: data.created_at,
        expires_at: data.expires_at,
        cost_estimate: 0.0
      })
    };

  } catch (error) {
    console.error('Error:', error);
    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify({ error: error.message })
    };
  }
};

async function processAnalysis(sessionId, sessionUrl, logContent) {
  const supabase = createClient(supabaseUrl, supabaseKey);

  try {
    const toolCallMatches = logContent.match(/<invoke name="([^"]+)">/g) || [];
    const toolCalls = toolCallMatches.map(m => m.match(/name="([^"]+)"/)[1]);

    const toolUsage = {};
    toolCalls.forEach(tool => {
      toolUsage[tool] = (toolUsage[tool] || 0) + 1;
    });

    const fileMatches = logContent.match(/['"]([\/][^'"]+\.[a-z]{1,4})['"]/g) || [];
    const referencedFiles = [...new Set(fileMatches.map(m => m.replace(/['"]/g, '')))];

    await supabase.from('analysis_results').insert({
      session_id: sessionId,
      analysis_type: 'tool_calls',
      result_data: {
        type: 'tool_calls',
        total_calls: toolCalls.length,
        tool_usage: toolUsage,
        recent_tools: toolCalls.slice(-20),
        file_operations: toolCalls.filter(t => ['Read', 'Write', 'Edit'].includes(t)).length,
        most_used_tool: Object.entries(toolUsage).sort((a, b) => b[1] - a[1])[0]?.[0]
      },
      status: 'completed',
      signal_score: Math.min(0.5 + (toolCalls.length / 100), 0.9),
      completed_at: new Date().toISOString()
    });

    await supabase.from('analysis_results').insert({
      session_id: sessionId,
      analysis_type: 'file_structure',
      result_data: {
        type: 'file_structure',
        referenced_files: referencedFiles.slice(0, 20),
        total_files: referencedFiles.length
      },
      status: 'completed',
      signal_score: 0.6,
      completed_at: new Date().toISOString()
    });

    const insights = generateInsights(toolUsage, toolCalls.length, referencedFiles.length);

    for (const insight of insights) {
      await supabase.from('insights').insert({
        session_id: sessionId,
        insight_text: insight.text,
        insight_type: insight.type,
        signal_score: insight.score,
        confidence: 0.8,
        visualization_data: insight.viz,
        shown: false
      });
    }

    await supabase
      .from('sessions')
      .update({ status: 'completed' })
      .eq('id', sessionId);

  } catch (error) {
    console.error('Analysis error:', error);
    await supabase
      .from('sessions')
      .update({
        status: 'failed',
        metadata: { error: error.message }
      })
      .eq('id', sessionId);
  }
}

function generateInsights(toolUsage, totalCalls, fileCount) {
  const insights = [];

  const mostUsedTool = Object.entries(toolUsage).sort((a, b) => b[1] - a[1])[0];
  if (mostUsedTool && totalCalls > 5) {
    insights.push({
      text: `You've used ${mostUsedTool[0]} ${mostUsedTool[1]} times in this session. ${
        ['Read', 'Write', 'Edit'].includes(mostUsedTool[0])
          ? 'Consider reviewing your recent file changes for consistency.'
          : 'This suggests an active exploration phase.'
      }`,
      type: 'optimization',
      score: 0.75,
      viz: { chart_type: 'bar', data: toolUsage }
    });
  }

  if (fileCount > 10) {
    insights.push({
      text: `You're working across ${fileCount} files. Consider focusing on one module at a time to maintain context and reduce cognitive load.`,
      type: 'next_step',
      score: 0.65,
      viz: null
    });
  }

  if (totalCalls > 50) {
    insights.push({
      text: `High activity detected (${totalCalls} tool calls). This session shows extensive exploration. Next step: consolidate your findings and create a focused action plan.`,
      type: 'architecture',
      score: 0.8,
      viz: null
    });
  }

  return insights.sort((a, b) => b.score - a.score).slice(0, 5);
}
