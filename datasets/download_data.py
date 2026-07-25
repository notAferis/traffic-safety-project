from __future__ import annotations

from argparse import ArgumentParser
from hashlib import sha1
from pathlib import Path
from typing import Iterable

from better_bing_image_downloader import downloader

search_strings = {
    "accident": [
        "ghana car crashes",
        "Car Crash in Ghana",
        "Motor Accident Ghana",
        "Motor Ghana Accident Ghana",
        "Breaking News in Ghana Today Accident",
        "pick up car accident in ghana",
        "tro tro car accident in ghana",
        "bus accident middle of the road in ghana",
    ],
    "conjestions": [
        "Traffic Congestion in Ghana",
        "Traffic Congestion in Accra",
        "Traffic Congestion in Kumasi",
        "Traffic Congestion in Takoradi",
    ],
}

DATA_ROOT = Path(__file__).resolve().parent / "data"
DEFAULT_LIMIT = 50
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}


def _unique_items(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        normalized = " ".join(item.split()).casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        unique.append(item)
    return unique


def _dedupe_images(root: Path) -> int:
    seen_hashes: dict[str, Path] = {}
    removed = 0

    for path in sorted(root.glob("*")):
        if not path.is_file() or path.name.startswith("_"):
            continue

        digest = sha1(path.read_bytes()).hexdigest()
        if digest in seen_hashes:
            path.unlink()
            removed += 1
            continue

        seen_hashes[digest] = path

    return removed


def _flatten_class_folder(folder: Path) -> None:
    for path in sorted(folder.rglob("*"), reverse=True):
        if path.is_dir():
            if path != folder and not any(path.iterdir()):
                path.rmdir()
            continue

        if path.suffix.lower() not in IMAGE_SUFFIXES:
            path.unlink()
            continue

        if path.parent == folder:
            continue

        target = folder / path.name
        if target.exists():
            path.unlink()
            continue

        path.replace(target)


def _unique_target_path(folder: Path, source: Path) -> Path:
    candidate = folder / source.name
    if not candidate.exists():
        return candidate

    digest = sha1(source.read_bytes()).hexdigest()[:8]
    candidate = folder / f"{source.stem}_{digest}{source.suffix.lower()}"
    if not candidate.exists():
        return candidate

    index = 1
    while True:
        numbered = folder / f"{source.stem}_{digest}_{index}{source.suffix.lower()}"
        if not numbered.exists():
            return numbered
        index += 1


def _move_downloaded_images(temp_root: Path, folder: Path) -> None:
    for path in sorted(temp_root.rglob("*"), reverse=True):
        if path.is_dir():
            if not any(path.iterdir()):
                path.rmdir()
            continue

        if path.suffix.lower() not in IMAGE_SUFFIXES:
            path.unlink()
            continue

        target = _unique_target_path(folder, path)
        path.replace(target)

    if temp_root.exists():
        for path in sorted(temp_root.rglob("*"), reverse=True):
            if path.is_file() or path.is_symlink():
                path.unlink()
            elif path.exists():
                path.rmdir()
        if temp_root.exists():
            temp_root.rmdir()


def _download_query_to_flat_folder(query: str, folder: Path, limit: int, force_replace: bool) -> None:
    temp_root = folder / "_tmp_downloads"
    temp_root.mkdir(parents=True, exist_ok=True)

    downloader(
        query=query,
        limit=limit,
        output_dir=str(temp_root),
        engine="bing",
        adult_filter_off=True,
        force_replace=force_replace,
        verbose=False,
        manifest=False,
    )

    _move_downloaded_images(temp_root, folder)


def download_dataset(limit: int = DEFAULT_LIMIT, force_replace: bool = False) -> None:
    DATA_ROOT.mkdir(parents=True, exist_ok=True)

    for category, queries in search_strings.items():
        output_dir = DATA_ROOT / category
        output_dir.mkdir(parents=True, exist_ok=True)
        _flatten_class_folder(output_dir)

        for query in _unique_items(queries):
            _download_query_to_flat_folder(query, output_dir, limit, force_replace)

        _flatten_class_folder(output_dir)
        removed = _dedupe_images(output_dir)
        print(f"{category}: removed {removed} duplicate images")


if __name__ == "__main__":
    parser = ArgumentParser(description="Download accident and congestion image datasets.")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--force-replace", action="store_true")
    args = parser.parse_args()
    download_dataset(limit=args.limit, force_replace=args.force_replace)
