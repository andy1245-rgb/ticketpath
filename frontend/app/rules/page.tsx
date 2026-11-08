import type { Metadata } from "next";
import { ApiError, getHealth } from "@/lib/api";
import type { Health } from "@/lib/types";
import { Chip, DataSourceNote } from "@/components/ui";
import { capCeilingLamports, isWithinCap } from "@/lib/cap";
import { formatBpsPercent, formatLamports } from "@/lib/format";
import { verificationMessage } from "@/lib/solana";

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

interface Failure {
  message: string;
  code: string;
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
            The cap is the only thing in this product that carries the warning colour. That chip and
            the dashed rule a price chart draws at the ceiling are the two places it appears.
          </p>
        </section>

        <section className="mt-16">
          <h2 className="h-section text-ink">The boundary, in whole lamports</h2>
          <p className="t-body mt-2 text-muted">
            One SOL of face value, capped at 2500 bps over it. The four lines are the comparison
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
            afterwards. Nothing can raise the cap and nothing can lower it: an organiser who wanted a
            different number would be initialising a different record.
          </p>
          <p className="t-body mt-2 text-muted">
            The jurisdiction gate sits above that and can only tighten it. It resolves the legal
            ceiling for the region, compares it with the platform cap, and takes the lower of the
            two. A jurisdiction can make the ceiling smaller. It can never make it larger.
          </p>
        </section>

        <section className="mt-16">
          <h2 className="h-section text-ink">Enforcement today</h2>
          <p className="t-body mt-2 text-ink">
            The cap program is written. It is not deployed on any cluster, so nothing is enforced at
            runtime today. A resale above the ceiling is not refused by anything on chain.
          </p>

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
                  ? "The server queried a cluster, so this is a read of that cluster rather than a claim about it."
                  : "The server queried no cluster, so programDeployed records that no check was made."}
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
