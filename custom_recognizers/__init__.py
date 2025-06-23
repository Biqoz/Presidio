from presidio_analyzer import PatternRecognizer, AnalyzerEngine

class MyCustomRecognizerClass:
    """
    A class to hold and register custom Presidio recognizers.
    This class is referenced in the default.yaml.
    """
    
    # Recognizer pour les numéros de registre national belges (BE_NATIONAL_REGISTER_NUMBER)
    belgian_nrn_recognizer = PatternRecognizer(
        entity_name="BE_NATIONAL_REGISTER_NUMBER",
        supported_language="fr",
        patterns=[
            {"name": "NRN_Pattern", "regex": "\\b(?:[0-9]{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12][0-9]|3[01]))-?\\d{3}\\.?\\d{2}\\b", "score": 1.0}
        ],
        context=["registre national", "nrn", "niss", "numéro national"]
    )

    # Recognizer pour les numéros d'entreprise belges (BE_ENTERPRISE_NUMBER)
    belgian_enterprise_recognizer = PatternRecognizer(
        entity_name="BE_ENTERPRISE_NUMBER",
        supported_language="fr",
        patterns=[
            {"name": "BTW_Pattern", "regex": "\\bBE\\s?0\\d{3}[\\.\\s]?\\d{3}[\\.\\s]?\\d{3}\\b", "score": 0.95}
        ],
        context=["entreprise", "btw", "tva", "numéro d'entreprise", "rcs", "kbo"]
    )

    # Recognizer pour les IBAN (qui inclura les IBAN belges)
    iban_recognizer = PatternRecognizer(
        entity_name="IBAN",
        supported_language="fr",
        patterns=[
            {"name": "IBAN_Pattern", "regex": "\\b[A-Z]{2}\\d{2}\\s?(?:[A-Z0-9]{4}\\s?){2,7}[A-Z0-9]{1,4}\\b", "score": 0.95}
        ],
        context=["iban", "compte", "bancaire", "bancaires", "bic", "swift"]
    )

    # Recognizer pour les numéros de téléphone
    phone_recognizer = PatternRecognizer(
        entity_name="PHONE_NUMBER",
        supported_language="fr",
        patterns=[
            {"name": "Phone_Pattern", "regex": "\\b(?:(?:\\+|00)?(?:32|33|352)|0)\\s?[1-9](?:[\\s.-]?\\d{2}){3,4}\\b", "score": 0.8}
        ],
        context=["téléphone", "tel", "mobile", "gsm", "contact"]
    )

    # Recognizer pour les adresses email
    email_recognizer = PatternRecognizer(
        entity_name="EMAIL_ADDRESS",
        supported_language="fr",
        patterns=[
            {"name": "Email_Pattern", "regex": "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b", "score": 1.0}
        ],
        context=["email", "courriel", "adresse électronique"]
    )

    # Recognizer pour les montants monétaires
    money_recognizer = PatternRecognizer(
        entity_name="MONEY",
        supported_language="fr",
        patterns=[
            {"name": "Money_Pattern", "regex": "(?:EUR|€)\\s*\\d{1,3}(?:[.,\\s]\\d{3})*(?:[.,]\\d{2})?|\\d{1,3}(?:[.,\\s]\\d{3})*(?:[.,]\\d{2})?\\s*(?:EUR|€)", "score": 0.85}
        ]
    )

    # La liste des recognizers qui seront exposés par ce module
    # Presidio va les trouver automatiquement s'ils sont des instances de Recognizer
    # et accessibles dans le module spécifié.
    # On met directement les instances de PatternRecognizer ici
    __all__ = [
        "belgian_nrn_recognizer",
        "belgian_enterprise_recognizer",
        "iban_recognizer",
        "phone_recognizer",
        "email_recognizer",
        "money_recognizer"
    ]
