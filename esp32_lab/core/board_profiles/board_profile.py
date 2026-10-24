"""
Modèle unifié de profil de carte (BoardProfile) pour ESP32 MicroPython Lab
Permet l'interchangeabilité des cartes (ESP32 DevKit, Arduino Uno, etc.)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any
import json


class BoardPinType(str, Enum):
    DIGITAL_IO = "digital_io"
    INPUT_ONLY = "input_only"
    POWER = "power"
    GROUND = "ground"
    NC = "not_connected"


@dataclass
class PinProfile:
    """Définition d'une broche matérielle d'une carte."""
    number: int
    name: str
    pin_type: BoardPinType = BoardPinType.DIGITAL_IO
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
        return self.pin_type != BoardPinType.INPUT_ONLY

    @property
    def input_only(self) -> bool:
        return self.pin_type == BoardPinType.INPUT_ONLY

    def to_dict(self) -> dict[str, Any]:
        return {
            "number": self.number,
            "name": self.name,
            "pin_type": self.pin_type.value if isinstance(self.pin_type, BoardPinType) else str(self.pin_type),
            "adc_channel": self.adc_channel,
            "pwm_supported": self.pwm_supported,
            "touch_channel": self.touch_channel,
            "default_state": self.default_state,
            "pull_up_down": self.pull_up_down,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PinProfile:
        pin_type_raw = data.get("pin_type", "digital_io")
        try:
            p_type = BoardPinType(pin_type_raw)
        except ValueError:
            p_type = BoardPinType.DIGITAL_IO

        return cls(
            number=data["number"],
            name=data["name"],
            pin_type=p_type,
            adc_channel=data.get("adc_channel"),
            pwm_supported=data.get("pwm_supported", True),
            touch_channel=data.get("touch_channel"),
            default_state=data.get("default_state", 0),
            pull_up_down=data.get("pull_up_down", True),
            description=data.get("description", ""),
        )


@dataclass
class BoardProfile:
    """Spécifications électriques, logiques et fonctionnelles d'une carte microcontrôleur."""
    id: str
    name: str
    mcu: str
    voltage: float = 3.3
    clock_mhz: int = 240
    adc_resolution: int = 4095
    adc_bits: int = 12
    pwm_max_duty: int = 1023
    pwm_frequency_default: int = 1000
    built_in_led: int | None = 2
    digital_pins: list[int] = field(default_factory=list)
    analog_pins: list[int | str] = field(default_factory=list)
    pwm_pins: list[int] = field(default_factory=list)
    supported_languages: list[str] = field(default_factory=lambda: ["micropython", "arduino_c"])
    default_language: str = "micropython"
    component_type: str = "esp32"
    pins: dict[str, PinProfile] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_pin(self, pin_identifier: int | str) -> PinProfile | None:
        """Trouve une broche par son numéro numérique ou son nom/label."""
        if isinstance(pin_identifier, int):
            for p in self.pins.values():
                if p.number == pin_identifier:
                    return p
            # Recherche par clé stringifiée
            p_str = f"GPIO{pin_identifier}"
            if p_str in self.pins:
                return self.pins[p_str]
            return self.pins.get(str(pin_identifier))

        p_str = str(pin_identifier).strip().upper()
        if p_str in self.pins:
            return self.pins[p_str]
        for key, p in self.pins.items():
            if key.upper() == p_str or p.name.upper() == p_str:
                return p
        if p_str.startswith("GPIO") and p_str[4:].isdigit():
            return self.get_pin(int(p_str[4:]))
        if p_str.startswith("D") and p_str[1:].isdigit():
            return self.get_pin(int(p_str[1:]))
        if p_str.isdigit():
            return self.get_pin(int(p_str))
        return None

    def is_valid_pin(self, pin: int) -> bool:
        p = self.get_pin(pin)
        return p is not None and p.pin_type in (BoardPinType.DIGITAL_IO, BoardPinType.INPUT_ONLY)

    def is_input_only(self, pin: int) -> bool:
        p = self.get_pin(pin)
        return p is not None and p.input_only

    def supports_pwm(self, pin: int) -> bool:
        p = self.get_pin(pin)
        return p is not None and p.pwm_supported

    def supports_adc(self, pin: int | str) -> bool:
        p = self.get_pin(pin)
        return p is not None and p.supports_adc

    @property
    def fqbn(self) -> str:
        """FQBN (Fully Qualified Board Name) pour compilation via arduino-cli."""
        if self.metadata and "fqbn" in self.metadata:
            return self.metadata["fqbn"]
        if "uno" in self.id.lower():
            return "arduino:avr:uno"
        return "esp32:esp32:esp32"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "mcu": self.mcu,
            "voltage": self.voltage,
            "clock_mhz": self.clock_mhz,
            "adc_resolution": self.adc_resolution,
            "adc_bits": self.adc_bits,
            "pwm_max_duty": self.pwm_max_duty,
            "pwm_frequency_default": self.pwm_frequency_default,
            "built_in_led": self.built_in_led,
            "digital_pins": self.digital_pins,
            "analog_pins": self.analog_pins,
            "pwm_pins": self.pwm_pins,
            "supported_languages": self.supported_languages,
            "default_language": self.default_language,
            "component_type": self.component_type,
            "pins": {k: v.to_dict() for k, v in self.pins.items()},
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BoardProfile:
        pins_dict = {}
        for k, v in data.get("pins", {}).items():
            pins_dict[k] = PinProfile.from_dict(v)

        return cls(
            id=data["id"],
            name=data["name"],
            mcu=data["mcu"],
            voltage=float(data.get("voltage", 3.3)),
            clock_mhz=int(data.get("clock_mhz", 240)),
            adc_resolution=int(data.get("adc_resolution", 4095)),
            adc_bits=int(data.get("adc_bits", 12)),
            pwm_max_duty=int(data.get("pwm_max_duty", 1023)),
            pwm_frequency_default=int(data.get("pwm_frequency_default", 1000)),
            built_in_led=data.get("built_in_led"),
            digital_pins=data.get("digital_pins", []),
            analog_pins=data.get("analog_pins", []),
            pwm_pins=data.get("pwm_pins", []),
            supported_languages=data.get("supported_languages", ["micropython", "arduino_c"]),
            default_language=data.get("default_language", "micropython"),
            component_type=data.get("component_type", "esp32"),
            pins=pins_dict,
            metadata=data.get("metadata", {}),
        )
