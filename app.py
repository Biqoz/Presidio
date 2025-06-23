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
    
    # 1. Charger la configuration
    CONFIG_FILE_PATH = os.environ.get("PRESIDIO_ANALYZER_CONFIG_FILE", "conf/default.yaml")
    logger.info(f"Loading configuration from: {CONFIG_FILE_PATH}")
    with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    logger.info("Configuration file loaded successfully.")

    # 2. Créer le fournisseur de moteur NLP
    logger.info("Creating NLP engine provider...")
    provider = NlpEngineProvider(nlp_configuration=config)
    
    # 3. Créer et VIDER le registre pour garantir une base saine
    logger.info("Creating a new RecognizerRegistry...")
    registry = RecognizerRegistry()
    logger.info(f"Initial registry state supports: {registry.supported_languages}")
    
    # === CORRECTION DÉFINITIVE : VIDER LE REGISTRE ===
    registry.recognizers.clear()
    logger.info(f"Registry cleared. Now supports: {registry.supported_languages}")
    
    # 4. Ajouter les détecteurs requis
    # Ajouter les détecteurs personnalisés pour le français
    for recognizer_conf in config.get("recognizers", []):
        patterns = [Pattern(name=p['name'], regex=p['regex'], score=p['score']) for p in recognizer_conf['patterns']]
        registry.add_recognizer(PatternRecognizer(
            supported_entity=recognizer_conf['entity_name'],
            name=recognizer_conf['name'],
            supported_language=recognizer_conf['supported_language'],
            patterns=patterns,
            context=recognizer_conf.get('context')
        ))
        logger.info(f"Added custom recognizer: {recognizer_conf['name']}")

    # Ajouter le support des entités de base (PERSON, LOC) pour les deux langues
    registry.add_recognizer(SpacyRecognizer(supported_language="en"))
    registry.add_recognizer(SpacyRecognizer(supported_language="fr"))
    logger.info("Added SpacyRecognizer for 'en' and 'fr'.")

    logger.info(f"Final registry state. Now supports: {registry.supported_languages}")

    # 5. Créer l'AnalyzerEngine
    logger.info("Initializing AnalyzerEngine...")
    analyzer = AnalyzerEngine(
        nlp_engine=provider.create_engine(),
        registry=registry,
        supported_languages=config.get("supported_languages")
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
