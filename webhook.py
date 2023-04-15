import asyncio
import logging
import os
from datetime import datetime, timedelta

from fastapi import FastAPI, Request

GITHUB_API = "https://api.github.com"
TRIGGER_WORKFLOW = "/repos/pawamoy/sponsors/actions/workflows/insiders/dispatches"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
COOLDOWN = timedelta(seconds=60)
HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "X-GitHub-Api-Version": "2022-11-28",
}

logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(message)s")
app = FastAPI()


async def trigger_workflow() -> None:
    logging.info("Triggering workflow")
    async with httpx.AsyncClient(base_url=GITHUB_API) as client:
        response = await client.post(TRIGGER_WORKFLOW, headers=HEADERS)
        response.raise_for_status()


class Workflow:
    def __init__(self) -> None:
        self.last_trigger = datetime.now() - COOLDOWN
        self.scheduled = False

    async def wait_and_trigger(self, delta: timedelta) -> None:
        await asyncio.sleep(max(0, delta.seconds))
        self.last_trigger = datetime.now()
        await trigger_workflow()
        self.scheduled = False

    async def batched_trigger(self) -> None:
        if datetime.now() - self.last_trigger >= COOLDOWN:
            self.last_trigger = datetime.now()
            await trigger_workflow()
        elif not self.scheduled:
            self.scheduled = True
            delta = COOLDOWN - (datetime.now() - self.last_trigger)
            logging.info(f"Scheduled workflow trigger in {delta.seconds} seconds")
            asyncio.create_task(self.wait_and_trigger(delta))
        else:
            logging.info("Trigger already scheduled")


workflow = Workflow()


@app.post("/")
async def handle_webhook(request: Request):
    logging.info(f"Received webhook event: {await request.json()}")
    await workflow.batched_trigger()
