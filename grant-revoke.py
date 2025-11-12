import os
from pathlib import Path

from insiders import GitHub, Polar, update_sponsors_file, update_numbers_file


GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
POLAR_TOKEN = os.environ["POLAR_TOKEN"]
TEAM = "pawamoy-insiders/insiders"
MIN_AMOUNT = 10

beneficiaries = {
    "github": {
        "activeloopai": [
            {"account": "activeloop-bot", "grant": True},
            {"account": "nvoxland-al", "grant": True},
            {"account": "davidbuniat", "grant": True},
        ],
        "Cusp-AI": [
            {"account": "pimdh", "grant": True},
        ],
        "kolenaIO": [
            {"account": "kolenabot", "grant": True},
        ],
        "livingbio": [
            {"account": "lucemia", "grant": True},
        ],
        "latentai": [
            {"account": "polloelastico", "grant": True},
        ],
        "logfire": [
            {"account": "samuelcolvin", "grant": True},
            {"account": "Kludex", "grant": True},
        ],
        "NemetschekAllplan": [
            {"account": "bmarciniec", "grant": True},
        ],
        "Nixtla": [
            {"account": "deven367", "grant": True},
            {"account": "nasaul", "grant": True},
        ],
        "NyckelAI": [
            {"account": "beijbom", "grant": True},
        ],
        "okio-ai": [
            {"account": "faradox", "grant": True},
            {"account": "aaronabebe", "grant": True},
        ],
        "RapidataAI": [
            {"account": "LinoGiger", "grant": True},
            {"account": "kannwism", "grant": True},
        ],
        "tektronix": [
            {"account": "tek-githubbot-1010", "grant": True},
            {"account": "nfelt14", "grant": True},
        ],
        "theSymbolSyndicate": [
            {"account": "Wayonb", "grant": True},
        ],
        "willmcgugan": [
            "&Textualize",
            {"account": "darrenburns", "grant": True},
            {"account": "willmcgugan", "grant": True},
        ],
    },
    "polar": {
        "patrick91": ["patrick91"],
        "birkjernstrom": ["birkjernstrom"],
    }
}

include_users = {
    "pawamoy",  # Myself.
    "squidfunk",  # For their contributions to the MkDocs ecosystem.
    "facelessuser",  # For their contributions to the MkDocs ecosystem.
    "waylan",  # For their contributions to the MkDocs ecosystem.
    "bswck",  # For their contributions to the Python ecosystem.
    "ZeroIntensity",  # For their contributions to the C handler.
    "alexvoss",  # Work-related.
}

exclude_users = {
    "medecau",  # Doesn't want to join the team.
}


def main():
    with GitHub(GITHUB_TOKEN) as github, Polar(POLAR_TOKEN) as polar:
        sponsors = github.get_sponsors() + polar.get_sponsors()
        github.consolidate_beneficiaries(sponsors, beneficiaries)  # type: ignore[arg-type]
        github.sync_team(
            TEAM,
            sponsors=sponsors,
            min_amount=MIN_AMOUNT,
            include_users=include_users,
            exclude_users=exclude_users,
        )

    update_numbers_file(sponsors.sponsorships, filepath=Path("numbers.json"))
    update_sponsors_file(sponsors.sponsorships, filepath=Path("sponsors.json"), exclude_private=True)


if __name__ == "__main__":
    raise SystemExit(main())
