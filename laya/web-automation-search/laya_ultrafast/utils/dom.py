from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ElementSnapshot:
    """Snapshot estruturado de um elemento do DOM."""

    id: str
    index: int
    tag: str
    role: str
    label: str
    selector: str
    bbox: dict[str, float]  # x, y, width, height, top, right, bottom, left
    attrs: dict[str, str]
    state: dict[str, bool | str]
    is_visible: bool
    is_obstructed: bool
    is_interactive: bool
    is_editable: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "index": self.index,
            "tag": self.tag,
            "role": self.role,
            "label": self.label,
            "selector": self.selector,
            "bbox": self.bbox,
            "attrs": self.attrs,
            "state": self.state,
            "is_visible": self.is_visible,
            "is_obstructed": self.is_obstructed,
            "is_interactive": self.is_interactive,
            "is_editable": self.is_editable,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ElementSnapshot:
        return cls(
            id=data["id"],
            index=data["index"],
            tag=data["tag"],
            role=data["role"],
            label=data["label"],
            selector=data["selector"],
            bbox=data["bbox"],
            attrs=data["attrs"],
            state=data["state"],
            is_visible=data["is_visible"],
            is_obstructed=data["is_obstructed"],
            is_interactive=data["is_interactive"],
            is_editable=data["is_editable"],
        )

    def get_bbox(self) -> tuple[float, float, float, float]:
        """Retorna (x, y, width, height)."""
        return (
            self.bbox["x"],
            self.bbox["y"],
            self.bbox["width"],
            self.bbox["height"],
        )

    def get_center(self) -> tuple[float, float]:
        """Retorna centro (x, y)."""
        return (
            self.bbox["x"] + self.bbox["width"] / 2,
            self.bbox["y"] + self.bbox["height"] / 2,
        )


def sanitize_selector(selector: str) -> str:
    """Sanitiza seletor CSS para prevenir injeção."""
    # Remove caracteres perigosos
    dangerous = ["<", ">", '"', "'", "`", "$", "{", "}"]
    for char in dangerous:
        selector = selector.replace(char, "")
    return selector


def normalize_label(label: str, max_length: int = 100) -> str:
    """Normaliza label para uso em prompts."""
    if not label:
        return ""
    # Remove whitespace excessivo
    label = re.sub(r"\s+", " ", label).strip()
    # Trunca
    if len(label) > max_length:
        label = label[: max_length - 1] + "…"
    return label


def extract_interactive_elements(
    snapshots: list[ElementSnapshot],
    include_non_interactive: bool = False,
) -> list[ElementSnapshot]:
    """Filtra apenas elementos interativos."""
    if include_non_interactive:
        return snapshots
    return [s for s in snapshots if s.is_interactive or s.is_editable]


def filter_visible_elements(snapshots: list[ElementSnapshot]) -> list[ElementSnapshot]:
    """Filtra apenas elementos visíveis e não obstruídos."""
    return [s for s in snapshots if s.is_visible and not s.is_obstructed]


def sort_by_visual_order(snapshots: list[ElementSnapshot]) -> list[ElementSnapshot]:
    """Ordena por ordem visual (top-to-bottom, left-to-right)."""
    return sorted(snapshots, key=lambda s: (round(s.bbox["top"] / 10) * 10, s.bbox["left"]))


def group_by_role(snapshots: list[ElementSnapshot]) -> dict[str, list[ElementSnapshot]]:
    """Agrupa elementos por role ARIA."""
    groups: dict[str, list[ElementSnapshot]] = {}
    for s in snapshots:
        groups.setdefault(s.role, []).append(s)
    return groups


def find_element_by_id(snapshots: list[ElementSnapshot], element_id: str) -> ElementSnapshot | None:
    """Busca elemento por ID."""
    for s in snapshots:
        if s.id == element_id:
            return s
    return None


def find_element_by_selector(
    snapshots: list[ElementSnapshot], selector: str
) -> ElementSnapshot | None:
    """Busca elemento por seletor CSS."""
    for s in snapshots:
        if s.selector == selector:
            return s
    return None


def find_elements_by_label(
    snapshots: list[ElementSnapshot],
    label: str,
    fuzzy: bool = True,
) -> list[ElementSnapshot]:
    """Busca elementos por label (exato ou fuzzy)."""
    label_lower = label.lower()
    results = []
    for s in snapshots:
        s_label = s.label.lower()
        if fuzzy:
            if label_lower in s_label or s_label in label_lower:
                results.append(s)
        else:
            if s_label == label_lower:
                results.append(s)
    return results


def build_element_summary(
    snapshots: list[ElementSnapshot],
    max_elements: int = 50,
) -> str:
    """
    Constrói resumo textual dos elementos para prompt do LLM.

    Formato:
    [idx] role: "label" (tag) @ selector
    """
    lines = []
    for i, s in enumerate(snapshots[:max_elements]):
        state_str = ""
        if s.state.get("disabled"):
            state_str += " [DISABLED]"
        if s.state.get("readonly"):
            state_str += " [READONLY]"
        if s.state.get("checked") is True:
            state_str += " [CHECKED]"
        if s.state.get("selected") is True:
            state_str += " [SELECTED]"
        if s.state.get("expanded") is True:
            state_str += " [EXPANDED]"

        label_display = s.label if s.label else f"<{s.tag}>"
        lines.append(f'[{i}] {s.role}: "{label_display}" ({s.tag}) @ {s.selector}{state_str}')

    if len(snapshots) > max_elements:
        lines.append(f"... e mais {len(snapshots) - max_elements} elementos")

    return "\n".join(lines)


def compute_snapshot_diff(
    old: list[ElementSnapshot],
    new: list[ElementSnapshot],
) -> dict[str, list[ElementSnapshot]]:
    """
    Computa diff entre dois snapshots.

    Returns:
        dict com chaves: added, removed, changed, unchanged
    """
    old_by_id = {s.id: s for s in old}
    new_by_id = {s.id: s for s in new}

    added = []
    removed = []
    changed = []
    unchanged = []

    for new_id, new_snap in new_by_id.items():
        if new_id not in old_by_id:
            added.append(new_snap)
        else:
            old_snap = old_by_id[new_id]
            if _snapshot_changed(old_snap, new_snap):
                changed.append(new_snap)
            else:
                unchanged.append(new_snap)

    for old_id, old_snap in old_by_id.items():
        if old_id not in new_by_id:
            removed.append(old_snap)

    return {
        "added": added,
        "removed": removed,
        "changed": changed,
        "unchanged": unchanged,
    }


def _snapshot_changed(old: ElementSnapshot, new: ElementSnapshot) -> bool:
    """Verifica se snapshot mudou significativamente."""
    # Verifica bbox
    if old.bbox != new.bbox:
        return True
    # Verifica label
    if old.label != new.label:
        return True
    # Verifica estado
    if old.state != new.state:
        return True
    # Verifica visibilidade/obstrução
    if old.is_visible != new.is_visible:
        return True
    return old.is_obstructed != new.is_obstructed


def _format_history_line(entry: dict[str, Any], position: int) -> str:
    """Formata um passo do histórico como ``Step N: <ação> -> <alvo>``."""
    step = entry.get("step", position)
    action = entry.get("action", "unknown")
    target = entry.get("target_id", "none")
    return f"Step {step}: {action} -> {target}"


def estimate_prompt_tokens(
    snapshots: list[ElementSnapshot],
    goal: str,
    history: list[dict[str, Any]],
    chars_per_token: float = 3.5,
) -> int:
    """Estima tokens do prompt para controle de contexto."""
    summary = build_element_summary(snapshots)
    history_str = "\n".join(
        f"Step {h.get('step', i)}: {h.get('action', 'unknown')} -> {h.get('target_id', 'none')}"
        for i, h in enumerate(history[-5:])
    )
    total_chars = len(summary) + len(goal) + len(history_str) + 500  # ~500 para system prompt
    return int(total_chars / chars_per_token)


def truncate_snapshots_for_tokens(
    snapshots: list[ElementSnapshot],
    max_tokens: int,
    goal: str,
    history: list[dict[str, Any]],
    chars_per_token: float = 3.5,
) -> list[ElementSnapshot]:
    """Trunca lista de snapshots para caber no orçamento de tokens."""
    # Reserva tokens para goal + history + overhead
    reserved = (
        len(goal)
        + 500
        + sum(
            len(_format_history_line(h, i))
            for i, h in enumerate(history[-5:])
        )
    )
    available_chars = (max_tokens * chars_per_token) - reserved

    if available_chars <= 0:
        return snapshots[:10]  # Mínimo viável

    result = []
    current_chars = 0
    for s in snapshots:
        label = s.label if s.label else s.tag
        line = f"[{len(result)}] {s.role}: \"{label}\" ({s.tag}) @ {s.selector}\n"
        if current_chars + len(line) > available_chars:
            break
        result.append(s)
        current_chars += len(line)

    return result
