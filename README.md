# Bright Smile Voice Booking Agent

This project is a conversational voice agent for booking dental appointments. A caller joins a LiveKit room from the Next.js UI, speaks naturally with an AI receptionist, and the backend agent can check availability, book a slot, transfer to a human teammate, and generate a short post-call summary.

For installation and local running steps, start here: [SETUP.md](./SETUP.md).

## What It Does

- Starts a browser-based voice call through LiveKit.
- Runs a Python LiveKit Agent named `booking-agent`.
- Uses Deepgram for speech-to-text and text-to-speech.
- Uses Groq for the conversational LLM and post-call summary.
- Collects the caller's intent, name, service, preferred date/time, and phone number.
- Checks and books appointment slots in a local SQLite database.
- Streams live monitor events to the frontend: transcript, agent state, intent, current action, call status, and latency metrics.
- Supports an optional warm transfer to a real phone number through LiveKit SIP/Twilio settings.
- Saves post-call summaries under `backend/data/summaries/`.

## How It Works

The frontend asks `/api/token` for a LiveKit token, creates a fresh call room, and dispatches the `booking-agent` worker into that room. The caller speaks through the browser microphone.

The backend connects the agent session to LiveKit, wires together Deepgram STT/TTS and the Groq LLM, and exposes booking tools to the model. When the model understands the caller's goal, it calls tools such as `note_intent`, `check_availability`, `book_appointment`, `transfer_to_human`, and `end_call`.

The agent publishes monitor events on the `agent-monitor` data topic. The frontend listens to those events and updates the live dashboard with transcript bubbles, status cards, intent, action progress, and activity logs. When the call ends, the backend summarizes the transcript and sends the summary back to the UI.

## Fully Working Parts

- Browser call flow with microphone audio.
- LiveKit agent dispatch from the Next.js token endpoint.
- Real-time voice conversation using STT, LLM, and TTS.
- Appointment availability lookup.
- Appointment booking into SQLite.
- Live transcript and interim caller transcript.
- Agent state display: listening, thinking, speaking, idle, and related states.
- Detected intent display.
- Current action display for availability checks, booking, and transfer attempts.
- Activity and latency logging for model, STT, TTS, turn detection, call status, and tool actions.
- Caller-controlled call ending through the `call-control` data topic.
- Post-call summary generation and local summary persistence.
- Optional outbound warm transfer when SIP trunk and phone number configuration is present.

## Known Limitations

- The appointment database is local SQLite and seeded with simple fixed weekday slots. It is good for a demo, but not a production scheduler.
- There is no admin dashboard yet to view, edit, cancel, or reschedule bookings.
- The frontend exposes the caller experience and monitor-style dashboard, but it does not yet implement a true watcher takeover button that pauses the agent and lets a human continue in-browser.
- Warm transfer depends on real SIP/Twilio configuration. If `LIVEKIT_SIP_TRUNK_ID` or `TRANSFER_PHONE_NUMBER` is missing, the agent politely says the team is unavailable.
- The warm transfer currently dials the human and steps the agent aside after the call is answered. It does not yet ask the human to explicitly accept or decline from a custom UI.
- Some frontend copy is hard-coded for Bright Smile, while the backend business name is configurable with `BUSINESS_NAME`.
- There are no automated tests in the repo yet.
- No authentication or role-based access is implemented for a real monitoring/admin user.

## What I'd Do With More Time

- Add a real watcher takeover flow with a monitor role, takeover button, agent pause/resume, and direct human-to-caller audio.
- Add an admin bookings page for viewing appointments, cancellations, rescheduling, and manual slot management.
- Integrate a real scheduling backend such as Cal.com or Google Calendar.
- Add automated tests for booking logic, token generation, monitor event handling, and summary generation.
- Add persistent call records with searchable transcripts, summaries, booking details, and transfer outcomes.
- Make the business branding fully configurable across both backend and frontend.
- Improve warm transfer with explicit human accept/decline handling and a cleaner handoff summary.
- Add support for more appointment tools such as cancel, reschedule, look up an existing booking, and collect structured caller details live.
- Add better production readiness: auth, rate limits, structured logging, deployment docs, and secret management.
