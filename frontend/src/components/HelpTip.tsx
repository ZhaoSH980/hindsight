/** Small "?" chip that reveals a plain-language explanation on hover/focus.
 *  Styling lives in index.css (.helptip) — CSS-only, keyboard accessible. */
export function HelpTip({ text }: { text: string }) {
  return (
    <span className="helptip">
      <button type="button" aria-label={text} tabIndex={0}>
        ?
      </button>
      <span role="tooltip">{text}</span>
    </span>
  );
}
