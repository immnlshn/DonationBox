from __future__ import annotations

import os

from alembic import command
from alembic.config import Config


async def run_migrations() -> None:
    """
    Runs `alembic upgrade head` programmatically.
    """
    # backend/database/init_db.py
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    alembic_ini_path = os.path.join(backend_dir, "alembic.ini")

    if not os.path.exists(alembic_ini_path):
        raise FileNotFoundError(
            f"alembic.ini not found at {alembic_ini_path}. "
            "Did you run `alembic init alembic`?"
        )

    alembic_cfg = Config(alembic_ini_path)

    # ensure script_location resolves correctly
    alembic_cfg.set_main_option(
        "script_location",
        os.path.join(backend_dir, "alembic"),
    )

    await command.upgrade(alembic_cfg, "head")
