"""
Instala las extensiones necesarias en la tienda de Suwayomi.
El workflow reinicia Suwayomi después para que cargue las fuentes.
"""

from __future__ import annotations

import json
import os
import time
import urllib.request

URL = os.getenv("SUWAYOMI_URL", "http://127.0.0.1:4567").rstrip("/")
GRAPHQL = URL + "/api/graphql"

PACKAGES = [
    "eu.kanade.tachiyomi.extension.es.manhwaweb",
    "eu.kanade.tachiyomi.extension.es.olympusscanlation",
    "eu.kanade.tachiyomi.extension.es.taurusfansub",
    "eu.kanade.tachiyomi.extension.es.mhscans",
    "eu.kanade.tachiyomi.extension.all.novelcool",
    "eu.kanade.tachiyomi.extension.all.mayotune",
]


def gql(query: str, variables=None) -> dict:
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    request = urllib.request.Request(
        GRAPHQL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        data = json.loads(response.read().decode("utf-8"))
    if data.get("errors"):
        raise RuntimeError(data["errors"][0].get("message", "GraphQL error"))
    return data.get("data") or {}


def main() -> int:
    print("Actualizando tienda de extensiones...")
    try:
        gql("mutation { fetchExtensions(input: {}) { clientMutationId } }")
    except Exception as exc:
        print(f"AVISO al refrescar la tienda: {exc}")

    try:
        data = gql("{ extensions { totalCount } }")
        count = (data.get("extensions") or {}).get("totalCount")
        print(f"Extensiones en tienda: {count}")
    except Exception as exc:
        print(f"AVISO consultando tienda: {exc}")

    install = """
    mutation Install($input: UpdateExtensionInput!) {
      updateExtension(input: $input) {
        extension { pkgName name isInstalled }
      }
    }
    """

    for package in PACKAGES:
        try:
            data = gql(install, {
                "input": {
                    "id": package,
                    "patch": {"install": True},
                }
            })
            result = data.get("updateExtension") or {}
            ext = result.get("extension") or {}
            print(
                f"OK {package} -> "
                f"{ext.get('name')} instalada={ext.get('isInstalled')}"
            )
        except Exception as exc:
            print(f"AVISO {package}: {exc}")
        time.sleep(1)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
