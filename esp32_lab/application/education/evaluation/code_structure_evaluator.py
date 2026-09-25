import ast
from typing import Dict, List, Any

class CodeStructureEvaluator:
    """Evaluates MicroPython code using AST without executing it."""
    
    def evaluate(self, code: str) -> Dict[str, Any]:
        result = {
            "imports": [],
            "pins": [],
            "pwm": [],
            "adc": [],
            "i2c": [],
            "spi": [],
            "uart": []
        }
        
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return result
            
        for node in ast.walk(tree):
            # Parse imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    result["imports"].append({"module": alias.name, "name": None})
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    result["imports"].append({"module": node.module, "name": alias.name})
                    
            # Parse Call nodes (Pin, PWM, ADC, etc.)
            elif isinstance(node, ast.Call):
                func_name = None
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                    
                if func_name == "Pin":
                    pin_info = self._extract_pin(node)
                    if pin_info:
                        result["pins"].append(pin_info)
                elif func_name == "PWM":
                    pwm_info = self._extract_pwm(node)
                    if pwm_info:
                        result["pwm"].append(pwm_info)
                elif func_name == "ADC":
                    adc_info = self._extract_adc(node)
                    if adc_info:
                        result["adc"].append(adc_info)
                elif func_name == "I2C":
                    i2c_info = self._extract_i2c(node)
                    if i2c_info:
                        result["i2c"].append(i2c_info)
                        
        return result
        
    def _extract_pin(self, node: ast.Call) -> Dict[str, Any]:
        gpio = None
        mode = None
        if node.args and isinstance(node.args[0], ast.Constant):
            gpio = node.args[0].value
            
        if len(node.args) > 1:
            if isinstance(node.args[1], ast.Attribute):
                mode = node.args[1].attr
            elif isinstance(node.args[1], ast.Name):
                mode = node.args[1].id
                
        # Keyword arg for mode
        for kw in node.keywords:
            if kw.arg == "mode":
                if isinstance(kw.value, ast.Attribute):
                    mode = kw.value.attr
                elif isinstance(kw.value, ast.Name):
                    mode = kw.value.id
                    
        if gpio is not None:
            return {"gpio": gpio, "mode": mode}
        return {}
        
    def _extract_pwm(self, node: ast.Call) -> Dict[str, Any]:
        gpio = None
        # PWM(Pin(25))
        if node.args and isinstance(node.args[0], ast.Call):
            pin_info = self._extract_pin(node.args[0])
            gpio = pin_info.get("gpio")
        return {"gpio": gpio} if gpio is not None else {}
        
    def _extract_adc(self, node: ast.Call) -> Dict[str, Any]:
        gpio = None
        if node.args and isinstance(node.args[0], ast.Call):
            pin_info = self._extract_pin(node.args[0])
            gpio = pin_info.get("gpio")
        return {"gpio": gpio} if gpio is not None else {}
        
    def _extract_i2c(self, node: ast.Call) -> Dict[str, Any]:
        sda = None
        scl = None
        for kw in node.keywords:
            if kw.arg in ("sda", "scl") and isinstance(kw.value, ast.Call):
                pin_info = self._extract_pin(kw.value)
                if kw.arg == "sda":
                    sda = pin_info.get("gpio")
                else:
                    scl = pin_info.get("gpio")
        return {"sda": sda, "scl": scl}
