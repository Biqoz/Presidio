import os
import logging
import yaml
from flask import Flask, request, jsonify, make_response

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_analyzer.predefined_recognizers import (
    CreditCardRecognizer, CryptoRecognizer, DateRecognizer, IpRecognizer,
    MedicalLicenseRecognizer, UrlRecognizer, SpacyRecognizer
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

PREDEFINED_RECOGNIZERS_MAP = {
    "SpacyRecognizer": SpacyRecognizer,
    "CreditCardRecognizer": CreditCardRecognizer,
    "CryptoRecognizer": CryptoRecognizer,
    "DateRecognizer": DateRecognizer,
    "IpRecognizer": IpRecognizer,
    "MedicalLicenseRecognizer": MedicalLicenseRecognizer,
    "UrlRecognizer": UrlRecognizer,
}

analyzer = None
try:
    logger.info("--- Presidio Analyzer Service Starting ---")
    
    CONFIG_FILE_PATH = os.environ.get("PRESIDIO_ANALYZER_CONFIG_FILE", "conf/default.yaml")
    logger.info(f"Loading configuration from: {CONFIG_FILE_PATH}")
    with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    logger.info("Configuration file loaded successfully.")

    logger.info("Creating NLP engine provider...")
    provider = NlpEngineProvider(nlp_configuration=config)
    
    logger.info("Creating and populating recognizer registry from config file...")
    registry = RecognizerRegistry()
    
    # === CORRECTION DÉFINITIVE : ASSURER UN REGISTRE PROPRE ===
    logger.info("Removing any default recognizers to ensure a clean slate...")
    registry.remove_all_recognizers()
    
    supported_languages = config.get("supported_languages", ["en"])

    # Construire les détecteurs personnalisés
    custom_recognizers = {}
    for recognizer_conf in config.get("recognizers", []):
        patterns = [Pattern(name=p['name'], regex=p['regex'], score=p['score']) for p in recognizer_conf['patterns']]
        custom_recognizers[recognizer_conf['name']] = PatternRecognizer(
            supported_entity=recognizer_conf['entity_name'],
            name=recognizer_conf['name'],
            supported_language=recognizer_conf['supported_language'],
            patterns=patterns,
            context=recognizer_conf.get('context')
        )
    
    # Activer les détecteurs listés dans la configuration
    for recognizer_name in config.get("recognizer_registry", []):
        if recognizer_name in custom_recognizers:
            registry.add_recognizer(custom_recognizers[recognizer_name])
            logger.info(f"Loaded CUSTOM recognizer: {recognizer_name}")
        
        elif recognizer_name in PREDEFINED_RECOGNIZERS_MAP:
            recognizer_class = PREDEFINED_RECOGNIZERS_MAP[recognizer_name]
            for lang in supported_languages:
                # Le SpacyRecognizer est un cas spécial, il n'a pas de paramètre de langue
                if recognizer_class == SpacyRecognizer:
                    if 'SpacyRecognizer_added' not in locals(): # Pour ne l'ajouter qu'une seule fois
                       registry.add_recognizer(recognizer_class(supported_entities=config.get("spacy_entities", [])))
                       logger.info(f"Loaded PREDEFINED singleton recognizer: {recognizer_name}")
                       SpacyRecognizer_added = True
                else:
                    instance = recognizer_class(supported_language=lang)
                    registry.add_recognizer(instance)
            if recognizer_class != SpacyRecognizer:
                logger.info(f"Loaded PREDEFINED recognizer '{recognizer_name}' for languages: {supported_languages}")

        else:
            logger.warning(f"Recognizer '{recognizer_name}' from registry list was not found.")


    logger.info("Initializing AnalyzerEngine with custom components...")
    analyzer = AnalyzerEngine(
        nlp_engine=provider.create_engine(),
        registry=registry,
        supported_languages=supported_languages
    )
    analyzer.set_allow_list(config.get("allow_list", []))

    logger.info("--- Presidio Analyzer Service Ready ---")

except Exception as e:
    logger.exception("FATAL: Error during AnalyzerEngine initialization.")
    analyzer = None 

# Le reste du fichier Flask est identique
@app.route('/analyze', methods=['POST'])
def analyze_text():
    if not analyzer: return jsonify({"error": "Analyzer engine is not available."}), 500
    try:
        data = request.get_json(force=True)
        text = data.get("text", "")
        lang = data.get("language", "fr")
        if not text: return jsonify({"error": "text field is missing"}), 400
        results = analyzer.analyze(text=text, language=lang)
        return make_response(jsonify([res.to_dict() for res in results]), 200)
    except Exception as e:
        logger.exception("Error during analysis request.")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
