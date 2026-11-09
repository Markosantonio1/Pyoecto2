# actualizador_headless.py
# Versión para GitHub Actions:
# - No Flask, no interfaz.
# - Usa catalog.json/aliases.json.
# - Busca huecos y capítulos nuevos en Suwayomi.
# - Empaqueta y sube a Telegram.
# - Verifica cada PDF en Telegram y borra el archivo local.
# - Manda/edita un mensaje de progreso cada 10 segundos.

from __future__ import annotations

import asyncio
import io
import json
import os
import re
import shutil
import sys
import time
import unicodedata
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Optional

try:
    from PIL import Image, ImageFile
    ImageFile.LOAD_TRUNCATED_IMAGES = True
except ImportError:
    Image = None

try:
    from pypdf import PdfWriter
except ImportError:
    try:
        from PyPDF2 import PdfWriter
    except ImportError:
        PdfWriter = None

try:
    from telethon import TelegramClient
    from telethon.sessions import StringSession
except ImportError:
    TelegramClient = None
    StringSession = None


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
WORK_DIR = Path(os.getenv("WORK_DIR", str(BASE_DIR / "work")))
PDF_DIR = WORK_DIR / "pdfs"
TMP_DIR = WORK_DIR / "tmp"
CACHE_FILE = WORK_DIR / "suwayomi_cache.json"

SUWAYOMI_URL = os.getenv("SUWAYOMI_URL", "http://127.0.0.1:4567").rstrip("/")
GRAPHQL_URL = f"{SUWAYOMI_URL}/api/graphql"
UPLOAD_CHANNEL = int(
    os.getenv("TELEGRAM_UPLOAD_CHAT") or "-1004473963265"
)
PROGRESS_CHAT = (
    os.getenv("PROGRESS_CHAT") or "@Markosantonio"
)
MAX_WORKERS = int(os.getenv("SCAN_WORKERS", "4"))
PACKAGE_SIZE = 10
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "35"))
MAX_SERIES = int(os.getenv("MAX_SERIES", "0"))

TELEGRAM_SESSION = os.getenv("TELEGRAM_SESSION", "")
TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID", "")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")

PROGRESS: dict[str, Any] = {
    "phase": "iniciando",
    "message": "Preparando...",
    "series_total": 0,
    "series_done": 0,
    "gaps": 0,
    "new_chapters": 0,
    "pdfs_uploaded": 0,
    "pdfs_failed": 0,
    "current": "",
    "started": time.time(),
    "finished": False,
}


def log(message: str) -> None:
    stamp = time.strftime("%H:%M:%S")
    print(f"[{stamp}] {message}", flush=True)


def set_progress(**changes) -> None:
    PROGRESS.update(changes)


def load_json(path: Path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    tmp.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    os.replace(tmp, path)


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = value.encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-z0-9]+", " ", value.lower())
    return re.sub(r"\s+", " ", value).strip()


def similar(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def gql(query: str, variables: Optional[dict] = None) -> dict:
    payload: dict[str, Any] = {"query": query}
    if variables:
        payload["variables"] = variables
    req = urllib.request.Request(
        GRAPHQL_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
        data = json.loads(response.read().decode("utf-8"))
    if data.get("errors"):
        raise RuntimeError(data["errors"][0].get("message", "Error GraphQL"))
    return data.get("data") or {}


def catalog_chapters(item: dict) -> set[int]:
    present: set[int] = set()
    for package in item.get("packages") or []:
        chapters = package.get("chapters")
        if isinstance(chapters, list):
            for value in chapters:
                try:
                    number = int(float(value))
                except Exception:
                    continue
                if number >= 0:
                    present.add(number)
        else:
            try:
                present.update(
                    range(
                        int(package.get("first") or 0),
                        int(package.get("last") or 0) + 1,
                    )
                )
            except Exception:
                pass
    if not present:
        try:
            latest = int(item.get("latest_chapter") or 0)
        except Exception:
            latest = 0
        present.update(range(1, latest + 1))
    return present


def load_catalog() -> list[dict]:
    catalog = load_json(DATA_DIR / "catalog.json", {})
    aliases = load_json(DATA_DIR / "aliases.json", {})
    if not isinstance(aliases, dict):
        aliases = {}

    result = []
    for item in catalog.get("series", []):
        hashtag = str(item.get("hashtag") or "").strip()
        if not hashtag:
            continue
        present = catalog_chapters(item)
        try:
            declared = int(item.get("latest_chapter") or 0)
        except Exception:
            declared = 0
        latest = max(max(present) if present else 0, declared)
        genres = [str(g).strip().lower() for g in (item.get("genres") or [])]
        packages = item.get("packages") or []
        is_backup = "respaldo" in genres or any(
            str(p.get("channel_id") or "") == "-1004367557958"
            for p in packages
        )
        names = [item.get("name") or hashtag.lstrip("#")]
        names.extend(item.get("aliases") or [])
        names.extend(aliases.get(hashtag, []) or [])
        result.append({
            "hashtag": hashtag,
            "title": item.get("name") or hashtag.lstrip("#").replace("_", " "),
            "names": list(dict.fromkeys(n for n in names if n)),
            "present": present,
            "latest": latest,
            "backup": is_backup,
        })
        if MAX_SERIES and len(result) >= MAX_SERIES:
            break
    return result


def get_sources() -> list[dict]:
    data = gql("{ sources { nodes { id name displayName lang } } }")
    result = []
    for source in (data.get("sources") or {}).get("nodes", []):
        name = str(source.get("name") or "")
        display = str(source.get("displayName") or name)
        lang = str(source.get("lang") or "").lower()
        if name.lower() in ("local source", "suwayomi"):
            continue
        if lang not in ("es", "en"):
            continue
        result.append({
            "id": str(source.get("id")),
            "display": display,
            "lang": lang,
        })
    result.sort(key=lambda s: (0 if s["lang"] == "es" else 1, s["display"]))
    return result


def get_cached_mangas() -> list[dict]:
    data = gql("{ mangas { nodes { id title sourceId inLibrary url } } }")
    return list((data.get("mangas") or {}).get("nodes", []))


def search_source(source_id: str, query: str) -> list[dict]:
    mutation = """
    mutation Search($input: FetchSourceMangaInput!) {
      fetchSourceManga(input: $input) {
        mangas { id title sourceId inLibrary url }
      }
    }
    """
    try:
        data = gql(mutation, {"input": {
            "source": source_id,
            "query": query,
            "page": 1,
            "type": "SEARCH",
        }})
        return list((data.get("fetchSourceManga") or {}).get("mangas", []))
    except Exception:
        return []


def candidates_for(item: dict, sources: list[dict], cached: list[dict]) -> list[dict]:
    names = item["names"]
    candidates: dict[int, dict] = {}
    for manga in cached:
        score = max((similar(n, manga.get("title", "")) for n in names), default=0)
        if score >= 0.84:
            candidate = dict(manga)
            candidate["_score"] = score
            candidates[int(manga["id"])] = candidate

    cache = load_json(CACHE_FILE, {})
    for source in sources:
        for name in names[:3]:
            key = f"{source['id']}|{normalize(name)}"
            if key in cache:
                found = cache[key]
            else:
                found = search_source(source["id"], name)
                cache[key] = found
                save_json(CACHE_FILE, cache)
            for manga in found:
                score = max((similar(n, manga.get("title", "")) for n in names), default=0)
                if score < 0.82:
                    continue
                manga_id = int(manga["id"])
                candidate = dict(manga)
                candidate["_score"] = score
                candidate["sourceId"] = candidate.get("sourceId") or source["id"]
                previous = candidates.get(manga_id)
                if previous is None or score > previous.get("_score", 0):
                    candidates[manga_id] = candidate
    return list(candidates.values())


def fetch_chapters(manga_id: int) -> list[dict]:
    mutation = """
    mutation Fetch($input: FetchMangaAndChaptersInput!) {
      fetchMangaAndChapters(input: $input) {
        manga {
          chapters {
            nodes { id name chapterNumber isDownloaded pageCount uploadDate }
          }
        }
      }
    }
    """
    try:
        data = gql(mutation, {"input": {
            "id": int(manga_id),
            "fetchManga": False,
            "fetchChapters": True,
        }})
        node = (data.get("fetchMangaAndChapters") or {}).get("manga") or {}
        return list((node.get("chapters") or {}).get("nodes", []))
    except Exception:
        return []


def chapter_number(chapter: dict) -> Optional[float]:
    try:
        number = float(chapter.get("chapterNumber"))
    except Exception:
        return None
    return number if number >= 0 else None


def scan_one(item: dict, sources: list[dict], cached: list[dict]) -> Optional[dict]:
    candidates = candidates_for(item, sources, cached)
    if not candidates:
        return None

    chapter_map: dict[int, dict] = {}
    source_names = set()
    source_lookup = {s["id"]: s["display"] for s in sources}
    for candidate in candidates:
        manga_id = int(candidate["id"])
        source_id = str(candidate.get("sourceId") or "")
        source_name = source_lookup.get(source_id, source_id)
        for chapter in fetch_chapters(manga_id):
            number = chapter_number(chapter)
            if number is None or not float(number).is_integer():
                continue
            number = int(number)
            if number in chapter_map:
                continue
            chapter_map[number] = {
                "id": int(chapter["id"]),
                "number": number,
                "name": str(chapter.get("name") or ""),
                "manga_id": manga_id,
                "source_id": source_id,
                "source": source_name,
            }
            source_names.add(source_name)

    present = item["present"]
    latest = item["latest"]
    missing = [n for n in range(1, latest + 1) if n not in present]
    gaps = [n for n in missing if n in chapter_map]
    unresolved = [n for n in missing if n not in chapter_map]
    new_numbers = sorted(n for n in chapter_map if n > latest)
    if not gaps and not new_numbers:
        return None

    return {
        "hashtag": item["hashtag"],
        "title": item["title"],
        "latest": latest,
        "backup": item["backup"],
        "gaps": gaps,
        "new_chapters": new_numbers,
        "unresolved": unresolved,
        "sources": sorted(s for s in source_names if s),
        "chapter_map": {
            str(n): chapter_map[n]
            for n in sorted(set(gaps + new_numbers))
        },
    }


def scan_all() -> list[dict]:
    set_progress(
        phase="catalog",
        message="Cargando catálogo...",
        series_total=0,
        series_done=0,
        gaps=0,
        new_chapters=0,
    )
    catalog = load_catalog()
    if not catalog:
        raise RuntimeError("catalog.json vacío o no encontrado en data/.")

    set_progress(series_total=len(catalog), message="Conectando con Suwayomi...")
    sources = get_sources()
    cached = get_cached_mangas()
    log(f"Series: {len(catalog)} · fuentes: {len(sources)} · cacheadas: {len(cached)}")

    results = []
    done = 0
    pool = ThreadPoolExecutor(max_workers=MAX_WORKERS)
    futures = {
        pool.submit(scan_one, item, sources, cached): item
        for item in catalog
    }
    try:
        for future in as_completed(futures):
            item = futures[future]
            done += 1
            try:
                result = future.result()
                if result:
                    results.append(result)
            except Exception as exc:
                log(f"Error con {item['hashtag']}: {exc}")
            set_progress(
                series_done=done,
                current=item["title"],
                gaps=sum(len(r["gaps"]) for r in results),
                new_chapters=sum(len(r["new_chapters"]) for r in results),
                message=f"Escaneando {done}/{len(catalog)}...",
            )
    finally:
        pool.shutdown(wait=False, cancel_futures=True)

    results.sort(
        key=lambda r: (
            -len(r.get("gaps", [])),
            -len(r.get("new_chapters", [])),
            r.get("title", "").lower(),
        )
    )
    set_progress(
        phase="downloading",
        message=f"Listo: {len(results)} series con faltantes o nuevos.",
    )
    return results


# ============================================================
# DESCARGA / EMPAQUETADO
# ============================================================

def download_bytes(path: str) -> bytes:
    url = path if path.startswith("http") else SUWAYOMI_URL + path
    last = None
    for attempt in range(1, 4):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
                data = response.read()
            if data:
                return data
            last = RuntimeError("respuesta vacía")
        except Exception as exc:
            last = exc
        time.sleep(attempt)
    raise last or RuntimeError("no se pudo descargar la página")


def fetch_pages(chapter_id: int) -> list[str]:
    mutation = """
    mutation Pages($input: FetchChapterPagesInput!) {
      fetchChapterPages(input: $input) { pages }
    }
    """
    data = gql(mutation, {"input": {"chapterId": int(chapter_id)}})
    return list((data.get("fetchChapterPages") or {}).get("pages", []))


def safe_filename(value: str) -> str:
    value = re.sub(r'[\\/:*?"<>|]', "_", str(value or ""))
    value = re.sub(r"[\x00-\x1f]", "_", value).strip()
    return value[:150] or "serie"


def chapter_pdf(
    chapter: dict,
    index: int,
    total: int,
    temp_dir: Path,
) -> Optional[Path]:
    pages = fetch_pages(int(chapter["id"]))
    if not pages:
        return None
    number = int(chapter["number"])
    images = []
    for page_index, page in enumerate(pages, start=1):
        img = None
        last_error = None
        for attempt in range(1, 4):
            try:
                data = download_bytes(page)
                img = Image.open(io.BytesIO(data))
                img.load()
                if img.mode != "RGB":
                    img = img.convert("RGB")
                break
            except Exception as exc:
                last_error = exc
                img = None
                time.sleep(attempt * 0.8)
        if img is None:
            log(f"  Página {page_index} fallida: {last_error}")
        else:
            images.append(img)
        set_progress(
            current=f"{chapter.get('name') or number} · página {page_index}/{len(pages)}",
            message=f"Capítulo {number} ({index}/{total})",
        )

    if not images:
        return None
    path = temp_dir / f"{number:07d}.pdf"
    images[0].save(
        path,
        "PDF",
        save_all=True,
        append_images=images[1:],
        optimize=False,
    )
    return path


def contiguous_runs(numbers: list[int]) -> list[list[int]]:
    runs, current = [], []
    for number in sorted(set(int(n) for n in numbers)):
        if not current or number == current[-1] + 1:
            current.append(number)
        else:
            runs.append(current)
            current = [number]
    if current:
        runs.append(current)
    return runs


def build_groups(chapter_pdfs: list[tuple[int, Path]]) -> list[tuple[list[tuple[int, Path]], bool]]:
    by_number = {n: p for n, p in chapter_pdfs}
    groups = []
    for run in contiguous_runs(list(by_number)):
        items = [(n, by_number[n]) for n in run]
        if len(items) >= 10:
            groups.append((items, True))
        elif len(items) >= 5:
            for start in range(0, len(items), 5):
                chunk = items[start:start + 5]
                if len(chunk) == 5:
                    groups.append((chunk, True))
                else:
                    groups.extend(([item], False) for item in chunk)
        else:
            groups.extend(([item], False) for item in items)
    return groups


def merge_pdfs(paths: list[Path], output: Path) -> bool:
    if PdfWriter is None:
        return False
    writer = PdfWriter()
    for path in paths:
        try:
            writer.append(str(path))
        except Exception:
            continue
    if len(writer.pages) == 0:
        return False
    with output.open("wb") as handle:
        writer.write(handle)
    return True


def download_result(result: dict) -> list[str]:
    numbers = sorted(set(result.get("gaps", []) + result.get("new_chapters", [])))
    numbers = [int(n) for n in numbers if float(n).is_integer()]
    if not numbers:
        return []

    PDF_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    result_tmp = TMP_DIR / safe_filename(result["title"])
    result_tmp.mkdir(parents=True, exist_ok=True)

    chapter_pdfs = []
    chapter_map = result.get("chapter_map") or {}
    for index, number in enumerate(numbers, start=1):
        chapter = chapter_map.get(str(number))
        if not chapter:
            continue
        set_progress(
            phase="downloading",
            current=f"{result['title']} · capítulo {number}",
            message=f"Descargando {index}/{len(numbers)}",
        )
        pdf = chapter_pdf(
            chapter,
            index,
            len(numbers),
            result_tmp,
        )
        if pdf:
            chapter_pdfs.append((number, pdf))

    generated = []
    for group, merge in build_groups(chapter_pdfs):
        first, last = group[0][0], group[-1][0]
        base = (
            f"「{first}」{safe_filename(result['title'])}.pdf"
            if first == last
            else f"「{first}-{last}」{safe_filename(result['title'])}.pdf"
        )
        output = PDF_DIR / base
        counter = 2
        while output.exists():
            output = PDF_DIR / f"{Path(base).stem} ({counter}).pdf"
            counter += 1
        if merge:
            if merge_pdfs([p for _, p in sorted(group)], output):
                generated.append(str(output))
        else:
            try:
                shutil.copy2(group[0][1], output)
                generated.append(str(output))
            except Exception:
                pass
    return generated


# ============================================================
# TELEGRAM
# ============================================================

class Reporter:
    def __init__(self, client: TelegramClient):
        self.client = client
        self.message = None
        self.chat = PROGRESS_CHAT

    def text(self) -> str:
        total = max(1, int(PROGRESS["series_total"] or 0))
        done = int(PROGRESS["series_done"] or 0)
        pct = min(100, int(done / total * 100)) if total else 0
        bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
        elapsed = int(time.time() - PROGRESS["started"])
        return (
            "📦 ACTUALIZADOR\n"
            f"[{bar}] {pct}%\n"
            f"Series: {done}/{PROGRESS['series_total']}\n"
            f"Huecos: {PROGRESS['gaps']} · Nuevos: {PROGRESS['new_chapters']}\n"
            f"PDFs subidos: {PROGRESS['pdfs_uploaded']} · fallidos: {PROGRESS['pdfs_failed']}\n"
            f"⏱️ {elapsed // 60:02d}:{elapsed % 60:02d}\n"
            f"📌 {PROGRESS['message']}\n"
            f"🔎 {PROGRESS['current'][:80]}"
        )

    async def update(self) -> None:
        text = self.text()
        try:
            if self.message is None:
                self.message = await self.client.send_message(self.chat, text)
            else:
                await self.client.edit_message(self.message, text)
        except Exception as exc:
            log(f"Progreso no enviado a {self.chat}: {exc}")
            if self.message is None:
                try:
                    self.message = await self.client.send_message("me", text)
                    self.chat = "me"
                except Exception:
                    pass

    async def loop(self) -> None:
        while not PROGRESS["finished"]:
            await self.update()
            await asyncio.sleep(10)
        await self.update()


async def upload_verified(client: TelegramClient, path: Path, caption: str) -> bool:
    for attempt in range(1, 4):
        try:
            sent = await client.send_file(
                UPLOAD_CHANNEL,
                str(path),
                caption=caption,
                force_document=True,
                parse_mode=None,
            )
            check = await client.get_messages(UPLOAD_CHANNEL, ids=sent.id)
            size = None
            if check and getattr(check, "document", None):
                size = getattr(check.document, "size", None)
            if size != path.stat().st_size:
                raise RuntimeError(
                    f"tamaño no coincide ({size} != {path.stat().st_size})"
                )
            return True
        except Exception as exc:
            log(f"Subida fallida ({attempt}/3) {path.name}: {exc}")
            await asyncio.sleep(2 * attempt)
    return False


async def main() -> int:
    if TelegramClient is None or StringSession is None:
        log("Falta Telethon.")
        return 2
    if not TELEGRAM_SESSION or not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
        log("Faltan TELEGRAM_SESSION / API_ID / API_HASH.")
        return 2
    if Image is None or PdfWriter is None:
        log("Faltan Pillow o pypdf.")
        return 2

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    client = TelegramClient(
        StringSession(TELEGRAM_SESSION),
        int(TELEGRAM_API_ID),
        TELEGRAM_API_HASH,
        flood_sleep_threshold=60,
    )
    await client.start()
    reporter = Reporter(client)
    reporter_task = asyncio.create_task(reporter.loop())

    try:
        results = await asyncio.to_thread(scan_all)
        set_progress(
            phase="uploading",
            message=f"Series con faltantes/nuevos: {len(results)}",
        )

        for index, result in enumerate(results, start=1):
            if not result.get("gaps") and not result.get("new_chapters"):
                continue
            set_progress(
                current=f"{index}/{len(results)} · {result['title']}",
                message=f"Descargando {result['title']}",
            )
            try:
                files = await asyncio.to_thread(download_result, result)
            except Exception as exc:
                PROGRESS["pdfs_failed"] += 1
                log(f"❌ Error descargando {result['title']}: {exc}")
                files = []

            for file_path in files:
                path = Path(file_path)
                label = "Respaldo" if result.get("backup") else "Principal"
                caption = f"{result['hashtag']} ({label})"
                ok = await upload_verified(client, path, caption)
                if ok:
                    PROGRESS["pdfs_uploaded"] += 1
                    log(f"✅ Subido y verificado: {path.name} · {caption}")
                    try:
                        path.unlink()
                    except Exception:
                        pass
                else:
                    PROGRESS["pdfs_failed"] += 1
                    log(f"❌ No subido: {path.name}")

            # Limpiar temporales de esta serie.
            try:
                shutil.rmtree(TMP_DIR / safe_filename(result["title"]), ignore_errors=True)
            except Exception:
                pass

        set_progress(
            phase="done",
            message="Proceso terminado.",
            finished=True,
        )
        return 0
    except Exception as exc:
        log(f"ERROR GENERAL: {exc}")
        set_progress(
            phase="error",
            message=f"Error: {str(exc)[:180]}",
            finished=True,
        )
        return 1
    finally:
        PROGRESS["finished"] = True
        try:
            await asyncio.wait_for(reporter_task, timeout=20)
        except Exception:
            pass
        await client.disconnect()


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        sys.exit(130)

