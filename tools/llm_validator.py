from jsonschema import validate, ValidationError
from typing import Tuple, List
import re


# Mais rígido, mas ainda compatível com os testes existentes
PLAN_SCHEMA = {
    "type": "array",
    "maxItems": 20,
    "items": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "minLength": 1, "maxLength": 50},
            "params": {"type": "object"}
        },
        "required": ["action"],
        "additionalProperties": False,
    },
}


def validate_plan_structure(plan_obj) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    try:
        validate(instance=plan_obj, schema=PLAN_SCHEMA)
        return True, []
    except ValidationError as e:
        # Retornar mensagens curtas e legíveis
        errors.append(e.message)
        return False, errors


# Lista de padrões proibidos na geração de código — mantenha simples e eficaz
_CODE_BLACKLIST = [
    r"\bsubprocess\b",
    r"\bos\.system\b",
    r"\beval\(",
    r"\bexec\(",
    r"__import__",
    r"\bsocket\b",
    r"\bstdin\b",
    r"\brequests\b",
]


def validate_generated_code(code: str, max_length: int = 20000) -> Tuple[bool, List[str]]:
    issues: List[str] = []
    if not code:
        issues.append("code_missing")
    if len(code) > max_length:
        issues.append("code_too_long")
    for pattern in _CODE_BLACKLIST:
        if re.search(pattern, code):
            issues.append(f"forbidden_pattern:{pattern}")
    return (len(issues) == 0), issues
