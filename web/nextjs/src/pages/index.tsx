import Head from 'next/head';
import { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Clock3,
  Database,
  Globe2,
  GraduationCap,
  Plane,
  Radio,
  RefreshCw,
  Rocket,
  Satellite,
  ShieldCheck,
  Sparkles,
  Sun,
  Zap,
} from 'lucide-react';

import {
  RoleKey,
  RoleStory,
  SpaceWeatherSnapshot,
  fetchSpaceWeatherSnapshot,
} from '@/lib/spaceWeather';

const roleIcons: Record<RoleKey, typeof GraduationCap> = {
  student: GraduationCap,
  pilot: Plane,
  satellite: Satellite,
  grid: Zap,
  astronaut: Rocket,
  aurora: Sparkles,
};

const levelStyles = {
  quiet: 'border-emerald-300/40 bg-emerald-300/10 text-emerald-100',
  watch: 'border-amber-300/50 bg-amber-300/10 text-amber-100',
  active: 'border-orange-300/50 bg-orange-300/10 text-orange-100',
  storm: 'border-rose-300/50 bg-rose-300/10 text-rose-100',
};

function formatTime(value: string): string {
  try {
    return new Intl.DateTimeFormat(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(value));
  } catch {
    return value;
  }
}

function formatNumber(value: number | null, suffix = ''): string {
  if (value === null || Number.isNaN(value)) return 'Unavailable';
  return `${Math.round(value * 10) / 10}${suffix}`;
}

function dataModeLabel(snapshot: SpaceWeatherSnapshot): string {
  if (snapshot.dataMode === 'live') return 'Live open data';
  if (snapshot.dataMode === 'partial') return 'Partial live data';
  return 'Marked fallback sample';
}

function LoadingState() {
  return (
    <main className="min-h-screen bg-[#070b12] text-white">
      <div className="mx-auto flex min-h-screen max-w-7xl flex-col justify-center px-5 py-10">
        <div className="max-w-2xl">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-cyan-300/30 bg-cyan-300/10 px-3 py-1 text-sm text-cyan-100">
            <RefreshCw className="h-4 w-4 animate-spin" />
            Loading NASA and NOAA open feeds
          </div>
          <div className="h-12 w-3/4 rounded bg-white/10" />
          <div className="mt-4 h-5 w-full rounded bg-white/10" />
          <div className="mt-2 h-5 w-2/3 rounded bg-white/10" />
          <div className="mt-10 grid gap-4 md:grid-cols-4">
            {[0, 1, 2, 3].map((item) => (
              <div key={item} className="h-28 rounded-lg border border-white/10 bg-white/[0.06]" />
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <main className="min-h-screen bg-[#070b12] text-white">
      <div className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center px-5 py-10">
        <div className="rounded-lg border border-rose-300/30 bg-rose-300/10 p-6">
          <AlertTriangle className="mb-4 h-8 w-8 text-rose-200" />
          <h1 className="text-2xl font-semibold">Open data could not be loaded</h1>
          <p className="mt-3 text-sm leading-6 text-rose-50/80">{message}</p>
          <button
            type="button"
            onClick={onRetry}
            className="mt-5 inline-flex items-center gap-2 rounded-md bg-white px-4 py-2 text-sm font-semibold text-[#111827] transition hover:bg-cyan-50"
          >
            <RefreshCw className="h-4 w-4" />
            Retry
          </button>
        </div>
      </div>
    </main>
  );
}

function MetricCard({
  label,
  value,
  detail,
  icon: Icon,
}: {
  label: string;
  value: string;
  detail: string;
  icon: typeof Activity;
}) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.06] p-4">
      <div className="mb-4 flex h-9 w-9 items-center justify-center rounded-md bg-white/10 text-cyan-100">
        <Icon className="h-5 w-5" />
      </div>
      <div className="text-2xl font-semibold tracking-normal text-white">{value}</div>
      <div className="mt-1 text-sm font-medium text-white/80">{label}</div>
      <p className="mt-2 text-xs leading-5 text-white/55">{detail}</p>
    </div>
  );
}

function RoleButton({
  role,
  active,
  onClick,
}: {
  role: RoleStory;
  active: boolean;
  onClick: () => void;
}) {
  const Icon = roleIcons[role.id];

  return (
    <button
      type="button"
      onClick={onClick}
      className={`min-h-[112px] rounded-lg border p-4 text-left transition ${
        active
          ? 'border-cyan-200 bg-cyan-200/10 shadow-[0_0_0_1px_rgba(165,243,252,0.3)]'
          : 'border-white/10 bg-white/[0.04] hover:border-white/30 hover:bg-white/[0.07]'
      }`}
    >
      <div className="flex items-center gap-3">
        <span className="flex h-9 w-9 items-center justify-center rounded-md bg-white/10 text-cyan-100">
          <Icon className="h-5 w-5" />
        </span>
        <span>
          <span className="block text-sm font-semibold text-white">{role.title}</span>
          <span className="mt-1 block text-xs text-white/55">{role.audience}</span>
        </span>
      </div>
      <p className="mt-3 text-xs leading-5 text-white/65">{role.signal}</p>
    </button>
  );
}

function EmptyEvents() {
  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.04] p-5 text-sm text-white/65">
      <ShieldCheck className="mb-3 h-6 w-6 text-emerald-200" />
      No recent DONKI event dominates this snapshot. The app still shows NOAA context so quiet space weather can be used as a baseline.
    </div>
  );
}

export default function SolarStorylinePage() {
  const [snapshot, setSnapshot] = useState<SpaceWeatherSnapshot | null>(null);
  const [selectedRole, setSelectedRole] = useState<RoleKey>('student');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [epicImageFailed, setEpicImageFailed] = useState(false);

  const loadSnapshot = async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);

    setError(null);
    setEpicImageFailed(false);

    try {
      const data = await fetchSpaceWeatherSnapshot();
      setSnapshot(data);
      setSelectedRole((current) => data.roles.find((role) => role.id === current)?.id || 'student');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unexpected error loading open data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadSnapshot();
  }, []);

  const activeRole = useMemo(() => {
    if (!snapshot) return null;
    return snapshot.roles.find((role) => role.id === selectedRole) || snapshot.roles[0];
  }, [selectedRole, snapshot]);

  if (loading) return <LoadingState />;
  if (error || !snapshot || !activeRole) {
    return <ErrorState message={error || 'Snapshot was empty'} onRetry={() => loadSnapshot()} />;
  }

  const RoleIcon = roleIcons[activeRole.id];

  return (
    <>
      <Head>
        <title>Solar Storyline | NASA Space Apps MVP</title>
        <meta
          name="description"
          content="A role-based space weather storytelling MVP using NASA DONKI, NASA EPIC, NASA GIBS, and NOAA SWPC open data."
        />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <main className="min-h-screen bg-[#070b12] text-white">
        <section className="relative overflow-hidden border-b border-white/10">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_22%_12%,rgba(250,204,21,0.28),transparent_30%),radial-gradient(circle_at_86%_10%,rgba(34,211,238,0.18),transparent_34%),linear-gradient(135deg,#0b1120_0%,#111827_50%,#15110d_100%)]" />
          <div className="relative mx-auto grid max-w-7xl gap-8 px-5 py-8 lg:grid-cols-[1.05fr_0.95fr] lg:px-8 lg:py-10">
            <div className="flex flex-col justify-between">
              <div>
                <div className="mb-5 flex flex-wrap items-center gap-2">
                  <span className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em] ${levelStyles[snapshot.activityLevel]}`}>
                    <Activity className="h-4 w-4" />
                    {snapshot.activityLevel}
                  </span>
                  <span className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs text-white/75">
                    <Database className="h-4 w-4" />
                    {dataModeLabel(snapshot)}
                  </span>
                </div>

                <h1 className="max-w-3xl text-4xl font-semibold tracking-normal text-white sm:text-5xl">
                  Solar Storyline
                </h1>
                <p className="mt-4 max-w-2xl text-base leading-7 text-white/75">
                  A NASA Space Apps MVP that turns live space weather data into role-based stories people can act on and understand.
                </p>
              </div>

              <div className="mt-8 grid gap-3 sm:grid-cols-3">
                <div className="rounded-lg border border-white/10 bg-black/20 p-4">
                  <div className="text-xs uppercase tracking-[0.12em] text-white/45">Activity score</div>
                  <div className="mt-2 text-3xl font-semibold">{snapshot.activityScore}/100</div>
                </div>
                <div className="rounded-lg border border-white/10 bg-black/20 p-4">
                  <div className="text-xs uppercase tracking-[0.12em] text-white/45">Confidence</div>
                  <div className="mt-2 text-3xl font-semibold">{Math.round(snapshot.confidence * 100)}%</div>
                </div>
                <div className="rounded-lg border border-white/10 bg-black/20 p-4">
                  <div className="text-xs uppercase tracking-[0.12em] text-white/45">Updated</div>
                  <div className="mt-2 text-lg font-semibold">{formatTime(snapshot.generatedAt)}</div>
                </div>
              </div>
            </div>

            <div className="min-h-[420px] overflow-hidden rounded-lg border border-white/10 bg-black/30">
              {snapshot.epicImageUrl && !epicImageFailed ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={snapshot.epicImageUrl}
                  alt="NASA EPIC recent Earth imagery"
                  className="h-72 w-full object-cover"
                  onError={() => setEpicImageFailed(true)}
                />
              ) : (
                <div className="flex h-72 items-center justify-center bg-[radial-gradient(circle_at_center,rgba(34,197,94,0.28),transparent_34%),linear-gradient(135deg,#0f172a,#111827)]">
                  <Globe2 className="h-20 w-20 text-cyan-100/80" />
                </div>
              )}
              <div className="p-5">
                <div className="flex items-center gap-2 text-sm font-semibold text-cyan-100">
                  <Sun className="h-4 w-4" />
                  {snapshot.headline}
                </div>
                <p className="mt-3 text-sm leading-6 text-white/70">{snapshot.summary}</p>
                <button
                  type="button"
                  onClick={() => loadSnapshot(true)}
                  disabled={refreshing}
                  className="mt-5 inline-flex items-center gap-2 rounded-md border border-white/15 bg-white/10 px-4 py-2 text-sm font-semibold text-white transition hover:bg-white/15 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
                  Refresh open data
                </button>
              </div>
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-7xl px-5 py-8 lg:px-8">
          {snapshot.warnings.length > 0 && (
            <div className="mb-6 rounded-lg border border-amber-300/30 bg-amber-300/10 p-4 text-sm text-amber-50">
              <div className="mb-2 flex items-center gap-2 font-semibold">
                <AlertTriangle className="h-4 w-4" />
                Data caveats
              </div>
              <ul className="space-y-1 text-amber-50/80">
                {snapshot.warnings.slice(0, 4).map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              icon={Sun}
              label="Recent DONKI events"
              value={`${snapshot.metrics.cmeCount + snapshot.metrics.flareCount + snapshot.metrics.sepCount + snapshot.metrics.stormCount}`}
              detail={`${snapshot.metrics.cmeCount} CMEs (${snapshot.metrics.earthDirectedCmeCount} Earth-directed), ${snapshot.metrics.flareCount} flares, ${snapshot.metrics.sepCount} SEP, ${snapshot.metrics.stormCount} GST`}
            />
            <MetricCard
              icon={Radio}
              label="Strongest flare"
              value={snapshot.metrics.strongestFlare}
              detail="Solar flares can affect radio quickly when they are strong and Earth-facing."
            />
            <MetricCard
              icon={Activity}
              label="Planetary K index"
              value={formatNumber(snapshot.metrics.kpIndex)}
              detail="Kp summarizes global geomagnetic disturbance on a 0 to 9 scale."
            />
            <MetricCard
              icon={ArrowRight}
              label="Solar wind"
              value={formatNumber(snapshot.metrics.solarWindSpeed, ' km/s')}
              detail={`Bz magnetic field: ${formatNumber(snapshot.metrics.bzGsm, ' nT')}`}
            />
          </div>
        </section>

        <section className="mx-auto grid max-w-7xl gap-6 px-5 pb-8 lg:grid-cols-[0.95fr_1.05fr] lg:px-8">
          <div>
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.12em] text-white/50">
              <BookOpen className="h-4 w-4" />
              Pick the human story
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {snapshot.roles.map((role) => (
                <RoleButton
                  key={role.id}
                  role={role}
                  active={role.id === activeRole.id}
                  onClick={() => setSelectedRole(role.id)}
                />
              ))}
            </div>
          </div>

          <div className="rounded-lg border border-white/10 bg-white/[0.06] p-6">
            <div className="flex items-start gap-4">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-cyan-200/10 text-cyan-100">
                <RoleIcon className="h-6 w-6" />
              </div>
              <div>
                <div className="text-sm uppercase tracking-[0.14em] text-cyan-100/70">{activeRole.audience}</div>
                <h2 className="mt-2 text-2xl font-semibold tracking-normal">{activeRole.title}</h2>
              </div>
            </div>

            <div className="mt-6 rounded-lg border border-cyan-200/15 bg-cyan-200/10 p-4">
              <div className="text-sm font-semibold text-cyan-50">{activeRole.signal}</div>
              <p className="mt-2 text-sm leading-6 text-white/75">{activeRole.summary}</p>
            </div>

            <p className="mt-5 text-sm leading-6 text-white/70">{activeRole.whyItMatters}</p>

            <div className="mt-6">
              <div className="mb-3 text-sm font-semibold text-white">Recommended demo talking points</div>
              <div className="grid gap-2">
                {activeRole.actions.map((action) => (
                  <div key={action} className="flex items-start gap-2 text-sm text-white/70">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-200" />
                    <span>{action}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="mx-auto grid max-w-7xl gap-6 px-5 pb-8 lg:grid-cols-[1fr_1fr] lg:px-8">
          <div className="rounded-lg border border-white/10 bg-white/[0.05] p-6">
            <div className="mb-5 flex items-center gap-2">
              <Clock3 className="h-5 w-5 text-amber-100" />
              <h2 className="text-lg font-semibold">Sun to Earth timeline</h2>
            </div>
            <div className="space-y-4">
              {snapshot.timeline.map((step) => (
                <div key={step.label} className="grid grid-cols-[auto_1fr] gap-4">
                  <div className="flex flex-col items-center">
                    <div className="h-3 w-3 rounded-full bg-cyan-200" />
                    <div className="mt-2 h-full w-px bg-white/15" />
                  </div>
                  <div className="pb-4">
                    <div className="text-sm font-semibold text-white">{step.label}</div>
                    <div className="mt-1 text-xs uppercase tracking-[0.12em] text-white/45">{step.time}</div>
                    <div className="mt-2 text-sm font-medium text-cyan-100">{step.status}</div>
                    <p className="mt-1 text-sm leading-6 text-white/65">{step.detail}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-lg border border-white/10 bg-white/[0.05] p-6">
            <div className="mb-5 flex items-center gap-2">
              <Database className="h-5 w-5 text-cyan-100" />
              <h2 className="text-lg font-semibold">Evidence and sources</h2>
            </div>

            <div className="mb-5">
              <div className="mb-3 text-sm font-semibold text-white">Recent DONKI evidence</div>
              {snapshot.events.length ? (
                <div className="space-y-3">
                  {snapshot.events.slice(0, 4).map((event) => (
                    <a
                      key={`${event.type}-${event.id}`}
                      href={event.sourceUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="block rounded-lg border border-white/10 bg-black/20 p-4 transition hover:border-cyan-200/40"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-sm font-semibold text-white">{event.title}</span>
                        <span className="rounded-full bg-white/10 px-2 py-1 text-xs text-white/65">{event.type}</span>
                      </div>
                      <div className="mt-2 text-xs text-white/45">{formatTime(event.time)} | {event.id}</div>
                      <p className="mt-2 text-sm leading-5 text-white/65">{event.detail}</p>
                    </a>
                  ))}
                </div>
              ) : (
                <EmptyEvents />
              )}
            </div>

            <div>
              <div className="mb-3 text-sm font-semibold text-white">Feed health</div>
              <div className="space-y-2">
                {snapshot.sources.map((source) => (
                  <a
                    key={source.name}
                    href={source.url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center justify-between gap-3 rounded-md border border-white/10 bg-black/20 px-3 py-2 text-sm transition hover:border-white/25"
                  >
                    <span className="min-w-0 truncate text-white/75">{source.name}</span>
                    <span className={source.status === 'ok' ? 'text-emerald-200' : 'text-amber-200'}>
                      {source.status === 'ok' ? 'Loaded' : 'Check'}
                    </span>
                  </a>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-7xl px-5 pb-10 lg:px-8">
          <div className="rounded-lg border border-white/10 bg-black/25 p-5 text-sm leading-6 text-white/60">
            <strong className="text-white">Scientific caveat:</strong> Solar Storyline is an educational NASA Space Apps prototype.
            It uses NASA and NOAA open data to explain space weather context, but it is not an official operational forecast.
            Operational decisions should use NOAA Space Weather Prediction Center products and mission-specific procedures.
          </div>
        </section>
      </main>
    </>
  );
}
