export type RoleKey =
  | 'student'
  | 'pilot'
  | 'satellite'
  | 'grid'
  | 'astronaut'
  | 'aurora';

export type DataMode = 'live' | 'partial' | 'fallback';
export type ActivityLevel = 'quiet' | 'watch' | 'active' | 'storm';

export interface SourceStatus {
  name: string;
  url: string;
  status: 'ok' | 'error';
  detail: string;
}

export interface OpenDataEvent {
  id: string;
  type: 'CME' | 'FLARE' | 'SEP' | 'GST';
  time: string;
  title: string;
  detail: string;
  sourceUrl: string;
}

export interface RoleStory {
  id: RoleKey;
  title: string;
  audience: string;
  signal: string;
  summary: string;
  whyItMatters: string;
  actions: string[];
}

export interface TimelineStep {
  label: string;
  time: string;
  status: string;
  detail: string;
}

export interface SpaceWeatherSnapshot {
  generatedAt: string;
  dataMode: DataMode;
  activityLevel: ActivityLevel;
  activityScore: number;
  confidence: number;
  headline: string;
  summary: string;
  metrics: {
    cmeCount: number;
    flareCount: number;
    sepCount: number;
    stormCount: number;
    strongestFlare: string;
    earthDirectedCmeCount: number;
    kpIndex: number | null;
    solarWindSpeed: number | null;
    bzGsm: number | null;
    sourceCount: number;
  };
  primaryEvent: OpenDataEvent | null;
  events: OpenDataEvent[];
  roles: RoleStory[];
  timeline: TimelineStep[];
  sources: SourceStatus[];
  warnings: string[];
  epicImageUrl: string | null;
}

interface FetchResult<T> {
  name: string;
  url: string;
  data: T | null;
  error: string | null;
}

const NASA_KEY = process.env.NEXT_PUBLIC_NASA_API_KEY || 'DEMO_KEY';
const NASA_DONKI_BASE = 'https://api.nasa.gov/DONKI';
const NOAA_JSON_BASE = 'https://services.swpc.noaa.gov/json';
const NOAA_PRODUCTS_BASE = 'https://services.swpc.noaa.gov/products';

function isoDate(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function daysAgo(days: number): Date {
  const date = new Date();
  date.setUTCDate(date.getUTCDate() - days);
  return date;
}

async function fetchJson<T>(name: string, url: string): Promise<FetchResult<T>> {
  try {
    const response = await fetch(url, { cache: 'no-store' });
    if (!response.ok) {
      throw new Error(`${response.status} ${response.statusText}`);
    }

    return {
      name,
      url,
      data: (await response.json()) as T,
      error: null,
    };
  } catch (error) {
    return {
      name,
      url,
      data: null,
      error: error instanceof Error ? error.message : 'Unknown fetch error',
    };
  }
}

function asArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

function parseNumber(value: unknown): number | null {
  if (value === null || value === undefined || value === '') return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function latestObject(list: unknown): Record<string, unknown> | null {
  const rows = asArray<Record<string, unknown>>(list);
  return rows.length ? rows[rows.length - 1] : null;
}

function latestProductRow(product: unknown, field: string): number | null {
  const rows = asArray<unknown[]>(product);
  if (rows.length < 2 || !Array.isArray(rows[0])) return null;

  const headers = rows[0].map(String);
  const index = headers.findIndex((header) => header.toLowerCase() === field.toLowerCase());
  const row = rows[rows.length - 1];

  if (index < 0 || !Array.isArray(row)) return null;
  return parseNumber(row[index]);
}

function flareRank(classType: string): number {
  const normalized = classType.trim().toUpperCase();
  const letter = normalized[0] || 'A';
  const magnitude = Number(normalized.slice(1)) || 0;
  const base = { A: 1, B: 2, C: 3, M: 4, X: 5 }[letter as 'A' | 'B' | 'C' | 'M' | 'X'] || 0;
  return base * 100 + magnitude;
}

function strongestFlare(flares: Array<Record<string, unknown>>): string {
  const classes = flares
    .map((flare) => String(flare.classType || ''))
    .filter(Boolean)
    .sort((a, b) => flareRank(b) - flareRank(a));

  return classes[0] || 'None';
}

function eventTime(event: Record<string, unknown>, fallback = new Date().toISOString()): string {
  return String(
    event.startTime ||
      event.beginTime ||
      event.eventTime ||
      event.peakTime ||
      event.submissionTime ||
      fallback
  );
}

function eventId(event: Record<string, unknown>, fallback: string): string {
  return String(event.activityID || event.flrID || event.sepID || event.gstID || fallback);
}

function eventSourceUrl(type: OpenDataEvent['type'], id: string): string {
  const map = {
    CME: 'CME',
    FLARE: 'FLR',
    SEP: 'SEP',
    GST: 'GST',
  };

  return `${NASA_DONKI_BASE}/${map[type]}?startDate=${isoDate(daysAgo(7))}&endDate=${isoDate(
    new Date()
  )}&api_key=${NASA_KEY}#${encodeURIComponent(id)}`;
}

interface CmeAssessment {
  speed: number | null;
  isEarthDirected: boolean;
  locationLabel: string;
}

// DONKI CME analyses describe the launch geometry. A CME is broadly
// "Earth-directed" when its source sits near the Sun-Earth line (small
// heliographic longitude/latitude) and it has a wide enough cone to sweep
// Earth, or when a linked note explicitly mentions Earth. A high raw CME
// count alone says nothing about Earth impact, so we score geometry, not tally.
function assessCme(cme: Record<string, unknown>): CmeAssessment {
  const analyses = asArray<Record<string, unknown>>(cme.cmeAnalyses);
  const analysis =
    analyses.find((entry) => entry.isMostAccurate === true) ||
    analyses[analyses.length - 1] ||
    null;

  const speed = analysis ? parseNumber(analysis.speed) : null;
  const longitude = analysis ? parseNumber(analysis.longitude) : null;
  const latitude = analysis ? parseNumber(analysis.latitude) : null;
  const halfAngle = analysis ? parseNumber(analysis.halfAngle) : null;

  const facingEarth =
    longitude !== null && latitude !== null
      ? Math.abs(longitude) <= 45 && Math.abs(latitude) <= 45
      : false;
  const wideCone = halfAngle !== null && halfAngle >= 30;
  const earthInNote = String(cme.note || '').toLowerCase().includes('earth');
  const isEarthDirected = (facingEarth && wideCone) || earthInNote;

  const sourceLocation = String(cme.sourceLocation || '').trim();
  const locationLabel = sourceLocation
    ? sourceLocation
    : isEarthDirected
      ? 'Earth-directed'
      : analysis
        ? 'off the Sun–Earth line'
        : 'analysis pending';

  return { speed, isEarthDirected, locationLabel };
}

function normalizeEvents(
  cmes: Array<Record<string, unknown>>,
  flares: Array<Record<string, unknown>>,
  seps: Array<Record<string, unknown>>,
  storms: Array<Record<string, unknown>>
): OpenDataEvent[] {
  const cmeEvents = cmes.map((cme, index) => {
    const id = eventId(cme, `CME-${index + 1}`);
    const { speed, isEarthDirected, locationLabel } = assessCme(cme);
    const speedText = speed ? `, estimated speed ${Math.round(speed)} km/s` : ', analysis pending';

    return {
      id,
      type: 'CME' as const,
      time: eventTime(cme),
      title: isEarthDirected ? 'Earth-directed CME detected' : 'Coronal mass ejection detected',
      detail: `${locationLabel}${speedText}`,
      sourceUrl: eventSourceUrl('CME', id),
    };
  });

  const flareEvents = flares.map((flare, index) => {
    const id = eventId(flare, `FLR-${index + 1}`);
    const classType = String(flare.classType || 'unclassified');

    return {
      id,
      type: 'FLARE' as const,
      time: eventTime(flare),
      title: `${classType} solar flare`,
      detail: `${String(flare.sourceLocation || 'unknown region')} peak activity`,
      sourceUrl: eventSourceUrl('FLARE', id),
    };
  });

  const sepEvents = seps.map((sep, index) => {
    const id = eventId(sep, `SEP-${index + 1}`);

    return {
      id,
      type: 'SEP' as const,
      time: eventTime(sep),
      title: 'Solar energetic particle event',
      detail: 'Particle event reported in DONKI',
      sourceUrl: eventSourceUrl('SEP', id),
    };
  });

  const stormEvents = storms.map((storm, index) => {
    const id = eventId(storm, `GST-${index + 1}`);

    return {
      id,
      type: 'GST' as const,
      time: eventTime(storm),
      title: 'Geomagnetic storm record',
      detail: 'Geomagnetic storm activity reported in DONKI',
      sourceUrl: eventSourceUrl('GST', id),
    };
  });

  return [...cmeEvents, ...flareEvents, ...sepEvents, ...stormEvents]
    .sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime())
    .slice(0, 8);
}

// Activity is weighted toward *measured* near-Earth conditions (Kp, Bz, solar
// wind, geomagnetic storm records) because those describe what Earth is
// experiencing now. Solar drivers (CMEs, flares, SEPs) only add weight when
// they are plausibly geoeffective — a high count of off-disk CMEs should not
// inflate the score while Earth itself is quiet.
function calculateActivityScore(params: {
  earthDirectedCmeCount: number;
  maxEarthDirectedSpeed: number | null;
  sepCount: number;
  stormCount: number;
  kpIndex: number | null;
  solarWindSpeed: number | null;
  bzGsm: number | null;
  strongestFlare: string;
}): number {
  // Measured near-Earth state (dominant).
  const kpScore = params.kpIndex !== null ? Math.min(Math.max(params.kpIndex - 1, 0) * 9, 45) : 0;
  const bzScore =
    params.bzGsm !== null && params.bzGsm < 0 ? Math.min(Math.abs(params.bzGsm) * 1.6, 18) : 0;
  const windScore =
    params.solarWindSpeed !== null ? Math.min(Math.max(params.solarWindSpeed - 400, 0) / 25, 12) : 0;
  const stormScore = Math.min(params.stormCount * 14, 22);

  // Solar drivers (only when geoeffective).
  const fastCmeBonus =
    params.maxEarthDirectedSpeed !== null && params.maxEarthDirectedSpeed > 800 ? 8 : 0;
  const cmeScore =
    params.earthDirectedCmeCount > 0
      ? Math.min(8 + params.earthDirectedCmeCount * 4 + fastCmeBonus, 22)
      : 0;
  const flareScore = params.strongestFlare.startsWith('X')
    ? 16
    : params.strongestFlare.startsWith('M')
      ? 9
      : 0;
  const sepScore = Math.min(params.sepCount * 10, 16);

  return Math.min(
    100,
    Math.round(kpScore + bzScore + windScore + stormScore + cmeScore + flareScore + sepScore)
  );
}

function activityLevel(
  score: number,
  kpIndex: number | null,
  stormCount: number,
  earthDirectedInbound: boolean
): ActivityLevel {
  if ((kpIndex !== null && kpIndex >= 6) || stormCount >= 2) return 'storm';
  if ((kpIndex !== null && kpIndex >= 5) || stormCount >= 1 || score >= 55) return 'active';
  if (score >= 22 || earthDirectedInbound) return 'watch';
  return 'quiet';
}

function buildHeadline(level: ActivityLevel): string {
  switch (level) {
    case 'storm':
      return 'Geomagnetic storm conditions need attention';
    case 'active':
      return 'Active space weather signals are building';
    case 'watch':
      return 'Solar activity watch';
    default:
      return 'Quiet to unsettled space weather';
  }
}

function buildSummary(params: {
  level: ActivityLevel;
  cmeCount: number;
  earthDirectedCmeCount: number;
  flareCount: number;
  sepCount: number;
  stormCount: number;
  kpIndex: number | null;
  strongestFlare: string;
}): string {
  const kpText =
    params.kpIndex === null
      ? 'latest Kp unavailable'
      : `latest Kp near ${params.kpIndex.toFixed(1)} (${
          params.kpIndex >= 5 ? 'disturbed' : 'quiet'
        } near-Earth conditions)`;
  const cmeText = `${params.cmeCount} CMEs (${params.earthDirectedCmeCount} Earth-directed)`;
  return `${cmeText}, ${params.flareCount} flares, ${params.sepCount} particle events, and ${params.stormCount} geomagnetic storm records were found in the recent DONKI window; strongest flare: ${params.strongestFlare}; ${kpText}.`;
}

function buildRoles(params: {
  level: ActivityLevel;
  activityScore: number;
  strongestFlare: string;
  kpIndex: number | null;
  solarWindSpeed: number | null;
  bzGsm: number | null;
  earthDirectedCmeCount: number;
  sepCount: number;
}): RoleStory[] {
  const kp = params.kpIndex;
  const flareMajor = params.strongestFlare.startsWith('M') || params.strongestFlare.startsWith('X');
  const active = params.level === 'active' || params.level === 'storm';

  return [
    {
      id: 'student',
      title: 'Student explainer',
      audience: 'Classroom and public outreach',
      signal: active ? 'The Sun is giving us a teachable event.' : 'A calm Sun is still a useful baseline.',
      summary: active
        ? 'Today is a good moment to explain how energy leaves the Sun, travels through space, and changes conditions near Earth.'
        : 'Quiet conditions help students compare normal space weather against storm periods.',
      whyItMatters:
        'Space weather connects heliophysics to everyday systems: radios, GPS, satellites, auroras, and human spaceflight.',
      actions: ['Compare today with a past storm', 'Open the evidence panel', 'Ask which systems depend on space technology'],
    },
    {
      id: 'pilot',
      title: 'Pilot briefing',
      audience: 'Aviation and polar routes',
      signal: flareMajor || active ? 'Watch radio and navigation conditions.' : 'No elevated aviation signal from current data.',
      summary:
        flareMajor || active
          ? 'Solar flares and geomagnetic activity can degrade HF radio and navigation reliability, especially at high latitudes.'
          : 'Current open feeds do not show a strong aviation-impact signal.',
      whyItMatters:
        'Polar aviation depends on communication and navigation systems that can be affected by ionospheric disturbance.',
      actions: ['Check official NOAA/SWPC products', 'Monitor HF radio advisories', 'Review high-latitude route contingency plans'],
    },
    {
      id: 'satellite',
      title: 'Satellite operator',
      audience: 'LEO operators and mission teams',
      signal:
        active || params.earthDirectedCmeCount > 0
          ? 'Track drag and anomaly risk.'
          : 'Normal monitoring posture.',
      summary:
        active || params.earthDirectedCmeCount > 0
          ? 'CMEs and geomagnetic activity can heat the upper atmosphere and increase drag on low-Earth-orbit satellites.'
          : 'No strong drag-risk signal is visible in the current open-data snapshot.',
      whyItMatters:
        'Even moderate storms can affect orbit prediction, attitude control, and anomaly response planning.',
      actions: ['Monitor Kp and solar wind speed', 'Check spacecraft anomaly logs', 'Review drag-sensitive operations'],
    },
    {
      id: 'grid',
      title: 'Grid operator',
      audience: 'Power infrastructure planners',
      signal: kp && kp >= 5 ? 'Geomagnetic activity deserves attention.' : 'No strong grid-risk signal.',
      summary:
        kp && kp >= 5
          ? 'Elevated Kp indicates disturbed geomagnetic conditions that can induce currents in long conductors.'
          : 'Current Kp readings do not indicate a major grid-facing concern.',
      whyItMatters:
        'Geomagnetically induced currents are a low-frequency, high-impact operational planning problem.',
      actions: ['Use official SWPC alerts for operations', 'Track Kp trend', 'Prepare internal situational awareness updates'],
    },
    {
      id: 'astronaut',
      title: 'Astronaut safety',
      audience: 'Human spaceflight awareness',
      signal: params.sepCount > 0 || params.strongestFlare.startsWith('X') ? 'Radiation context matters.' : 'Routine radiation awareness.',
      summary:
        params.sepCount > 0 || params.strongestFlare.startsWith('X')
          ? 'Particle events and major flares can increase radiation concern beyond Earth protection.'
          : 'Current open feeds do not show a major radiation event in this snapshot.',
      whyItMatters:
        'Astronauts outside Earth protection need timely awareness of solar energetic particle risk.',
      actions: ['Track SEP reports', 'Compare flare class and particle data', 'Use official mission rules for any action'],
    },
    {
      id: 'aurora',
      title: 'Aurora chaser',
      audience: 'Sky watchers and photographers',
      signal: kp && kp >= 5 ? 'Aurora chances improve.' : 'Aurora likely favors high latitudes.',
      summary:
        kp && kp >= 5
          ? 'Elevated Kp can push aurora visibility farther from the poles, depending on cloud cover and local darkness.'
          : 'Aurora may still occur at high latitudes, but current Kp does not suggest broad mid-latitude visibility.',
      whyItMatters:
        'Aurora is the public-facing signal of a Sun-Earth connection that starts with plasma and magnetic fields.',
      actions: ['Check local darkness and clouds', 'Watch Kp trend', 'Use the timeline to estimate the viewing window'],
    },
  ];
}

function buildTimeline(params: {
  primaryEvent: OpenDataEvent | null;
  level: ActivityLevel;
  kpIndex: number | null;
  solarWindSpeed: number | null;
  bzGsm: number | null;
}): TimelineStep[] {
  const eventTimeLabel = params.primaryEvent
    ? new Date(params.primaryEvent.time).toLocaleString()
    : 'Recent window';

  return [
    {
      label: '1. Solar signal',
      time: eventTimeLabel,
      status: params.primaryEvent ? params.primaryEvent.type : 'No major event',
      detail: params.primaryEvent
        ? `${params.primaryEvent.title}: ${params.primaryEvent.detail}`
        : 'No recent DONKI event dominates this snapshot.',
    },
    {
      label: '2. Propagation',
      time: 'Minutes to days',
      status: 'Uncertain by physics',
      detail:
        'Flares can affect radio quickly; CMEs may take roughly one to three days, depending on speed and direction.',
    },
    {
      label: '3. Earth conditions',
      time: 'Latest NOAA feed',
      status: params.kpIndex === null ? 'Kp unavailable' : `Kp ${params.kpIndex.toFixed(1)}`,
      detail:
        params.solarWindSpeed || params.bzGsm
          ? `Solar wind speed ${params.solarWindSpeed ? Math.round(params.solarWindSpeed) : 'unknown'} km/s; Bz ${params.bzGsm ?? 'unknown'} nT.`
          : 'Real-time solar wind data was not available in this browser session.',
    },
    {
      label: '4. Human story',
      time: 'Now',
      status: buildHeadline(params.level),
      detail: 'The same open data is translated differently for each user role.',
    },
  ];
}

function buildEpicImageUrl(frame: Record<string, unknown> | null): string | null {
  if (!frame) return null;

  const image = String(frame.image || '');
  const dateValue = String(frame.date || '');
  if (!image || !dateValue) return null;

  const date = new Date(dateValue);
  if (Number.isNaN(date.getTime())) return null;

  const year = date.getUTCFullYear();
  const month = String(date.getUTCMonth() + 1).padStart(2, '0');
  const day = String(date.getUTCDate()).padStart(2, '0');

  return `https://api.nasa.gov/EPIC/archive/natural/${year}/${month}/${day}/jpg/${image}.jpg?api_key=${NASA_KEY}`;
}

function fallbackSnapshot(): SpaceWeatherSnapshot {
  const generatedAt = new Date().toISOString();
  const primaryEvent: OpenDataEvent = {
    id: 'SAMPLE-CME-001',
    type: 'CME',
    time: generatedAt,
    title: 'Sample CME for offline demo',
    detail: 'Marked fallback data because live public endpoints were unavailable',
    sourceUrl: 'https://ccmc.gsfc.nasa.gov/tools/DONKI/',
  };

  const roles = buildRoles({
    level: 'watch',
    activityScore: 38,
    strongestFlare: 'M1.0 sample',
    kpIndex: 4,
    solarWindSpeed: 480,
    bzGsm: -4,
    earthDirectedCmeCount: 1,
    sepCount: 0,
  });

  return {
    generatedAt,
    dataMode: 'fallback',
    activityLevel: 'watch',
    activityScore: 38,
    confidence: 0.35,
    headline: 'Solar activity watch',
    summary:
      'Live open-data endpoints could not be reached, so the app is showing a clearly marked sample snapshot for demo continuity.',
    metrics: {
      cmeCount: 1,
      flareCount: 1,
      sepCount: 0,
      stormCount: 0,
      strongestFlare: 'M1.0 sample',
      earthDirectedCmeCount: 1,
      kpIndex: 4,
      solarWindSpeed: 480,
      bzGsm: -4,
      sourceCount: 0,
    },
    primaryEvent,
    events: [primaryEvent],
    roles,
    timeline: buildTimeline({
      primaryEvent,
      level: 'watch',
      kpIndex: 4,
      solarWindSpeed: 480,
      bzGsm: -4,
    }),
    sources: [
      {
        name: 'Fallback sample',
        url: 'https://ccmc.gsfc.nasa.gov/tools/DONKI/',
        status: 'error',
        detail: 'Live public data unavailable in this session',
      },
    ],
    warnings: ['Fallback sample is not live data. Refresh when network access is available.'],
    epicImageUrl: null,
  };
}

export async function fetchSpaceWeatherSnapshot(): Promise<SpaceWeatherSnapshot> {
  const startDate = isoDate(daysAgo(7));
  const endDate = isoDate(new Date());

  const requests = [
    fetchJson<Record<string, unknown>[]>('NASA DONKI CMEs', `${NASA_DONKI_BASE}/CME?startDate=${startDate}&endDate=${endDate}&api_key=${NASA_KEY}`),
    fetchJson<Record<string, unknown>[]>('NASA DONKI Flares', `${NASA_DONKI_BASE}/FLR?startDate=${startDate}&endDate=${endDate}&api_key=${NASA_KEY}`),
    fetchJson<Record<string, unknown>[]>('NASA DONKI SEP', `${NASA_DONKI_BASE}/SEP?startDate=${startDate}&endDate=${endDate}&api_key=${NASA_KEY}`),
    fetchJson<Record<string, unknown>[]>('NASA DONKI Geomagnetic Storms', `${NASA_DONKI_BASE}/GST?startDate=${startDate}&endDate=${endDate}&api_key=${NASA_KEY}`),
    fetchJson<Record<string, unknown>[]>('NASA EPIC Recent Earth Imagery', `https://api.nasa.gov/EPIC/api/natural?api_key=${NASA_KEY}`),
    fetchJson<Record<string, unknown>[]>('NOAA Planetary K Index', `${NOAA_JSON_BASE}/planetary_k_index_1m.json`),
    fetchJson<unknown[][]>('NOAA Solar Wind Plasma', `${NOAA_PRODUCTS_BASE}/solar-wind/plasma-1-day.json`),
    fetchJson<unknown[][]>('NOAA Solar Wind Magnetic Field', `${NOAA_PRODUCTS_BASE}/solar-wind/mag-1-day.json`),
  ];

  const results = await Promise.all(requests);
  const successful = results.filter((result) => result.data !== null);

  if (successful.length === 0) {
    return fallbackSnapshot();
  }

  const [cmeResult, flareResult, sepResult, stormResult, epicResult, kpResult, plasmaResult, magResult] = results;

  const cmes = asArray<Record<string, unknown>>(cmeResult.data);
  const flares = asArray<Record<string, unknown>>(flareResult.data);
  const seps = asArray<Record<string, unknown>>(sepResult.data);
  const storms = asArray<Record<string, unknown>>(stormResult.data);
  const latestKp = latestObject(kpResult.data);
  const kpIndex = latestKp ? parseNumber(latestKp.kp_index ?? latestKp.Kp ?? latestKp.kp) : null;
  const solarWindSpeed = latestProductRow(plasmaResult.data, 'speed');
  const bzGsm = latestProductRow(magResult.data, 'bz_gsm') ?? latestProductRow(magResult.data, 'bz');
  const strongest = strongestFlare(flares);
  const cmeAssessments = cmes.map(assessCme);
  const earthDirectedCmes = cmeAssessments.filter((cme) => cme.isEarthDirected);
  const earthDirectedCmeCount = earthDirectedCmes.length;
  const maxEarthDirectedSpeed = earthDirectedCmes.reduce<number | null>(
    (max, cme) => (cme.speed !== null && (max === null || cme.speed > max) ? cme.speed : max),
    null
  );
  const activityScore = calculateActivityScore({
    earthDirectedCmeCount,
    maxEarthDirectedSpeed,
    sepCount: seps.length,
    stormCount: storms.length,
    kpIndex,
    solarWindSpeed,
    bzGsm,
    strongestFlare: strongest,
  });
  const level = activityLevel(activityScore, kpIndex, storms.length, earthDirectedCmeCount > 0);
  const events = normalizeEvents(cmes, flares, seps, storms);
  const primaryEvent = events[0] || null;
  const dataMode: DataMode = successful.length === results.length ? 'live' : 'partial';
  const roles = buildRoles({
    level,
    activityScore,
    strongestFlare: strongest,
    kpIndex,
    solarWindSpeed,
    bzGsm,
    earthDirectedCmeCount,
    sepCount: seps.length,
  });

  const warnings = results
    .filter((result) => result.error)
    .map((result) => `${result.name}: ${result.error}`);

  if (NASA_KEY === 'DEMO_KEY') {
    warnings.push('Using NASA DEMO_KEY. Add NEXT_PUBLIC_NASA_API_KEY for better API limits.');
  }

  return {
    generatedAt: new Date().toISOString(),
    dataMode,
    activityLevel: level,
    activityScore,
    confidence: Math.min(0.9, 0.42 + successful.length * 0.06),
    headline: buildHeadline(level),
    summary: buildSummary({
      level,
      cmeCount: cmes.length,
      earthDirectedCmeCount,
      flareCount: flares.length,
      sepCount: seps.length,
      stormCount: storms.length,
      kpIndex,
      strongestFlare: strongest,
    }),
    metrics: {
      cmeCount: cmes.length,
      flareCount: flares.length,
      sepCount: seps.length,
      stormCount: storms.length,
      strongestFlare: strongest,
      earthDirectedCmeCount,
      kpIndex,
      solarWindSpeed,
      bzGsm,
      sourceCount: successful.length,
    },
    primaryEvent,
    events,
    roles,
    timeline: buildTimeline({
      primaryEvent,
      level,
      kpIndex,
      solarWindSpeed,
      bzGsm,
    }),
    sources: results.map((result) => ({
      name: result.name,
      url: result.url,
      status: result.data ? 'ok' : 'error',
      detail: result.error || 'Loaded',
    })),
    warnings,
    epicImageUrl: buildEpicImageUrl(asArray<Record<string, unknown>>(epicResult.data)[0] || null),
  };
}
