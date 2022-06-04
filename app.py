import hmac
import hashlib
import os
import json
import tempfile
from pathlib import Path
from subprocess import run

from fastapi import FastAPI, Request
from loguru import logger

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
DEPLOY_KEY = os.getenv("DEPLOY_KEY")

app = FastAPI()


def is_valid_signature(secret, payload, their_hash):
    payload_bytes = json.dumps(payload).encode("utf8")
    our_hash = hmac.new(secret.encode("utf8"), payload_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(our_hash, their_hash)


@app.post("/")
async def trigger_workflow(request: Request):
    payload_hash = request.headers["X-Hub-Signature-256"][7:]  # remove leading sha256=
    payload_data = await request.json()
    if not is_valid_signature(WEBHOOK_SECRET, payload_data, payload_hash):
        logger.error("Invalid payload hash")
        return "Invalid payload hash", 400
    
    push_update(payload_data)


def push_update(payload):
    with tempfile.TemporaryDirectory() as tmpdir:
        logger.debug("Preparing SSH key and setting up git")
        tmpkey_path = Path(tmpdir, "deploy_key")
        tmpkey_path.write_text(DEPLOY_KEY)
        ssh_cmd = f"ssh -i {tmpkey_path} -oIdentitiesOnly=yes -oStrictHostKeyChecking=no -oUserKnownHostsFile=/dev/null"
        os.environ["GIT_SSH_COMMAND"] = ssh_cmd

        logger.debug("Cloning repository")
        repo_dir = Path(tmpdir, "sponsors")
        run(["git", "clone", "git@github.com:pawamoy/sponsors", str(repo_dir)])

        logger.debug("Updating history")
        history_file = repo_dir / "history.json"
        history = json.loads(history_file.read_text())
        history.append(payload)
        history_file.write_text(json.dumps(history))

        logger.debug("Updating current payload")
        payload_file = repo_dir / "payload.json"
        payload_file.write_text(json.dumps(payload))

        logger.debug("Committing and pushing")
        run(["git", "-C", str(repo_dir), "commit", "-am", "sponsors update"])
        run(["git", "-C", str(repo_dir), "push"])
