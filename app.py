import os
import logging
import yaml
from flask import Flask, request, jsonify, make_response

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_analyzer.predefined_recognizers import SpacyRecognizer

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialisation de l'application Flask
app = Flask(__name__)

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
    
    # 3. Créer un registre de recognizers VIDE
    logger.info("Creating a clean RecognizerRegistry...")
    registry = RecognizerRegistry()
    
    # 4. Charger les recognizers personnalisés (définis sous la clé 'recognizers')
    logger.info("Loading custom recognizers from YAML...")
    custom_recognizers_conf = config.get("recognizers", [])
    for recognizer_conf in custom_recognizers_conf:
        patterns = [Pattern(name=p['name'], regex=p['regex'], score=p['score']) for p in recognizer_conf['patterns']]
        custom_recognizer = PatternRecognizer(
            supported_entity=recognizer_conf['entity_name'],
            name=recognizer_conf['name'],
            supported_language=recognizer_conf['supported_language'],
            patterns=patterns,
            context=recognizer_conf.get('context')
        )
        # On ajoute UNIQUEMENT les détecteurs customs définis pour le français
        if recognizer_conf['supported_language'] == 'fr':
            registry.add_recognizer(custom_recognizer)
            logger.info(f"Loaded and registered custom recognizer: {custom_recognizer.name}")

    # 5. Ajouter le SpacyRecognizer, qui est un cas spécial pour les entités de base
    registry.add_recognizer(SpacyRecognizer(supported_language="en"))
    registry.add_recognizer(SpacyRecognizer(supported_language="fr"))
    logger.info("Registered SpacyRecognizer for 'en' and 'fr'.")

    # 6. Créer l'AnalyzerEngine
    logger.info("Initializing AnalyzerEngine with custom components...")
    analyzer = AnalyzerEngine(
        nlp_engine=provider.create_engine(),
        registry=registry,
        supported_languages=config.get("supported_languages", ["en", "fr"])
    )
    analyzer.set_allow_list(config.get("allow_list", []))

    logger.info("--- Presidio Analyzer Service Ready ---")
    logger.info(f"Final supported languages in registry: {registry.supported_languages}")

except Exception as e:
    logger.exception("FATAL: Error during AnalyzerEngine initialization.")
    analyzer = None 

# Le reste du fichier Flask reste identique...
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
