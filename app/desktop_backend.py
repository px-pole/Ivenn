import os
import sys
from pathlib import Path

import uvicorn
from alembic import command
from alembic.config import Config

from app.services.backup import apply_pending_restore


def main() -> None:
    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent)).resolve()
    apply_pending_restore(os.environ["DATABASE_URL"], os.environ["STORAGE_DIR"])
    alembic_config = Config(bundle_root / "alembic.ini")
    alembic_config.set_main_option("script_location", str(bundle_root / "app/db/migrations"))
    command.upgrade(alembic_config, "head")

    from app.main import app

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=int(os.environ.get("INVENTORY_VAULT_PORT", "8765")),
        log_level="info",
    )


if __name__ == "__main__":
    main()