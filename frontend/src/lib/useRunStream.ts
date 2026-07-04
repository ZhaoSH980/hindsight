import { useEffect, useRef, useState } from "react";
import { api } from "./api";
import type { TraceEvent } from "./types";

export function useRunStream(runId: string | null) {
  const [events, setEvents] = useState<TraceEvent[]>([]);
  const [status, setStatus] = useState<string>("idle");
  const pollRef = useRef<number | null>(null);
  // effect closures would capture a stale `status`; the ref always has the
  // live value so the ws.onclose fallback decision is correct
  const terminalRef = useRef(false);

  useEffect(() => {
    if (!runId) return;
    setEvents([]);
    setStatus("running");
    terminalRef.current = false;
    let closed = false;

    const stopPolling = () => {
      if (pollRef.current) {
        window.clearInterval(pollRef.current);
        pollRef.current = null; // reset, or the fallback is dead for the next run
      }
    };

    const startPolling = () => {
      if (pollRef.current) return;
      pollRef.current = window.setInterval(async () => {
        try {
          const [trace, detail] = await Promise.all([api.trace(runId), api.run(runId)]);
          setEvents(trace);
          if (detail.status === "done" || detail.status === "failed") {
            setStatus(detail.status);
            terminalRef.current = true;
            stopPolling();
          }
        } catch { /* keep polling */ }
      }, 1500);
    };

    const proto = location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${proto}://${location.host}/api/runs/${runId}/stream`);
    ws.onmessage = (m) => {
      const evt = JSON.parse(m.data);
      if (evt.type === "status") {
        setStatus(evt.payload.status);
        terminalRef.current = true;
        ws.close();
      } else {
        setEvents((prev) => [...prev, evt]);
      }
    };
    ws.onerror = () => { if (!closed) startPolling(); };
    ws.onclose = () => { if (!closed && !terminalRef.current) startPolling(); };

    return () => {
      closed = true;
      ws.close();
      stopPolling();
    };
  }, [runId]);

  return { events, status };
}
