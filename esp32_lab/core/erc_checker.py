"""
Moteur de vérification des règles électriques (Electrical Rules Checker - ERC).

Analyse la topologie des connexions et les composants pour détecter :
1. Les courts-circuits directs ou indirects entre rails d'alimentation (VCC/3V3/VIN et GND).
2. Les composants fragiles non protégés (ex: LED branchée directement sur alimentation/GPIO sans résistance série).
3. Les conflits de bus logique (Bus Contention : deux sorties numériques reliées avec états contradictoires).
4. Les broches d'alimentation mal polarisées ou flottantes.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from .electrical_net_resolver import ElectricalNetResolver, PinRef
from .breadboard_topology import BreadboardTopology


class ERCSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ERCViolation:
    id: str
    severity: ERCSeverity
    title: str
    message: str
    component_ids: List[str] = field(default_factory=list)
    pin_refs: List[Tuple[str, str]] = field(default_factory=list)
    recommendation: str = ""


class ElectricalRulesChecker:
    """Analyseur automatique de règles de conception électrique (ERC)."""

    def __init__(self, resolver: Optional[ElectricalNetResolver] = None):
        self.resolver = resolver or ElectricalNetResolver()

    def analyze(
        self,
        components: List[dict],
        connections: List[dict],
        topology: Optional[BreadboardTopology] = None,
        gpio_states: Optional[Dict[int, dict]] = None,
    ) -> List[ERCViolation]:
        """Exécute l'audit complet du circuit et retourne la liste des violations détectées."""
        violations: List[ERCViolation] = []

        # 1. Construire le résolveur de filets (nets)
        resolver = ElectricalNetResolver(topology=topology)
        for conn in connections:
            c1 = conn.get("from_component", "")
            p1 = conn.get("from_pin", "")
            c2 = conn.get("to_component", "")
            p2 = conn.get("to_pin", "")
            if c1 and p1 and c2 and p2:
                resolver.add_connection(c1, p1, c2, p2)

        all_nets = resolver.get_all_nets(breadboard_id="breadboard_1")

        # 2. Vérification n°1 : Courts-circuits Alim / Masse (Power Short-Circuit)
        vcc_keywords = {"3V3", "3.3V", "VCC", "5V", "VIN"}
        gnd_keywords = {"GND", "GND_1", "GND_2", "GROUND"}

        for net_idx, net in enumerate(all_nets, 1):
            power_pins = []
            ground_pins = []

            for comp_id, pin_id in net:
                pid_upper = pin_id.upper()
                if pid_upper in vcc_keywords or any(k in pid_upper for k in ("3V3", "VIN", "VCC")):
                    power_pins.append((comp_id, pin_id))
                elif pid_upper in gnd_keywords or "GND" in pid_upper:
                    ground_pins.append((comp_id, pin_id))

            if power_pins and ground_pins:
                culprit_comps = list({c for c, _ in power_pins + ground_pins})
                violations.append(
                    ERCViolation(
                        id=f"SHORT_CIRCUIT_NET_{net_idx}",
                        severity=ERCSeverity.ERROR,
                        title="Court-circuit d'alimentation franc détecté",
                        message=(
                            f"La ligne d'alimentation ({power_pins[0][1]}) est reliée directement "
                            f"à la masse ({ground_pins[0][1]})."
                        ),
                        component_ids=culprit_comps,
                        pin_refs=power_pins + ground_pins,
                        recommendation="Retirez la liaison directe entre l'alimentation (3V3/VIN) et la masse (GND) pour éviter d'endommager la carte.",
                    )
                )

        # 3. Vérification n°2 : Protection des Diodes LED (Résistance de limitation manquante)
        led_components = [c for c in components if str(c.get("type", "")).lower() in ("led",)]
        resistor_components = [c for c in components if str(c.get("type", "")).lower() in ("resistor", "resistance")]

        # Construire l'ensemble des nets qui touchent au moins une borne de résistance
        resistor_touched_nets = set()
        for r in resistor_components:
            r_id = r.get("id")
            for net_idx, net in enumerate(all_nets):
                if any(c == r_id for c, _ in net):
                    resistor_touched_nets.add(net_idx)

        for led in led_components:
            led_id = led.get("id")
            anode_net_idx = None
            cathode_net_idx = None

            for idx, net in enumerate(all_nets):
                if (led_id, "anode") in net:
                    anode_net_idx = idx
                if (led_id, "cathode") in net:
                    cathode_net_idx = idx

            # Si la LED est branchée des deux côtés
            if anode_net_idx is not None and cathode_net_idx is not None:
                # Vérifier si l'un des deux nets de la LED passe par une résistance
                has_series_resistor = (
                    anode_net_idx in resistor_touched_nets or cathode_net_idx in resistor_touched_nets
                )

                anode_net = all_nets[anode_net_idx]
                cathode_net = all_nets[cathode_net_idx]

                has_source = any(
                    (p.upper() in vcc_keywords or p.startswith("GPIO") or p.isdigit())
                    for _, p in anode_net
                )
                has_ground = any(
                    (p.upper() in gnd_keywords or "GND" in p.upper())
                    for _, p in cathode_net
                )

                if has_source and has_ground and not has_series_resistor:
                    violations.append(
                        ERCViolation(
                            id=f"LED_NO_RESISTOR_{led_id}",
                            severity=ERCSeverity.WARNING,
                            title="LED sans résistance de limitation",
                            message=(
                                f"La LED '{led_id}' est raccordée sans résistance série de limitation. "
                                "En pratique, un courant excessif détruirait la LED et la sortie de l'ESP32."
                            ),
                            component_ids=[led_id],
                            pin_refs=[(led_id, "anode"), (led_id, "cathode")],
                            recommendation="Insérez une résistance de 220 Ω à 1 kΩ en série avec l'anode ou la cathode de la LED.",
                        )
                    )

        # 4. Vérification n°3 : Conflits de broches de sortie (Bus Contention / Output Collision)
        if gpio_states:
            for net_idx, net in enumerate(all_nets, 1):
                driven_outputs = []
                for comp_id, pin_id in net:
                    if comp_id == "esp32" and pin_id.startswith("GPIO"):
                        try:
                            g_num = int(pin_id.replace("GPIO", ""))
                            st = gpio_states.get(g_num)
                            if st and st.get("mode") == "OUT":
                                driven_outputs.append((pin_id, st.get("value", 0)))
                        except Exception:
                            pass

                if len(driven_outputs) > 1:
                    values = {v for _, v in driven_outputs}
                    if len(values) > 1:
                        pin_names = [p for p, _ in driven_outputs]
                        violations.append(
                            ERCViolation(
                                id=f"OUTPUT_COLLISION_NET_{net_idx}",
                                severity=ERCSeverity.ERROR,
                                title="Conflit de sortie logique (Collision de bus)",
                                message=(
                                    f"Les broches de sortie {', '.join(pin_names)} sont interconnectées "
                                    "avec des états logiques opposés (HIGH et LOW simultanés)."
                                ),
                                recommendation="Évitez de relier directement deux sorties numériques configurées en mode OUTPUT sans résistance de tirage.",
                            )
                        )

        # 5. Vérification n°4 : GPIO Input-Only utilisés pour piloter (ex: LED)
        from .models.board import create_default_esp32_wroom, PinType
        board = create_default_esp32_wroom()
        
        for net_idx, net in enumerate(all_nets, 1):
            input_only_pins = []
            driven_components = []
            
            for comp_id, pin_id in net:
                if comp_id == "esp32" and pin_id.startswith("GPIO"):
                    try:
                        g_num = int(pin_id.replace("GPIO", ""))
                        pin_def = board.get_pin(g_num)
                        if pin_def and pin_def.pin_type == PinType.INPUT_ONLY:
                            input_only_pins.append((comp_id, pin_id))
                    except Exception:
                        pass
                elif "led" in comp_id.lower() or "buzzer" in comp_id.lower() or "relay" in comp_id.lower():
                    driven_components.append((comp_id, pin_id))
                    
            if input_only_pins and driven_components:
                # Si le net n'a pas d'autre source d'alimentation ou de GPIO normal, c'est une erreur probable
                has_other_source = any(
                    (p.upper() in vcc_keywords or (c == "esp32" and p.startswith("GPIO") and (c, p) not in input_only_pins))
                    for c, p in net
                )
                if not has_other_source:
                    violations.append(
                        ERCViolation(
                            id=f"INPUT_ONLY_DRIVE_NET_{net_idx}",
                            severity=ERCSeverity.ERROR,
                            title="Utilisation d'une broche Input-Only comme sortie",
                            message=(
                                f"La broche {input_only_pins[0][1]} est de type 'Input Only' (entrée seule) "
                                f"mais semble être utilisée pour piloter le composant '{driven_components[0][0]}'."
                            ),
                            component_ids=[c for c, _ in input_only_pins + driven_components],
                            pin_refs=input_only_pins,
                            recommendation="Les broches 34, 35, 36, 39 de l'ESP32 ne peuvent pas fournir de courant (pas de mode OUT). Utilisez une autre broche GPIO (ex: GPIO2, GPIO4).",
                        )
                    )

        return violations
