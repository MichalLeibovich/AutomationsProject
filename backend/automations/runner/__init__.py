"""The runner: what turns a queued run into an executed automation.

Without this process a run created by the dashboard stays queued forever. The
runner polls the API for queued work, executes the matching pytest target, and
lets the suite report its own steps and outcome.
"""
