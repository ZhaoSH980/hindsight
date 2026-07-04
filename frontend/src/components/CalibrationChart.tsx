import {
  CartesianGrid, ReferenceLine, Scatter, ScatterChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";

interface Bucket { lo: number; hi: number; n: number; avg_confidence: number | null; hit_rate: number | null }

export function CalibrationChart({ buckets }: { buckets: Bucket[] }) {
  const pts = buckets
    .filter((b) => b.n > 0 && b.avg_confidence !== null && b.hit_rate !== null)
    .map((b) => ({ x: b.avg_confidence, y: b.hit_rate, n: b.n }));
  return (
    <div className="panel p-3 h-64">
      <ResponsiveContainer>
        <ScatterChart margin={{ top: 10, right: 16, bottom: 8, left: 0 }}>
          <CartesianGrid stroke="#1f2937" strokeDasharray="3 3" />
          <XAxis type="number" dataKey="x" domain={[0, 1]} tick={{ fill: "#8b98ad", fontSize: 10 }}
            label={{ value: "confidence", fill: "#8b98ad", fontSize: 10, position: "insideBottom", offset: -2 }} />
          <YAxis type="number" dataKey="y" domain={[0, 1]} tick={{ fill: "#8b98ad", fontSize: 10 }} width={36}
            label={{ value: "hit rate", fill: "#8b98ad", fontSize: 10, angle: -90, position: "insideLeft" }} />
          <ReferenceLine segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]} stroke="#8b98ad" strokeDasharray="4 4" />
          <Tooltip contentStyle={{ background: "#11161f", border: "1px solid #1f2937" }}
            formatter={(v: number | string | readonly (number | string)[] | undefined) =>
              typeof v === "number" ? v.toFixed(2) : v
            } />
          <Scatter data={pts} fill="#38bdf8" shape={(p: any) => (
            <g>
              <circle cx={p.cx} cy={p.cy} r={4 + Math.min(p.payload.n, 6)} fill="#38bdf8" fillOpacity={0.7} />
              <text x={p.cx} y={p.cy - 10} fill="#8b98ad" fontSize={9} textAnchor="middle">n={p.payload.n}</text>
            </g>
          )} />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
