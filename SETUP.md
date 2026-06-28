# Setup Guide

This guide explains how to run the project locally from a fresh clone. It is written for a newer developer, so follow the steps in order.

## Project Structure

```text
livekit-test/
|-- README.md
|-- SETUP.md
|-- backend/
|   |-- .env.example
|   |-- .env.local              # local secrets, not committed
|   |-- requirements.txt
|   |-- run.sh                  # starts one LiveKit agent worker
|   |-- data/                   # generated locally, ignored by git
|   |   |-- bookings.db         # SQLite database
|   |   `-- summaries/          # post-call summary text files
|   |-- scripts/
|   |   `-- create_sip_trunk.py # optional Twilio/LiveKit SIP helper
|   `-- src/
|       |-- agent.py            # LiveKit agent entrypoint
|       |-- booking_agent.py    # LLM tools exposed to the voice agent
|       |-- booking.py          # appointment availability and booking logic
|       |-- config.py           # backend environment settings
|       |-- db.py               # SQLite schema and seed slots
|       |-- lifecycle.py        # call ending and summary lifecycle
|       |-- monitor.py          # live dashboard data events
|       |-- prompts.py          # agent system instructions
|       |-- summary.py          # post-call summary generation
|       |-- transcript.py       # transcript rendering helpers
|       `-- transfer.py         # optional warm transfer flow
`-- frontend/
    |-- .env.example
    |-- .env.local              # local frontend secrets, not committed
    |-- package.json
    |-- package-lock.json
    |-- app/
    |   |-- api/token/route.ts  # creates LiveKit room tokens
    |   |-- globals.css
    |   |-- layout.tsx
    |   `-- page.tsx            # main call page
    |-- components/             # call UI, transcript, logs, cards
    `-- lib/                    # token fetch and monitor event helpers
```

Generated folders such as `backend/.venv/`, `backend/data/`, `frontend/node_modules/`, and `frontend/.next/` are ignored by git.

## Prerequisites

Install or create these before running the project:

- Python 3.12 or a recent Python 3 version.
- Node.js 20 or newer.
- A LiveKit Cloud project, or another LiveKit server URL.
- LiveKit API key and API secret.
- Deepgram API key for STT and TTS.
- Groq API key for the LLM.
- Optional: Twilio SIP credentials and a LiveKit outbound SIP trunk if you want real phone warm transfer.

## 1. Clone And Enter The Repo

```bash
git clone <your-repo-url>
cd livekit-test
```

If you already have the repo locally, just open a terminal in the `livekit-test` folder.

## 2. Configure The Backend

Go into the backend folder:

```bash
cd backend
```

Create a Python virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Create the backend environment file:

```bash
cp .env.example .env.local
```

Open `backend/.env.local` and fill in these required values:

```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

DEEPGRAM_API_KEY=your_deepgram_api_key
GROQ_API_KEY=your_groq_api_key
```

These values can stay as defaults unless you want to change models or business details:

```env
STT_MODEL=nova-3
TTS_MODEL=aura-2-andromeda-en
LLM_MODEL=llama-3.1-8b-instant

BUSINESS_NAME=Bright Smile Dental
BUSINESS_TIMEZONE=America/New_York
```

Leave these blank if you are not testing warm transfer:

```env
LIVEKIT_SIP_TRUNK_ID=
TRANSFER_PHONE_NUMBER=
```

## 3. Initialize The Local Database

From inside `backend/`, run:

```bash
python -m src.db
```

This creates `backend/data/bookings.db` and seeds appointment slots for the next 14 business days. Each business day gets these default times:

```text
09:00, 10:00, 11:00, 14:00, 15:00, 16:00
```

## 4. Configure The Frontend

Open a second terminal and go to the frontend folder:

```bash
cd frontend
```

Install Node dependencies:

```bash
npm install
```

Create the frontend environment file:

```bash
cp .env.example .env.local
```

Open `frontend/.env.local` and fill in:

```env
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

NEXT_PUBLIC_LIVEKIT_URL=wss://your-project.livekit.cloud
NEXT_PUBLIC_ROOM_NAME=booking-room
```

Use the same LiveKit API key, secret, and URL that you used in the backend.

## 5. Run The Backend Agent

In the backend terminal, make sure your virtual environment is active:

```bash
cd backend
source .venv/bin/activate
```

Start the LiveKit worker:

```bash
./run.sh dev
```

The worker registers an agent named `booking-agent`. Keep this terminal open while testing.

If `run.sh` is not executable on your machine, run:

```bash
chmod +x run.sh
./run.sh dev
```

## 6. Run The Frontend

In the frontend terminal, run:

```bash
cd frontend
npm run dev
```

Open the local URL printed by Next.js. It is usually:

```text
http://localhost:3000
```

Click **Start call**, allow microphone access, and speak to the booking assistant.

Example thing to say:

```text
I'd like to book a cleaning for tomorrow afternoon.
```

## 7. Test The Expected Flow

During a successful demo, you should see:

- The browser joins a LiveKit room.
- The backend terminal shows the agent worker handling the session.
- The assistant greets the caller.
- The live transcript appears in the frontend.
- The dashboard updates the assistant state.
- The detected intent appears after the agent understands the caller.
- Availability and booking actions appear when the agent calls tools.
- A booking is stored in `backend/data/bookings.db`.
- Ending the call generates a summary in the frontend and saves a `.txt` file in `backend/data/summaries/`.

## Optional: Warm Transfer Setup

Warm transfer needs more than the basic demo because it calls a real phone number.

You need:

- A Twilio phone number.
- Twilio SIP termination credentials.
- A LiveKit outbound SIP trunk connected to Twilio.
- A human transfer phone number in E.164 format, for example `+14155550123`.

Add these temporary Twilio values to `backend/.env.local`:

```env
TWILIO_SIP_ADDRESS=your-trunk.pstn.twilio.com
TWILIO_NUMBER=+1XXXXXXXXXX
TWILIO_SIP_USERNAME=your_sip_username
TWILIO_SIP_PASSWORD=your_sip_password
```

Then run:

```bash
cd backend
source .venv/bin/activate
python scripts/create_sip_trunk.py
```

The script prints a value like:

```env
LIVEKIT_SIP_TRUNK_ID=ST_xxxxx
```

Put that value in `backend/.env.local`, set `TRANSFER_PHONE_NUMBER`, and restart the backend worker:

```env
LIVEKIT_SIP_TRUNK_ID=ST_xxxxx
TRANSFER_PHONE_NUMBER=+14155550123
```

Now, if the caller says something like "I want to talk to a person", the agent will try to dial the configured human number.

## Common Problems

### The frontend says LiveKit credentials are missing

Check `frontend/.env.local`. The token route needs:

```env
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=
NEXT_PUBLIC_LIVEKIT_URL=
```

After editing `.env.local`, restart `npm run dev`.

### The backend says an environment variable is missing

Check `backend/.env.local`. The backend requires:

```env
LIVEKIT_URL=
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=
DEEPGRAM_API_KEY=
GROQ_API_KEY=
```

After editing `.env.local`, restart `./run.sh dev`.

### The browser joins but no agent answers

Make sure the backend worker is running with:

```bash
cd backend
source .venv/bin/activate
./run.sh dev
```

Also make sure the agent name in `frontend/app/api/token/route.ts` is `booking-agent`, which matches `backend/src/agent.py`.

### The microphone does not work

Use `http://localhost:3000` in a browser and allow microphone permission when prompted. If permission was blocked earlier, reset the site permission in the browser settings.

### Warm transfer says the team is unavailable

That usually means one of these is missing or incorrect:

```env
LIVEKIT_SIP_TRUNK_ID=
TRANSFER_PHONE_NUMBER=
```

It can also happen if the SIP trunk cannot dial the number or the human does not answer before the ringing timeout.

## Reset Local Booking Data

If you want to clear all local bookings and regenerate fresh slots, stop the backend and delete the local database:

```bash
rm backend/data/bookings.db
```

Then recreate it:

```bash
cd backend
source .venv/bin/activate
python -m src.db
```

Be careful: deleting `bookings.db` removes all local demo appointments.
