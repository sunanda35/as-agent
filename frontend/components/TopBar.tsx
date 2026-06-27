import Link from "next/link";

export function TopBar({ active }: { active?: "call" | "monitor" }) {
  return (
    <div className="topbar">
      <Link href="/" className="brand" style={{ textDecoration: "none", color: "inherit" }}>
        <span className="brand-dot" />
        Bright Smile
      </Link>
      <nav style={{ display: "flex", gap: 4 }}>
        <Link
          href="/call"
          className="link"
          style={active === "call" ? { background: "var(--surface-muted)", color: "var(--text)" } : undefined}
        >
          Call
        </Link>
        <Link
          href="/monitor"
          className="link"
          style={active === "monitor" ? { background: "var(--surface-muted)", color: "var(--text)" } : undefined}
        >
          Live monitor
        </Link>
      </nav>
    </div>
  );
}
