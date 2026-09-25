import pytest
from esp32_lab.application.education.evaluation.code_structure_evaluator import CodeStructureEvaluator

def test_ast_valid_pins():
    code = "from machine import Pin\nled = Pin(18, Pin.OUT)\nbtn = Pin(4, Pin.IN)"
    evaluator = CodeStructureEvaluator()
    res = evaluator.evaluate(code)
    
    assert len(res["pins"]) == 2
    assert {"gpio": 18, "mode": "OUT"} in res["pins"]
    assert {"gpio": 4, "mode": "IN"} in res["pins"]

def test_ast_pwm():
    code = "from machine import PWM, Pin\np = PWM(Pin(25), freq=1000)"
    evaluator = CodeStructureEvaluator()
    res = evaluator.evaluate(code)
    
    assert len(res["pwm"]) == 1
    assert res["pwm"][0]["gpio"] == 25

def test_ast_adc():
    code = "from machine import ADC, Pin\na = ADC(Pin(34))"
    evaluator = CodeStructureEvaluator()
    res = evaluator.evaluate(code)
    
    assert len(res["adc"]) == 1
    assert res["adc"][0]["gpio"] == 34

def test_ast_i2c():
    code = "from machine import I2C, Pin\ni2c = I2C(scl=Pin(22), sda=Pin(21))"
    evaluator = CodeStructureEvaluator()
    res = evaluator.evaluate(code)
    
    assert len(res["i2c"]) == 1
    assert res["i2c"][0]["scl"] == 22
    assert res["i2c"][0]["sda"] == 21

def test_ast_adversarial_strings():
    # Should ignore text/strings that say "GPIO18"
    code = "message = 'GPIO18'\npin_num = 18\n# Pin(18)"
    evaluator = CodeStructureEvaluator()
    res = evaluator.evaluate(code)
    
    assert len(res["pins"]) == 0
    assert len(res["pwm"]) == 0

def test_ast_syntax_error():
    code = "Pin(18, Pin.OUT" # Missing parenthesis
    evaluator = CodeStructureEvaluator()
    res = evaluator.evaluate(code)
    
    # Should not crash, just return empty/partial
    assert len(res["pins"]) == 0
