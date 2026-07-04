import { useLang } from "../lib/i18n";
import type { Claim } from "../lib/types";

/** Per-claim confidence-vs-outcome strip — the honest replacement for a
 *  bucketed calibration curve at n=3–5 claims. Pure SVG, no chart lib.
 *  Each graded claim becomes one marker on a 0→100% confidence axis:
 *  green filled = hit, red filled = miss, dashed hollow = ungradable. */

const VIEW_W = 600;
const VIEW_H = 130;
const PAD_X = 28;
const AXIS_W = VIEW_W - PAD_X * 2;
const AXIS_Y = 65;
const TICKS = [0, 0.25, 0.5, 0.75, 1];
/** markers closer than this (px in viewBox units) get their labels lane-flipped */
const CROWD_PX = 24;

const LINE = "#1c2740"; // line token
const MUTED = "#7d8aa5"; // muted token
const UP = "#34d399"; // up token
const DOWN = "#f87171"; // down token

interface Props {
  claims: Claim[];
}

interface Marker {
  claim: Claim;
  x: number;
}

export function ConfidenceStrip({ claims }: Props) {
  const { t } = useLang();

  const graded: Marker[] = claims
    .filter((c) => Boolean(c.status))
    .map((c) => ({
      claim: c,
      x: PAD_X + Math.min(Math.max(c.confidence ?? 0, 0), 1) * AXIS_W,
    }))
    .sort((a, b) => a.x - b.x);

  // Label lanes: above the axis by default; when two markers crowd each other
  // horizontally, flip alternating labels below the axis to avoid overlap.
  const lanes: Array<1 | -1> = [];
  graded.forEach((m, i) => {
    if (i > 0 && m.x - graded[i - 1].x < CROWD_PX) {
      lanes.push(lanes[i - 1] === 1 ? -1 : 1);
    } else {
      lanes.push(1);
    }
  });

  // no claims at all (e.g. failed run) vs. claims awaiting their reveal —
  // different situations, different messages
  if (claims.length === 0) {
    return (
      <div className="panel p-4">
        <p className="text-xs text-muted">{t("noClaims")}</p>
      </div>
    );
  }
  if (graded.length === 0) {
    return (
      <div className="panel p-4">
        <p className="text-xs text-muted">{t("noGradedClaims")}</p>
      </div>
    );
  }

  return (
    <div className="panel p-4 flex flex-col gap-2">
      <svg
        viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
        className="w-full h-auto"
        role="img"
        aria-label={t("confVsOutcome")}
      >
        {/* confidence axis */}
        <line x1={PAD_X} y1={AXIS_Y} x2={PAD_X + AXIS_W} y2={AXIS_Y} stroke={LINE} strokeWidth={1} />
        {TICKS.map((f) => {
          const x = PAD_X + f * AXIS_W;
          return (
            <g key={f}>
              <line x1={x} y1={AXIS_Y - 4} x2={x} y2={AXIS_Y + 4} stroke={LINE} strokeWidth={1} />
              <text
                x={x}
                y={VIEW_H - 10}
                fill={MUTED}
                fontSize={9}
                textAnchor="middle"
                className="font-mono"
              >
                {Math.round(f * 100)}%
              </text>
            </g>
          );
        })}

        {/* one marker per graded claim */}
        {graded.map((m, i) => {
          const { claim, x } = m;
          const labelY = lanes[i] === 1 ? AXIS_Y - 18 : AXIS_Y + 24;
          return (
            <g
              key={claim.claim_id}
              className="animate-fade-up"
              style={{ animationDelay: `${i * 100}ms` }}
            >
              {claim.status === "hit" && (
                <>
                  <circle cx={x} cy={AXIS_Y} r={11} fill={UP} opacity={0.18} />
                  <circle cx={x} cy={AXIS_Y} r={7} fill={UP} />
                </>
              )}
              {claim.status === "miss" && (
                <>
                  <circle cx={x} cy={AXIS_Y} r={11} fill={DOWN} opacity={0.18} />
                  <circle cx={x} cy={AXIS_Y} r={7} fill={DOWN} />
                </>
              )}
              {claim.status === "ungradable" && (
                <circle cx={x} cy={AXIS_Y} r={6} fill="none" stroke={MUTED} strokeDasharray="2 2" />
              )}
              <text
                x={x}
                y={labelY}
                fill={MUTED}
                fontSize={9}
                textAnchor="middle"
                className="font-mono"
              >
                {claim.claim_id}
              </text>
            </g>
          );
        })}
      </svg>
      <p className="text-xs text-muted leading-relaxed">{t("confVsOutcomeHint")}</p>
    </div>
  );
}
