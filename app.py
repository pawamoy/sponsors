import hmac
import hashlib
import os
import json
import tempfile
from pathlib import Path
from subprocess import run

from fastapi import FastAPI, Request, HTTPException
from loguru import logger

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
DEPLOY_KEY = os.getenv("DEPLOY_KEY")

app = FastAPI()


def is_valid_signature(secret, payload, their_hash):
    our_hash = hmac.new(secret.encode("utf8"), payload, hashlib.sha256).hexdigest()
    logger.debug(f"Our computed hash: {our_hash}")
    logger.debug(f"GitHub's hash: {their_hash}")
    return hmac.compare_digest(our_hash, their_hash.replace("sha256=", ""))


@app.post("/")
async def handle_webhook(request: Request):
    payload_data = await request.body()
    payload_hash = request.headers["X-Hub-Signature-256"]
    if not is_valid_signature(WEBHOOK_SECRET, payload_data, payload_hash):
        logger.error("Invalid payload hash")
        raise HTTPException(status_code=400, detail="Invalid payload hash.")
    
    push_update(await request.json())


def push_update(payload):
    with tempfile.TemporaryDirectory() as tmpdir:
        logger.debug("Preparing SSH key and setting up git")
        tmpkey_path = Path(tmpdir, "deploy_key")
        tmpkey_path.write_text(DEPLOY_KEY + "\n")
        ssh_cmd = f"ssh -i {tmpkey_path} -oIdentitiesOnly=yes -oStrictHostKeyChecking=no -oUserKnownHostsFile=/dev/null"
        os.environ["GIT_SSH_COMMAND"] = ssh_cmd

        logger.debug("Cloning repository")
        repo_dir = Path(tmpdir, "sponsors")
        run(["git", "clone", "git@github.com:pawamoy/sponsors", str(repo_dir)], check=True)

        logger.debug("Updating history")
        history_file = repo_dir / "history.json"
        history = json.loads(history_file.read_text())
        history.append(payload)
        history_file.write_text(json.dumps(history))

        logger.debug("Updating current payload")
        payload_file = repo_dir / "payload.json"
        payload_file.write_text(json.dumps(payload))

        logger.debug("Committing and pushing")
        run(["git", "-C", str(repo_dir), "commit", "-am", "sponsors update"], check=True)
        run(["git", "-C", str(repo_dir), "push"], check=True)
