import { ActionView } from "@/lib/types";

const ICON = { done: "✓", failed: "✕" } as const;

export function ActionCard({ action }: { action: ActionView | null }) {
  if (!action) {
    return <div className="empty">No booking actions yet.</div>;
  }

  const cls = action.status === "running" ? "" : action.status;
  return (
    <div className={`action ${cls}`}>
      {action.status === "running" ? (
        <span className="spinner" />
      ) : (
        <span style={{ fontWeight: 700, color: action.status === "failed" ? "var(--danger)" : "var(--success)" }}>
          {ICON[action.status]}
        </span>
      )}
      <div>
        <div className="action-label">
          {action.label}
          {action.status === "running" ? "…" : ""}
        </div>
        {action.detail && <div className="action-detail">{action.detail}</div>}
      </div>
    </div>
  );
}
