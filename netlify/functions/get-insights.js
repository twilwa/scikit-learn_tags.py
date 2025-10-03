const { createClient } = require('@supabase/supabase-js');

const supabaseUrl = process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_ANON_KEY || process.env.VITE_SUPABASE_ANON_KEY;

exports.handler = async (event) => {
  if (event.httpMethod !== 'GET') {
    return {
      statusCode: 405,
      body: JSON.stringify({ error: 'Method not allowed' })
    };
  }

  try {
    const pathParts = event.path.split('/');
    const sessionUrl = pathParts[pathParts.length - 2];

    if (!sessionUrl) {
      return {
        statusCode: 400,
        body: JSON.stringify({ error: 'session_url is required' })
      };
    }

    const supabase = createClient(supabaseUrl, supabaseKey);

    const { data: session, error: sessionError } = await supabase
      .from('sessions')
      .select('id')
      .eq('session_url', sessionUrl)
      .maybeSingle();

    if (sessionError) throw sessionError;

    if (!session) {
      return {
        statusCode: 404,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        },
        body: JSON.stringify({ error: 'Session not found' })
      };
    }

    const { data: insights, error: insightsError } = await supabase
      .from('insights')
      .select('*')
      .eq('session_id', session.id)
      .order('signal_score', { ascending: false });

    if (insightsError) throw insightsError;

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify(insights)
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
