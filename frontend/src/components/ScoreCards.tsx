import { useLang } from "../lib/i18n";
import { num, pct } from "../lib/format";
import type { Scores } from "../lib/types";

interface Props { scores: Scores | null }

interface Card { labelKey: "hitRate" | "brier" | "groundingRate" | "reasoningConsistency" | "retrievalSufficiency" | "totalTokens"; value: string; polarity?: "good" | "bad" | "neutral" }

function polarityClass(p: Card["polarity"]): string {
  if (p === "good") return "text-up";
  if (p === "bad") return "text-down";
  return "text-slate-200";
}

export function ScoreCards({ scores }: Props) {
  const { t } = useLang();

  const outcome = scores?.outcome;
  const process = scores?.process;
  const cost = scores?.cost;

  const hitRate = outcome?.hit_rate ?? null;
  const brier = outcome?.brier ?? null;
  const groundingRate = process?.grounding_rate ?? null;
  const reasoningConsistency = process?.reasoning_consistency ?? null;
  const retrievalSufficiency = process?.retrieval_sufficiency ?? null;
  const totalTokens = cost
    ? Object.values(cost).reduce((sum, c) => sum + (c?.prompt_tokens ?? 0) + (c?.completion_tokens ?? 0), 0)
    : null;

  const cards: Card[] = [
    {
      labelKey: "hitRate",
      value: pct(hitRate),
      polarity: hitRate === null ? "neutral" : hitRate >= 0.5 ? "good" : "bad",
    },
    {
      labelKey: "brier",
      value: brier === null || brier === undefined ? "—" : brier.toFixed(3),
      polarity: brier === null || brier === undefined ? "neutral" : brier <= 0.25 ? "good" : "bad",
    },
    {
      labelKey: "groundingRate",
      value: pct(groundingRate),
      polarity: groundingRate === null ? "neutral" : groundingRate >= 0.8 ? "good" : "bad",
    },
    {
      labelKey: "reasoningConsistency",
      value: reasoningConsistency === null || reasoningConsistency === undefined ? "—" : `${num(reasoningConsistency)}/5`,
      polarity: "neutral",
    },
    {
      labelKey: "retrievalSufficiency",
      value: retrievalSufficiency === null || retrievalSufficiency === undefined ? "—" : `${num(retrievalSufficiency)}/5`,
      polarity: "neutral",
    },
    {
      labelKey: "totalTokens",
      value: num(totalTokens),
      polarity: "neutral",
    },
  ];

  return (
    <section className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
      {cards.map((c) => (
        <div key={c.labelKey} className="panel p-3 flex flex-col gap-1">
          <span className="text-[10px] text-muted font-mono">{t(c.labelKey)}</span>
          <span className={`num text-lg font-semibold ${polarityClass(c.polarity)}`}>{c.value}</span>
        </div>
      ))}
    </section>
  );
}
