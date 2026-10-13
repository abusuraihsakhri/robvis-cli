"""Test-only configuration. Never used by production entry points."""
import os

os.environ.setdefault("AUDIT_SECRET_KEY", "test-only-ephemeral-key-do-not-use-in-production")
