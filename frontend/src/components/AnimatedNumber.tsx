import { useEffect, useRef, useState } from "react";

interface Props {
  /** target numeric value; null renders an em-dash */
  value: number | null;
  /** formats the in-flight number each frame (e.g. pct, toFixed) */
  format: (n: number) => string;
  durationMs?: number;
  className?: string;
}

/** Counts up from 0 to `value` on mount / value change (ease-out cubic).
 *  Jumps straight to the end when the user prefers reduced motion. */
export function AnimatedNumber({ value, format, durationMs = 900, className }: Props) {
  const [display, setDisplay] = useState<number | null>(value === null ? null : 0);
  const raf = useRef<number>(0);

  useEffect(() => {
    if (value === null) {
      setDisplay(null);
      return;
    }
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) {
      setDisplay(value);
      return;
    }
    const start = performance.now();
    const from = 0;
    const tick = (now: number) => {
      const p = Math.min(1, (now - start) / durationMs);
      const eased = 1 - Math.pow(1 - p, 3);
      setDisplay(from + (value - from) * eased);
      if (p < 1) raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf.current);
  }, [value, durationMs]);

  return <span className={className}>{display === null ? "—" : format(display)}</span>;
}
