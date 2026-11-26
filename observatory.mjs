const fields = [
  ['lunar_objectives', 'lunar_objective_rows', 'Lunar objective rows'],
  ['mars_objectives', 'mars_objective_rows', 'Mars objective rows'],
  ['technology_gaps', 'technology_gaps', 'Technology gaps'],
  ['data_gaps', 'data_gaps', 'Normalized data gaps']
];
const isObject = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const positiveInt = value => Number.isSafeInteger(value) && value > 0;

export function parseManifest(raw) {
  if (!isObject(raw) || !isObject(raw.sources) || !isObject(raw.normalized_counts) ||
      raw.revision !== 'C' || typeof raw.document_id !== 'string' || !/^\d+$/.test(raw.document_id) ||
      typeof raw.generated_at !== 'string' || !/^\d{4}-\d{2}-\d{2}T/.test(raw.generated_at) ||
      !Number.isFinite(Date.parse(raw.generated_at))) throw new Error('Invalid manifest metadata');
  const sources = fields.map(([key, countKey, label]) => {
    const source = raw.sources[key];
    const count = raw.normalized_counts[countKey];
    if (!isObject(source) || !positiveInt(count) || !positiveInt(source.record_count) ||
        !positiveInt(source.bytes) || typeof source.filename !== 'string' ||
        !/^[A-Za-z0-9._-]+\.xlsx$/.test(source.filename) ||
        typeof source.sha256 !== 'string' || !/^[a-f0-9]{64}$/i.test(source.sha256) ||
        typeof source.url !== 'string') throw new Error('Invalid source: ' + key);
    const url = new URL(source.url);
    if (url.protocol !== 'https:' || !['www.nasa.gov', 'nasa.gov'].includes(url.hostname) ||
        url.username || url.password || url.port || !url.pathname.startsWith('/wp-content/uploads/') ||
        !url.pathname.endsWith('/' + source.filename)) throw new Error('Unexpected source URL: ' + key);
    if (key === 'data_gaps' ? count > source.record_count : count !== source.record_count)
      throw new Error('Inconsistent counts: ' + key);
    return { label, count, rawCount: source.record_count, bytes: source.bytes, filename: source.filename,
      sha256: source.sha256.toLowerCase(), url: url.href };
  });
  return { generatedAt: raw.generated_at, revision: raw.revision, documentId: raw.document_id, sources };
}

function element(tag, text) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  return node;
}

async function loadCatalog() {
  const status = document.getElementById('status');
  const catalog = document.getElementById('catalog');
  try {
    const response = await fetch('data/moon_to_mars_source_manifest.json', { cache: 'no-store' });
    if (!response.ok) throw new Error('Manifest unavailable');
    const data = parseManifest(await response.json());
    document.getElementById('snapshot').textContent = 'Recorded snapshot: ' + data.generatedAt +
      ' | Revision ' + data.revision + ' | Document ' + data.documentId;
    const counts = document.getElementById('counts');
    const sources = document.getElementById('sources');
    for (const source of data.sources) {
      const count = element('div');
      count.append(element('dt', source.label), element('dd', source.count.toLocaleString('en-US')));
      counts.append(count);
      const row = element('article');
      row.className = 'source';
      const link = element('a', source.filename);
      link.href = source.url;
      row.append(link, element('p', 'Source rows: ' + source.rawCount.toLocaleString('en-US') +
        ' | Bytes: ' + source.bytes.toLocaleString('en-US')),
        element('code', 'Recorded SHA-256: ' + source.sha256));
      sources.append(row);
    }
    status.textContent = 'Manifest structure accepted. Source bytes not independently verified.';
    catalog.hidden = false;
  } catch {
    catalog.hidden = true;
    status.textContent = 'Source manifest unavailable or invalid. No evidence counts displayed.';
  }
}

if (typeof document !== 'undefined') loadCatalog();
