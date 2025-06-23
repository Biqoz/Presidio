import os
import logging
import yaml
from flask import Flask, request, jsonify, make_response

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider
# On importe les recognizers prédéfinis qu'on veut pouvoir utiliser
from presidio_analyzer.predefined_recognizers import (
    CreditCardRecognizer, CryptoRecognizer, DateRecognizer, IpRecognizer,
    MedicalLicenseRecognizer, UrlRecognizer, SpacyRecognizer
)

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialisation de l'application Flask
app = Flask(__name__)

# --- Dictionnaire pour mapper les noms du YAML aux classes Python ---
# C'est ce qui nous permet de lire la liste 'recognizer_registry' du YAML
PREDEFINED_RECOGNIZERS_MAP = {
    "SpacyRecognizer": SpacyRecognizer,
    "CreditCardRecognizer": CreditCardRecognizer,
    "CryptoRecognizer": CryptoRecognizer,
    "DateRecognizer": DateRecognizer,
    "IpRecognizer": IpRecognizer,
    "MedicalLicenseRecognizer": MedicalLicenseRecognizer,
    "UrlRecognizer": UrlRecognizer,
}


# --- Initialisation Globale de l'Analyseur ---
analyzer = None
try:
    logger.info("--- Presidio Analyzer Service Starting ---")
    
    # 1. Charger la configuration depuis le fichier YAML
    CONFIG_FILE_PATH = os.environ.get("PRESIDIO_ANALYZER_CONFIG_FILE", "conf/default.yaml")
    logger.info(f"Loading configuration from: {CONFIG_FILE_PATH}")
    with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    logger.info("Configuration file loaded successfully.")

    # 2. Créer le fournisseur de moteur NLP
    logger.info("Creating NLP engine provider...")
    provider = NlpEngineProvider(nlp_configuration=config)
    
    # 3. Créer le registre de recognizers EN SUIVANT LE YAML
    logger.info("Creating and populating recognizer registry from config file...")
    registry = RecognizerRegistry()

    # === DÉBUT DE LA CORRECTION MAJEURE ===

    # A) Charger les recognizers PRÉDÉFINIS listés dans le YAML
    supported_languages = config.get("supported_languages", ["en"])
    for recognizer_name in config.get("recognizer_registry", []):
        if recognizer_name in PREDEFINED_RECOGNIZERS_MAP:
            recognizer_class = PREDEFINED_RECOGNIZERS_MAP[recognizer_name]
            # On passe les langues supportées à chaque recognizer qu'on instancie
            registry.add_recognizer(recognizer_class(supported_languages=supported_languages))
            logger.info(f"Loaded predefined recognizer: {recognizer_name}")

    # B) Charger les recognizers PERSONNALISÉS définis dans le YAML
    custom_recognizers_conf = config.get("recognizers", [])
    for recognizer_conf in custom_recognizers_conf:
        patterns = [Pattern(name=p['name'], regex=p['regex'], score=p['score']) for p in recognizer_conf['patterns']]
        # On s'assure de ne pas recréer un recognizer prédéfini mais bien un custom
        custom_recognizer = PatternRecognizer(
            supported_entity=recognizer_conf['entity_name'],
            name=recognizer_conf['name'],
            supported_language=recognizer_conf['supported_language'],
            patterns=patterns,
            context=recognizer_conf.get('context')
        )
        registry.add_recognizer(custom_recognizer)
        logger.info(f"Loaded custom recognizer from YAML: {custom_recognizer.name}")

    # === FIN DE LA CORRECTION MAJEURE ===

    # 4. Créer l'AnalyzerEngine avec tous les composants
    logger.info("Initializing AnalyzerEngine with custom components...")
    analyzer = AnalyzerEngine(
        nlp_engine=provider.create_engine(),
        registry=registry,
        supported_languages=supported_languages
    )
    # L'allow list est chargée automatiquement par l'AnalyzerEngine
    analyzer.set_allow_list(config.get("allow_list", []))

    logger.info("--- Presidio Analyzer Service Ready ---")

except Exception as e:
    logger.exception("FATAL: Error during AnalyzerEngine initialization.")
    analyzer = None 

@app.route('/analyze', methods=['POST'])
def analyze_text():
    if not analyzer:
        return jsonify({"error": "Analyzer engine is not available. Check startup logs for errors."}), 500
    
    try:
        data = request.get_json(force=True)
        text_to_analyze = data.get("text", "")
        # Utiliser la première langue supportée comme langue par défaut si non fournie
        default_lang = analyzer.supported_languages[0] if analyzer.supported_languages else "en"
        language = data.get("language", default_lang)

        if not text_to_analyze:
             return jsonify({"error": "text field is missing or empty"}), 400
        
        results = analyzer.analyze(
            text=text_to_analyze,
            language=language
        )
        
        response_data = [res.to_dict() for res in results]
        return make_response(jsonify(response_data), 200)
    except Exception as e:
        logger.exception(f"Error during analysis request for language '{language}'.")
        if "No matching recognizers" in str(e):
             return jsonify({"error": f"No recognizers available for language '{language}'. Please ensure the language model and recognizers are configured."}), 400
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
