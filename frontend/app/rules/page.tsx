import type { Metadata } from "next";
import { ApiError, getDevnetRecord, getHealth } from "@/lib/api";
import type { DevnetRecord, Health, SolanaCluster } from "@/lib/types";
import { Chip, DataSourceNote } from "@/components/ui";
import { AddressPill } from "@/components/AddressPill";
import { RecordedOrLive } from "@/components/proof/RecordedOrLive";
import { capCeilingLamports, isWithinCap } from "@/lib/cap";
import { formatBpsPercent, formatDateTime, formatLamports, shortAddress } from "@/lib/format";
import { explorerTxUrl, verificationMessage } from "@/lib/solana";
import v2 from "@/data/devnet-v2.json";

export const metadata: Metadata = {
  title: "How the cap works",
  description:
    "The cap predicate, the worked boundary in lamports, what is fixed at record initialisation, and what is actually enforced at runtime.",
};

/**
 * The predicate is arithmetic and nothing else, so the page demonstrates it with
 * the same functions the rest of the app uses rather than quoting numbers it
 * typed by hand. Face value is one SOL, and the cap is the 2500 bps the fixture
 * events run with.
 */
const FACE = 1_000_000_000;
const CAP_BPS = 2_500;
const CEILING = capCeilingLamports(FACE, CAP_BPS);

const PREDICATE = "price * 10000 <= face * (10000 + cap_bps)";

const ADMITS_CEILING = isWithinCap(CEILING, FACE, CAP_BPS);
const ADMITS_ABOVE_CEILING = isWithinCap(CEILING + 1, FACE, CAP_BPS);

const ARITHMETIC = [
  `face    ${FACE} lamports`,
  `cap     ${CAP_BPS} bps`,
  `bound   face * (10000 + ${CAP_BPS}) = ${FACE * (10_000 + CAP_BPS)}`,
  `price   ${CEILING} * 10000 = ${CEILING * 10_000}   ${ADMITS_CEILING ? "admitted" : "refused"}`,
  `price   ${CEILING + 1} * 10000 = ${(CEILING + 1) * 10_000}   ${ADMITS_ABOVE_CEILING ? "admitted" : "refused"}`,
].join("\n");

/**
 * The frozen message, with its two variable slots named rather than filled. It
 * is built by lib/solana.ts, so every fixed line and the cluster in it are the
 * bytes the backend checks, not a description of them.
 */
const MESSAGE_SLOTS = verificationMessage("<wallet>", "<nonce>");

/**
 * The record carries its cluster as free text off the wire, and the cluster is
 * what an explorer link is built on. Unknown text falls back to devnet, which
 * is the cluster the record was written against.
 */
function clusterOf(name: string | undefined): SolanaCluster {
  return (name ?? "devnet") as SolanaCluster;
}

interface Failure {
  message: string;
  code: string;
}

/**
 * A unix block time as the record carries it. Printed in UTC because this page
 * renders on the server and a local string would differ between two renders of
 * the same record.
 */
function blockTimeLabel(seconds: number | null | undefined): string {
  if (seconds == null) return "—";
  return new Date(seconds * 1000).toLocaleString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "UTC",
  });
}

/** One labelled field of the recorded block, in the page's own two type sizes. */
function Recorded({
  label,
  children,
  mono = true,
}: {
  label: string;
  children: React.ReactNode;
  mono?: boolean;
}): React.ReactElement {
  return (
    <div>
      <dt className="figure t-micro text-muted">{label}</dt>
      <dd className={`mt-1 break-words text-ink ${mono ? "figure t-meta" : "t-body"}`}>
        {children}
      </dd>
    </div>
  );
}

export default async function RulesPage(): Promise<React.ReactElement> {
  let health: Health | null = null;
  let failure: Failure | null = null;
  try {
    health = await getHealth();
  } catch (error) {
    failure =
      error instanceof ApiError
        ? { message: error.message, code: error.code }
        : {
            message: error instanceof Error ? error.message : "The health read failed.",
            code: "unexpected_error",
          };
  }

  // The recorded artefact, read the same way the console reads it. A page that
  // could not read it prints the absence rather than the claim.
  let devnet: DevnetRecord | null = null;
  try {
    devnet = await getDevnetRecord();
  } catch {
    devnet = null;
  }
  const artefact = devnet?.loaded ? devnet.record : null;
  const accepted = artefact?.transfers?.acceptedAtCap ?? null;
  const refused = artefact?.transfers?.refusedOverCap ?? null;

  return (
    <div className="box pt-16 pb-24">
      <div className="max-w-3xl">
        <h1 className="h-display text-ink">How the cap works</h1>
        <p className="t-deck mt-4 text-muted">
          A resale price is admitted or refused by one comparison between integers. This page shows
          the comparison, works its boundary, and then says plainly what enforces it today.
        </p>

        <section className="mt-16">
          <div className="flex flex-wrap items-center gap-4">
            <h2 className="h-section text-ink">The predicate</h2>
            <Chip tone="warning">Cap {formatBpsPercent(CAP_BPS)}</Chip>
          </div>
          <pre className="figure t-meta mt-6 whitespace-pre-wrap break-words rounded-panel border border-line bg-inset p-6 text-ink">
            {PREDICATE}
          </pre>
          <p className="t-body mt-4 text-muted">
            Every term is an integer. There is no division in the predicate and no rounding, so the
            boundary is exact: a price on the ceiling is admitted, and one lamport above it is
            refused.
          </p>
          <p className="t-body mt-2 text-muted">
            The warning colour appears only where the cap is at issue: this chip, the dashed rule a
            price chart draws at the ceiling, and the &ldquo;above the cap&rdquo; chip on a listing
            form.
          </p>
        </section>

        <section className="mt-16">
          <h2 className="h-section text-ink">The boundary, in whole lamports</h2>
          <p className="t-body mt-2 text-muted">
            One SOL of face value, capped at 2500 bps over it. The five lines are the comparison
            above with those numbers in it.
          </p>
          <pre className="figure t-meta mt-6 whitespace-pre-wrap break-words rounded-panel border border-line bg-inset p-6 text-ink">
            {ARITHMETIC}
          </pre>
          <dl className="mt-6 space-y-4">
            <div>
              <dt className="t-micro-caps text-muted">The ceiling</dt>
              <dd className="figure t-meta mt-1 text-ink">{formatLamports(CEILING)} lamports</dd>
              <dd className="t-micro mt-1 text-muted">
                Computed as face * (10000 + cap_bps) / 10000, floored.
              </dd>
            </div>
            <div>
              <dt className="t-micro-caps text-muted">One lamport above it</dt>
              <dd className="figure t-meta mt-1 text-ink">{formatLamports(CEILING + 1)} lamports</dd>
              <dd className="t-micro mt-1 text-muted">Refused. This is the case that matters.</dd>
            </div>
          </dl>
        </section>

        <section className="mt-16">
          <h2 className="h-section text-ink">What is fixed, and when</h2>
          <p className="t-body mt-2 text-muted">
            The cap is set once, at InitializeRecord. The instruction takes the face value and the
            cap in basis points as arguments, and there is no instruction that changes either one
            afterwards. The cap in basis points is immutable: an organiser who wanted a different
            number would be initialising a different record.
          </p>
          <p className="t-body mt-2 text-muted">
            The ceiling actually enforced is <span className="figure">min(cap, jurisdiction limit)</span>,
            so it can only be lower than the cap. The gate resolves the legal ceiling for the region,
            compares it with the platform cap, and takes the lower of the two. That is the one thing
            that moves, and it moves one way.
          </p>
        </section>

        <section id="enforcement-today" className="mt-16 scroll-mt-24">
          <h2 className="h-section text-ink">Enforcement today</h2>

          {artefact ? (
            <>
              <div className="mt-3 flex flex-wrap items-center gap-3">
                <RecordedOrLive askedCluster={health?.chain.askedCluster ?? null} verifiedAt={artefact.checkedAt} />
                <Chip tone="neutral">Program v1 · {artefact.cluster ?? "a cluster"}</Chip>
              </div>
              <p className="t-body mt-4 text-ink">
                The v1 cap program is deployed on Solana {artefact.cluster ?? "devnet"}. A verified
                run recorded the program id, the mint it guards, and two transfers against it: one
                priced exactly at the ceiling, which executed, and one lamport above it, which the
                program refused. The panel below is that record, printed as it was written.
              </p>

              <div className="mt-6 rounded-panel border border-line bg-surface p-6">
                <p className="t-micro-caps text-muted">The recorded deployment</p>
                <dl className="mt-4 grid gap-x-6 gap-y-4 sm:grid-cols-2">
                  <div>
                    <dt className="figure t-micro text-muted">program v1</dt>
                    <dd className="mt-1 break-words text-ink">
                      {artefact.programId ? (
                        <AddressPill address={artefact.programId} label="program address" />
                      ) : (
                        "—"
                      )}
                    </dd>
                  </div>
                  <Recorded label="cluster">{artefact.cluster ?? "—"}</Recorded>
                  <Recorded label="verification instant">
                    {formatDateTime(artefact.checkedAt)}
                  </Recorded>
                  <Recorded label="quote signature">
                    {artefact.signature ? (
                      <a
                        href={artefact.explorer?.transaction ?? "#"}
                        target="_blank"
                        rel="noopener noreferrer"
                        title={artefact.signature}
                        className="u-transition underline-offset-4 hover:underline"
                      >
                        {shortAddress(artefact.signature, 8, 8)}
                      </a>
                    ) : (
                      "—"
                    )}
                  </Recorded>
                  <Recorded label="slot">{artefact.slot?.toLocaleString("en-US") ?? "—"}</Recorded>
                  <Recorded label="block time">{blockTimeLabel(artefact.blockTime)}</Recorded>
                </dl>
                <p className="t-micro mt-4 text-muted">
                  The record&rsquo;s three links:{" "}
                  {[
                    ["program", artefact.explorer?.program],
                    ["mint", artefact.explorer?.mint],
                    ["quote transaction", artefact.explorer?.transaction],
                  ].map(([label, href], index) =>
                    href ? (
                      <span key={label}>
                        {index > 0 && " · "}
                        <a
                          href={href}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="u-transition text-accent underline underline-offset-2 hover:text-accent-press"
                        >
                          {label}
                        </a>
                      </span>
                    ) : null,
                  )}{" "}
                  on the Solana explorer. The mint {" "}
                  <span className="figure">
                    {shortAddress(artefact.mint, 6, 6)}
                  </span>{" "}
                  is the token the program guards.
                </p>
              </div>

              {(accepted || refused) && (
                <div className="mt-6 rounded-panel border border-line bg-surface p-6">
                  <p className="t-micro-caps text-muted">The boundary, executed</p>
                  <div className="mt-4 grid gap-x-6 gap-y-6 sm:grid-cols-2">
                    {accepted && (
                      <div>
                        <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
                          <Chip tone="positive">Executed</Chip>
                          <span className="figure t-meta text-ink">
                            {formatLamports(accepted.priceLamports)} lamports
                          </span>
                        </div>
                        <p className="mt-3 space-y-1">
                          <a
                            href={explorerTxUrl(accepted.signature ?? "", clusterOf(artefact.cluster))}
                            target="_blank"
                            rel="noopener noreferrer"
                            title={accepted.signature}
                            className="figure t-micro block break-words text-accent underline underline-offset-2 hover:text-accent-press"
                          >
                            {shortAddress(accepted.signature, 8, 8)}
                          </a>
                          <span className="figure t-micro block text-muted">
                            slot {accepted.slot?.toLocaleString("en-US") ?? "—"} ·{" "}
                            {blockTimeLabel(accepted.blockTime)}
                          </span>
                        </p>
                      </div>
                    )}
                    {refused && (
                      <div>
                        <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
                          <Chip tone="danger">Refused</Chip>
                          <span className="figure t-meta text-ink">
                            {formatLamports(refused.priceLamports)} lamports
                          </span>
                        </div>
                        <p className="mt-3 space-y-1">
                          <span className="figure t-micro block break-words text-ink">
                            {refused.error ?? "—"}
                          </span>
                          <a
                            href={explorerTxUrl(refused.signature ?? "", clusterOf(artefact.cluster))}
                            target="_blank"
                            rel="noopener noreferrer"
                            title={refused.signature}
                            className="figure t-micro block break-words text-accent underline underline-offset-2 hover:text-accent-press"
                          >
                            {shortAddress(refused.signature, 8, 8)}
                          </a>
                          <span className="figure t-micro block text-muted">
                            slot {refused.slot?.toLocaleString("en-US") ?? "—"} ·{" "}
                            {blockTimeLabel(refused.blockTime)}
                          </span>
                        </p>
                      </div>
                    )}
                  </div>
                  <p className="t-micro mt-4 text-muted">
                    Each signature is a link to its transaction, and each opens the
                    transaction that carries the refusal or the execution itself.
                  </p>
                </div>
              )}

              <div className="mt-6 rounded-panel border border-line bg-surface p-6">
                <p className="t-micro-caps text-muted">The fee legs</p>
                <p className="t-body mt-2 text-muted">
                  The artist fee and the 15% flip tax are seller-paid lamport legs inside the same
                  sale transaction, so the buyer pays the price and the seller carries both. They
                  are measured by <span className="figure">tools/artist_fee_proof.py</span> and{" "}
                  <span className="figure">tools/flip_tax_proof.py</span> on a throw-away local
                  validator, not by the two transfers above: those were priced on an event with no
                  fee turned on, so neither carries a fee leg. The tax is off unless an event
                  enables it and runs from 15% under an hour toward zero at thirty days, and the
                  program does not enforce it: a sale can move the ticket and pay nothing.
                </p>
              </div>

              <p className="t-body mt-4 text-muted">
                The current v2 program is {" "}
                <a
                  href={v2.explorer?.program ?? "#"}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="u-transition text-accent underline underline-offset-2 hover:text-accent-press"
                >
                  {shortAddress(v2.programId, 8, 8)}
                </a>{" "}
                on Solana {v2.cluster}, written at {formatDateTime(v2.writtenAt)}. The frozen record
                above predates it and names the program it was published against; the two are not
                the same id and neither one is substituted for the other here.
              </p>

              <p className="t-micro mt-3 text-muted">
                Read from {devnet?.source || "the artefact file"} at build time. This build asked
                no cluster, so this is the recorded verification and not a live re-read: the fields
                above are what a verified run wrote, and they stay what it wrote.
              </p>
            </>
          ) : (
            <p className="t-body mt-2 text-ink">
              No verified artefact is available to this build, so this page prints no deployment.
              {devnet?.reason ? ` ${devnet.reason}` : ""} The predicate and the arithmetic above
              are the program&rsquo;s own rules and stand whatever any cluster holds.
            </p>
          )}

          {health ? (
            <>
              <dl className="mt-6 grid gap-x-6 gap-y-4 sm:grid-cols-2">
                <div>
                  <dt className="figure t-micro text-muted">chain.programDeployed</dt>
                  <dd className="figure t-meta mt-1 text-ink">
                    {String(health.chain.programDeployed)}
                  </dd>
                </div>
                <div>
                  <dt className="figure t-micro text-muted">chain.cluster</dt>
                  <dd className="figure t-meta mt-1 break-words text-ink">{health.chain.cluster}</dd>
                </div>
                <div>
                  <dt className="figure t-micro text-muted">chain.askedCluster</dt>
                  <dd className="figure t-meta mt-1 text-ink">
                    {String(health.chain.askedCluster)}
                  </dd>
                </div>
                <div>
                  <dt className="figure t-micro text-muted">chain.reason</dt>
                  <dd className="figure t-meta mt-1 break-words text-ink">{health.chain.reason}</dd>
                </div>
              </dl>
              <p className="t-body mt-4 text-muted">{health.chain.detail}</p>
              <p className="t-micro mt-3 text-muted">
                {health.chain.askedCluster
                  ? "This build queried a cluster, so this is a read of that cluster rather than a claim about it."
                  : "This build queried no cluster, so programDeployed records that no check was made. It is not a statement that the program is absent: the recorded deployment above is what a verified run wrote."}
              </p>
              <div className="mt-4">
                <DataSourceNote dataSource={health.dataSource} />
              </div>
            </>
          ) : (
            <p className="t-body mt-4 text-muted">
              This page could not reach <span className="figure">/health</span>, so it prints no
              programDeployed figure: the sentence above is the status without a number. The figure
              comes from the backend&rsquo;s own health report, which is where a deployment claim is
              actually checked.
              {failure && (
                <>
                  {" "}
                  <span className="figure t-micro">
                    {failure.message} ({failure.code})
                  </span>
                </>
              )}
            </p>
          )}
        </section>

        <section id="security" className="mt-16 scroll-mt-24">
          <h2 className="h-section text-ink">Security model</h2>
          <p className="t-body mt-2 text-muted">
            There is no account and no session in this backend. Nothing authorizes a caller, so every
            screen in this build is open. The one check the backend performs is the signature below,
            and it proves exactly one thing: that whoever asked holds the private key for the wallet
            in the message.
          </p>
          <p className="t-body mt-2 text-muted">
            This deployment is a static export: the reads on this page happened at build time and
            nothing is asked at request time, so that check runs nowhere on this site. /verify says
            so on the screen where a visitor would look for it. The check described here is the one
            the backend implements, and the rest of this section is its specification rather than a
            record of a verification.
          </p>
          <dl className="mt-6 grid gap-x-6 gap-y-4 sm:grid-cols-2">
            <div>
              <dt className="t-micro-caps text-muted">Signature</dt>
              <dd className="t-meta mt-1 text-ink">
                Ed25519, detached, over a frozen message
              </dd>
            </div>
            <div>
              <dt className="t-micro-caps text-muted">Nonce</dt>
              <dd className="t-meta mt-1 text-ink">32 hex characters</dd>
            </div>
            <div>
              <dt className="t-micro-caps text-muted">Lifetime</dt>
              <dd className="figure t-meta mt-1 text-ink">300 seconds</dd>
            </div>
            <div>
              <dt className="t-micro-caps text-muted">Use</dt>
              <dd className="t-meta mt-1 text-ink">Once</dd>
            </div>
            <div>
              <dt className="t-micro-caps text-muted">Bound to</dt>
              <dd className="t-meta mt-1 text-ink">The wallet that asked for it</dd>
            </div>
          </dl>

          <p className="t-body mt-8 text-muted">
            The message is rebuilt byte for byte on the backend before the signature is checked. Its
            first line, its blank line and its cluster are fixed, and the format belongs to one
            function in this front end. Changing it invalidates every nonce already in flight.
          </p>
          <pre className="figure t-meta mt-4 whitespace-pre-wrap break-words rounded-panel border border-line bg-inset p-6 text-ink">
            {MESSAGE_SLOTS}
          </pre>
          <p className="t-micro mt-3 text-muted">
            The two angle-bracket values are the wallet address and the single-use nonce. Everything
            else, including the cluster line, is the fixed part.
          </p>

          <p className="t-body mt-8 text-muted">
            The verification record carries canPurchase, canReceiveTransfer and a flags array. They
            gate nothing at runtime. They are advisory: no endpoint refuses a request on them, and no
            screen decides a purchase or a transfer from them.
          </p>
        </section>
      </div>
    </div>
  );
}
