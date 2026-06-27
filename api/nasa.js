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

  // APOD only changes once a day, so cache it hard — one success serves everyone
  // for hours and shields us from NASA's intermittently slow APOD endpoint.
  // DONKI feeds get a short edge cache to ease rate limits without going stale.
  const cacheControl = type === 'apod'
    ? 's-maxage=43200, stale-while-revalidate=86400'   // 12h fresh, 24h SWR
    : 's-maxage=300, stale-while-revalidate=600';      // 5m fresh, 10m SWR

  // Fail fast and cleanly (JSON, not Vercel's HTML 504) if NASA is slow.
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 20000);
  try {
    const upstream = await fetch(url, { signal: controller.signal });
    clearTimeout(timer);
    const data = await upstream.json();
    res.setHeader('Cache-Control', cacheControl);
    return res.status(upstream.status).json(data);
  } catch (e) {
    clearTimeout(timer);
    const aborted = e && e.name === 'AbortError';
    return res.status(aborted ? 504 : 502).json({
      error: aborted ? 'NASA upstream timed out' : (e.message || 'NASA proxy error')
    });
  }
};
