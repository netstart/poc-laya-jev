from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True, slots=True)
class BoundingBox:
    """Retângulo de bounding box com utilitários geométricos."""

    x: float
    y: float
    width: float
    height: float

    @property
    def left(self) -> float:
        return self.x

    @property
    def top(self) -> float:
        return self.y

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height

    @property
    def center_x(self) -> float:
        return self.x + self.width / 2

    @property
    def center_y(self) -> float:
        return self.y + self.height / 2

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def center(self) -> tuple[float, float]:
        return (self.center_x, self.center_y)

    def contains_point(self, x: float, y: float) -> bool:
        return self.x <= x <= self.right and self.y <= y <= self.bottom

    def contains(self, other: Self) -> bool:
        return (
            self.x <= other.x
            and self.y <= other.y
            and self.right >= other.right
            and self.bottom >= other.bottom
        )

    def intersects(self, other: Self) -> bool:
        return not (
            self.right <= other.x
            or other.right <= self.x
            or self.bottom <= other.y
            or other.bottom <= self.y
        )

    def intersection(self, other: Self) -> Self | None:
        if not self.intersects(other):
            return None
        x = max(self.x, other.x)
        y = max(self.y, other.y)
        right = min(self.right, other.right)
        bottom = min(self.bottom, other.bottom)
        return BoundingBox(x=x, y=y, width=right - x, height=bottom - y)

    def union(self, other: Self) -> Self:
        x = min(self.x, other.x)
        y = min(self.y, other.y)
        right = max(self.right, other.right)
        bottom = max(self.bottom, other.bottom)
        return BoundingBox(x=x, y=y, width=right - x, height=bottom - y)

    def iou(self, other: Self) -> float:
        """Intersection over Union."""
        inter = self.intersection(other)
        if inter is None:
            return 0.0
        inter_area = inter.area
        union_area = self.area + other.area - inter_area
        return inter_area / union_area if union_area > 0 else 0.0

    def distance_to(self, other: Self) -> float:
        """Distância euclidiana entre centros."""
        dx = self.center_x - other.center_x
        dy = self.center_y - other.center_y
        return math.hypot(dx, dy)

    def scale(self, factor: float, center: tuple[float, float] | None = None) -> Self:
        if center is None:
            center = self.center
        cx, cy = center
        new_w = self.width * factor
        new_h = self.height * factor
        new_x = cx - new_w / 2
        new_y = cy - new_h / 2
        return BoundingBox(x=new_x, y=new_y, width=new_w, height=new_h)

    def expand(self, padding: float) -> Self:
        return BoundingBox(
            x=self.x - padding,
            y=self.y - padding,
            width=self.width + 2 * padding,
            height=self.height + 2 * padding,
        )

    def clamp(self, viewport: Self) -> Self:
        """Limita o bounding box dentro do viewport."""
        x = max(viewport.x, min(self.x, viewport.right - self.width))
        y = max(viewport.y, min(self.y, viewport.bottom - self.height))
        w = min(self.width, viewport.width)
        h = min(self.height, viewport.height)
        return BoundingBox(x=x, y=y, width=w, height=h)

    def to_dict(self) -> dict[str, float]:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "left": self.left,
            "top": self.top,
            "right": self.right,
            "bottom": self.bottom,
        }

    @classmethod
    def from_dict(cls, data: dict[str, float]) -> Self:
        return cls(
            x=data["x"],
            y=data["y"],
            width=data["width"],
            height=data["height"],
        )

    @classmethod
    def from_dom_rect(cls, rect: dict[str, float]) -> Self:
        """Cria a partir de DOMRect (getBoundingClientRect)."""
        return cls(
            x=rect["x"],
            y=rect["y"],
            width=rect["width"],
            height=rect["height"],
        )


@dataclass(frozen=True, slots=True)
class Viewport:
    """Viewport do navegador.

    ``scroll_x``/``scroll_y`` são apenas informativos (offset de rolagem do
    documento): as caixas dos elementos vêm de ``getBoundingClientRect()``,
    ou seja, são **relativas ao viewport**, por isso :attr:`bbox` sempre tem
    origem ``(0, 0)``.
    """

    width: float
    height: float
    scroll_x: float = 0
    scroll_y: float = 0

    @property
    def bbox(self) -> BoundingBox:
        return BoundingBox(
            x=0.0,
            y=0.0,
            width=self.width,
            height=self.height,
        )

    def is_in_viewport(self, box: BoundingBox, threshold: float = 0.5) -> bool:
        """Verifica se o box está visível no viewport (com threshold de área)."""
        inter = box.intersection(self.bbox)
        if inter is None:
            return False
        return inter.area / box.area >= threshold

    def is_fully_in_viewport(self, box: BoundingBox) -> bool:
        return self.bbox.contains(box)


def compute_element_visibility(
    element_box: BoundingBox,
    viewport: Viewport,
    obstructing_boxes: list[BoundingBox] | None = None,
) -> tuple[bool, float]:
    """
    Calcula visibilidade do elemento.

    Returns:
        (is_visible, visible_ratio)
    """
    # Verifica se está no viewport
    if not viewport.is_in_viewport(element_box):
        return False, 0.0

    visible_area = element_box.area

    # Subtrai área obstruída
    if obstructing_boxes:
        for obs in obstructing_boxes:
            inter = element_box.intersection(obs)
            if inter:
                visible_area -= inter.area

    visible_ratio = max(0.0, visible_area / element_box.area) if element_box.area > 0 else 0.0
    return visible_ratio > 0.5, visible_ratio


def find_obstructing_elements(
    target: BoundingBox,
    candidates: list[BoundingBox],
    z_indices: list[int] | None = None,
) -> list[BoundingBox]:
    """
    Encontra elementos que obstruem o target.

    Args:
        target: Bounding box do elemento alvo
        candidates: Lista de bounding boxes candidatos
        z_indices: z-index opcional para cada candidato (maior = mais acima)

    Returns:
        Lista de bounding boxes que obstruem o target
    """
    obstructing = []

    for i, candidate in enumerate(candidates):
        if candidate is target:
            continue

        # Verifica interseção
        inter = target.intersection(candidate)
        if inter is None or inter.area < 1:
            continue

        # Se tem z-index, só obstrui se estiver acima
        if z_indices and z_indices[i] is not None:
            # Assumimos que target tem z-index 0 se não especificado
            target_z = 0  # seria passado separadamente em uso real
            if z_indices[i] <= target_z:
                continue

        obstructing.append(candidate)

    return obstructing


def get_stable_position(
    element_box: BoundingBox,
    previous_boxes: list[BoundingBox],
    threshold: float = 2.0,
) -> bool:
    """
    Verifica se a posição do elemento está estável (não moveu significativamente).

    Args:
        element_box: Box atual
        previous_boxes: Lista de boxes anteriores (mais recente primeiro)
        threshold: Threshold em pixels para considerar movimento

    Returns:
        True se posição está estável
    """
    if not previous_boxes:
        return True

    last_box = previous_boxes[0]
    distance = element_box.distance_to(last_box)
    return distance <= threshold
