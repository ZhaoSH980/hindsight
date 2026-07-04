import {
  Area, ComposedChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
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
  return (
    <div className="panel p-3 h-72 relative">
      <ResponsiveContainer>
        <ComposedChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <XAxis dataKey="date" tick={{ fill: "#8b98ad", fontSize: 10 }} minTickGap={40} />
          <YAxis domain={["auto", "auto"]} tick={{ fill: "#8b98ad", fontSize: 10 }} width={48} />
          <Tooltip
            contentStyle={{ background: "#11161f", border: "1px solid #1f2937" }}
            labelStyle={{ color: "#8b98ad" }}
          />
          <ReferenceLine x={asOf} stroke="#f59e0b" strokeDasharray="4 4"
            label={{ value: `${t("asOf")} ${asOf}`, fill: "#f59e0b", fontSize: 10, position: "insideTopRight" }} />
          <Area dataKey="past" stroke="#38bdf8" fill="#38bdf8" fillOpacity={0.08} strokeWidth={1.5} dot={false} isAnimationActive={false} />
          <Area dataKey="future" stroke="#22c55e" fill="#22c55e" fillOpacity={0.08} strokeWidth={1.5} dot={false} isAnimationActive={true} animationDuration={1200} />
        </ComposedChart>
      </ResponsiveContainer>
      {!revealed && (
        <div className="absolute inset-y-0 right-0 w-[38%] bg-gradient-to-r from-transparent to-ink-950/90 flex items-center justify-end pr-4 pointer-events-none">
          <span className="text-muted text-xs font-mono rotate-0">{t("theFuture")}</span>
        </div>
      )}
    </div>
  );
}
