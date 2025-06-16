"""
Reconnaisseurs personnalisés pour les données belges et françaises.
"""

from presidio_analyzer import Pattern, PatternRecognizer


class BelgianNrnRecognizer(PatternRecognizer):
    """Détecteur pour le Numéro de Registre National belge (NRN/NISS)."""
    
    def __init__(self):
        patterns = [
            Pattern(
                name="NRN format standard", 
                regex=r"\b\d{2}\.\d{2}\.\d{2}-\d{3}\.\d{2}\b", 
                score=1.0
            ),
            Pattern(
                name="NRN format compact", 
                regex=r"\b\d{11}\b", 
                score=0.7
            ),
            Pattern(
                name="NRN format espacé", 
                regex=r"\b\d{2}\s\d{2}\s\d{2}\s\d{3}\s\d{2}\b", 
                score=0.9
            )
        ]
        super().__init__(
            supported_entity="BE_NATIONAL_REGISTER_NUMBER",
            patterns=patterns,
            context=["registre national", "nrn", "niss", "numéro national", "identité"],
            supported_language="fr"
        )


class BelgianEnterpriseRecognizer(PatternRecognizer):
    """Détecteur pour le numéro d'entreprise belge (BTW/TVA)."""
    
    def __init__(self):
        patterns = [
            Pattern(
                name="BTW/TVA format standard", 
                regex=r"\bBE\s?0\d{3}\.\d{3}\.\d{3}\b", 
                score=0.95
            ),
            Pattern(
                name="BTW/TVA format compact", 
                regex=r"\bBE\s?0\d{9}\b", 
                score=0.9
            )
        ]
        super().__init__(
            supported_entity="BE_ENTERPRISE_NUMBER",
            patterns=patterns,
            context=["numéro d'entreprise", "btw", "tva", "entreprise", "société"],
            supported_language="fr"
        )


class BelgianBankAccountRecognizer(PatternRecognizer):
    """Détecteur pour les comptes bancaires belges."""
    
    def __init__(self):
        patterns = [
            Pattern(
                name="Compte bancaire belge", 
                regex=r"\b\d{3}-\d{7}-\d{2}\b", 
                score=0.9
            )
        ]
        super().__init__(
            supported_entity="BE_BANK_ACCOUNT",
            patterns=patterns,
            context=["compte", "bancaire", "virement", "domiciliation", "banque"],
            supported_language="fr"
        )


class ImprovedIbanRecognizer(PatternRecognizer):
    """Détecteur amélioré pour les IBAN européens."""
    
    def __init__(self):
        patterns = [
            Pattern(
                name="IBAN avec espaces", 
                regex=r"\b[A-Z]{2}\d{2}(?:\s\d{4}){3,7}(?:\s\d{1,4})?\b", 
                score=0.95
            ),
            Pattern(
                name="IBAN compact", 
                regex=r"\b[A-Z]{2}\d{2}[A-Z0-9]{4,32}\b", 
                score=0.9
            )
        ]
        super().__init__(
            supported_entity="IBAN",
            patterns=patterns,
            context=["iban", "compte", "bancaire", "virement", "international"],
            supported_language="fr"
        )


class ImprovedPhoneRecognizer(PatternRecognizer):
    """Détecteur amélioré pour les numéros de téléphone BE/FR/LUX."""
    
    def __init__(self):
        patterns = [
            Pattern(
                name="Téléphone international", 
                regex=r"\b(?:\+|00)(?:32|33|352)\s?[1-9](?:[\s.-]?\d{2}){3,4}\b", 
                score=0.9
            ),
            Pattern(
                name="Téléphone national", 
                regex=r"\b0[1-9](?:[\s.-]?\d{2}){4}\b", 
                score=0.8
            ),
            Pattern(
                name="Mobile belge", 
                regex=r"\b04\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}\b", 
                score=0.85
            )
        ]
        super().__init__(
            supported_entity="PHONE_NUMBER",
            patterns=patterns,
            context=["tel", "téléphone", "gsm", "mobile", "portable", "numéro"],
            supported_language="fr"
        )


class FrenchNIRRecognizer(PatternRecognizer):
    """Détecteur pour le Numéro de Sécurité Sociale français (NIR)."""
    
    def __init__(self):
        patterns = [
            Pattern(
                name="NIR avec espaces", 
                regex=r"\b[12]\s?\d{2}\s?(?:0[1-9]|1[0-2])\s?(?:2[ABab]|[0-9]{2})\s?\d{3}\s?\d{3}\s?\d{2}\b", 
                score=1.0
            ),
            Pattern(
                name="NIR compact", 
                regex=r"\b[12]\d{2}(?:0[1-9]|1[0-2])(?:2[ABab]|[0-9]{2})\d{6}\d{2}\b", 
                score=0.95
            )
        ]
        super().__init__(
            supported_entity="FR_SOCIAL_SECURITY_NUMBER",
            patterns=patterns,
            context=["sécurité sociale", "nir", "numéro social", "sécu"],
            supported_language="fr"
        )


class ImprovedEmailRecognizer(PatternRecognizer):
    """Détecteur d'email amélioré avec contexte français."""
    
    def __init__(self):
        patterns = [
            Pattern(
                name="Email standard", 
                regex=r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b", 
                score=0.9
            )
        ]
        super().__init__(
            supported_entity="EMAIL_ADDRESS",
            patterns=patterns,
            context=["email", "mail", "courriel", "adresse électronique", "e-mail", "@"],
            supported_language="fr"
        )


# Fonction pour créer les instances des reconnaisseurs
def get_custom_recognizers():
    """Retourne la liste des reconnaisseurs personnalisés instanciés."""
    return [
        BelgianNrnRecognizer(),
        BelgianEnterpriseRecognizer(),
        BelgianBankAccountRecognizer(),
        ImprovedIbanRecognizer(),
        ImprovedPhoneRecognizer(),
        FrenchNIRRecognizer(),
        ImprovedEmailRecognizer()
    ]


# Variable pour la compatibilité avec la configuration YAML
custom_recognizers = get_custom_recognizers()
