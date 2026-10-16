// Vercel serverless function for NASA live data.
//
// NASA changed both upstreams used by this project in September 2026:
// - APOD moved to the NASA Science WordPress API.
// - DONKI moved to the CCMC DONKI-API host.
//
// Keep those migrations here on the server so the browser UI has one stable
// endpoint and does not depend on legacy api.nasa.gov routes.

const DAY_MS = 86400000;
const APOD_LOOKBACK_DAYS = 7;
const NASA_SCIENCE_APOD = 'https://science.nasa.gov/wp-json/wp/v2/apod-basic/';
const DONKI_BASE = 'https://ccmc.gsfc.nasa.gov/DONKI-API/get';

function isoDateDaysAgo(daysAgo) {
  return new Date(Date.now() - daysAgo * DAY_MS).toISOString().slice(0, 10);
}

function absoluteUrl(value, base = 'https://science.nasa.gov') {
  if (!value) return null;
  try {
    return new URL(String(value), base).href;
  } catch (_) {
    return null;
  }
}

function firstHtmlUrl(html, tag, attribute = 'src') {
  if (!html) return null;
  const pattern = new RegExp(
    '<' + tag + '\\b[^>]*\\b' + attribute + '=["\\\']([^"\\\']+)["\\\']',
    'i'
  );
  const match = String(html).match(pattern);
  return match ? match[1] : null;
}

function stripHtml(value) {
  return String(value || '')
    .replace(/<script\\b[^>]*>[\\s\\S]*?<\\/script>/gi, ' ')
    .replace(/<style\\b[^>]*>[\\s\\S]*?<\\/style>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/gi, ' ')
    .replace(/&amp;/gi, '&')
    .replace(/&quot;/gi, '"')
    .replace(/&#39;|&apos;/gi, "'")
    .replace(/&lt;/gi, '<')
    .replace(/&gt;/gi, '>')
    .replace(/\\s+/g, ' ')
    .trim();
}

function normalizeApod(raw) {
  const data = Array.isArray(raw) ? raw[0] : raw;
  if (!data || typeof data !== 'object') return null;

  const html = String(data.basic_html || '');
  const declaredType = String(data.media_type || '').toLowerCase();

  const sourceUrl = absoluteUrl(firstHtmlUrl(html, 'source'));
  const videoUrl = absoluteUrl(firstHtmlUrl(html, 'video'));
  const iframeUrl = absoluteUrl(firstHtmlUrl(html, 'iframe'));
  const imageUrl = absoluteUrl(firstHtmlUrl(html, 'img'));
  const hdUrl = absoluteUrl(data.hdurl);

  let mediaKind = declaredType;
  let mediaUrl = null;

  if (declaredType === 'image') {
    mediaKind = 'image';
    mediaUrl = hdUrl || imageUrl;
  } else if (declaredType === 'video') {
    if (sourceUrl || videoUrl) {
      mediaKind = 'video';
      mediaUrl = sourceUrl || videoUrl;
    } else if (iframeUrl) {
      mediaKind = 'iframe';
      mediaUrl = iframeUrl;
    }
  } else if (declaredType === 'iframe') {
    mediaKind = 'iframe';
    mediaUrl = iframeUrl || sourceUrl || videoUrl;
  } else if (hdUrl || imageUrl) {
    mediaKind = 'image';
    mediaUrl = hdUrl || imageUrl;
  } else if (sourceUrl || videoUrl) {
    mediaKind = 'video';
    mediaUrl = sourceUrl || videoUrl;
  } else if (iframeUrl) {
    mediaKind = 'iframe';
    mediaUrl = iframeUrl;
  }

  const pageUrl = absoluteUrl(data.permalink || data.url);

  return {
    ...data,
    explanation: stripHtml(data.explanation),
    media_kind: mediaKind || (mediaUrl ? 'media' : 'link'),
    media_url: mediaUrl,
    page_url: pageUrl
  };
}

function isUsableApod(data) {
  if (!data || typeof data !== 'object') return false;
  if (!data.title && !data.date) return false;

  const fingerprint = [
    data.title,
    data.explanation,
    data.media_url,
    data.hdurl,
    data.page_url
  ].filter(Boolean).join(' ').toLowerCase();

  if (fingerprint.includes('to view this video please enable javascript')) return false;
  if (fingerprint.includes('supports html5 video')) return false;
  if (fingerprint.includes('nasa-logo@2x.png')) return false;
  if (String(data.title || '').trim().toLowerCase() === 'nasa science') return false;

  // A video/iframe may not expose its raw media URL in the API payload. In that
  // case the canonical NASA page is still a valid, honest fallback.
  return Boolean(data.media_url || data.page_url);
}

async function fetchJson(url, timeoutMs = 15000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const upstream = await fetch(url, {
      signal: controller.signal,
      headers: {
        Accept: 'application/json',
        'User-Agent': 'nasa-spa/1.0 (+https://nasa-spa.vercel.app)'
      }
    });

    let data;
    try {
      data = await upstream.json();
    } catch (_) {
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
    const params = new URLSearchParams({ date });
    if (key) params.set('api_key', key);

    const url = `${NASA_SCIENCE_APOD}?${params.toString()}`;

    try {
      const upstream = await fetchJson(url);

      if (!upstream.ok) {
        const message =
          upstream.data &&
          upstream.data.error &&
          (upstream.data.error.message || upstream.data.error);
        lastError = new Error(message || `NASA APOD returned HTTP ${upstream.status}`);
        continue;
      }

      const normalized = normalizeApod(upstream.data);
      if (!isUsableApod(normalized)) {
        lastError = new Error(`NASA APOD returned unusable media for ${date}`);
        continue;
      }

      return {
        ...normalized,
        requested_date: requestedDate,
        fallback_used: offset > 0,
        fallback_days: offset,
        source_api: 'NASA Science APOD WordPress API'
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

  // NASA CCMC migrated DONKI on 2026-09-30. These public endpoints do not use
  // api.nasa.gov or the NASA Open API key.
  const donkiParams = `startDate=${encodeURIComponent(weekAgo)}&endDate=${encodeURIComponent(today)}`;
  const endpoints = {
    cme: `${DONKI_BASE}/CME?${donkiParams}`,
    flr: `${DONKI_BASE}/FLR?${donkiParams}`,
    gst: `${DONKI_BASE}/GST?${donkiParams}`
  };

  if (type !== 'apod' && !endpoints[type]) {
    return res.status(400).json({ error: 'Unknown type: ' + type });
  }

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

    if (!upstream.ok) {
      const message =
        upstream.data &&
        upstream.data.error &&
        (upstream.data.error.message || upstream.data.error);
      return res.status(upstream.status).json({
        error: message || `NASA CCMC DONKI returned HTTP ${upstream.status}`
      });
    }

    return res.status(200).json(upstream.data);
  } catch (e) {
    const aborted = e && e.name === 'AbortError';
    return res.status(aborted ? 504 : 502).json({
      error: aborted ? 'NASA upstream timed out' : (e.message || 'NASA proxy error')
    });
  }
};
