import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Client-Info, Apikey',
};

interface ExecuteRequest {
  code: string;
  session_id: string;
  user_id: string;
}

serve(async (req: Request) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  try {
    const { code, session_id, user_id }: ExecuteRequest = await req.json();

    const startTime = Date.now();
    let output = '';
    let errorMessage = null;
    let outputType = 'text';

    try {
      // For now, use Deno's eval for simple cases
      // In production, you'd use a sandboxed Python runtime or WebAssembly
      const result = eval(`(function() { ${code} })()`);
      output = String(result);
    } catch (error) {
      errorMessage = error.message;
      outputType = 'error';
    }

    const executionTimeMs = Date.now() - startTime;

    // Store execution in database
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;

    const dbResponse = await fetch(`${supabaseUrl}/rest/v1/repl_executions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${supabaseKey}`,
        'apikey': supabaseKey,
      },
      body: JSON.stringify({
        session_id,
        user_id,
        code,
        output,
        output_type: outputType,
        execution_time_ms: executionTimeMs,
        error_message: errorMessage,
      }),
    });

    const execution = await dbResponse.json();

    return new Response(
      JSON.stringify({
        output,
        output_type: outputType,
        execution_time_ms: executionTimeMs,
        error_message: errorMessage,
        execution_id: execution[0]?.id,
      }),
      {
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json',
        },
      }
    );
  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message }),
      {
        status: 500,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json',
        },
      }
    );
  }
});