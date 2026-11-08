import type { Metadata } from "next";
import { ApiError, getGuidance, getHealth } from "@/lib/api";
import type { Guidance, Health } from "@/lib/types";
import run from "@/data/sim-run.json";
import { Chip, DataSourceNote } from "@/components/ui";

export const metadata: Metadata = {
  title: "Pricing and data",
  description:
    "What this deployment computes, what it only describes, and where each of its numbers came from.",
};

/**
 * The console is HTML at the backend's own origin, so the only thing this page
 * needs is that origin. It is read here rather than from lib/api because it is
 * configuration, not a payload, and the page never fetches from it: an iframe
 * would put the backend's HTML inside this document, and this page links out
 * instead.
 */
const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "").trim().replace(/\/+$/, "");

/** A raw wire value, printed as it arrived. `null` means the field is absent. */
function raw(value: string | number | boolean | null): string {
  return value === null ? "null" : String(value);
}

function Field({
  label,
  value,
  mono = true,
  note,
}: {
  label: string;
  value: string;
  /** False for a sentence the backend wrote, true for a machine value. */
  mono?: boolean;
  note?: string;
}): React.ReactElement {
  return (
    <div>
      <dt className="figure t-micro text-muted">{label}</dt>
      <dd className={`mt-1 break-words text-ink ${mono ? "figure t-meta" : "t-body"}`}>
        {value}
      </dd>
      {note && <p className="t-micro mt-1 text-muted">{note}</p>}
    </div>
  );
}

function ReadFailure({ message, code }: { message: string; code: string }): React.ReactElement {
  return (
    <div role="alert" className="mt-12 rounded-panel border border-danger bg-surface p-6">
      <Chip tone="danger">Failed</Chip>
      <h2 className="h-section mt-3 text-ink">The health read failed</h2>
      <dl className="mt-4 space-y-3">
        <div>
          <dt className="t-micro-caps text-muted">Message</dt>
          <dd className="t-body mt-1 text-ink">{message}</dd>
        </div>
        <div>
          <dt className="t-micro-caps text-muted">Code</dt>
          <dd className="figure t-meta mt-1 text-ink">{code}</dd>
        </div>
      </dl>
    </div>
  );
}

/**
 * The agents, grouped by the policy they ran: nine rows of one policy each is
 * nine lines nobody reads, and the grouping is the count the paragraph needs.
 */
function policySummary(agents: ReadonlyArray<{ policy: string }>): string {
  const counts = new Map<string, number>();
  for (const agent of agents) {
    counts.set(agent.policy, (counts.get(agent.policy) ?? 0) + 1);
  }
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .map(([policy, count]) => `${count} ${policy.replace(/_/g, " ")}`)
    .join(", ");
}

/**
 * The recorded run. It reads one committed file, `frontend/data/sim-run.json`,
 * transcribed by `tools/swarm_panel.py` from that run's own meta files, and it
 * prints the run's label verbatim: scripted agents, a dry run, synthetic data.
 *
 * The figures here are the ones on disk, which is a nine-agent scripted run and
 * not the six-agent live run the film's voice describes. Pairing six-agent
 * numbers with the charts below, which belong to this run, would attribute one
 * run's numbers to another; the panel says which run it is and the voice is
 * corrected to match, never the other way round.
 */
function RunPanel(): React.ReactElement {
  return (
    <section id="what-was-run" className="mt-16 scroll-mt-24">
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="h-section text-ink">What was run</h2>
        <Chip tone="neutral">{run.label}</Chip>
      </div>

      <p className="t-body mt-2 text-muted">
        {run.agentCount} agents on scripted policies, {run.modes[0]?.rounds ?? 0} rounds: one event
        with the cap in force, one monitored event with no cap. {run.chain}
      </p>

      <dl className="mt-6 grid gap-x-6 gap-y-4 sm:grid-cols-2">
        <Field label="run" value={run.runId} />
        <Field label="recorded" value={run.recordedOn} />
        <Field label="agents" value={String(run.agentCount)} note={policySummary(run.agents)} />
        <Field
          label="cost"
          value={run.cost.usd === null ? "no model calls" : `$${String(run.cost.usd)}`}
          note={run.cost.reason}
        />
      </dl>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        {run.modes.map((mode) => (
          <div key={mode.mode} className="rounded-panel border border-line bg-surface p-6">
            <div className="flex flex-wrap items-center gap-3">
              <p className="t-micro-caps text-muted">{mode.mode}</p>
              <span className="figure t-micro text-muted">
                {/* 65535 is the harness's uncapped sentinel, not a 655% cap. */}
                {mode.capBps === null || mode.capBps >= 65_535
                  ? "cap none"
                  : `cap ${mode.capBps} bps`}{" "}
                · ceiling{" "}
                {mode.ceilingLamports === null
                  ? "none"
                  : `${mode.ceilingLamports.toLocaleString("en-US")} lamports`}
              </span>
            </div>
            <p className="figure t-meta mt-3 text-ink">
              {mode.decisions.executed.toLocaleString("en-US")} executed ·{" "}
              {mode.decisions.refused.toLocaleString("en-US")} refused ·{" "}
              {mode.decisions.skipped.toLocaleString("en-US")} skipped
            </p>
            <p className="t-micro mt-1 text-muted">
              {mode.decisions.total.toLocaleString("en-US")} decisions over {mode.rounds} rounds.{" "}
              {mode.tickets.toLocaleString("en-US")} tickets.
            </p>
            {/* A static SVG out of `public/charts`, copied there from
                `docs/charts` by the same tool that wrote the JSON. next/image
                cannot optimise an SVG without a flag and would inline it as a
                data URL, so this is a plain image. */}
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={mode.chart}
              alt={`Price path for the ${mode.mode} run: every recorded sale against its ceiling`}
              className="mt-4 w-full rounded-card border border-line bg-surface"
            />
          </div>
        ))}
      </div>

      <p className="t-micro mt-4 text-muted">{run.sourceNote}</p>
    </section>
  );
}

/**
 * The engine's refusals for the selection this page reads, with the count.
 *
 * The count is printed, not assumed: it is a property of the event and the tier
 * the engine was asked about, and the sentence a person says out loud has to
 * match the number on the frame. The panel names the event it computed for so
 * the two can be checked against each other.
 */
async function RefusalPanel(): Promise<React.ReactElement> {
  let guidance: Guidance;
  try {
    guidance = await getGuidance();
  } catch (error) {
    const message =
      error instanceof ApiError ? error.message : "The refusal list could not be read.";
    const code = error instanceof ApiError ? error.code : "unexpected_error";
    return (
      <section className="mt-12">
        <h2 className="h-section text-ink">What the engine returns, and what it refuses</h2>
        <div role="alert" className="mt-4 rounded-panel border border-danger bg-surface p-6">
          <Chip tone="danger">No list</Chip>
          <p className="t-body mt-3 text-ink">
            The engine&rsquo;s refusals were not read, so this page prints no count. A zero here
            would be a measurement nobody made.
          </p>
          <p className="figure t-micro mt-2 text-muted">
            {message} ({code})
          </p>
        </div>
      </section>
    );
  }

  return (
    <section id="refusals" className="mt-12 scroll-mt-24">
      <h2 className="h-section text-ink">What the engine returns, and what it refuses</h2>
      <p className="t-body mt-2 text-muted">
        For {guidance.event.name}
        {guidance.tier ? `, ${guidance.tier.name}` : ""}, the engine returns a floor and not a
        forecast: the highest price this tier&rsquo;s own record will carry, offered as an
        unvalidated bound. Every refusal below names an observation this record does not hold.
      </p>

      <div className="mt-6 flex items-baseline gap-4">
        <p className="figure text-[32px] leading-[38px] font-semibold tracking-[-0.02em] text-ink">
          {guidance.count === null ? "—" : guidance.count}
        </p>
        <p className="t-meta text-muted">
          refusals, each naming the observation that is missing
        </p>
      </div>

      <ul className="mt-4 border-t border-line">
        {guidance.refusals.map((refusal) => (
          <li
            key={refusal.code}
            className="flex flex-col gap-1 border-b border-line py-3 sm:flex-row sm:items-baseline sm:gap-6"
          >
            <span className="figure t-micro w-56 shrink-0 text-muted">{refusal.code}</span>
            <span className="t-body text-ink">{refusal.sentence}</span>
          </li>
        ))}
      </ul>
      <p className="t-micro mt-3 text-muted">
        Computed by the backend for {guidance.event.id} at {guidance.asOf}. {guidance.source}.
      </p>
    </section>
  );
}

/**
 * What is computed from the record, what is only described, and what does not
 * exist. Three lists rather than one, because a reader who cannot tell them
 * apart cannot tell what the product does from what it says it does.
 */
function ComputedPanel({ health }: { health: Health }): React.ReactElement {
  const { pricingModel } = health;
  return (
    <section className="mt-16">
      <h2 className="h-section text-ink">Computed, described, and not built</h2>

      <dl className="mt-6 grid gap-x-6 gap-y-4 sm:grid-cols-2">
        <Field label="available" value={raw(pricingModel.available)} />
        <Field
          label="kind"
          value={raw(pricingModel.kind)}
          note={pricingModel.kind === null ? "No model is registered." : undefined}
        />
        <Field
          label="fitted"
          value={raw(pricingModel.fitted)}
          note={pricingModel.fitted === false ? "No model was fitted." : undefined}
        />
        <Field label="modelVersion" value={raw(pricingModel.modelVersion)} />
      </dl>

      {!pricingModel.available && (
        <div className="mt-4 rounded-panel border border-line bg-surface p-6">
          <p className="t-micro-caps text-muted">Not available</p>
          <p className="figure t-meta mt-2 text-ink">{pricingModel.reason}</p>
          {pricingModel.note && <p className="t-body mt-2 text-muted">{pricingModel.note}</p>}
        </div>
      )}

      <div className="mt-8 grid gap-6 lg:grid-cols-3">
        <div className="rounded-panel border border-line bg-surface p-6">
          <p className="t-micro-caps text-muted">Computed</p>
          <p className="t-body mt-2 text-ink">
            A price bound from this event&rsquo;s own resale record, and the cap comparison in whole
            lamports. Both are arithmetic, and both are reproducible from the rows on screen.
          </p>
        </div>
        <div className="rounded-panel border border-line bg-surface p-6">
          <p className="t-micro-caps text-muted">Described</p>
          <p className="t-body mt-2 text-ink">
            The demand response and the fee model. The engine refuses both rather than fitting
            either, so nothing here is a number it made up to fill the shape.
          </p>
        </div>
        <div className="rounded-panel border border-line bg-surface p-6">
          <p className="t-micro-caps text-muted">Not built</p>
          <p className="t-body mt-2 text-ink">
            A sale probability, an upper bound, and an asking price: no listing was ever recorded,
            so no row anywhere holds what a seller wanted.
          </p>
        </div>
      </div>

      <p className="t-micro mt-4 text-muted">
        Nothing was fitted behind the price bound, and the bound itself is unvalidated. The refusal
        list above is what makes that checkable line by line.
      </p>
    </section>
  );
}

/**
 * Everything below the title comes from GET /health. The page's job is to print
 * each field as the backend sent it: a false is printed as false, a null as null,
 * and the one sentence that explains what the fields mean is short enough to be
 * read beside them.
 */
async function HealthReport(): Promise<React.ReactElement> {
  let health: Health;
  try {
    health = await getHealth();
  } catch (error) {
    if (error instanceof ApiError) {
      return <ReadFailure message={error.message} code={error.code} />;
    }
    return (
      <ReadFailure
        message={error instanceof Error ? error.message : "The health read failed."}
        code="unexpected_error"
      />
    );
  }

  const { dataSource, chain, contract } = health;

  return (
    <>
      <ComputedPanel health={health} />

      <section className="mt-16">
        <h2 className="h-section text-ink">Where the data comes from</h2>
        <dl className="mt-6 grid gap-x-6 gap-y-4 sm:grid-cols-2">
          <Field label="Mode" value={dataSource.mode} />
          <Field label="Synthetic" value={raw(dataSource.synthetic)} />
        </dl>
        <div className="mt-4">
          <DataSourceNote dataSource={dataSource} />
          {!dataSource.synthetic && (
            <p className="t-micro mt-1 text-muted">{dataSource.label}</p>
          )}
        </div>
      </section>

      <section className="mt-16">
        <h2 className="h-section text-ink">The chain</h2>
        <p className="t-body mt-2 text-muted">
          What the server was told, what it asked, and what a verified artefact records. These are
          three different things and they are printed as three different fields.
        </p>
        <dl className="mt-6 grid gap-x-6 gap-y-4 sm:grid-cols-2">
          <Field label="programDeployed" value={raw(chain.programDeployed)} />
          <Field label="rpcEnabled" value={raw(chain.rpcEnabled)} />
          <Field label="askedCluster" value={raw(chain.askedCluster)} />
          <Field label="cluster" value={chain.cluster} />
          <Field label="reason" value={chain.reason} />
          <Field label="detail" value={chain.detail} mono={false} />
        </dl>
        <p className="t-micro mt-4 text-muted">
          {chain.askedCluster
            ? "The server queried a cluster, so programDeployed is a read of that cluster."
            : "The server queried no cluster, so programDeployed is the absence of a check rather than the result of one."}
        </p>
      </section>

      <section className="mt-16">
        <h2 className="h-section text-ink">The contract</h2>
        <p className="t-body mt-2 text-muted">
          How much of the documented contract the server says it implements.
        </p>
        <dl className="mt-6 grid gap-x-6 gap-y-4 sm:grid-cols-3">
          <Field label="endpointsInContract" value={raw(contract.endpointsInContract)} />
          <Field label="endpointsImplemented" value={raw(contract.endpointsImplemented)} />
          <Field label="routesImplemented" value={raw(contract.routesImplemented)} />
        </dl>
        <p className="t-micro mt-4 text-muted">Counted against {contract.source}.</p>
      </section>

      <section className="mt-16">
        <h2 className="h-section text-ink">The guidance console</h2>
        {API_BASE ? (
          <p className="t-body mt-2 text-muted">
            The backend serves an HTML console at its own origin.{" "}
            <a
              href={`${API_BASE}/`}
              target="_blank"
              rel="noreferrer"
              className="u-transition text-accent underline underline-offset-2 hover:text-accent-press"
            >
              Open the guidance console
            </a>{" "}
            in a new tab. This page never frames it.
          </p>
        ) : (
          <p className="t-body mt-2 text-muted">
            The console is served by the backend at its own origin. No backend origin is configured
            in this build, so there is nothing here to link to.
          </p>
        )}
      </section>
    </>
  );
}

/**
 * The whole page is awaited before it is sent. It used to wrap the two reads in
 * Suspense, which streamed a skeleton first; that is the right shape for a long
 * page and the wrong one for this page, because a deep link then lands before
 * the panel it names exists, and a frame a camera sees has content arriving in
 * it. Nothing here loads after the page is drawn.
 */
export default async function PricingPage(): Promise<React.ReactElement> {
  const [refusals, health] = await Promise.all([RefusalPanel(), HealthReport()]);

  return (
    <div className="box pt-16 pb-24">
      <div className="max-w-4xl">
        <h1 className="h-display text-ink">Pricing and data</h1>
        <p className="t-deck mt-4 text-muted">
          What this deployment computes, what it only describes, and where each number came from.
        </p>

        {refusals}

        <RunPanel />

        {/* The deep link lands here, above the section that follows, because an
            id inside an async child is not in the first HTML the browser parses
            and a jump to it happens before the element exists. */}
        <span id="computed" aria-hidden="true" className="block scroll-mt-24" />

        {health}
      </div>
    </div>
  );
}
