import Link from "next/link";
import { TopBar } from "@/components/TopBar";

export default function Home() {
  return (
    <main className="page">
      <TopBar />
      <section className="hero">
        <h1>Book an appointment, just by talking.</h1>
        <p>
          A voice assistant handles the call. Open the live monitor in another tab
          to watch every word and action as it happens.
        </p>
      </section>

      <div className="choices">
        <Link href="/call" className="choice">
          <div className="emoji">🎙️</div>
          <h3>Start a call</h3>
          <p>
            Speak with the booking assistant. Allow your microphone and say what
            you need — it will check times and book for you.
          </p>
        </Link>
        <Link href="/monitor" className="choice">
          <div className="emoji">📊</div>
          <h3>Open live monitor</h3>
          <p>
            Watch the conversation, the assistant&apos;s state, and each booking
            action stream in live. A post-call summary appears at the end.
          </p>
        </Link>
      </div>
    </main>
  );
}
