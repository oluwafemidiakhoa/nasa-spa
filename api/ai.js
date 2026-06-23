// Vercel serverless function — proxies AI provider calls so Claude and DeepSeek
// (which block direct browser requests via CORS) work from the deployed site.
//
// The browser sends the user's own key in the request body; this function
// forwards it server-side. If no key is supplied it falls back to a server
// env var (CLAUDE_API_KEY / OPENAI_API_KEY / DEEPSEEK_API_KEY / GEMINI_API_KEY)
// so you can optionally configure keys in Vercel — but note that exposes your
// credits to any visitor, so per-user keys are the safer default.

module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'POST only' });
    return;
  }

  try {
    const { provider, key, system, messages } = req.body || {};
    if (!provider) return res.status(400).json({ error: 'provider required' });

    const envKey = process.env[`${String(provider).toUpperCase()}_API_KEY`];
    const apiKey = key || envKey;
    if (!apiKey) return res.status(400).json({ error: 'No API key provided for ' + provider });

    const turns = Array.isArray(messages) ? messages : [];
    let url, headers, body, extract;

    if (provider === 'claude') {
      url = 'https://api.anthropic.com/v1/messages';
      headers = { 'Content-Type': 'application/json', 'x-api-key': apiKey, 'anthropic-version': '2023-06-01' };
      body = { model: 'claude-sonnet-4-6', max_tokens: 700, system: system || '', messages: turns };
      extract = (d) => d.content && d.content[0] && d.content[0].text;
    } else if (provider === 'openai') {
      url = 'https://api.openai.com/v1/chat/completions';
      headers = { 'Content-Type': 'application/json', 'Authorization': `Bearer ${apiKey}` };
      body = { model: 'gpt-4o', max_tokens: 700, messages: [{ role: 'system', content: system || '' }, ...turns] };
      extract = (d) => d.choices && d.choices[0] && d.choices[0].message && d.choices[0].message.content;
    } else if (provider === 'deepseek') {
      url = 'https://api.deepseek.com/v1/chat/completions';
      headers = { 'Content-Type': 'application/json', 'Authorization': `Bearer ${apiKey}` };
      body = { model: 'deepseek-chat', max_tokens: 700, messages: [{ role: 'system', content: system || '' }, ...turns] };
      extract = (d) => d.choices && d.choices[0] && d.choices[0].message && d.choices[0].message.content;
    } else if (provider === 'gemini') {
      const model = 'gemini-1.5-flash';
      url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`;
      headers = { 'Content-Type': 'application/json' };
      body = {
        system_instruction: { parts: [{ text: system || '' }] },
        contents: turns.map((m) => ({ role: m.role === 'assistant' ? 'model' : 'user', parts: [{ text: m.content }] })),
        generationConfig: { maxOutputTokens: 700, temperature: 0.7 }
      };
      extract = (d) => d.candidates && d.candidates[0] && d.candidates[0].content &&
        d.candidates[0].content.parts && d.candidates[0].content.parts[0] && d.candidates[0].content.parts[0].text;
    } else {
      return res.status(400).json({ error: 'Unknown provider: ' + provider });
    }

    const upstream = await fetch(url, { method: 'POST', headers, body: JSON.stringify(body) });
    const data = await upstream.json();
    if (!upstream.ok) {
      return res.status(upstream.status).json({ error: (data.error && data.error.message) || JSON.stringify(data) });
    }
    const text = extract(data);
    if (!text) return res.status(502).json({ error: 'Empty response from ' + provider });
    return res.status(200).json({ text });
  } catch (e) {
    return res.status(500).json({ error: e.message || 'Proxy error' });
  }
};
