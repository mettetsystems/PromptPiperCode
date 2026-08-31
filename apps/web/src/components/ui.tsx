import { useEffect, useRef, type ReactNode, type Ref } from "react";

export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="page-header">
      <div>
        <h1>{title}</h1>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </div>
  );
}

export function Panel({
  title,
  children,
  className = "",
}: {
  title?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`panel ${className}`.trim()}>
      {title && <h2>{title}</h2>}
      {children}
    </section>
  );
}

export function DraftBlock({ body, label = "Draft" }: { body: string; label?: string }) {
  return (
    <div className="draft-block">
      <div className="draft-label">{label}</div>
      <pre className="draft-text">{body}</pre>
    </div>
  );
}

export interface DraftHighlight {
  lineNumber: number;
  start: number;
  end: number;
}

function renderHighlightedLine(
  line: string,
  highlight: { start: number; end: number } | null,
  markRef?: Ref<HTMLElement>,
): ReactNode {
  if (!highlight || highlight.start < 0 || highlight.end <= highlight.start) {
    return line;
  }
  const start = Math.min(highlight.start, line.length);
  const end = Math.min(highlight.end, line.length);
  if (start >= end) {
    return line;
  }
  return (
    <>
      {line.slice(0, start)}
      <mark ref={markRef} className="precision-term-highlight">
        {line.slice(start, end)}
      </mark>
      {line.slice(end)}
    </>
  );
}

/** Full draft with optional character-range highlight on one line; scrolls the mark into view. */
export function HighlightedDraft({
  body,
  label = "Draft",
  highlight = null,
}: {
  body: string;
  label?: string;
  highlight?: DraftHighlight | null;
}) {
  const markRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    markRef.current?.scrollIntoView({ block: "center", behavior: "smooth" });
  }, [highlight?.lineNumber, highlight?.start, highlight?.end, body]);

  const lines = body.split("\n");

  return (
    <div className="draft-block">
      <div className="draft-label">{label}</div>
      <pre className="draft-text draft-text-highlighted">
        {lines.map((line, index) => {
          const lineNumber = index + 1;
          const isTarget = highlight?.lineNumber === lineNumber;
          const lineHighlight =
            isTarget && highlight
              ? { start: highlight.start, end: highlight.end }
              : null;
          return (
            <span key={`line-${lineNumber}`} className={isTarget ? "draft-line is-active" : "draft-line"}>
              {renderHighlightedLine(line, lineHighlight, isTarget ? markRef : undefined)}
              {index < lines.length - 1 ? "\n" : null}
            </span>
          );
        })}
      </pre>
    </div>
  );
}

export function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="callout callout-error" role="alert">
      {message}
    </div>
  );
}

export function WarningBanner({ message }: { message: string }) {
  return (
    <div className="callout callout-warn" role="status">
      {message}
    </div>
  );
}

export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return <p className="loading-state">{label}</p>;
}
