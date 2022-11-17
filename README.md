# Sponsors management system for mkdocstrings

This system is composed of a webhook handler
and two GitHub workflows (pipelines).

The webhook handler is a FastAPI app, deployed on Heroku,
that receives event payloads emitted by GitHub
when users subscribe to, or cancel, sponsor tiers
on my own account (@pawamoy). It verifies
the integrity of the event payload and uses
git to push the payload onto this very same repository.

Pushing a commit triggers the insiders workflow,
which reads the updated event payload to grant/revoke
access to/from the private repositories of the organization.
It does so by adding/removing users from the insiders team,
which itself grants access to several repositories.

The second workflow is scheduled to run once or twice each day,
and is responsible for syncing things up: sponsors
and users in the insiders team, in case something went wrong.
