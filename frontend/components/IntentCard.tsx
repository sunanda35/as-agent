export function IntentCard({ intent }: { intent: string | null }) {
  if (!intent) {
    return <div className="empty">Listening for what you need…</div>;
  }
  return (
    <div className="intent">
      <span className="intent-icon">🎯</span>
      <span className="intent-text">{intent}</span>
    </div>
  );
}
