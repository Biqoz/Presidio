from presidio_analyzer import Pattern, PatternRecognizer

# --- DÉTECTEURS BELGES ---

class BelgianNrnRecognizer(PatternRecognizer):
    """Détecteur pour le Numéro de Registre National belge."""
    PATTERNS = [Pattern(name="NRN", regex=r"\b(?:[0-9]{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12][0-9]|3[01]))-?\d{3}\.?\d{2}\b", score=1.0)]
    CONTEXT = ["registre national", "nrn", "niss"]
    SUPPORTED_ENTITY = "BE_NATIONAL_REGISTER_NUMBER"

class BelgianEnterpriseRecognizer(PatternRecognizer):
    """Détecteur pour le N° d'entreprise belge."""
    PATTERNS = [Pattern(name="BTW/TVA", regex=r"\bBE\s?0\d{3}\.\d{3}\.\d{3}\b", score=0.95)]
    CONTEXT = ["numéro d'entreprise", "btw", "tva"]
    SUPPORTED_ENTITY = "BE_ENTERPRISE_NUMBER"

# --- DÉTECTEURS RGPD GÉNÉRIQUES ---

class IbanRecognizer(PatternRecognizer):
    """Détecteur pour les IBAN."""
    PATTERNS = [Pattern(name="IBAN", regex=r"\b[A-Z]{2}\d{2}\s?(?:\d{4}\s?){4,7}\d{1,4}\b", score=0.95)]
    CONTEXT = ["iban", "compte", "bancaire"]
    SUPPORTED_ENTITY = "IBAN"

class PhoneRecognizer(PatternRecognizer):
    """Détecteur pour les numéros de téléphone EU."""
    PATTERNS = [Pattern(name="Phone (EU)", regex=r"\b(?:(?:\+|00)(?:32|33|352)|0)\s?[1-9](?:[\s.-]?\d{2}){3,4}\b", score=0.8)]
    CONTEXT = ["tel", "téléphone", "gsm"]
    SUPPORTED_ENTITY = "PHONE_NUMBER"

# ... Ajoutez ici d'autres classes pour les autres regex si nécessaire ...

# Liste de tous les reconnaisseurs à charger par Presidio
custom_recognizers = [
    BelgianNrnRecognizer,
    BelgianEnterpriseRecognizer,
    IbanRecognizer,
    PhoneRecognizer,
]
