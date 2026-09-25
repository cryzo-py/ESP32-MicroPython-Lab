"""Moteur d'enfichage multi-broches (snap-to-holes) pour la platine d'expérimentation."""
import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF

if TYPE_CHECKING:
    from ...core.breadboard_topology import BreadboardTopology

from .items.pin_item import PinAnchorItem


@dataclass
class PinInfo:
    """Information sur une broche relative au centre du composant."""
    pin_id: str
    rel_x: float  # position X relative au centre du composant
    rel_y: float  # position Y relative au centre du composant


@dataclass 
class SnapResult:
    """Résultat du calcul de placement."""
    local_pos: QPointF       # position locale sur la breadboard pour le composant
    pin_to_hole: dict[str, str]  # mapping {pin_id: hole_id}


@dataclass
class PlacementPreview:
    """Structure formelle de prévisualisation du placement physique (Section 18)."""
    valid: bool
    target_holes: list[str]            # Trous ciblés pour les broches
    invalid_holes: list[str]           # Trous en conflit (occupés, hors grille, espacement incompatible)
    pin_to_hole_map: dict[str, str]    # Mapping {pin_id: hole_id}
    snap_position: QPointF             # Position magnétique suggérée
    rotation: float                    # Angle de rotation du composant
    reason: str | None = None          # Motif en cas d'invalidation


class SnapEngine:
    """Calcule le placement optimal d'un composant sur la breadboard."""

    def __init__(self):
        self.last_collision_hole: str | None = None
        self.last_collision_holes: list[str] = []

    def compute_placement_preview(
        self,
        pins: list[PinInfo],
        drop_local_pos: QPointF,
        topology: 'BreadboardTopology',
        rotation: float = 0.0,
        current_comp_id: str | None = None,
        max_search_radius: float = 28.0
    ) -> PlacementPreview:
        """Calcule la prévisualisation complète (VALID_PREVIEW ou INVALID_PREVIEW) d'un composant."""
        self.last_collision_hole = None
        self.last_collision_holes.clear()

        if not pins:
            return PlacementPreview(
                valid=True,
                target_holes=[],
                invalid_holes=[],
                pin_to_hole_map={},
                snap_position=drop_local_pos,
                rotation=rotation
            )

        anchor_pin = pins[0]
        anchor_target_x = drop_local_pos.x() + anchor_pin.rel_x
        anchor_target_y = drop_local_pos.y() + anchor_pin.rel_y

        candidates = []
        for h_id, hole in topology.holes.items():
            dx = hole.local_x - anchor_target_x
            dy = hole.local_y - anchor_target_y
            dist = math.hypot(dx, dy)
            if dist <= max_search_radius:
                candidates.append((dist, h_id))

        candidates.sort(key=lambda c: c[0])

        if not candidates:
            return PlacementPreview(
                valid=False,
                target_holes=[],
                invalid_holes=[],
                pin_to_hole_map={},
                snap_position=drop_local_pos,
                rotation=rotation,
                reason="OUT_OF_REACH"
            )

        best_anchor_id = candidates[0][1]
        best_pos = topology.get_hole_position(best_anchor_id)
        if not best_pos:
            return PlacementPreview(
                valid=False,
                target_holes=[],
                invalid_holes=[],
                pin_to_hole_map={},
                snap_position=drop_local_pos,
                rotation=rotation,
                reason="HOLE_NOT_FOUND"
            )

        cx = best_pos[0] - anchor_pin.rel_x
        cy = best_pos[1] - anchor_pin.rel_y

        is_valid = True
        target_holes = []
        invalid_holes = []
        pin_to_hole = {}
        reason = None

        for pin in pins:
            px = cx + pin.rel_x
            py = cy + pin.rel_y
            nearest_id = topology.find_nearest_hole(px, py, max_dist=3.0)
            if nearest_id:
                target_holes.append(nearest_id)
                if topology.is_hole_occupied(nearest_id):
                    occ = topology.get_occupant(nearest_id)
                    if occ and occ[0] != current_comp_id:
                        is_valid = False
                        invalid_holes.append(nearest_id)
                        self.last_collision_hole = nearest_id
                        self.last_collision_holes.append(nearest_id)
                        if not reason:
                            reason = f"HOLE_OCCUPIED_{nearest_id}"
                    else:
                        pin_to_hole[pin.pin_id] = nearest_id
                else:
                    pin_to_hole[pin.pin_id] = nearest_id
            else:
                is_valid = False
                wider_id = topology.find_nearest_hole(px, py, max_dist=5.5)
                if wider_id:
                    target_holes.append(wider_id)
                    invalid_holes.append(wider_id)
                else:
                    invalid_holes.append(best_anchor_id)
                if not reason:
                    reason = "INVALID_PIN_SPACING_OR_ORIENTATION"

        if is_valid and len(pin_to_hole) == len(pins):
            # Vérifier qu'aucune paire de broches n'est court-circuitée sur la même bande de connexion
            if len(pins) > 1:
                strips = [topology.get_strip_for_hole(h) for h in pin_to_hole.values() if h]
                if len(strips) != len(set(strips)):
                    is_valid = False
                    reason = "PINS_IN_SAME_STRIP"
                    from collections import Counter
                    strip_counts = Counter(strips)
                    dup_strips = {s for s, count in strip_counts.items() if count > 1}
                    for pin_id, h_id in pin_to_hole.items():
                        if topology.get_strip_for_hole(h_id) in dup_strips:
                            if h_id not in invalid_holes:
                                invalid_holes.append(h_id)

            if is_valid:
                return PlacementPreview(
                    valid=True,
                    target_holes=target_holes,
                    invalid_holes=[],
                    pin_to_hole_map=pin_to_hole,
                    snap_position=QPointF(cx, cy),
                    rotation=rotation,
                    reason=None
                )

        return PlacementPreview(
            valid=False,
            target_holes=target_holes,
            invalid_holes=invalid_holes or target_holes,
            pin_to_hole_map={},
            snap_position=QPointF(cx, cy),
            rotation=rotation,
            reason=reason or "INVALID_PLACEMENT"
        )

    def compute_snap(
        self,
        pins: list[PinInfo],
        drop_local_pos: QPointF,
        topology: 'BreadboardTopology',
        max_search_radius: float = 30.0
    ) -> SnapResult | None:
        """Tente de trouver un placement où toutes les broches s'alignent sur des trous libres."""
        preview = self.compute_placement_preview(pins, drop_local_pos, topology, max_search_radius=max_search_radius)
        if preview.valid and preview.pin_to_hole_map:
            return SnapResult(local_pos=preview.snap_position, pin_to_hole=preview.pin_to_hole_map)
        return None

    def try_snap_at_hole(
        self,
        pins: list[PinInfo],
        anchor_hole_id: str,
        topology: 'BreadboardTopology'
    ) -> SnapResult | None:
        """Tente un placement direct avec la première broche ancrée sur un trou spécifique."""
        self.last_collision_hole = None
        self.last_collision_holes.clear()
        if not pins:
            return None
        return self._try_placement(pins, anchor_hole_id, pins[0], topology)

    def _try_placement(
        self,
        pins: list[PinInfo],
        anchor_hole_id: str,
        anchor_pin: PinInfo,
        topology: 'BreadboardTopology'
    ) -> SnapResult | None:
        """Tente d'aligner toutes les broches à partir d'un trou d'ancrage pour la broche de référence."""
        hole_pos = topology.get_hole_position(anchor_hole_id)
        if not hole_pos:
            return None
            
        hole_x, hole_y = hole_pos
        
        cx = hole_x - anchor_pin.rel_x
        cy = hole_y - anchor_pin.rel_y
        
        pin_to_hole = {}
        
        for pin in pins:
            px = cx + pin.rel_x
            py = cy + pin.rel_y
            
            # Vérifier la présence d'un trou dans la tolérance de 3.0 px
            nearest_id = topology.find_nearest_hole(px, py, max_dist=3.0)
            if not nearest_id:
                return None
                
            # Vérifier l'occupation du trou (collision)
            if topology.is_hole_occupied(nearest_id):
                self.last_collision_hole = nearest_id
                if nearest_id not in self.last_collision_holes:
                    self.last_collision_holes.append(nearest_id)
                return None
                
            pin_to_hole[pin.pin_id] = nearest_id
            
        if len(pins) > 1:
            strips = [topology.get_strip_for_hole(h) for h in pin_to_hole.values() if h]
            if len(strips) != len(set(strips)):
                return None

        return SnapResult(
            local_pos=QPointF(cx, cy),
            pin_to_hole=pin_to_hole
        )


def extract_pins(item, rotation: float | None = None) -> list[PinInfo]:
    """Extrait les PinInfo depuis un composant en appliquant sa rotation physique."""
    pins = []
    rot = rotation if rotation is not None else (item.rotation() if hasattr(item, "rotation") else 0.0)
    rad = math.radians(rot)
    cos_r = math.cos(rad)
    sin_r = math.sin(rad)
    ox, oy = 0.0, 0.0
    if hasattr(item, "transformOriginPoint"):
        origin = item.transformOriginPoint()
        ox, oy = origin.x(), origin.y()
    for child in item.childItems():
        if isinstance(child, PinAnchorItem):
            p = child.pos()
            if abs(rot) > 0.001:
                dx = p.x() - ox
                dy = p.y() - oy
                rx = ox + (dx * cos_r - dy * sin_r)
                ry = oy + (dx * sin_r + dy * cos_r)
            else:
                rx, ry = p.x(), p.y()
            pins.append(PinInfo(
                pin_id=child.pin_id,
                rel_x=round(rx, 4),
                rel_y=round(ry, 4)
            ))
    return pins


