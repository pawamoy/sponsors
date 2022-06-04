import os
import hmac
import hashlib
import json

import httpx

secret = os.getenv("WEBHOOK_SECRET").encode("utf8")
payload = {"some": "payload"}
message = json.dumps(payload).encode("utf8")
digest = hmac.new(secret, message, hashlib.sha256).hexdigest()
httpx.post("http://localhost:5000", json={"some": "payload"}, headers={"X-Hub-Signature-256": f"sha256={digest}"})
