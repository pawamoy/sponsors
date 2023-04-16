# Sponsors management system

This system is composed of a webhook handler
and a GitHub workflow (pipeline).

The webhook handler is a FastAPI app
that receives event payloads emitted by GitHub
when users subscribe to, or cancel, sponsor tiers
on my own account (@pawamoy). 

When it receives such an event, it triggers a GitHub workflow,
which in turn synchronizes sponsors and members
of my configured insiders teams, effectively granting/revoking
access to/from private repositories.
