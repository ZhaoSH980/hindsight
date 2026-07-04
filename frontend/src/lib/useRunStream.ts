import { useEffect, useRef, useState } from "react";
import { api } from "./api";
import type { TraceEvent } from "./types";

export function useRunStream(runId: string | null) {
  const [events, setEvents] = useState<TraceEvent[]>([]);
  const [status, setStatus] = useState<string>("idle");
  const pollRef = useRef<number | null>(null);

  useEffect(() => {
    if (!runId) return;
    setEvents([]);
    setStatus("running");
    let closed = false;

    const startPolling = () => {
      if (pollRef.current) return;
      pollRef.current = window.setInterval(async () => {
        try {
          const [trace, detail] = await Promise.all([api.trace(runId), api.run(runId)]);
          setEvents(trace);
          if (detail.status === "done" || detail.status === "failed") {
            setStatus(detail.status);
            if (pollRef.current) window.clearInterval(pollRef.current);
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
        ws.close();
      } else {
        setEvents((prev) => [...prev, evt]);
      }
    };
    ws.onerror = () => { if (!closed) startPolling(); };
    ws.onclose = () => { if (!closed && status === "running") startPolling(); };

    return () => {
      closed = true;
      ws.close();
      if (pollRef.current) window.clearInterval(pollRef.current);
    };
  }, [runId]);

  return { events, status };
}
