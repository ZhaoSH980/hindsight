import { useState } from "react";
import { api } from "../lib/api";
import { useLang } from "../lib/i18n";

interface DocDraft {
  title: string;
  published_at: string;
  source: string;
  url: string;
  text: string;
}

const emptyDoc = (): DocDraft => ({ title: "", published_at: "", source: "", url: "", text: "" });

const inputCls =
  "w-full rounded bg-ink-700 border border-line px-2 py-1.5 text-sm text-slate-200 focus:border-accent/60 focus:outline-none";
const labelCls = "flex flex-col gap-1 text-[11px] font-mono text-muted";

interface Props {
  onCreated: (caseId: string, windowOpen: boolean) => void;
  onCancel: () => void;
}

export function CaseWizard({ onCreated, onCancel }: Props) {
  const { t } = useLang();
  const [ticker, setTicker] = useState("");
  const [asOf, setAsOf] = useState("");
  const [windowDays, setWindowDays] = useState(40);
  const [title, setTitle] = useState("");
  const [titleZh, setTitleZh] = useState("");
  const [desc, setDesc] = useState("");
  const [descZh, setDescZh] = useState("");
  const [tags, setTags] = useState("");
  const [docs, setDocs] = useState<DocDraft[]>([emptyDoc(), emptyDoc()]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function patchDoc(i: number, patch: Partial<DocDraft>) {
    setDocs((ds) => ds.map((d, j) => (j === i ? { ...d, ...patch } : d)));
  }

  const docDateLate = (d: DocDraft) => Boolean(asOf && d.published_at && d.published_at > asOf);
  const ready =
    ticker.trim() &&
    asOf &&
    title.trim().length >= 3 &&
    desc.trim().length >= 10 &&
    docs.length >= 2 &&
    docs.every((d) => d.title.trim().length >= 3 && d.published_at && d.text.trim().length >= 100) &&
    !docs.some(docDateLate);

  async function submit() {
    if (!ready || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await api.createCase({
        ticker: ticker.trim(),
        as_of: asOf,
        outcome_window_days: windowDays,
        title: title.trim(),
        title_zh: titleZh.trim(),
        description: desc.trim(),
        description_zh: descZh.trim(),
        tags: tags.split(",").map((s) => s.trim()).filter(Boolean),
        docs: docs.map((d) => ({
          title: d.title.trim(),
          published_at: d.published_at,
          source: d.source.trim() || "user-supplied",
          url: d.url.trim(),
          doc_type: "news",
          text: d.text.trim(),
        })),
      });
      onCreated(res.case_id, res.outcome_window_still_open);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="panel hud-corners p-4 flex flex-col gap-4 animate-fade-up">
      <div>
        <h3 className="hud-label mb-1">{t("newCaseTitle")}</h3>
        <p className="text-xs text-muted leading-relaxed">{t("newCaseIntro")}</p>
      </div>

      <div className="border-l-2 border-l-amber pl-3 text-xs text-slate-300 leading-relaxed">
        {t("newCaseHonesty")}
      </div>

      {/* case fields */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        <label className={labelCls}>
          {t("wizTicker")}
          <input className={`${inputCls} font-mono uppercase`} value={ticker}
            onChange={(e) => setTicker(e.target.value)} placeholder="NVDA" />
        </label>
        <label className={labelCls}>
          {t("wizAsOf")}
          <input type="date" className={`${inputCls} font-mono`} value={asOf}
            onChange={(e) => setAsOf(e.target.value)} />
        </label>
        <label className={labelCls}>
          {t("wizWindow")}
          <input type="number" min={1} max={250} className={`${inputCls} num`} value={windowDays}
            onChange={(e) => setWindowDays(Number(e.target.value) || 40)} />
        </label>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <label className={labelCls}>
          {t("wizTitleEn")}
          <input className={inputCls} value={title} onChange={(e) => setTitle(e.target.value)} />
        </label>
        <label className={labelCls}>
          {t("wizTitleZh")}
          <input className={inputCls} value={titleZh} onChange={(e) => setTitleZh(e.target.value)} />
        </label>
        <label className={labelCls}>
          {t("wizDescEn")}
          <textarea rows={2} className={inputCls} value={desc} onChange={(e) => setDesc(e.target.value)} />
        </label>
        <label className={labelCls}>
          {t("wizDescZh")}
          <textarea rows={2} className={inputCls} value={descZh} onChange={(e) => setDescZh(e.target.value)} />
        </label>
      </div>
      <label className={labelCls}>
        {t("wizTags")}
        <input className={`${inputCls} font-mono`} value={tags}
          onChange={(e) => setTags(e.target.value)} placeholder="earnings, semis" />
      </label>

      {/* documents */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h4 className="hud-label">{t("wizDocs")}</h4>
          <span className="text-[10px] text-muted">{t("wizMinDocs")}</span>
        </div>
        {docs.map((d, i) => (
          <div key={i} className="panel p-3 flex flex-col gap-2">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <label className={`${labelCls} col-span-2`}>
                {t("wizDocTitle")}
                <input className={inputCls} value={d.title}
                  onChange={(e) => patchDoc(i, { title: e.target.value })} />
              </label>
              <label className={labelCls}>
                {t("wizDocDate")}
                <input type="date" className={`${inputCls} font-mono ${docDateLate(d) ? "border-down text-down" : ""}`}
                  value={d.published_at}
                  onChange={(e) => patchDoc(i, { published_at: e.target.value })} />
                {docDateLate(d) && <span className="text-down">{t("wizDocDateBad")}</span>}
              </label>
              <label className={labelCls}>
                {t("wizDocSource")}
                <input className={inputCls} value={d.source}
                  onChange={(e) => patchDoc(i, { source: e.target.value })} />
              </label>
            </div>
            <label className={labelCls}>
              {t("wizDocUrl")}
              <input className={`${inputCls} font-mono`} value={d.url}
                onChange={(e) => patchDoc(i, { url: e.target.value })} />
            </label>
            <label className={labelCls}>
              {t("wizDocText")}
              <textarea rows={5} className={`${inputCls} font-mono text-xs`} value={d.text}
                onChange={(e) => patchDoc(i, { text: e.target.value })} />
            </label>
            {docs.length > 2 && (
              <button type="button"
                onClick={() => setDocs((ds) => ds.filter((_, j) => j !== i))}
                className="self-end rounded border border-line px-2 py-0.5 font-mono text-[10px] text-muted hover:border-down/60 hover:text-down transition-colors">
                {t("wizRemoveDoc")}
              </button>
            )}
          </div>
        ))}
        <button type="button" onClick={() => setDocs((ds) => [...ds, emptyDoc()])}
          className="self-start rounded border border-line px-3 py-1 font-mono text-xs text-accent hover:border-accent/60 hover:shadow-glow-sm transition">
          + {t("wizAddDoc")}
        </button>
      </div>

      {error && (
        <div className="panel border-down/50 p-3 text-down text-xs break-all">{error}</div>
      )}

      <div className="flex items-center gap-3">
        <button type="button" onClick={submit} disabled={!ready || submitting}
          className="rounded-md bg-accent px-5 py-1.5 text-sm font-semibold text-ink-950 shadow-glow transition hover:brightness-110 disabled:opacity-40">
          {submitting ? t("wizSubmitting") : t("wizSubmit")}
        </button>
        <button type="button" onClick={onCancel}
          className="rounded-md border border-line px-4 py-1.5 text-sm text-muted hover:text-slate-200 transition-colors">
          {t("wizCancel")}
        </button>
        <span className="ml-auto text-[10px] text-muted">{t("wizNeedsOnline")}</span>
      </div>
    </section>
  );
}
