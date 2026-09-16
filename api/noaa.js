// Same-origin NOAA SWPC proxy for the Artemis Mission Intelligence console.
module.exports = async (req, res) => {
  const type = String((req.query && req.query.type) || '');
  const endpoints = {
    kp: 'https://services.swpc.noaa.gov/json/planetary_k_index_1m.json',
    plasma: 'https://services.swpc.noaa.gov/products/solar-wind/plasma-1-day.json',
    mag: 'https://services.swpc.noaa.gov/products/solar-wind/mag-1-day.json'
  };
  const url = endpoints[type];
  if (!url) return res.status(400).json({ error: 'Unknown type: ' + type });
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 12000);
  try {
    const upstream = await fetch(url, { signal: controller.signal });
    clearTimeout(timer);
    const data = await upstream.json();
    res.setHeader('Cache-Control', 's-maxage=120, stale-while-revalidate=300');
    return res.status(upstream.status).json(data);
  } catch (e) {
    clearTimeout(timer);
    const aborted = e && e.name === 'AbortError';
    return res.status(aborted ? 504 : 502).json({ error: aborted ? 'NOAA upstream timed out' : (e.message || 'NOAA proxy error') });
  }
};