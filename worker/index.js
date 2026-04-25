// Cloudflare Worker — AU/PR Navigator API proxy
// Deploy: wrangler deploy
// Secret:  wrangler secret put ANTHROPIC_API_KEY

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: CORS });
    }

    const url = new URL(request.url);

    if (url.pathname === '/health') {
      return Response.json({ ok: true }, { headers: CORS });
    }

    if (url.pathname === '/messages' && request.method === 'POST') {
      const body = await request.json();
      delete body.apiKey; // strip if accidentally included — key lives in Worker secret

      const upstream = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'x-api-key': env.ANTHROPIC_API_KEY,
          'anthropic-version': '2023-06-01',
          'content-type': 'application/json',
        },
        body: JSON.stringify(body),
      });

      return new Response(upstream.body, {
        status: upstream.status,
        headers: {
          ...CORS,
          'Content-Type': upstream.headers.get('Content-Type') ?? 'text/event-stream',
        },
      });
    }

    return new Response('Not found', { status: 404 });
  },
};
