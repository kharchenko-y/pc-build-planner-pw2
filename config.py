"""Runtime configuration for the local app and public deployment."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENVIRONMENT = os.getenv("PCBUILDER_ENV", "development")
if ENVIRONMENT not in {"development", "production"}:
    raise RuntimeError("Use development or production for PCBUILDER_ENV.")
PRODUCTION = ENVIRONMENT == "production"
SESSION_SECONDS = 2 * 60 * 60
LOCAL_PASSWORD = "demo12345"
SESSION_SECRET = os.getenv("SESSION_SECRET", "")
if PRODUCTION and (len(SESSION_SECRET) < 43 or not os.getenv("PCBUILDER_DB")):
    raise RuntimeError("Set SESSION_SECRET and an absolute persistent PCBUILDER_DB path.")
if PRODUCTION and not Path(os.environ["PCBUILDER_DB"]).is_absolute():
    raise RuntimeError("PCBUILDER_DB must be an absolute persistent path.")
SESSION_SECRET = SESSION_SECRET or "local-dev-secret-change-me"
