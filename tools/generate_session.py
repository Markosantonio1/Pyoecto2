r"""
Genera una StringSession NUEVA para la cuenta de Telegram que usará
GitHub Actions. No reutiliza la sesión de funcional.py/todost.py.

Uso:
    cd C:\ManhuasCatalog\github_actualizador
    python .\tools\generate_session.py

El resultado se guarda en tools/session_new.txt y se imprime en pantalla.
NO subas session_new.txt al repositorio.
"""

import asyncio
import getpass
import sys
from pathlib import Path

from telethon import TelegramClient
from telethon.sessions import StringSession

OUTPUT = Path(__file__).resolve().parent / "session_new.txt"


async def main() -> int:
    print("Cuenta nueva para GitHub Actions")
    print("--------------------------------")
    phone = input("Teléfono (ej. +5355733510): ").strip()
    api_id = input("API ID: ").strip()
    api_hash = getpass.getpass("API Hash (no se mostrará): ").strip()

    if not phone or not api_id or not api_hash:
        print("Faltan datos.")
        return 1

    client = TelegramClient(
        StringSession(),
        int(api_id),
        api_hash,
    )

    try:
        print("\nConectando. Telegram pedirá el código que llegue a la cuenta...")
        await client.start(phone=phone)
        if not await client.is_user_authorized():
            print("La cuenta no quedó autorizada.")
            return 2

        me = await client.get_me()
        print(f"Cuenta: {me.first_name or ''} @{me.username or ''}")

        value = StringSession.save(client.session)
        OUTPUT.write_text(value, encoding="utf-8")

        print("\nSesión generada correctamente.")
        print(f"Archivo local: {OUTPUT}")
        print("\nCopia el contenido de session_new.txt en el secret TELEGRAM_SESSION.")
        print("No subas ese archivo a GitHub.")
        return 0
    except Exception as exc:
        print(f"\nError: {exc}")
        return 3
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
