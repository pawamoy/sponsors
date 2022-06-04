import os
import hmac
import hashlib

from fastapi import FastAPI, Request
import httpx

SECRET = os.getenv("WEBHOOK_SECRET")

app = FastAPI()


def is_valid_signature(secret, payload, their_hash):
    our_hash = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(our_hash, their_hash)


@app.post("/")
async def trigger_workflow(request: Request):
    payload_hash = request.headers.pop("X-Hub-Signature-256")[7:]  # remove leading sha256=
    payload_data = await request.body()
    if not is_valid_signature(SECRET, payload_data, payload_hash):
        return "Invalid payload hash", 400

    received_payload = await request.json()
    payload = {"event_type": "sponsors_update", "client_payload": received_payload}
    headers = {**request.headers, "accept": "application/vnd.github.v3+json"}
    url = "https://api.github.com/repos/pawamoy/sponsors/dispatches"
    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload, headers=headers)
