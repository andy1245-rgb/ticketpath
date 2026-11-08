import { Chip } from "@/components/ui";
import { shortAddress } from "@/lib/format";
import live from "@/data/swarm-live-onchain.json";
import totals from "@/data/swarm-totals.json";

/**
 * The six-agent run, printed from the record it wrote.
 *
 * `data/swarm-live-onchain.json` is a byte copy of `records/swarm-live-onchain.json`
 * and `data/swarm-totals.json` is the totals out of the sweep summary, both copied
 * unchanged so the page can read them at build time: a static export cannot read
 * outside its own root. The label, the disclaimer and the note are the run's own
 * strings, not this page's paraphrase.
 *
 * Two runs, two panels, and they are never added together:
 *
 * - the six-agent run below sent instructions to a validator this machine
 *   started and is what the film's voice describes;
 * - the nine-agent run the charts above belong to is a dry run, simulated in the
 *   process with no chain at all.
 *
 * The sweep totals underneath are the campaign's own counts, kept split by kind
 * for the same reason: a refusal a validator returned and one the hook predicted
 * are different measurements, and a single number would merge them.
 */

function n(value: number): string {
  return value.toLocaleString("en-US");
}

function Line({
  label,
  value,
  note,
}: {
  label: string;
  value: string;
  note?: string;
}): React.ReactElement {
  return (
    <div>
      <dt className="figure t-micro text-muted">{label}</dt>
      <dd className="mt-1 break-words text-ink">
        <span className="figure t-meta">{value}</span>
        {note && <span className="t-micro mt-1 block text-muted">{note}</span>}
      </dd>
    </div>
  );
}

export function SwarmRunPanel(): React.ReactElement {
  const events = live.events;
  const agents = live.agents;

  return (
    <section id="swarm" className="mt-16 scroll-mt-24">
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="h-section text-ink">The six-agent run, on a validator</h2>
        <Chip tone="neutral">{live.label}</Chip>
      </div>

      <p className="t-body mt-2 text-muted">
        Six scripted policies ({agents} agent slots) traded one synthetic ticket through the cap
        program on a validator this machine started. {live.executed} instructions executed and{" "}
        {live.refused} were refused, every refusal carrying code{" "}
        {Object.keys(live.refused_by_code).join(", ")}. Nothing here is a market: the ticket is
        synthetic and the prices are the policies&rsquo; own.
      </p>

      <dl className="mt-6 grid gap-x-6 gap-y-4 sm:grid-cols-2">
        <Line label="run" value={live.run_id} note={`seed ${live.seed} · ${live.agents} agents · ${events.length} events`} />
        <Line
          label="chain"
          value={live.validator ? "local validator" : "none"}
          note="funded at genesis; nothing rented, no public cluster"
        />
        <Line
          label="executed / refused on chain"
          value={`${n(live.executed)} / ${n(live.refused_on_chain)}`}
          note={`${n(live.unfilled_bids)} unfilled bids · ${n(live.unfilled_asks)} unfilled asks`}
        />
        <Line label="cost" value={`$${live.cost.usd.toFixed(2)}`} note={live.cost.basis} />
      </dl>

      <ul className="mt-6 border-t border-line">
        {events.map((event) => (
          <li
            key={event.event_id}
            className="flex flex-col gap-1 border-b border-line py-3 sm:flex-row sm:items-baseline sm:gap-6"
          >
            <span className="figure t-micro w-40 shrink-0 text-muted">{event.event_id}</span>
            <span className="t-body text-ink">
              {event.mode} · {n(event.executed)} executed · {n(event.refused_on_chain)} refused ·{" "}
              {n(event.rounds_completed)} rounds · ceiling {n(event.ceiling_lamports)} lamports
            </span>
          </li>
        ))}
      </ul>

      <p className="t-micro mt-3 text-muted">
        Dataset {live.events[0]?.dataset ? shortAddress(live.events[0].dataset, 24, 12) : "—"},
        sha256 {shortAddress(live.events[0]?.dataset_sha256 ?? null, 12, 8)}. {live.note}
      </p>
      <p className="t-micro mt-2 text-muted">{live.disclaimer}</p>

      <div className="mt-10 rounded-panel border border-line bg-surface p-6">
        <p className="t-micro-caps text-muted">The sweep behind the numbers</p>
        <p className="t-body mt-3 text-ink">
          {n(totals.runs)} runs in total: {n(totals.runsValidator)} on a local validator (
          {totals.validatorRuns.scripted} scripted, {totals.validatorRuns.liveModel} with a live
          model) and {n(totals.runsDry)} dry. {n(totals.decisions)} decisions,{" "}
          {n(totals.executed)} trades executed, {n(totals.listings)} listings with no chain
          instruction behind them, {n(totals.refused)} refusals of which {n(totals.refusedOnChain)}{" "}
          carry code 6010, and {n(totals.declinedByPolicy)} policy declines. Model spend $
          {totals.usd.toFixed(4)} across the three live-model runs; every other run is scripted and
          spent nothing.
        </p>
        <dl className="mt-4 grid gap-x-6 gap-y-3 sm:grid-cols-2">
          <Line
            label="local validator runs"
            value={n(totals.runsValidator)}
            note="sent the instruction to a validator; the refusals are the program's own"
          />
          <Line
            label="dry runs"
            value={n(totals.runsDry)}
            note="simulated gateway: built nothing, signed nothing, sent nothing"
          />
        </dl>
        <p className="t-micro mt-4 text-muted">{totals.dryRunNote}</p>
        <p className="t-micro mt-2 text-muted">{totals.validatorNote}</p>
      </div>
    </section>
  );
}
