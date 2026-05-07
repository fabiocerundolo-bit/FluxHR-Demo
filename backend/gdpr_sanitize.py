import re

def sanitize_cv(text: str) -> str:
    text = re.sub(r"(?i)(allergia|disabilità|malattia|disturbo|diagnosi|patologia|fumatore|obesità|gravidanza).*?[.\n]", "[REDATTO - DATO SANITARIO]", text)
    text = re.sub(r"(?i)(partito|sindacato|sciopero|voto|elezioni|democrazia|socialista|comunista|destra|sinistra).*?[.\n]", "[REDATTO - OPINIONE POLITICA]", text)
    text = re.sub(r"(?i)(chiesa|moschea|sinagoga|preghiera|dio|allah|buddista|cattolico|musulmano|ebraico).*?[.\n]", "[REDATTO - CREDO RELIGIOSO]", text)
    return text