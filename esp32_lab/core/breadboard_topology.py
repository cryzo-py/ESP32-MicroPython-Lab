"""Modèle logique pur de la topologie électrique d'une platine d'expérimentation."""
from dataclasses import dataclass, field
from typing import Optional, Set, Tuple, Dict, List


@dataclass
class ConnectionGroup:
    """Groupe de connexion équipotentiel (bande de contact interne à 5 trous ou rail)."""
    id: str
    group_type: str  # "terminal_strip", "power_rail"
    hole_ids: Set[str] = field(default_factory=set)


@dataclass
class Hole:
    """Modèle d'un trou physique de la breadboard selon les spécifications architecturales.
    
    Attributs :
        id : identifiant unique (ex: 'r10_a', 'rail_l_plus_5')
        row : rangée 1-30
        column : colonne 'a'..'j', 'l+', 'l-', 'r-', 'r+'
        position : coordonnées locales (x, y) en pixels sur la breadboard
        side : 'left', 'right', ou 'rail'
        rail : identifiant du rail d'alimentation ou None
        connection_group_id : ID de la bande équipotentielle
        occupied : booléen d'occupation physique
        occupied_by : tuple (component_id, pin_id) ou None
    """
    id: str
    row: int
    column: str
    position: Tuple[float, float]
    side: str
    rail: Optional[str] = None
    connection_group_id: str = ""
    occupied: bool = False
    occupied_by: Optional[Tuple[str, str]] = None

    # Propriétés de compatibilité ascendante avec l'API existante (HoleInfo)
    @property
    def hole_id(self) -> str:
        return self.id

    @property
    def col(self) -> str:
        return self.column

    @property
    def strip_id(self) -> str:
        return self.connection_group_id

    @property
    def local_x(self) -> float:
        return self.position[0]

    @property
    def local_y(self) -> float:
        return self.position[1]


# Alias rétrocompatible
HoleInfo = Hole


class BreadboardTopology:
    """Topologie électrique d'une platine d'expérimentation MB-102 (400/420 points).
    
    Source de vérité pour toutes les connexions électriques déterminées
    par l'insertion physique des broches dans les trous.
    """

    ROW_START_Y = 28.0
    ROW_STEP_Y = 8.5
    NUM_ROWS = 30

    COL_LEFT_START_X = 46.0
    COL_STEP_X = 8.5
    COLS_LEFT = ["a", "b", "c", "d", "e"]

    COL_RIGHT_START_X = 118.0
    COLS_RIGHT = ["f", "g", "h", "i", "j"]

    RAIL_L_PLUS_X = 12.0
    RAIL_L_MINUS_X = 24.0
    RAIL_R_MINUS_X = 181.0
    RAIL_R_PLUS_X = 193.0

    def __init__(self) -> None:
        self.holes: Dict[str, Hole] = {}
        self.connection_groups: Dict[str, ConnectionGroup] = {}
        self.strips: Dict[str, Set[str]] = {}  # alias vers connection_groups.hole_ids
        self.occupants: Dict[str, Tuple[str, str]] = {}  # hole_id -> (comp_id, pin_id)
        
        self._build_topology()

    def _build_topology(self) -> None:
        """Construit les 420 trous et 64 groupes de connexion de la breadboard."""
        # 1. Rails d'alimentation verticaux (4 groupes)
        rail_groups = {
            "rail_left_plus": ("power_rail", "rail", "left_plus"),
            "rail_left_minus": ("power_rail", "rail", "left_minus"),
            "rail_right_minus": ("power_rail", "rail", "right_minus"),
            "rail_right_plus": ("power_rail", "rail", "right_plus"),
        }

        for r_id, (g_type, _, _) in rail_groups.items():
            cg = ConnectionGroup(id=r_id, group_type=g_type)
            self.connection_groups[r_id] = cg
            self.strips[r_id] = cg.hole_ids

        # 2. Bandes de composants horizontales (30 gauche + 30 droite = 60 groupes)
        for row in range(1, self.NUM_ROWS + 1):
            s_left = f"row_{row}_left"
            cg_l = ConnectionGroup(id=s_left, group_type="terminal_strip")
            self.connection_groups[s_left] = cg_l
            self.strips[s_left] = cg_l.hole_ids

            s_right = f"row_{row}_right"
            cg_r = ConnectionGroup(id=s_right, group_type="terminal_strip")
            self.connection_groups[s_right] = cg_r
            self.strips[s_right] = cg_r.hole_ids

        # 3. Création des trous
        for row in range(1, self.NUM_ROWS + 1):
            y = self.ROW_START_Y + (row - 1) * self.ROW_STEP_Y

            # Bande gauche (colonnes a-e)
            s_left = f"row_{row}_left"
            for i, col in enumerate(self.COLS_LEFT):
                x = self.COL_LEFT_START_X + i * self.COL_STEP_X
                h_id = f"r{row}_{col}"
                hole = Hole(
                    id=h_id,
                    row=row,
                    column=col,
                    position=(x, y),
                    side="left",
                    connection_group_id=s_left,
                )
                self.holes[h_id] = hole
                self.connection_groups[s_left].hole_ids.add(h_id)

            # Bande droite (colonnes f-j)
            s_right = f"row_{row}_right"
            for i, col in enumerate(self.COLS_RIGHT):
                x = self.COL_RIGHT_START_X + i * self.COL_STEP_X
                h_id = f"r{row}_{col}"
                hole = Hole(
                    id=h_id,
                    row=row,
                    column=col,
                    position=(x, y),
                    side="right",
                    connection_group_id=s_right,
                )
                self.holes[h_id] = hole
                self.connection_groups[s_right].hole_ids.add(h_id)

            # Rails d'alimentation (gauche +, gauche -, droite -, droite +)
            rails_info = [
                (f"rail_l_plus_{row}", "l+", self.RAIL_L_PLUS_X, "rail_left_plus"),
                (f"rail_l_minus_{row}", "l-", self.RAIL_L_MINUS_X, "rail_left_minus"),
                (f"rail_r_minus_{row}", "r-", self.RAIL_R_MINUS_X, "rail_right_minus"),
                (f"rail_r_plus_{row}", "r+", self.RAIL_R_PLUS_X, "rail_right_plus"),
            ]
            for h_id, col, rx, r_group in rails_info:
                hole = Hole(
                    id=h_id,
                    row=row,
                    column=col,
                    position=(rx, y),
                    side="rail",
                    rail=r_group,
                    connection_group_id=r_group,
                )
                self.holes[h_id] = hole
                self.connection_groups[r_group].hole_ids.add(h_id)

    def insert_pin(self, comp_id: str, pin_id: str, hole_id: str) -> bool:
        """Insère une broche dans un trou."""
        hole = self.holes.get(hole_id)
        if not hole:
            return False
        if hole.occupied or hole_id in self.occupants:
            return False
        hole.occupied = True
        hole.occupied_by = (comp_id, pin_id)
        self.occupants[hole_id] = (comp_id, pin_id)
        return True

    def remove_component(self, comp_id: str) -> list[str]:
        """Retire toutes les broches d'un composant, retourne les ID des trous libérés."""
        freed = []
        to_remove = []
        for h_id, (c_id, p_id) in self.occupants.items():
            if c_id == comp_id:
                to_remove.append(h_id)
        for h_id in to_remove:
            del self.occupants[h_id]
            hole = self.holes.get(h_id)
            if hole:
                hole.occupied = False
                hole.occupied_by = None
            freed.append(h_id)
        return freed

    def get_strip_for_hole(self, hole_id: str) -> str | None:
        """Retourne l'ID de la piste à laquelle appartient le trou."""
        hole = self.holes.get(hole_id)
        return hole.strip_id if hole else None

    def get_holes_in_strip(self, strip_id: str) -> set[str]:
        """Retourne tous les trous appartenant à une piste."""
        return self.strips.get(strip_id, set()).copy()

    def get_connected_holes(self, hole_id: str) -> set[str]:
        """Retourne tous les trous connectés électriquement (même piste)."""
        strip_id = self.get_strip_for_hole(hole_id)
        if not strip_id:
            return set()
        return self.get_holes_in_strip(strip_id)

    def is_hole_occupied(self, hole_id: str) -> bool:
        """Vérifie si un trou est occupé par une broche."""
        return hole_id in self.occupants

    def get_occupant(self, hole_id: str) -> tuple[str, str] | None:
        """Retourne (comp_id, pin_id) ou None pour un trou."""
        return self.occupants.get(hole_id)

    def get_pin_hole(self, comp_id: str, pin_id: str) -> str | None:
        """Retourne le trou occupé par une broche spécifique."""
        for h_id, (c_id, p_id) in self.occupants.items():
            if c_id == comp_id and p_id == pin_id:
                return h_id
        return None

    def get_component_holes(self, comp_id: str) -> dict[str, str]:
        """Retourne {pin_id: hole_id} pour toutes les broches d'un composant."""
        holes = {}
        for h_id, (c_id, p_id) in self.occupants.items():
            if c_id == comp_id:
                holes[p_id] = h_id
        return holes

    def find_nearest_hole(self, local_x: float, local_y: float, max_dist: float = 18.0) -> str | None:
        """Trouve le trou le plus proche par position X/Y."""
        nearest_id = None
        min_dist_sq = max_dist * max_dist
        
        for h_id, hole in self.holes.items():
            dx = hole.local_x - local_x
            dy = hole.local_y - local_y
            dist_sq = dx*dx + dy*dy
            if dist_sq <= min_dist_sq:
                min_dist_sq = dist_sq
                nearest_id = h_id
                
        return nearest_id

    def get_hole_position(self, hole_id: str) -> tuple[float, float] | None:
        """Retourne (local_x, local_y) d'un trou, ou None."""
        hole = self.holes.get(hole_id)
        if hole:
            return hole.local_x, hole.local_y
        return None

    def clear(self) -> None:
        """Réinitialise toutes les insertions, en gardant la topologie intacte."""
        self.occupants.clear()
        for hole in self.holes.values():
            hole.occupied = False
            hole.occupied_by = None
