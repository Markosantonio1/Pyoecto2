"""
Convierte una sesión local de Telethon en StringSession para GitHub Secrets.

Uso:
    python tools/export_session.py

Por defecto busca manhuas_downloader.session en C:\\ManhuasCatalog.
Cierra funcional.py / todost.py / tarantino.py antes de ejecutarlo.
No subas el resultado a GitHub: cópialo en el secret TELEGRAM_SESSION.
"""

import asyncio
import os
import sys
from pathlib import Path

from telethon import TelegramClient
from telethon.sessions import StringSession

BASE = Path(r"C:\ManhuasCatalog")
ENV = BASE / ".env"
SESSION = BASE / "manhuas_downloader"


def env_value(key: str) -> str:
    if ENV.exists():
        for line in ENV.read_text(encoding="utf-8").splitlines():
            if line.startswith(key + "="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.getenv(key, "")


async def export() -> int:
    api_id = env_value("TELEGRAM_API_ID")
    api_hash = env_value("TELEGRAM_API_HASH")
    if not api_id or not api_hash:
        print("Faltan TELEGRAM_API_ID / TELEGRAM_API_HASH en .env")
        return 1

    client = TelegramClient(str(SESSION), int(api_id), api_hash)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            print("La sesión local no está autorizada.")
            return 2
        value = StringSession.save(client.session)
        print("\nCopia TODO esto en el secret TELEGRAM_SESSION:\n")
        print(value)
        print("\nNo lo compartas ni lo subas al repositorio.")
        return 0
    except Exception as exc:
        print(f"Error abriendo la sesión: {exc}")
        print("Cierra funcional.py/todost.py/tarantino.py e inténtalo de nuevo.")
        return 3
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(asyncio.run(export()))
