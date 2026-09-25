"""
Module 'machine' simulé pour l'environnement MicroPython
Fournit machine.Pin, machine.PWM, machine.ADC
"""

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..gpio import GPIOManager


class Pin:
    IN = 1
    OUT = 3
    OPEN_DRAIN = 7
    PULL_UP = 1
    PULL_DOWN = 2

    # IRQ trigger constants (MicroPython-compatible)
    IRQ_RISING   = 1
    IRQ_FALLING  = 2
    IRQ_ANY_EDGE = 3   # RISING | FALLING convenience alias

    _gpio_manager: "GPIOManager | None" = None
    # Injected by SimulationEngine; points to the InterruptController instance.
    _irq_controller = None

    @classmethod
    def set_gpio_manager(cls, manager: "GPIOManager"):
        cls._gpio_manager = manager

    # Broches GPIO matérielles valides sur ESP-WROOM-32 DevKit V1
    VALID_GPIOS = {
        0, 1, 2, 3, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33, 34, 35, 36, 39
    }
    # Broches 6 à 11 réservées à la mémoire SPI Flash interne
    FLASH_GPIOS = {6, 7, 8, 9, 10, 11}
    # Broches d'entrée uniquement (pas de pull-up interne, pas de sortie)
    INPUT_ONLY_GPIOS = {34, 35, 36, 39}

    def __init__(self, id: int, mode: int = -1, pull: int = -1, value: int | None = None):
        self.id = int(id)
        # Validation is now delegated entirely to GPIOManager.configure
        # which uses the central board profile.
        
        self.mode = mode
        self.pull = pull
        
        if self._gpio_manager:
            if mode != -1:
                self._gpio_manager.configure(self.id, mode, pull if pull != -1 else 0)
            if value is not None:
                self._gpio_manager.write(self.id, value)

    def value(self, val: int | None = None) -> int | None:
        if self._gpio_manager is None:
            return 0
            
        if val is None:
            return self._gpio_manager.read(self.id)
        else:
            self._gpio_manager.write(self.id, val)
            return None

    def on(self):
        self.value(1)

    def off(self):
        self.value(0)

    def irq(self, handler=None, trigger=None, *, wake=None):
        """
        Register (or deregister) a GPIO interrupt handler.

        MicroPython-compatible API:
            pin.irq(trigger=Pin.IRQ_FALLING, handler=my_callback)
            pin.irq(handler=None)   # disable

        The handler receives the Pin object as its sole argument:
            def callback(pin): ...

        Callbacks are dispatched inside the MicroPython sandbox thread,
        NOT in the Qt GUI thread.  They execute between logical lines of
        user code via the sys.settrace hook in SimulationWorker.
        """
        if trigger is None:
            trigger = Pin.IRQ_RISING | Pin.IRQ_FALLING

        ctrl = Pin._irq_controller
        if ctrl is None:
            # IRQ controller not yet attached (test or detached mode) — ignore silently.
            return
        ctrl.register_irq(self.id, trigger, handler, self)

    @property
    def pin_num(self) -> int:
        return self.id

    def __int__(self) -> int:
        return self.id

    def __repr__(self):
        return f"Pin({self.id}, mode={self.mode})"


class PWM:
    _pwm_manager = None

    @classmethod
    def set_pwm_manager(cls, manager):
        cls._pwm_manager = manager

    def __init__(self, pin: Pin, freq: int = 1000, duty: int = 0):
        self.pin = pin
        if self._pwm_manager:
            self._pwm_manager.set_frequency(self.pin.id, freq)
            self._pwm_manager.set_duty(self.pin.id, duty)
        else:
            self._freq = freq
            self._duty = duty

    def freq(self, f: int | None = None) -> int | None:
        if f is None:
            return self._pwm_manager.get_frequency(self.pin.id) if self._pwm_manager else getattr(self, '_freq', 1000)
        if self._pwm_manager:
            self._pwm_manager.set_frequency(self.pin.id, f)
        else:
            self._freq = f
        return None

    def duty(self, d: int | None = None) -> int | None:
        if d is None:
            return self._pwm_manager.get_duty(self.pin.id) if self._pwm_manager else getattr(self, '_duty', 0)
        if self._pwm_manager:
            self._pwm_manager.set_duty(self.pin.id, d)
        else:
            self._duty = d
        return None

    def duty_u16(self, d: int | None = None) -> int | None:
        if d is None:
            val = self._pwm_manager.get_duty(self.pin.id) if self._pwm_manager else getattr(self, '_duty', 0)
            return int(val * 65535 / 1023)
        if self._pwm_manager:
            self._pwm_manager.set_duty(self.pin.id, int(d * 1023 / 65535))
        else:
            self._duty = int(d * 1023 / 65535)
        return None

    def deinit(self):
        if self._pwm_manager:
            self._pwm_manager.deinit(self.pin.id)


class ADC:
    ATTN_6DB = 2
    ATTN_11DB = 3
    WIDTH_12BIT = 3
    
    _adc_manager = None

    @classmethod
    def set_adc_manager(cls, manager):
        cls._adc_manager = manager

    def __init__(self, pin: Pin):
        self.pin = pin
        self._atten = self.ATTN_11DB
        self._width = self.WIDTH_12BIT
        if self._adc_manager:
            self._adc_manager.configure(self.pin.id)

    def read(self) -> int:
        if self._adc_manager:
            return self._adc_manager.read(self.pin.id)
        return 0

    def read_u16(self) -> int:
        if self._adc_manager:
            return self._adc_manager.read_u16(self.pin.id)
        return 0

    def atten(self, att: int):
        self._atten = att

    def width(self, w: int):
        self._width = w


class I2C:
    """Bus I2C virtuel relié au gestionnaire backend de la topologie"""
    _i2c_manager = None

    @classmethod
    def set_i2c_manager(cls, manager):
        cls._i2c_manager = manager

    def __init__(self, id_or_scl=None, scl=None, sda=None, freq=400000):
        # MicroPython API: I2C(id, scl=Pin, sda=Pin, freq=400000)
        self.id = 0
        
        # Determine actual SCL
        if scl is not None:
            self.scl = scl
            if isinstance(id_or_scl, int):
                self.id = id_or_scl
        elif id_or_scl is not None:
            if isinstance(id_or_scl, int):
                self.id = id_or_scl
            else:
                self.scl = id_or_scl
        else:
            raise ValueError("I2C missing SCL pin")
            
        self.sda = sda
        self.freq = freq
        
        # Validation
        if not hasattr(self.scl, 'id') or not hasattr(self.sda, 'id'):
            raise ValueError("I2C pins must be Pin objects")
            
        if self._i2c_manager:
            self._i2c_manager.configure_bus(self.id, self.scl.id, self.sda.id, self.freq)

    def scan(self) -> list[int]:
        if self._i2c_manager:
            return self._i2c_manager.scan(self.id)
        return []

    def writeto(self, addr: int, buf: bytes | bytearray, stop: bool = True) -> int:
        if self._i2c_manager:
            return self._i2c_manager.writeto(self.id, addr, buf)
        return len(buf)

    def readfrom(self, addr: int, nbytes: int, stop: bool = True) -> bytes:
        if self._i2c_manager:
            return self._i2c_manager.readfrom(self.id, addr, nbytes)
        return bytes([0] * nbytes)

    def writeto_mem(self, addr: int, memaddr: int, buf: bytes | bytearray):
        if self._i2c_manager:
            self._i2c_manager.writeto_mem(self.id, addr, memaddr, buf)

    def readfrom_mem(self, addr: int, memaddr: int, nbytes: int) -> bytes:
        if self._i2c_manager:
            return self._i2c_manager.readfrom_mem(self.id, addr, memaddr, nbytes)
        return bytes([0] * nbytes)

    @classmethod
    def register_device(cls, address, device):
        pass

    @classmethod
    def unregister_device(cls, address):
        pass



def time_pulse_us(pin, pulse_level: int, timeout_us: int = 1000000) -> int:
    """
    Mesure la durée d'une impulsion sur une broche en microsecondes (MicroPython machine.time_pulse_us).
    Dans le simulateur, si un capteur ultrason HC-SR04 est présent, convertit la distance courante en durée d'écho.
    """
    try:
        from .hcsr04 import _hcsr04_distances
        pin_id = pin.id if hasattr(pin, "id") else int(pin)
        # Recherche si la broche est déclarée comme echo_pin
        for (trig, echo), dist in _hcsr04_distances.items():
            if echo == pin_id:
                # Durée (us) = (distance_cm * 2) / 0.0343
                return int((dist * 2.0) / 0.0343)
        # Si une distance par défaut existe
        return int((25.0 * 2.0) / 0.0343)
    except Exception:
        return 1457 # Correspond à ~25 cm

class SPI:
    """Bus SPI virtuel relie au gestionnaire backend de la topologie"""
    _spi_manager = None
    
    MSB = 0
    LSB = 1

    @classmethod
    def set_spi_manager(cls, manager):
        cls._spi_manager = manager
        
    def __init__(self, id, baudrate=1000000, polarity=0, phase=0, bits=8, firstbit=0, sck=None, mosi=None, miso=None):
        self.id = id
        self.baudrate = baudrate
        self.polarity = polarity
        self.phase = phase
        self.bits = bits
        self.firstbit = firstbit
        
        sck_id = sck.id if hasattr(sck, 'id') else sck
        mosi_id = mosi.id if hasattr(mosi, 'id') else mosi
        miso_id = miso.id if hasattr(miso, 'id') else miso
        
        self.sck = sck_id
        self.mosi = mosi_id
        self.miso = miso_id
        
        if self._spi_manager:
            self._spi_manager.init_bus(self.id, self.sck, self.mosi, self.miso, 
                                     freq=self.baudrate, polarity=self.polarity, 
                                     phase=self.phase, firstbit=self.firstbit)
                                     
    def deinit(self):
        if self._spi_manager:
            self._spi_manager.deinit_bus(self.id)
            
    def write(self, buf):
        if self._spi_manager:
            self._spi_manager.transfer(self.id, bytes(buf))
            
    def read(self, nbytes, write=0x00):
        if self._spi_manager:
            tx_data = bytes([write] * nbytes)
            return self._spi_manager.transfer(self.id, tx_data)
        return bytes([0xFF] * nbytes)
        
    def readinto(self, buf, write=0x00):
        if self._spi_manager:
            tx_data = bytes([write] * len(buf))
            rx = self._spi_manager.transfer(self.id, tx_data)
            for i in range(min(len(buf), len(rx))):
                buf[i] = rx[i]
                
    def write_readinto(self, write_buf, read_buf):
        if self._spi_manager:
            rx = self._spi_manager.transfer(self.id, bytes(write_buf))
            for i in range(min(len(read_buf), len(rx))):\
                read_buf[i] = rx[i]


class Timer:
    """
    MicroPython-compatible machine.Timer for ESP32 Lab simulator.

    Usage:
        from machine import Timer

        def tick(timer):
            print("tick")

        tim = Timer(0)
        tim.init(period=500, mode=Timer.PERIODIC, callback=tick)
        # ... later ...
        tim.deinit()

    Callbacks execute inside the MicroPython sandbox thread via the
    shared RuntimeCallbackQueue (same mechanism as GPIO IRQ).
    Never executed in the Qt GUI thread.
    """

    ONE_SHOT = 0
    PERIODIC  = 1

    # Injected by SimulationEngine; points to the TimerManager instance.
    _timer_manager = None

    def __init__(self, id: int):
        from ..timers import MIN_TIMER_ID, MAX_TIMER_ID
        if not (MIN_TIMER_ID <= int(id) <= MAX_TIMER_ID):
            raise ValueError(
                f"Timer ID {id} invalide. "
                f"Valeurs acceptées: {MIN_TIMER_ID}..{MAX_TIMER_ID}"
            )
        self._id = int(id)
        self._active = False

    def init(self, *, period: int, mode: int = PERIODIC, callback=None):
        """
        Configure and start the timer.

        :param period:   Period in milliseconds (≥ 1).
        :param mode:     Timer.ONE_SHOT or Timer.PERIODIC.
        :param callback: callable(timer) — receives this Timer object.
        """
        mgr = Timer._timer_manager
        if mgr is None:
            # No manager attached (e.g. detached test mode) — ignore silently.
            return
        mgr.register(self._id, period, mode, callback, self)
        self._active = True

    def deinit(self):
        """Stop and deactivate the timer."""
        mgr = Timer._timer_manager
        if mgr is not None:
            mgr.unregister(self._id)
        self._active = False

    @property
    def id(self) -> int:
        return self._id

    def __repr__(self) -> str:
        return f"Timer({self._id}, active={self._active})"


class UART:
    """
    MicroPython-compatible machine.UART for ESP32 Lab simulator.
    """
    _uart_manager = None

    def __init__(self, id: int, baudrate: int = 115200, **kwargs):
        self._id = id
        if self._uart_manager is None:
            return
            
        if kwargs:
            self.init(baudrate=baudrate, **kwargs)

    def init(self, baudrate=115200, bits=8, parity=None, stop=1, *, timeout=0, timeout_char=0, tx=None, rx=None):
        if self._uart_manager is None:
            return
            
        # tx and rx can be Pin objects or ints. Convert to ints.
        tx_pin = tx.id if hasattr(tx, 'id') else tx
        rx_pin = rx.id if hasattr(rx, 'id') else rx
        
        if tx_pin is None or rx_pin is None:
            raise ValueError("tx and rx pins must be provided for UART initialization")
            
        self._uart_manager.init_uart(self._id, baudrate, bits, parity, stop, timeout, timeout_char, tx_pin, rx_pin)

    def deinit(self):
        if self._uart_manager:
            self._uart_manager.deinit_uart(self._id)

    def any(self) -> int:
        if not self._uart_manager: return 0
        return self._uart_manager.get_channel(self._id).any()

    def read(self, nbytes=None):
        if not self._uart_manager: return None
        return self._uart_manager.get_channel(self._id).read(nbytes)

    def readline(self):
        if not self._uart_manager: return None
        return self._uart_manager.get_channel(self._id).readline()

    def readinto(self, buf, nbytes=None):
        if not self._uart_manager: return None
        return self._uart_manager.get_channel(self._id).readinto(buf, nbytes)

    def write(self, buf):
        if not self._uart_manager: return None
        # Convert to bytes if it's a string
        if isinstance(buf, str):
            buf = buf.encode('utf-8')
        return self._uart_manager.write(self._id, buf)
