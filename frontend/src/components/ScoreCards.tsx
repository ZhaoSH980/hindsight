import { useLang } from "../lib/i18n";
import { num, pct } from "../lib/format";
import { HelpTip } from "./HelpTip";
import { AnimatedNumber } from "./AnimatedNumber";
import type { Scores } from "../lib/types";

interface Props { scores: Scores | null }

interface Card {
  labelKey: "hitRate" | "brier" | "groundingRate" | "reasoningConsistency" | "retrievalSufficiency" | "totalTokens";
  helpKey: "hitRateHelp" | "brierHelp" | "groundingHelp" | "reasoningHelp" | "retrievalHelp" | "tokensHelp";
  /** raw numeric value; null renders an em-dash */
  value: number | null;
  /** formats the in-flight animated number */
  format: (n: number) => string;
  polarity?: "good" | "bad" | "neutral";
}

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

  // polarity is always computed from the FINAL value, never the animated one
  const cards: Card[] = [
    {
      labelKey: "hitRate",
      helpKey: "hitRateHelp",
      value: hitRate,
      format: (n) => pct(n),
      polarity: hitRate === null ? "neutral" : hitRate >= 0.5 ? "good" : "bad",
    },
    {
      labelKey: "brier",
      helpKey: "brierHelp",
      value: brier,
      format: (n) => n.toFixed(3),
      polarity: brier === null ? "neutral" : brier <= 0.25 ? "good" : "bad",
    },
    {
      labelKey: "groundingRate",
      helpKey: "groundingHelp",
      value: groundingRate,
      format: (n) => pct(n),
      polarity: groundingRate === null ? "neutral" : groundingRate >= 0.8 ? "good" : "bad",
    },
    {
      labelKey: "reasoningConsistency",
      helpKey: "reasoningHelp",
      value: reasoningConsistency,
      format: (n) => `${Math.round(n)}/5`,
      polarity: "neutral",
    },
    {
      labelKey: "retrievalSufficiency",
      helpKey: "retrievalHelp",
      value: retrievalSufficiency,
      format: (n) => `${Math.round(n)}/5`,
      polarity: "neutral",
    },
    {
      labelKey: "totalTokens",
      helpKey: "tokensHelp",
      value: totalTokens,
      format: (n) => num(Math.round(n)),
      polarity: "neutral",
    },
  ];

  return (
    <section className="stagger grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
      {cards.map((c) => (
        <div key={c.labelKey} className="panel panel-hover p-3 flex flex-col gap-1">
          <span className="flex items-center gap-1 text-[10px] text-muted font-mono">
            {t(c.labelKey)}
            <HelpTip text={t(c.helpKey)} />
          </span>
          <AnimatedNumber
            value={c.value}
            format={c.format}
            className={`num text-lg font-semibold ${polarityClass(c.polarity)}`}
          />
        </div>
      ))}
    </section>
  );
}
