from datetime import datetime
import os
import json
from pathlib import Path

import httpx

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
SPONSORED_ACCOUNT = os.getenv("SPONSORED_ACCOUNT", "pawamoy")
MIN_AMOUNT = os.getenv("MIN_AMOUNT", 10)
GITHUB_ORG = os.getenv("GITHUB_ORG", "mkdocstrings")
INSIDERS_TEAM = os.getenv("INSIDERS_TEAM", "insiders")
PRIVILEGED_USERS = frozenset({
    "pawamoy",
    "oprypin",
    "squidfunk",
    # "facelessuser",
    # "waylan",
})


def grant(user: str):
    with httpx.Client() as client:
        response = client.put(
            f"https://api.github.com/orgs/{GITHUB_ORG}/teams/{INSIDERS_TEAM}/memberships/{user}",
            headers={"Authorization": f"Bearer {GITHUB_TOKEN}"}
        )
        try:
            response.raise_for_status()
        except httpx.HTTPError as error:
            print(f"Couldn't add @{user} to {INSIDERS_TEAM} team: {error}")
        else:
            print(f"@{user} added to {INSIDERS_TEAM} team")


def revoke(user: str):
    with httpx.Client() as client:
        response = client.delete(
            f"https://api.github.com/orgs/{GITHUB_ORG}/teams/{INSIDERS_TEAM}/memberships/{user}",
            headers={"Authorization": f"Bearer {GITHUB_TOKEN}"}
        )
        try:
            response.raise_for_status()
        except httpx.HTTPError as error:
            print(f"Couldn't remove @{user} from {INSIDERS_TEAM} team: {error}")
        else:
            print(f"@{user} removed from {INSIDERS_TEAM} team")


def handle_event(event):
    # event payload examples:
    # https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads#sponsorship
    action = event["action"]
    sponsor = event["sponsorship"]["sponsor"]
    tier = event["sponsorship"]["tier"]

    # credits to Martin Donath @squidfunk
    if sponsor["type"] == "User" and not tier["is_one_time"]:
        # Sponsorship
        if action == "created":
            if tier["monthly_price_in_dollars"] >= MIN_AMOUNT:
                grant(sponsor["login"])

        # Sponsorship cancellation
        elif action == "cancelled":
            if tier["monthly_price_in_dollars"] >= MIN_AMOUNT:
                revoke(sponsor["login"])

        # Sponsorship tier change
        elif action == "tier_changed":
            previous = event["changes"]["tiers"]["from"]
            if tier["monthly_price_in_dollars"] >= MIN_AMOUNT:
                if previous["monthly_price_in_dollars"] < MIN_AMOUNT:
                    grant(sponsor["login"])
            else:
                revoke(sponsor["login"])


def get_sponsors():
    subscriptions = []
    with httpx.Client(base_url="https://api.github.com") as client:
        cursor = "null"
        while True:
            payload = {
                "query": """
                    query {
                    viewer {
                        sponsorshipsAsMaintainer(
                        first: 100,
                        after: %s
                        includePrivate: true,
                        orderBy: {
                            field: CREATED_AT,
                            direction: DESC
                        }
                        ) {
                        pageInfo {
                            hasNextPage
                            endCursor
                        }
                        nodes {
                            createdAt,
                            isOneTimePayment,
                            privacyLevel,
                            sponsorEntity {
                            ...on Actor {
                                __typename,
                                login,
                                avatarUrl,
                                url
                            }
                            },
                            tier {
                            monthlyPriceInDollars
                            }
                        }
                        }
                    }
                    }
                """ % cursor
            }
            response = client.post(f"https://api.github.com/graphql", json=payload, headers={"Authorization": f"Bearer {GITHUB_TOKEN}"})
            response.raise_for_status()

            # Post-process subscription data
            data = response.json()["data"]
            for item in data["viewer"]["sponsorshipsAsMaintainer"]["nodes"]:
                if item["isOneTimePayment"]:
                    continue

                # Determine insider type
                insider_type = "user" if item["sponsorEntity"]["__typename"] == "User" else "organization"

                # Determine insider data
                user = {
                    "type": insider_type,
                    "name": item["sponsorEntity"]["login"],
                    "image": item["sponsorEntity"]["avatarUrl"],
                    "url": item["sponsorEntity"]["url"]
                }

                # Add subscription
                subscriptions.append({
                    "user": user,
                    "visibility": item["privacyLevel"].lower(),
                    "created": datetime.strptime(item["createdAt"], "%Y-%m-%dT%H:%M:%SZ"),
                    "amount": item["tier"]["monthlyPriceInDollars"]
                })

            # Check for next page
            if (data["viewer"]["sponsorshipsAsMaintainer"]["pageInfo"]["hasNextPage"]):
                cursor = f'"{data["viewer"]["sponsorshipsAsMaintainer"]["pageInfo"]["endCursor"]}"'
            else:
                break

    return subscriptions


def get_insiders() -> list[str]:
    response = httpx.get(
        f"https://api.github.com/orgs/{GITHUB_ORG}/teams/{INSIDERS_TEAM}/members",
        params={"per_page": 100},
        headers={"Authorization": f"Bearer {GITHUB_TOKEN}"}
    )
    response.raise_for_status()
    return {user["login"] for user in response.json()}


def get_invited() -> list[str]:
    response = httpx.get(
        f"https://api.github.com/orgs/{GITHUB_ORG}/teams/{INSIDERS_TEAM}/invitations",
        params={"per_page": 100},
        headers={"Authorization": f"Bearer {GITHUB_TOKEN}"}
    )
    response.raise_for_status()
    return {user["login"] for user in response.json()}


def main(args=None):
    if args:
        payload_path = args[0]
        event = json.loads(Path(payload_path).read_text())
        handle_event(event)
    else:
        sponsors = get_sponsors()
        insiders = get_insiders() #| get_invited()

        eligible_users = {sponsor["user"]["name"] for sponsor in sponsors if sponsor["amount"] >= MIN_AMOUNT}
        eligible_users |= PRIVILEGED_USERS

        # revoke accesses
        for user in insiders:
            if user not in eligible_users:
                revoke(user)

        # grant accesses
        for user in eligible_users:
            if user not in insiders:
                grant(user)


if __name__ == "__main__":
    raise SystemExit(main())
