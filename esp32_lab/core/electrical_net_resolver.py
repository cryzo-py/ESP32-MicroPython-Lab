"""
Moteur de résolution équipotentielle (ElectricalNetResolver) indépendant de toute interface graphique.

Garantit la séparation stricte :
- Domaine (BreadboardTopology, Hole, ConnectionGroup)
- Simulation (ElectricalNetResolver)
- Présentation (Qt QGraphicsItem)
"""
from typing import Optional, Set, Tuple, Dict, List
from .breadboard_topology import BreadboardTopology

PinRef = Tuple[str, str]  # (component_id, pin_id)


class ElectricalNetResolver:
    """Résolveur déterministe de netlist électrique sans dépendance graphique.
    
    Construit le graphe équipotentiel et résout les équipotentielles (nets) à partir :
    1. Des barrettes de contact internes de la breadboard (ConnectionGroups).
    2. Des broches insérées physiquement dans les trous de la breadboard.
    3. Des cavaliers / fils conducteurs physiques (jumpers).
    4. Des ponts conducteurs internes des composants passifs.
    """

    def __init__(self, topology: Optional[BreadboardTopology] = None) -> None:
        self.topology = topology or BreadboardTopology()
        self.connections: List[Tuple[PinRef, PinRef]] = []
        self.internal_bridges: List[Tuple[PinRef, PinRef]] = []

    def add_connection(self, comp1: str, pin1: str, comp2: str, pin2: str) -> None:
        """Enregistre un fil ou cavalier conducteur entre deux broches/trous."""
        self.connections.append(((comp1, pin1), (comp2, pin2)))

    def add_internal_bridge(self, comp_id: str, pin1: str, pin2: str) -> None:
        """Enregistre une continuité électrique interne au composant (ex: résistance, interrupteur fermé)."""
        self.internal_bridges.append(((comp_id, pin1), (comp_id, pin2)))

    def build_graph(self, breadboard_id: Optional[str] = "breadboard_1") -> Dict[PinRef, Set[PinRef]]:
        """Construit le graphe d'adjacence équipotentiel complet."""
        graph: Dict[PinRef, Set[PinRef]] = {}

        def add_edge(p1: PinRef, p2: PinRef) -> None:
            graph.setdefault(p1, set()).add(p2)
            graph.setdefault(p2, set()).add(p1)

        # 1. Topologie interne de la breadboard (groupes équipotentiels)
        if breadboard_id and self.topology:
            for strip_id, holes in self.topology.strips.items():
                strip_node = (breadboard_id, f"__strip_{strip_id}")
                for h in holes:
                    add_edge((breadboard_id, h), strip_node)

            # Insertions physiques de broches dans les trous
            for hole_id, (c_id, p_id) in self.topology.occupants.items():
                add_edge((c_id, p_id), (breadboard_id, hole_id))

        # 2. Fils et cavaliers physiques
        for p1, p2 in self.connections:
            add_edge(p1, p2)

        # 3. Ponts internes de composants
        for p1, p2 in self.internal_bridges:
            add_edge(p1, p2)

        return graph

    def get_connected_pins(self, start_comp: str, start_pin: str, breadboard_id: Optional[str] = "breadboard_1") -> Set[PinRef]:
        """Effectue un parcours BFS pour déterminer l'ensemble des broches/trous au même potentiel."""
        graph = self.build_graph(breadboard_id)
        start = (start_comp, start_pin)
        if start not in graph:
            return {start}

        visited: Set[PinRef] = set()
        queue: List[PinRef] = [start]
        while queue:
            curr = queue.pop(0)
            if curr not in visited:
                visited.add(curr)
                for neighbor in graph.get(curr, set()):
                    if neighbor not in visited:
                        queue.append(neighbor)
        return visited

    def are_connected(self, c1: str, p1: str, c2: str, p2: str, breadboard_id: Optional[str] = "breadboard_1") -> bool:
        """Indique si deux broches sont reliées au même potentiel."""
        connected = self.get_connected_pins(c1, p1, breadboard_id)
        return (c2, p2) in connected

    def get_all_nets(self, breadboard_id: Optional[str] = "breadboard_1") -> List[Set[PinRef]]:
        """Décompose le circuit en composantes connexes (nets équipotentiels distincts)."""
        graph = self.build_graph(breadboard_id)
        visited: Set[PinRef] = set()
        nets: List[Set[PinRef]] = []

        for node in graph:
            if node not in visited:
                net = set()
                queue = [node]
                while queue:
                    curr = queue.pop(0)
                    if curr not in visited:
                        visited.add(curr)
                        net.add(curr)
                        for neighbor in graph.get(curr, set()):
                            if neighbor not in visited:
                                queue.append(neighbor)
                # Filtrer les nœuds de bande virtuels pour la netlist composant
                clean_net = {p for p in net if not p[1].startswith("__strip_")}
                if clean_net:
                    nets.append(clean_net)

        return nets

    def inspect_pin(self, comp_id: str, pin_id: str, breadboard_id: Optional[str] = "breadboard_1") -> dict:
        """Fournit les métadonnées réelles d'une broche dérivées des structures de données."""
        hole_id = None
        strip_id = None
        connected_holes: List[str] = []

        if comp_id == breadboard_id:
            hole_id = pin_id
        elif self.topology:
            hole_id = self.topology.get_pin_hole(comp_id, pin_id)

        if hole_id and self.topology:
            strip_id = self.topology.get_strip_for_hole(hole_id)
            if strip_id:
                connected_holes = sorted(list(self.topology.get_holes_in_strip(strip_id)))

        nets = self.get_all_nets(breadboard_id)
        target_ref = (comp_id, pin_id)
        net_id = "DISCONNECTED"
        for idx, net in enumerate(nets, 1):
            if target_ref in net or (hole_id and (breadboard_id, hole_id) in net):
                net_id = f"NET_{idx:03d}"
                break

        occupant = None
        if self.topology and hole_id:
            occupant = self.topology.get_occupant(hole_id)

        return {
            "component": comp_id,
            "pin": pin_id,
            "inserted_into": hole_id,
            "strip": strip_id,
            "connected_holes": connected_holes,
            "net_id": net_id,
            "occupant": occupant,
        }

    def explain_path(self, c1: str, p1: str, c2: str, p2: str, breadboard_id: Optional[str] = "breadboard_1") -> List[str]:
        """Explique le chemin physique et électrique continu entre deux broches / bornes.
        
        Effectue une recherche BFS traçant les nœuds physiques parcourus (broches, cavaliers,
        trous d'alvéoles, barrettes internes ConnectionGroup).
        """
        graph = self.build_graph(breadboard_id)
        start = (c1, p1)
        target = (c2, p2)

        if start not in graph or target not in graph:
            return []
        if start == target:
            return [f"{c1}.{p1}"]

        queue: List[Tuple[PinRef, List[PinRef]]] = [(start, [start])]
        visited: Set[PinRef] = {start}

        shortest_path = None
        while queue:
            curr, path = queue.pop(0)
            if curr == target:
                shortest_path = path
                break
            for neighbor in graph.get(curr, set()):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        if not shortest_path:
            return []

        readable_steps: List[str] = []
        for c, p in shortest_path:
            if c == breadboard_id:
                if p.startswith("__strip_"):
                    strip_name = p.replace("__strip_", "")
                    readable_steps.append(f"ConnectionGroup {strip_name}")
                else:
                    readable_steps.append(f"Hole {p}")
            else:
                readable_steps.append(f"{c}.{p}")

        return readable_steps

