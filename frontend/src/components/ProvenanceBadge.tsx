import { useLang } from "../lib/i18n";
import { HelpTip } from "./HelpTip";
import { IconGlobe, IconZap } from "./icons";
import type { Scores } from "../lib/types";

/** "Why was this instant?" — shows whether a run replayed from the recorded
 *  cache (0 network calls) or actually hit the LLM endpoint. */
export function ProvenanceBadge({ scores }: { scores: Scores | null | undefined }) {
  const { t } = useLang();
  const prov = scores?.llm_provenance;
  if (!prov) return null;
  const replayed = prov.live_calls === 0;
  return (
    <span className="inline-flex items-center gap-1.5">
      <span
        className={`inline-flex items-center gap-1 rounded border px-2 py-0.5 font-mono text-[10px] ${
          replayed
            ? "border-violet/40 bg-violet/10 text-violet"
            : "border-accent/40 bg-accent/10 text-accent"
        }`}
      >
        {replayed ? <IconZap size={11} /> : <IconGlobe size={11} />}
        {replayed ? t("provReplay") : `${prov.live_calls} ${t("provLive")}`}
      </span>
      <HelpTip text={t("provHelp")} />
    </span>
  );
}
