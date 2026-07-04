export function pct(x: number | null | undefined, digits = 1): string {
  if (x === null || x === undefined || Number.isNaN(x)) return "—";
  return `${(x * 100).toFixed(digits)}%`;
}

export function num(x: number | null | undefined, digits = 0): string {
  if (x === null || x === undefined || Number.isNaN(x)) return "—";
  return x.toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: digits });
}

export function shortId(runId: string | null | undefined, len = 8): string {
  if (!runId) return "—";
  if (runId.length <= len) return runId;
  // keep the tail — run ids share a long case/date prefix and differ at the end
  const tail = runId.slice(-6);
  return `${runId.slice(0, Math.max(4, len - tail.length - 1))}…${tail}`;
}
