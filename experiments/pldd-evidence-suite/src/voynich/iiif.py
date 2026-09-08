"""Read-only helpers for Yale's IIIF Presentation 3 manifest."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Canvas:
    label: str
    canvas_id: str
    image_id: str
    image_service_id: str
    width: int
    height: int


def _first_label(value: dict[str, list[str]] | None) -> str:
    if not value:
        return ""
    for language in ("none", "en"):
        labels = value.get(language)
        if labels:
            return labels[0]
    return next(iter(value.values()))[0]


def extract_canvases(manifest: dict[str, Any]) -> list[Canvas]:
    canvases: list[Canvas] = []
    for item in manifest.get("items", []):
        body = item["items"][0]["items"][0]["body"]
        service = body.get("service", [{}])[0]
        canvases.append(
            Canvas(
                label=_first_label(item.get("label")),
                canvas_id=item["id"],
                image_id=body["id"],
                image_service_id=service.get("@id") or service.get("id") or "",
                width=int(item["width"]),
                height=int(item["height"]),
            )
        )
    return canvases


def load_canvases(path: str | Path) -> list[Canvas]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return extract_canvases(json.load(handle))


def serializable_index(
    canvases: list[Canvas], valid_ivtff_page_ids: set[str]
) -> dict[str, Any]:
    # Composite foldouts cannot be normalized safely to IVTFF page IDs. Keep
    # every Yale label verbatim and expose only exact simple folios as a helper.
    simple_folios = {
        f"f{canvas.label}": asdict(canvas)
        for canvas in canvases
        if __import__("re").fullmatch(r"\d+[rv]", canvas.label)
        and f"f{canvas.label}" in valid_ivtff_page_ids
    }
    unmapped_simple_labels = [
        canvas.label
        for canvas in canvases
        if __import__("re").fullmatch(r"\d+[rv]", canvas.label)
        and f"f{canvas.label}" not in valid_ivtff_page_ids
    ]
    return {
        "warning": (
            "Yale composite and partial-foldout labels require a reviewed explicit "
            "crosswalk before mapping to IVTFF panel IDs."
        ),
        "canvas_count": len(canvases),
        "canvases": [asdict(canvas) for canvas in canvases],
        "simple_folios": simple_folios,
        "unmapped_simple_canvas_labels": unmapped_simple_labels,
    }
