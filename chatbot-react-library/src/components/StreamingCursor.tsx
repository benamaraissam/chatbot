/** Blinking caret shown at end of streaming text */
export function StreamingCursor() {
  return (
    <span
      className="cb-ml-0.5 cb-inline-block cb-h-[1.1em] cb-w-[2px] cb-animate-pulse cb-rounded-sm cb-bg-cb-primary cb-align-text-bottom"
      aria-hidden
    />
  );
}
