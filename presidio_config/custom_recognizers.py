from presidio_analyzer import Pattern, PatternRecognizer

# --- DÉTECTEURS SPÉCIFIQUES À LA BELGIQUE ---

class BelgianNrnRecognizer(PatternRecognizer):
    """Détecteur pour le Numéro de Registre National belge (NRN/NISS)."""
    PATTERNS = [Pattern(name="NRN (format standard)", regex=r"\b(?:[0-9]{2}\.[0-9]{2}\.[0-9]{2}-\d{3}\.\d{2})\b", score=1.0)]
    CONTEXT = ["registre national", "nrn", "niss"]
    SUPPORTED_ENTITY = "BE_NATIONAL_REGISTER_NUMBER"

class BelgianEnterpriseRecognizer(PatternRecognizer):
    """Détecteur pour le N° d'entreprise belge (BTW/TVA)."""
    PATTERNS = [Pattern(name="BTW/TVA", regex=r"\bBE\s?0\d{3}\.\d{3}\.\d{3}\b", score=0.95)]
    CONTEXT = ["numéro d'entreprise", "btw", "tva"]
    SUPPORTED_ENTITY = "BE_ENTERPRISE_NUMBER"

# --- AMÉLIORATIONS DES DÉTECTEURS DE BASE ---

class ImprovedIbanRecognizer(PatternRecognizer):
    """Détecteur amélioré pour les IBAN, pour s'assurer qu'il est bien capturé."""
    PATTERNS = [Pattern(name="IBAN", regex=r"\b[A-Z]{2}\d{2}(?:\s?\d{4}){3,7}(?:\s?\d{1,4})?\b", score=0.95)]
    CONTEXT = ["iban", "compte", "bancaire", "virement"]
    SUPPORTED_ENTITY = "IBAN"

class ImprovedPhoneRecognizer(PatternRecognizer):
    """Détecteur amélioré pour les numéros de téléphone (BE/FR/LUX)."""
    PATTERNS = [Pattern(name="Phone (EU)", regex=r"\b(?:(?:\+|00)(?:32|33|352)|0)\s?[1-9](?:[\s.-]?\d{2}){3,4}\b", score=0.9)]
    CONTEXT = ["tel", "téléphone", "gsm", "mobile"]
    SUPPORTED_ENTITY = "PHONE_NUMBER"

# --- NOUVEAUX DÉTECTEURS RGPD ---

class FrenchNIRRecognizer(PatternRecognizer):
    """Détecteur pour le Numéro de Sécurité Sociale Français (NIR)."""
    PATTERNS = [Pattern(name="NIR", regex=r"\b[12]\s?\d{2}\s?(?:0[1-9]|1[0-2])\s?(?:2[ABab]|[0-9]{2})\s?\d{3}\s?\d{3}\s?\d{2}\b", score=1.0)]
    CONTEXT = ["sécurité sociale", "nir"]
    SUPPORTED_ENTITY = "FR_SOCIAL_SECURITY_NUMBER"

# --- LISTE FINALE À CHARGER ---
# C'est cette liste que le config.yaml va importer.
custom_recognizers = [
    BelgianNrnRecognizer,
    BelgianEnterpriseRecognizer,
    ImprovedIbanRecognizer,
    ImprovedPhoneRecognizer,
    FrenchNIRRecognizer,
]
