import type { ReactNode } from "react";

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
