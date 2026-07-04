import {
  Area, CartesianGrid, ComposedChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { useLang } from "../lib/i18n";
import type { Bar } from "../lib/types";

interface Props { bars: Bar[]; asOf: string; revealed: boolean }

export function PriceChart({ bars, asOf, revealed }: Props) {
  const { t } = useLang();
  const data = bars.map((b) => ({
    date: b.date,
    past: b.date <= asOf ? b.close : null,
    future: b.date >= asOf ? (revealed ? b.close : null) : null,
  }));
  // the x-axis is categorical over bar dates: if as-of falls on a non-trading
  // day recharts silently drops the ReferenceLine — snap to the last bar <= as-of
  const asOfX = [...bars].reverse().find((b) => b.date <= asOf)?.date ?? asOf;
  return (
    <div className="panel p-3 h-72 relative">
      <ResponsiveContainer>
        <ComposedChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid stroke="#1c2740" strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="date" tick={{ fill: "#7d8aa5", fontSize: 10 }} minTickGap={40} stroke="#1c2740" />
          <YAxis domain={["auto", "auto"]} tick={{ fill: "#7d8aa5", fontSize: 10 }} width={48} stroke="#1c2740" />
          <Tooltip
            contentStyle={{ background: "#0b111e", border: "1px solid #1c2740", borderRadius: 8 }}
            labelStyle={{ color: "#7d8aa5" }}
          />
          <ReferenceLine x={asOfX} stroke="#fbbf24" strokeDasharray="4 4"
            label={{ value: `${t("asOf")} ${asOf}`, fill: "#fbbf24", fontSize: 10, position: "insideTopRight" }} />
          <Area dataKey="past" stroke="#22d3ee" fill="#22d3ee" fillOpacity={0.08} strokeWidth={1.5} dot={false} isAnimationActive={false} />
          <Area dataKey="future" stroke="#34d399" fill="#34d399" fillOpacity={0.08} strokeWidth={1.5} dot={false} isAnimationActive={true} animationDuration={1200} />
        </ComposedChart>
      </ResponsiveContainer>
      {/* sealed-future mask — always mounted; dissolves on reveal so the seal visibly breaks */}
      <div
        aria-hidden="true"
        className={`absolute inset-y-0 right-0 w-[38%] pointer-events-none transition-opacity duration-1000 ease-out ${
          revealed ? "opacity-0" : "opacity-100"
        }`}
      >
        <div className="scan-zone h-full w-full bg-gradient-to-r from-transparent to-ink-950/90 flex items-center justify-end pr-4">
          <span className="font-mono text-[11px] text-accent/80 animate-blink">{t("theFuture")}</span>
        </div>
      </div>
    </div>
  );
}
