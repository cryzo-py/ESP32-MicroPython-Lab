# -*- coding: utf-8 -*-
"""
Success Profile Model & Validator
Contrat déclaratif pédagogique pour ESP32 Lab.
"""

import uuid
import re

VALID_CATEGORIES = {"topology", "code", "behavior", "constraints"}

VALID_TYPES = {
    "topology": {
        "required_component", "forbidden_component", 
        "required_connection", "forbidden_connection", "pin_capability"
    },
    "code": {
        "required_api", "forbidden_api", 
        "required_structure", "required_relation"
    },
    "behavior": {
        "causality_mapping", "threshold_response", 
        "state_transition", "value_relation"
    },
    "constraints": {
        "required_value", "allowed_range", 
        "required_pin", "forbidden_pin", "allowed_component"
    }
}

class SuccessProfileValidator:
    """Valide les profils de réussite (Success Profiles) selon le contrat pédagogique."""
    
    @classmethod
    def validate(cls, profile: dict) -> list[str]:
        """
        Valide l'ensemble du pedagogy_profile ou de la section criteria.
        Retourne une liste d'erreurs (vide si valide).
        """
        errors = []
        if not profile:
            return errors
            
        criteria = profile.get("criteria", [])
        if not isinstance(criteria, list):
            errors.append("'criteria' doit être une liste.")
            return errors
            
        for idx, crit in enumerate(criteria):
            if not isinstance(crit, dict):
                errors.append(f"Critère {idx} : doit être un dictionnaire.")
                continue
            errors.extend(cls.validate_criterion(crit, f"Critère {idx}"))
            
        return errors

    @classmethod
    def validate_criterion(cls, crit: dict, context: str = "") -> list[str]:
        errors = []
        prefix = f"{context} ({crit.get('id', 'unknown')}) : " if context else f"Critère {crit.get('id', 'unknown')} : "
        
        # Champs obligatoires de base
        for field in ["id", "category", "type", "description"]:
            if field not in crit:
                errors.append(f"{prefix}champ obligatoire manquant '{field}'.")
                
        # Typage et contraintes des champs
        if "id" in crit and not isinstance(crit["id"], str):
            errors.append(f"{prefix}'id' doit être une chaîne.")
            
        cat = crit.get("category")
        if cat and cat not in VALID_CATEGORIES:
            errors.append(f"{prefix}catégorie inconnue '{cat}'.")
            
        c_type = crit.get("type")
        if cat in VALID_CATEGORIES and c_type:
            if c_type not in VALID_TYPES[cat]:
                errors.append(f"{prefix}type '{c_type}' invalide pour la catégorie '{cat}'.")
                
        if "enabled" in crit and not isinstance(crit["enabled"], bool):
            errors.append(f"{prefix}'enabled' doit être un booléen.")
            
        if "blocking" in crit and not isinstance(crit["blocking"], bool):
            errors.append(f"{prefix}'blocking' doit être un booléen.")
            
        if "depends_on" in crit:
            if not isinstance(crit["depends_on"], list):
                errors.append(f"{prefix}'depends_on' doit être une liste d'IDs.")
                
        # Validation spécifique aux structures
        if c_type == "required_connection":
            if "target" not in crit:
                errors.append(f"{prefix}type 'required_connection' exige un champ 'target'.")
        elif c_type == "causality_mapping":
            if "trigger" not in crit or "expect" not in crit:
                errors.append(f"{prefix}type 'causality_mapping' exige les champs 'trigger' et 'expect'.")
        elif c_type == "allowed_range":
            if "min" not in crit and "max" not in crit:
                errors.append(f"{prefix}type 'allowed_range' exige au moins 'min' ou 'max'.")
                
        # Vérification d'absence totale d'exécution Python (sécurité déclarative)
        crit_str = str(crit)
        if re.search(r"lambda\s*:", crit_str) or "eval(" in crit_str or "exec(" in crit_str:
            errors.append(f"{prefix}exécution Python (lambda, eval, exec) formellement interdite.")
            
        return errors

def ensure_valid_profile(profile: dict):
    """Lève une ValueError si le profil n'est pas valide."""
    errors = SuccessProfileValidator.validate(profile)
    if errors:
        raise ValueError("\n".join(errors))

