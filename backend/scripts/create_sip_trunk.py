from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from livekit import api
from livekit.protocol.sip import SIPMediaEncryption, SIPTransport

load_dotenv(Path(__file__).resolve().parent.parent / ".env.local")

REQUIRED = ["TWILIO_SIP_ADDRESS", "TWILIO_NUMBER", "TWILIO_SIP_USERNAME", "TWILIO_SIP_PASSWORD"]


async def main() -> None:
    missing = [k for k in REQUIRED if not os.getenv(k)]
    if missing:
        print("Set these in backend/.env.local (or the environment) first:")
        for k in missing:
            print(f"  {k}")
        print(
            "\nTWILIO_SIP_ADDRESS  = your Twilio termination URI, e.g. my-trunk.pstn.twilio.com\n"
            "TWILIO_NUMBER       = your Twilio phone number in E.164, e.g. +1XXXXXXXXXX\n"
            "TWILIO_SIP_USERNAME = a Twilio SIP credential username (Termination > Credential Lists)\n"
            "TWILIO_SIP_PASSWORD = that credential's password"
        )
        sys.exit(1)

    lk = api.LiveKitAPI()
    try:
        trunk = api.SIPOutboundTrunkInfo(
            name="twilio-tls",
            address=os.environ["TWILIO_SIP_ADDRESS"],
            transport=SIPTransport.SIP_TRANSPORT_TLS,
            media_encryption=SIPMediaEncryption.SIP_MEDIA_ENCRYPT_REQUIRE,
            numbers=[os.environ["TWILIO_NUMBER"]],
            auth_username=os.environ["TWILIO_SIP_USERNAME"],
            auth_password=os.environ["TWILIO_SIP_PASSWORD"],
        )
        resp = await lk.sip.create_sip_outbound_trunk(
            api.CreateSIPOutboundTrunkRequest(trunk=trunk)
        )
        print("Created secure (TLS + SRTP) outbound trunk:")
        print(f"  LIVEKIT_SIP_TRUNK_ID={resp.sip_trunk_id}")
        print("\nPut that id in backend/.env.local and restart the worker.")
    finally:
        await lk.aclose()


if __name__ == "__main__":
    asyncio.run(main())
