"""
Tests unitaires et d'intégration pour l'interpréteur Arduino C / C++ (Commit 3).
"""

import time
import pytest
from esp32_lab.core.board_profiles import get_board_profile
from esp32_lab.simulator.gpio import GPIOManager, GPIOMode
from esp32_lab.simulator.adc import ADCManager
from esp32_lab.simulator.pwm import PWMManager
from esp32_lab.simulator.engine import SimulationEngine
from esp32_lab.simulator.arduino.lexer import ArduinoLexer
from esp32_lab.simulator.arduino.parser import ArduinoParser
from esp32_lab.simulator.arduino.interpreter import ArduinoInterpreter
from esp32_lab.simulator.arduino.libraries.servo import VirtualServo
from esp32_lab.simulator.arduino.libraries.liquidcrystal import VirtualLiquidCrystal


def test_lexer_tokens_and_preprocessor():
    code = """
    #include <Servo.h>
    #define LED_PIN 13
    #define BAUD 9600

    // Commentaire mono-ligne
    /* Commentaire
       multi-lignes */
    void setup() {
        int x = 42;
        float pi = 3.14;
        int hex_val = 0x2A;
        int bin_val = 0b1010;
        String msg = "Hello Arduino";
        Serial.begin(BAUD);
        pinMode(LED_PIN, OUTPUT);
    }
    """
    lexer = ArduinoLexer(code)
    tokens = lexer.tokenize()

    assert "Servo" in lexer.included_libraries
    assert lexer.macros["LED_PIN"] == "13"
    assert lexer.macros["BAUD"] == "9600"

    # Vérifier quelques tokens clés
    token_values = [t.value for t in tokens if t.type not in ("EOF", "DELIMITER")]
    assert "setup" in token_values
    assert 42 in token_values
    assert 3.14 in token_values
    assert 42 in token_values  # 0x2A = 42
    assert 10 in token_values  # 0b1010 = 10
    assert "Hello Arduino" in token_values


def test_parser_ast_structure():
    code = """
    const int buttonPin = 2;
    int state = 0;
    int scores[3] = {10, 20, 30};

    int add(int a, int b) {
        return a + b;
    }

    void setup() {
        pinMode(buttonPin, INPUT);
    }

    void loop() {
        if (digitalRead(buttonPin) == HIGH) {
            state = add(state, 1);
        } else {
            state = 0;
        }
    }
    """
    lexer = ArduinoLexer(code)
    tokens = lexer.tokenize()
    parser = ArduinoParser(tokens)
    prog = parser.parse()

    assert len(prog.statements) >= 5
    func_names = [s.name for s in prog.statements if hasattr(s, "name")]
    assert "add" in func_names
    assert "setup" in func_names
    assert "loop" in func_names


def test_interpreter_variables_and_math():
    code = """
    int a = 10;
    int b = 3;
    int sum = 0;
    int diff = 0;
    int prod = 0;
    int quot = 0;
    int rem = 0;
    int mapped = 0;
    int clamped = 0;

    void setup() {
        sum = a + b;
        diff = a - b;
        prod = a * b;
        quot = a / b;
        rem = a % b;
        mapped = map(50, 0, 100, 0, 1000);
        clamped = constrain(150, 0, 100);
    }
    """
    lexer = ArduinoLexer(code)
    parser = ArduinoParser(lexer.tokenize())
    prog = parser.parse()

    interp = ArduinoInterpreter()
    interp.run(prog)

    assert interp.globals["sum"] == 13
    assert interp.globals["diff"] == 7
    assert interp.globals["prod"] == 30
    assert interp.globals["quot"] == 3
    assert interp.globals["rem"] == 1
    assert interp.globals["mapped"] == 500
    assert interp.globals["clamped"] == 100


def test_interpreter_control_flow():
    code = """
    int for_count = 0;
    int while_count = 0;
    int switch_val = 0;

    void setup() {
        for (int i = 0; i < 5; i++) {
            for_count += 2;
        }

        int w = 0;
        while (w < 4) {
            while_count++;
            w++;
        }

        int choice = 2;
        switch (choice) {
            case 1:
                switch_val = 10;
                break;
            case 2:
                switch_val = 20;
                break;
            default:
                switch_val = 99;
                break;
        }
    }
    """
    lexer = ArduinoLexer(code)
    parser = ArduinoParser(lexer.tokenize())
    prog = parser.parse()

    interp = ArduinoInterpreter()
    interp.run(prog)

    assert interp.globals["for_count"] == 10
    assert interp.globals["while_count"] == 4
    assert interp.globals["switch_val"] == 20


def test_interpreter_serial_output():
    output = []
    code = """
    void setup() {
        Serial.begin(115200);
        Serial.print("Valeur: ");
        Serial.println(42);
    }
    """
    lexer = ArduinoLexer(code)
    parser = ArduinoParser(lexer.tokenize())
    prog = parser.parse()

    interp = ArduinoInterpreter(output_callback=output.append)
    interp.run(prog)

    result = "".join(output)
    assert "Valeur: 42\n" in result


def test_interpreter_gpio_and_digital_io():
    profile = get_board_profile("arduino_uno")
    gpio = GPIOManager(board_profile=profile)

    code = """
    void setup() {
        pinMode(13, OUTPUT);
        digitalWrite(13, HIGH);
        pinMode(2, INPUT);
    }
    """
    lexer = ArduinoLexer(code)
    parser = ArduinoParser(lexer.tokenize())
    prog = parser.parse()

    interp = ArduinoInterpreter(gpio_manager=gpio)
    interp.run(prog)

    assert gpio.get_mode(13) == GPIOMode.OUT
    assert gpio.read(13) == 1
    assert gpio.get_mode(2) == GPIOMode.IN


def test_interpreter_analog_and_pwm():
    profile = get_board_profile("arduino_uno")
    gpio = GPIOManager(board_profile=profile)
    adc = ADCManager(gpio, board_profile=profile)
    pwm = PWMManager(gpio, board_profile=profile)

    code = """
    void setup() {
        analogWrite(9, 128);
    }
    """
    lexer = ArduinoLexer(code)
    parser = ArduinoParser(lexer.tokenize())
    prog = parser.parse()

    interp = ArduinoInterpreter(gpio_manager=gpio, adc_manager=adc, pwm_manager=pwm)
    interp.run(prog)

    state = pwm.get(9)
    assert state is not None
    assert state["duty"] == 128


def test_virtual_servo_library():
    profile = get_board_profile("arduino_uno")
    gpio = GPIOManager(board_profile=profile)
    pwm = PWMManager(gpio, board_profile=profile)

    code = """
    #include <Servo.h>
    Servo myServo;

    void setup() {
        myServo.attach(9);
        myServo.write(180);
    }
    """
    lexer = ArduinoLexer(code)
    parser = ArduinoParser(lexer.tokenize())
    prog = parser.parse()

    interp = ArduinoInterpreter(gpio_manager=gpio, pwm_manager=pwm)
    interp.run(prog)

    servo_obj = interp.globals.get("myServo")
    assert isinstance(servo_obj, VirtualServo)
    assert servo_obj.read() == 180
    assert servo_obj.attached() is True


def test_virtual_liquidcrystal_library():
    code = """
    #include <LiquidCrystal.h>
    LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

    void setup() {
        lcd.begin(16, 2);
        lcd.print("Arduino Uno!");
    }
    """
    lexer = ArduinoLexer(code)
    parser = ArduinoParser(lexer.tokenize())
    prog = parser.parse()

    interp = ArduinoInterpreter()
    interp.run(prog)

    lcd_obj = interp.globals.get("lcd")
    assert isinstance(lcd_obj, VirtualLiquidCrystal)
    assert "Arduino Uno!" in lcd_obj.lines[0]


def test_simulation_engine_runs_arduino(app):
    profile = get_board_profile("arduino_uno")
    engine = SimulationEngine(board_profile=profile)

    serial_outputs = []
    engine.event_bus.serial_data_received.connect(serial_outputs.append)

    code = """
    void setup() {
        pinMode(13, OUTPUT);
        digitalWrite(13, HIGH);
        Serial.println("SETUP DONE");
    }
    void loop() {
    }
    """
    engine.start(code, language="arduino")
    deadline = time.time() + 1.5
    while time.time() < deadline and "SETUP DONE" not in "".join(serial_outputs):
        app.processEvents()
        time.sleep(0.02)
    engine.stop()

    assert engine.gpio_manager.read(13) == 1
    full_output = "".join(serial_outputs)
    assert "SETUP DONE" in full_output


def test_arduino_security_sandbox_blocks_dunder_and_private():
    """Vérifie le blocage d'accès aux attributs internes Python (__class__, __bases__, etc.)."""
    from esp32_lab.simulator.arduino.interpreter import ArduinoRuntimeError
    from esp32_lab.simulator.arduino.ast_nodes import MemberExpr, Identifier

    # 1. Rejet au niveau du parseur pour les identifiants dunder/protégés
    code_exploit = """
    void setup() {
        Serial.__class__;
    }
    void loop() {}
    """
    lexer = ArduinoLexer(code_exploit)
    tokens = lexer.tokenize()
    parser = ArduinoParser(tokens)
    with pytest.raises(SyntaxError, match="Accès refusé au membre protégé ou spécial"):
        parser.parse()

    # 2. Rejet au niveau de l'interpréteur si un AST contient un MemberExpr non autorisé
    interp = ArduinoInterpreter()
    bad_member = MemberExpr(Identifier("Serial", 1, 1), "__class__", 1, 1)
    with pytest.raises(ArduinoRuntimeError, match="Accès refusé au membre protégé ou spécial '__class__'"):
        interp.evaluate_expression(bad_member)

    bad_private = MemberExpr(Identifier("Serial", 1, 1), "_callback", 1, 1)
    with pytest.raises(ArduinoRuntimeError, match="Accès refusé au membre protégé ou spécial '_callback'"):
        interp.evaluate_expression(bad_private)


def test_arduino_dynamic_led_builtin_profile():
    """Vérifie que LED_BUILTIN s'aligne automatiquement sur le profil de carte actif (13 sur Uno, 2 sur ESP32)."""
    from esp32_lab.core.board_profiles import load_board_profile

    # Uno
    uno_prof = load_board_profile("arduino_uno")
    interp_uno = ArduinoInterpreter(board_profile=uno_prof)
    assert interp_uno.globals["LED_BUILTIN"] == 13

    # ESP32
    esp_prof = load_board_profile("esp32_wroom_32")
    interp_esp = ArduinoInterpreter(board_profile=esp_prof)
    assert interp_esp.globals["LED_BUILTIN"] == 2

    # Changement dynamique de profil
    interp_uno.set_board_profile(esp_prof)
    assert interp_uno.globals["LED_BUILTIN"] == 2


def test_arduino_analog_write_scaling_esp32():
    """Vérifie la mise à l'échelle automatique de analogWrite (0-255 -> 0-1023) pour les cartes ESP32."""
    from esp32_lab.core.board_profiles import load_board_profile

    # Cas Arduino Uno (échelle 8 bits standard 0-255)
    uno_prof = load_board_profile("arduino_uno")
    gpio_uno = GPIOManager(board_profile=uno_prof)
    pwm_uno = PWMManager(gpio_uno, board_profile=uno_prof)
    interp_uno = ArduinoInterpreter(gpio_manager=gpio_uno, pwm_manager=pwm_uno, board_profile=uno_prof)
    interp_uno._builtin_analog_write(3, 255)
    assert pwm_uno.get_duty(3) == 255
    interp_uno._builtin_analog_write(3, 128)
    assert pwm_uno.get_duty(3) == 128

    # Cas ESP32 (échelle 10 bits 0-1023)
    esp_prof = load_board_profile("esp32_wroom_32")
    gpio_esp = GPIOManager(board_profile=esp_prof)
    pwm_esp = PWMManager(gpio_esp, board_profile=esp_prof)
    interp_esp = ArduinoInterpreter(gpio_manager=gpio_esp, pwm_manager=pwm_esp, board_profile=esp_prof)
    interp_esp._builtin_analog_write(2, 255)
    assert pwm_esp.get_duty(2) == 1023
    interp_esp._builtin_analog_write(2, 128)
    assert pwm_esp.get_duty(2) == 514
    interp_esp._builtin_analog_write(2, 0)
    assert pwm_esp.get_duty(2) == 0


def test_board_profile_fqbn():
    """Vérifie la propriété FQBN pour le téléversement physique vers Uno et ESP32."""
    from esp32_lab.core.board_profiles import load_board_profile

    uno = load_board_profile("arduino_uno")
    assert uno.fqbn == "arduino:avr:uno"

    esp32 = load_board_profile("esp32_wroom_32")
    assert esp32.fqbn == "esp32:esp32:esp32"
