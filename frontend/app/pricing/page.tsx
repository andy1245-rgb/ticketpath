import type { Metadata } from "next";
import { Suspense } from "react";
import { ApiError, getHealth } from "@/lib/api";
import type { Health } from "@/lib/types";
import { Chip, DataSourceNote, Skeleton } from "@/components/ui";

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

  const { dataSource, chain, pricingModel, contract } = health;

  return (
    <>
      <section className="mt-12">
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
        <h2 className="h-section text-ink">The pricing model</h2>

        {pricingModel.available ? (
          <p className="t-body mt-2 text-ink">
            The pricing model is a rule-based bounded estimator. Nothing was fitted behind it, and
            the price bound it returns is unvalidated.
          </p>
        ) : (
          <div className="mt-4 rounded-panel border border-line bg-surface p-6">
            <p className="t-micro-caps text-muted">Not available</p>
            <p className="figure t-meta mt-2 text-ink">{pricingModel.reason}</p>
            {pricingModel.note && (
              <p className="t-body mt-2 text-muted">{pricingModel.note}</p>
            )}
          </div>
        )}

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

export default function PricingPage(): React.ReactElement {
  return (
    <div className="box pt-16 pb-24">
      <div className="max-w-4xl">
        <h1 className="h-display text-ink">Pricing and data</h1>
        <p className="t-deck mt-4 text-muted">
          What this deployment computes, what it only describes, and where each number came from.
        </p>

        <Suspense
          fallback={
            <div className="mt-12">
              <Skeleton lines={5} />
            </div>
          }
        >
          <HealthReport />
        </Suspense>
      </div>
    </div>
  );
}
