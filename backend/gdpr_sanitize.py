import re

def sanitize_cv(text: str) -> str:
    # Rimuove dati sanitari
    text = re.sub(r"(?i)(allergia|disabilità|malattia|disturbo|diagnosi|patologia|fumatore|obesità|gravidanza).*?[.\n]", "[REDATTO - DATO SANITARIO]", text)
    # Rimuove opinioni politiche/sindacali
    text = re.sub(r"(?i)(partito|sindacato|sciopero|voto|elezioni|democrazia|socialista|comunista|destra|sinistra).*?[.\n]", "[REDATTO - OPINIONE POLITICA]", text)
    # Rimuove religione
    text = re.sub(r"(?i)(chiesa|moschea|sinagoga|preghiera|dio|allah|buddista|cattolico|musulmano|ebraico).*?[.\n]", "[REDATTO - CREDO RELIGIOSO]", text)
    return text

def extract_only_pertinent(data: dict) -> dict:
    allowed = {"nome", "cognome", "email", "telefono", "competenze"}
    return {k: v for k, v in data.items() if k in allowed}