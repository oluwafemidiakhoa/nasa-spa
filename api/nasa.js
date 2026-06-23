// Vercel serverless function — proxies NASA open-data feeds using a server-side
// NASA_API_KEY env var, so the deployed site's live cards work with no key typed
// in the browser and the key is never exposed to the client. Falls back to
// DEMO_KEY if no env var is set (rate-limited).

module.exports = async (req, res) => {
  const key = process.env.NASA_API_KEY || 'DEMO_KEY';
  const type = String((req.query && req.query.type) || '');
  const today = new Date().toISOString().slice(0, 10);
  const weekAgo = new Date(Date.now() - 7 * 86400000).toISOString().slice(0, 10);

  const endpoints = {
    cme:  `https://api.nasa.gov/DONKI/CME?startDate=${weekAgo}&endDate=${today}&api_key=${key}`,
    flr:  `https://api.nasa.gov/DONKI/FLR?startDate=${weekAgo}&endDate=${today}&api_key=${key}`,
    gst:  `https://api.nasa.gov/DONKI/GST?startDate=${weekAgo}&endDate=${today}&api_key=${key}`,
    apod: `https://api.nasa.gov/planetary/apod?api_key=${key}`
  };

  const url = endpoints[type];
  if (!url) return res.status(400).json({ error: 'Unknown type: ' + type });

  try {
    const upstream = await fetch(url);
    const data = await upstream.json();
    // Short edge cache to ease rate limits without going stale (5 min).
    res.setHeader('Cache-Control', 's-maxage=300, stale-while-revalidate=600');
    return res.status(upstream.status).json(data);
  } catch (e) {
    return res.status(500).json({ error: e.message || 'NASA proxy error' });
  }
};
