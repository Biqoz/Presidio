"""
Reconnaisseurs personnalisés pour les données belges et françaises.
"""

from presidio_analyzer import Pattern, PatternRecognizer


class BelgianNrnRecognizer(PatternRecognizer):
    """Détecteur pour le Numéro de Registre National belge (NRN/NISS)."""
    
    def __init__(self):
        patterns = [
            # Format standard : 12.34.56-789.01
            Pattern(
                name="NRN format standard", 
                regex=r"\b\d{2}\.\d{2}\.\d{2}-\d{3}\.\d{2}\b", 
                score=1.0
            ),
            # Format compact : 12345678901
            Pattern(
                name="NRN format compact", 
                regex=r"\b\d{11}\b", 
                score=0.7
            ),
            # Format avec espaces : 12 34 56 789 01
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
            # Format standard : BE0123.456.789
            Pattern(
                name="BTW/TVA format standard", 
                regex=r"\bBE\s?0\d{3}\.\d{3}\.\d{3}\b", 
                score=0.95
            ),
            # Format sans points : BE0123456789
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
            # Format belge : 123-4567890-12
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
            # IBAN avec espaces
            Pattern(
                name="IBAN avec espaces", 
                regex=r"\b[A-Z]{2}\d{2}(?:\s\d{4}){3,7}(?:\s\d{1,4})?\b", 
                score=0.95
            ),
            # IBAN sans espaces
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
            # Format international : +32 1 23 45 67 89
            Pattern(
                name="Téléphone international", 
                regex=r"\b(?:\+|00)(?:32|33|352)\s?[1-9](?:[\s.-]?\d{2}){3,4}\b", 
                score=0.9
            ),
            # Format national : 01 23 45 67 89
            Pattern(
                name="Téléphone national", 
                regex=r"\b0[1-9](?:[\s.-]?\d{2}){4}\b", 
                score=0.8
            ),
            # Format mobile belge : 04xx xx xx xx
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
            # Format avec espaces : 1 23 04 75 123 456 78
            Pattern(
                name="NIR avec espaces", 
                regex=r"\b[12]\s?\d{2}\s?(?:0[1-9]|1[0-2])\s?(?:2[ABab]|[0-9]{2})\s?\d{3}\s?\d{3}\s?\d{2}\b", 
                score=1.0
            ),
            # Format compact : 12304751234567
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
            # Email standard avec domaines courants
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


# Liste des reconnaisseurs à charger
custom_recognizers = [
    BelgianNrnRecognizer(),
    BelgianEnterpriseRecognizer(),
    BelgianBankAccountRecognizer(),
    ImprovedIbanRecognizer(),
    ImprovedPhoneRecognizer(),
    FrenchNIRRecognizer(),
    ImprovedEmailRecognizer()
]
