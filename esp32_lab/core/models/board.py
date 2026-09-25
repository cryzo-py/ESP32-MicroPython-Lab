"""
Modèles pour les cartes cibles (ESP32) et leurs broches (Pins)
"""

from dataclasses import dataclass, field
from enum import Enum


class PinType(Enum):
    DIGITAL_IO = "digital_io"
    INPUT_ONLY = "input_only"
    POWER = "power"
    GROUND = "ground"
    NC = "not_connected"


@dataclass
class PinDefinition:
    number: int
    name: str
    pin_type: PinType = PinType.DIGITAL_IO
    adc_channel: int | None = None
    pwm_supported: bool = True
    touch_channel: int | None = None
    default_state: int = 0
    pull_up_down: bool = True
    description: str = ""

    @property
    def supports_adc(self) -> bool:
        return self.adc_channel is not None
        
    @property
    def supports_output(self) -> bool:
        return self.pin_type != PinType.INPUT_ONLY
        
    @property
    def input_only(self) -> bool:
        return self.pin_type == PinType.INPUT_ONLY

    @property
    def supports_i2c(self) -> bool:
        # I2C requires open-drain output, so INPUT_ONLY pins cannot be used
        return self.pin_type == PinType.DIGITAL_IO


@dataclass
class PhysicalHeaderPin:
    """Modélisation physique d'une broche d'en-tête de carte ESP32."""
    pin_id: str             # Identifiant universel : "GPIO2", "3V3", "GND_1", "VIN", etc.
    label: str              # Marquage sérigraphié sur le PCB : "2", "3V3", "GND", etc.
    gpio_num: int | None    # Numéro logique GPIO (ex: 2 pour GPIO2, None pour alimentation)
    rel_x: float            # Décalage physique X par rapport au centre de la carte (px)
    rel_y: float            # Décalage physique Y par rapport au centre de la carte (px)
    role: str               # "gpio", "power", "ground", "control"
    pin_length: float = 16.0
    pin_thickness: float = 1.6
    description: str = ""


@dataclass
class ESP32DevKitProfile:
    """Profil physique et électrique normalisé pour carte ESP32 DevKit V1 (30 broches)."""
    id: str = "esp32_devkit_v1"
    name: str = "ESP32 DevKit V1"
    model: str = "ESP-WROOM-32"
    width: float = 110.0
    height: float = 180.0
    header_span_x: float = 89.0  # Espacement 0.9" entre rangées (colonne b à colonne i sur breadboard)
    pin_step_y: float = 8.5      # Pas normalisé 2.54 mm (8.5 px)
    pins: dict[str, PhysicalHeaderPin] = field(default_factory=dict)

    def get_pin_by_gpio(self, gpio_num: int) -> PhysicalHeaderPin | None:
        """Trouve la broche physique correspondant à un numéro GPIO."""
        for p in self.pins.values():
            if p.gpio_num == gpio_num:
                return p
        return None

    def get_pin(self, pin_id_or_num: str | int) -> PhysicalHeaderPin | None:
        """Recherche par nom de broche (ex: 'GPIO2', 'IO2') ou numéro d'E/S (2)."""
        if isinstance(pin_id_or_num, int):
            return self.get_pin_by_gpio(pin_id_or_num)
        p_str = str(pin_id_or_num).upper().strip()
        if p_str in self.pins:
            return self.pins[p_str]
        # Tolérance '2' ou 'IO2' -> 'GPIO2'
        if p_str.startswith("IO") and p_str[2:].isdigit():
            return self.get_pin_by_gpio(int(p_str[2:]))
        if p_str.isdigit():
            return self.get_pin_by_gpio(int(p_str))
        return None


def create_esp32_devkit_profile() -> ESP32DevKitProfile:
    """Instancie le profil géométrique et physique standard de l'ESP32 DevKit V1."""
    profile = ESP32DevKitProfile()
    left_x = -profile.header_span_x / 2.0   # -44.5 px (colonne b sur platine)
    right_x = profile.header_span_x / 2.0   # +44.5 px (colonne i sur platine)

    # 15 broches à gauche (du haut vers le bas)
    left_defs = [
        ("EN", "EN", None, "control", "Ligne Reset / Enable active bas"),
        ("GPIO36", "VP", 36, "gpio", "Entrée ADC1_CH0 (Input only)"),
        ("GPIO39", "VN", 39, "gpio", "Entrée ADC1_CH3 (Input only)"),
        ("GPIO34", "34", 34, "gpio", "Entrée ADC1_CH6 (Input only)"),
        ("GPIO35", "35", 35, "gpio", "Entrée ADC1_CH7 (Input only)"),
        ("GPIO32", "32", 32, "gpio", "GPIO32 / ADC1_CH4 / Touch 9"),
        ("GPIO33", "33", 33, "gpio", "GPIO33 / ADC1_CH5 / Touch 8"),
        ("GPIO25", "25", 25, "gpio", "GPIO25 / DAC1 / ADC2_CH8"),
        ("GPIO26", "26", 26, "gpio", "GPIO26 / DAC2 / ADC2_CH9"),
        ("GPIO27", "27", 27, "gpio", "GPIO27 / ADC2_CH7 / Touch 7"),
        ("GPIO14", "14", 14, "gpio", "GPIO14 / HSPI_CLK / Touch 6"),
        ("GPIO12", "12", 12, "gpio", "GPIO12 / HSPI_Q / Touch 5"),
        ("GPIO13", "13", 13, "gpio", "GPIO13 / HSPI_D / Touch 4"),
        ("GND_1", "GND", None, "ground", "Masse système"),
        ("VIN", "VIN", None, "power", "Entrée alimentation externe 5V"),
    ]

    # 15 broches à droite (du haut vers le bas)
    right_defs = [
        ("3V3", "3V3", None, "power", "Sortie régulée 3.3V"),
        ("GND_2", "GND", None, "ground", "Masse système"),
        ("GPIO15", "15", 15, "gpio", "GPIO15 / HSPI_CS / Touch 3"),
        ("GPIO2", "2", 2, "gpio", "GPIO2 / LED intégrée / Touch 2"),
        ("GPIO4", "4", 4, "gpio", "GPIO4 / ADC2_CH0 / Touch 0"),
        ("GPIO16", "16", 16, "gpio", "GPIO16 / UART2 RX"),
        ("GPIO17", "17", 17, "gpio", "GPIO17 / UART2 TX"),
        ("GPIO5", "5", 5, "gpio", "GPIO5 / VSPI_CS"),
        ("GPIO18", "18", 18, "gpio", "GPIO18 / VSPI_CLK"),
        ("GPIO19", "19", 19, "gpio", "GPIO19 / VSPI_MISO"),
        ("GPIO21", "21", 21, "gpio", "GPIO21 / I2C_SDA"),
        ("GPIO3", "RX0", 3, "gpio", "GPIO3 / UART0 RX"),
        ("GPIO1", "TX0", 1, "gpio", "GPIO1 / UART0 TX"),
        ("GPIO22", "22", 22, "gpio", "GPIO22 / I2C_SCL"),
        ("GPIO23", "23", 23, "gpio", "GPIO23 / VSPI_MOSI"),
    ]

    start_y = -59.5 # 14 intervalles de 8.5px centrés sur 0 (-59.5 à +59.5)
    for i, (pid, lbl, gnum, role, desc) in enumerate(left_defs):
        py = start_y + i * profile.pin_step_y
        profile.pins[pid] = PhysicalHeaderPin(pid, lbl, gnum, left_x, py, role, description=desc)

    for i, (pid, lbl, gnum, role, desc) in enumerate(right_defs):
        py = start_y + i * profile.pin_step_y
        profile.pins[pid] = PhysicalHeaderPin(pid, lbl, gnum, right_x, py, role, description=desc)

    return profile


@dataclass
class BoardDefinition:
    id: str
    name: str
    model: str
    pins: dict[str, PinDefinition] = field(default_factory=dict)
    flash_size_mb: int = 4
    has_wifi: bool = True
    has_bluetooth: bool = True

    def get_pin(self, pin_name_or_num: str | int) -> PinDefinition | None:
        if isinstance(pin_name_or_num, int):
            for pin in self.pins.values():
                if pin.number == pin_name_or_num:
                    return pin
            return None
        return self.pins.get(str(pin_name_or_num))



def create_default_esp32_wroom() -> BoardDefinition:
    """Crée la définition de la carte ESP32 DevKit V1 (ESP-WROOM-32 30/38 pins)"""
    pins = {
        # Pins d'alimentation
        "3V3": PinDefinition(-1, "3V3", PinType.POWER, description="Alimentation régulée 3.3V"),
        "GND_1": PinDefinition(-1, "GND", PinType.GROUND, description="Masse"),
        "GND_2": PinDefinition(-1, "GND", PinType.GROUND, description="Masse"),
        "GND_3": PinDefinition(-1, "GND", PinType.GROUND, description="Masse"),
        "VIN": PinDefinition(-1, "VIN", PinType.POWER, description="Entrée alimentation 5V externe"),
        
        # GPIOs avec support standard
        "GPIO0": PinDefinition(0, "GPIO0", PinType.DIGITAL_IO, adc_channel=11, pwm_supported=True),
        "GPIO1": PinDefinition(1, "TX0", PinType.DIGITAL_IO, description="UART0 TX"),
        "GPIO2": PinDefinition(2, "GPIO2", PinType.DIGITAL_IO, adc_channel=12, pwm_supported=True, description="LED intégrée sur beaucoup de cartes"),
        "GPIO3": PinDefinition(3, "RX0", PinType.DIGITAL_IO, description="UART0 RX"),
        "GPIO4": PinDefinition(4, "GPIO4", PinType.DIGITAL_IO, adc_channel=10, pwm_supported=True),
        "GPIO5": PinDefinition(5, "GPIO5", PinType.DIGITAL_IO, pwm_supported=True),
        
        # Broches SPI bus 1
        "GPIO12": PinDefinition(12, "GPIO12", PinType.DIGITAL_IO, adc_channel=15, pwm_supported=True),
        "GPIO13": PinDefinition(13, "GPIO13", PinType.DIGITAL_IO, adc_channel=14, pwm_supported=True),
        "GPIO14": PinDefinition(14, "GPIO14", PinType.DIGITAL_IO, adc_channel=16, pwm_supported=True),
        "GPIO15": PinDefinition(15, "GPIO15", PinType.DIGITAL_IO, adc_channel=13, pwm_supported=True),
        "GPIO16": PinDefinition(16, "GPIO16", PinType.DIGITAL_IO, pwm_supported=True),
        "GPIO17": PinDefinition(17, "GPIO17", PinType.DIGITAL_IO, pwm_supported=True),
        "GPIO18": PinDefinition(18, "GPIO18", PinType.DIGITAL_IO, pwm_supported=True, description="VSPI SCK"),
        "GPIO19": PinDefinition(19, "GPIO19", PinType.DIGITAL_IO, pwm_supported=True, description="VSPI MISO"),
        "GPIO21": PinDefinition(21, "GPIO21", PinType.DIGITAL_IO, pwm_supported=True, description="I2C SDA"),
        "GPIO22": PinDefinition(22, "GPIO22", PinType.DIGITAL_IO, pwm_supported=True, description="I2C SCL"),
        "GPIO23": PinDefinition(23, "GPIO23", PinType.DIGITAL_IO, pwm_supported=True, description="VSPI MOSI"),
        "GPIO25": PinDefinition(25, "GPIO25", PinType.DIGITAL_IO, adc_channel=18, pwm_supported=True),
        "GPIO26": PinDefinition(26, "GPIO26", PinType.DIGITAL_IO, adc_channel=19, pwm_supported=True),
        "GPIO27": PinDefinition(27, "GPIO27", PinType.DIGITAL_IO, adc_channel=17, pwm_supported=True),
        "GPIO32": PinDefinition(32, "GPIO32", PinType.DIGITAL_IO, adc_channel=4, pwm_supported=True),
        "GPIO33": PinDefinition(33, "GPIO33", PinType.DIGITAL_IO, adc_channel=5, pwm_supported=True),
        
        # Entrées analogiques strictes (Input only, pas de pull-up interne)
        "GPIO34": PinDefinition(34, "GPIO34", PinType.INPUT_ONLY, adc_channel=6, pwm_supported=False, pull_up_down=False),
        "GPIO35": PinDefinition(35, "GPIO35", PinType.INPUT_ONLY, adc_channel=7, pwm_supported=False, pull_up_down=False),
        "GPIO36": PinDefinition(36, "VN", PinType.INPUT_ONLY, adc_channel=0, pwm_supported=False, pull_up_down=False),
        "GPIO39": PinDefinition(39, "VP", PinType.INPUT_ONLY, adc_channel=3, pwm_supported=False, pull_up_down=False),
    }
    
    return BoardDefinition(
        id="esp32_wroom_32",
        name="ESP32 DevKit V1",
        model="ESP-WROOM-32",
        pins=pins,
        flash_size_mb=4,
        has_wifi=True,
        has_bluetooth=True,
    )
