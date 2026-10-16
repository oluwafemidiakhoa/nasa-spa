// Vercel serverless function — proxies NASA open-data feeds using a server-side
// NASA_API_KEY env var, so the deployed site's live cards work with no key typed
// in the browser and the key is never exposed to the client. Falls back to
// DEMO_KEY if no env var is set (rate-limited).

const DAY_MS = 86400000;
const APOD_LOOKBACK_DAYS = 7;

function isoDateDaysAgo(daysAgo) {
  return new Date(Date.now() - daysAgo * DAY_MS).toISOString().slice(0, 10);
}

function isUsableApod(data) {
  if (!data || typeof data !== 'object') return false;
  if (!['image', 'video'].includes(data.media_type)) return false;
  if (!data.url) return false;

  // NASA's APOD upstream occasionally returns a NASA Science placeholder page
  // as if it were an image. On 2026-10-16, for example, the response contained
  // the NASA logo plus "enable JavaScript" instead of the actual APOD media.
  const fingerprint = [
    data.title,
    data.explanation,
    data.url,
    data.hdurl,
    data.thumbnail_url
  ].filter(Boolean).join(' ').toLowerCase();

  if (fingerprint.includes('to view this video please enable javascript')) return false;
  if (fingerprint.includes('supports html5 video')) return false;
  if (fingerprint.includes('nasa-logo@2x.png')) return false;
  if (String(data.title || '').trim().toLowerCase() === 'nasa science') return false;

  return true;
}

async function fetchJson(url, timeoutMs = 12000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const upstream = await fetch(url, {
      signal: controller.signal,
      headers: { 'Accept': 'application/json' }
    });

    let data;
    try {
      data = await upstream.json();
    } catch (parseError) {
      throw new Error(`NASA returned non-JSON data (HTTP ${upstream.status})`);
    }

    return { ok: upstream.ok, status: upstream.status, data };
  } finally {
    clearTimeout(timer);
  }
}

async function fetchApodWithFallback(key) {
  const requestedDate = isoDateDaysAgo(0);
  let lastError = null;

  for (let offset = 0; offset <= APOD_LOOKBACK_DAYS; offset++) {
    const date = isoDateDaysAgo(offset);
    const url = `https://api.nasa.gov/planetary/apod?api_key=${encodeURIComponent(key)}&date=${date}&thumbs=true`;

    try {
      const upstream = await fetchJson(url);

      if (!upstream.ok) {
        const message = upstream.data && upstream.data.error && upstream.data.error.message;
        lastError = new Error(message || `NASA APOD returned HTTP ${upstream.status}`);
        continue;
      }

      if (!isUsableApod(upstream.data)) {
        lastError = new Error(`NASA APOD returned unusable placeholder media for ${date}`);
        continue;
      }

      return {
        ...upstream.data,
        requested_date: requestedDate,
        fallback_used: offset > 0,
        fallback_days: offset
      };
    } catch (error) {
      lastError = error;
    }
  }

  throw lastError || new Error('NASA APOD did not return usable media');
}

module.exports = async (req, res) => {
  const key = process.env.NASA_API_KEY || 'DEMO_KEY';
  const type = String((req.query && req.query.type) || '');
  const today = isoDateDaysAgo(0);
  const weekAgo = isoDateDaysAgo(7);

  const endpoints = {
    cme:  `https://api.nasa.gov/DONKI/CME?startDate=${weekAgo}&endDate=${today}&api_key=${encodeURIComponent(key)}`,
    flr:  `https://api.nasa.gov/DONKI/FLR?startDate=${weekAgo}&endDate=${today}&api_key=${encodeURIComponent(key)}`,
    gst:  `https://api.nasa.gov/DONKI/GST?startDate=${weekAgo}&endDate=${today}&api_key=${encodeURIComponent(key)}`
  };

  if (type !== 'apod' && !endpoints[type]) {
    return res.status(400).json({ error: 'Unknown type: ' + type });
  }

  // APOD changes once a day, but we keep the edge TTL short enough to recover
  // quickly when NASA repairs a malformed daily entry. DONKI stays near-live.
  const cacheControl = type === 'apod'
    ? 's-maxage=3600, stale-while-revalidate=21600'
    : 's-maxage=300, stale-while-revalidate=600';

  try {
    if (type === 'apod') {
      const data = await fetchApodWithFallback(key);
      res.setHeader('Cache-Control', cacheControl);
      return res.status(200).json(data);
    }

    const upstream = await fetchJson(endpoints[type]);
    res.setHeader('Cache-Control', cacheControl);
    return res.status(upstream.status).json(upstream.data);
  } catch (e) {
    const aborted = e && e.name === 'AbortError';
    return res.status(aborted ? 504 : 502).json({
      error: aborted ? 'NASA upstream timed out' : (e.message || 'NASA proxy error')
    });
  }
};
