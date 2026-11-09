"""
Instala las extensiones necesarias en el Suwayomi del runner.
Se ejecuta después de que el servidor responde en 127.0.0.1:4567.
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
    gql("mutation { fetchExtensions(input: {}) { clientMutationId } }")

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
            ext = data.get("updateExtension", {}).get("extension", {})
            print(f"OK {package} -> {ext.get('name')} instalada={ext.get('isInstalled')}")
        except Exception as exc:
            print(f"AVISO {package}: {exc}")

    # Esperar a que las fuentes aparezcan.
    query = "{ sources { nodes { id name displayName lang } } }"
    for attempt in range(30):
        data = gql(query)
        nodes = data.get("sources", {}).get("nodes", [])
        print(f"Fuentes ({attempt + 1}/30): {[(n.get('displayName'), n.get('lang')) for n in nodes]}")
        if len(nodes) > 1:
            return 0
        time.sleep(3)

    print("No aparecieron fuentes distintas de Local source.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
