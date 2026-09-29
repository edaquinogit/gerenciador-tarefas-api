import re


def normalizar_telefone(value: str) -> str:
    """Valida formato brasileiro; não verifica existência ou titularidade da linha."""
    value = value.strip()
    error = "Informe telefone com DDD: 10 dígitos para fixo ou 11 para celular."
    if not re.fullmatch(r"\+?[0-9 ()-]+", value):
        raise ValueError(error)
    digits = re.sub(r"[^0-9]", "", value)
    if value.startswith("+") or len(digits) in (12, 13):
        if not digits.startswith("55"):
            raise ValueError("Use um telefone brasileiro com DDD e código +55.")
        digits = digits[2:]
    if not re.fullmatch(r"[1-9][0-9](?:[2-5][0-9]{7}|9[0-9]{8})", digits):
        raise ValueError(error)
    return "+55" + digits
