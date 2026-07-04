import { useLang } from "../lib/i18n";

type Attribution = "evidence_missing" | "misread_evidence" | "reasonable_but_wrong";

interface Props { attribution: string }

const STYLE: Record<Attribution, string> = {
  evidence_missing: "bg-amber/15 text-amber border-amber/40",
  misread_evidence: "bg-down/15 text-down border-down/40",
  // violet, not red: "reasonable but wrong" means the process was sound and
  // the world didn't cooperate — informative, not the agent's fault
  reasonable_but_wrong: "bg-violet/15 text-violet border-violet/40",
};

const LABEL_KEY: Record<Attribution, "attrEvidenceMissing" | "attrMisreadEvidence" | "attrReasonableButWrong"> = {
  evidence_missing: "attrEvidenceMissing",
  misread_evidence: "attrMisreadEvidence",
  reasonable_but_wrong: "attrReasonableButWrong",
};

export function AttributionBadge({ attribution }: Props) {
  const { t } = useLang();
  const known = attribution in STYLE;
  const style = known ? STYLE[attribution as Attribution] : "bg-ink-700 text-muted border-line";
  const label = known ? t(LABEL_KEY[attribution as Attribution]) : attribution;
  return (
    <span className={`rounded border px-1.5 py-0.5 font-mono text-[10px] whitespace-nowrap ${style}`}>
      {label}
    </span>
  );
}
