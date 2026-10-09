import re


def parse_budget(text: str) -> tuple[Optional[float], str]:
    if not text:
        return None, "no_detectado"
    t = text.lower().strip()
    if "cento e cinquenta" in t or "cento e cinquent" in t:
        return 150.0, "texto"
    if "cento e trinta" in t or "cento e trint" in t:
        return 130.0, "texto"
    patterns = [
        (r"([0-9]+(?:\.[0-9]{3})*(?:,[0-9]{1,2})?)\s*(?:mil|k)\b", "texto_mil"),
        (r"at[eé]\s*(?:r\$)?\s*([0-9]+(?:\.[0-9]{3})*(?:,[0-9]{1,2})?)\s*(?:reais?|mil|k)?", "texto"),
        (r"no\s+m[aá]ximo\s*(?:r\$)?\s*([0-9]+(?:\.[0-9]{3})*(?:,[0-9]{1,2})?)\s*(?:reais?|mil|k)?", "texto"),
        (r"entre\s*r\$\s*([0-9]+(?:\.[0-9]{3})*(?:,[0-9]{1,2})?)\s*e\s*r\$\s*([0-9]+(?:\.[0-9]{3})*(?:,[0-9]{1,2})?)", "texto_entre"),
        (r"uns\s+cem\s+conto", "aproximado"),
        (r"cem\s+contos?", "aproximado"),
        (r"uns\s+cem", "aproximado"),
    ]
    for pat, source in patterns:
        m = re.search(pat, t)
        if m:
            if source == "aproximado":
                return 110.0, "texto_aproximado"
            if source == "texto_entre":
                raw = m.group(2)
                val = _parse_number(raw)
                return val, "texto"
            raw = m.group(1)
            if source == "texto_mil":
                return _parse_number(raw) * 1000, "texto"
            val = _parse_number(raw)
            return val, "texto"
    return None, "no_detectado"


def _parse_number(raw: str) -> float:
    if "," in raw and "." in raw:
        return float(raw.replace(".", "").replace(",", "."))
    if "," in raw:
        parts = raw.split(",")
        if len(parts) == 2 and len(parts[1]) <= 2:
            return float(raw.replace(",", "."))
    return float(raw.replace(".", "").replace(",", ".")) if "," in raw and raw.count(",") == 1 and len(raw.split(",")[1]) == 3 else float(raw.replace(",", "."))


def bucket_budget(max_val: Optional[float]) -> str:
    if max_val is None:
        return "sem_limite"
    if max_val <= 50:
        return "ate_50"
    if max_val <= 100:
        return "ate_100"
    if max_val <= 150:
        return "ate_150"
    if max_val <= 200:
        return "ate_200"
    if max_val <= 300:
        return "ate_300"
    if max_val <= 500:
        return "ate_500"
    if max_val <= 1000:
        return "ate_1000"
    return "premium"
