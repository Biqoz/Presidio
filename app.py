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
    
    # 3. Créer un registre et le VIDER immédiatement
    logger.info("Creating a new RecognizerRegistry...")
    registry = RecognizerRegistry()
    logger.info(f"Initial registry state supports: {registry.supported_languages}")
    
    # === LA CORRECTION DÉFINITIVE ===
    # On vide la liste interne pour enlever le détecteur anglais par défaut.
    registry.recognizers.clear()
    logger.info(f"Registry cleared. Now supports: {registry.supported_languages}")
    
    # 4. Reconstruire le registre à partir de zéro
    logger.info("Rebuilding registry from scratch...")
    
    # D'abord, ajouter tous vos détecteurs personnalisés (qui sont surtout pour 'fr')
    for recognizer_conf in config.get("recognizers", []):
        patterns = [Pattern(name=p['name'], regex=p['regex'], score=p['score']) for p in recognizer_conf['patterns']]
        registry.add_recognizer(PatternRecognizer(
            supported_entity=recognizer_conf['entity_name'],
            name=recognizer_conf['name'],
            supported_language=recognizer_conf['supported_language'],
            patterns=patterns,
            context=recognizer_conf.get('context')
        ))
        logger.info(f"Added custom recognizer '{recognizer_conf['name']}' for language '{recognizer_conf['supported_language']}'")

    # Ensuite, ajouter le support des entités de base (PERSON, LOC) pour les DEUX langues
    registry.add_recognizer(SpacyRecognizer(supported_language="en"))
    logger.info("Added SpacyRecognizer for 'en'.")
    registry.add_recognizer(SpacyRecognizer(supported_language="fr"))
    logger.info("Added SpacyRecognizer for 'fr'.")

    logger.info(f"Final registry state. Should now support: {registry.supported_languages}")

    # 5. Créer l'AnalyzerEngine avec le registre maintenant cohérent
    logger.info("Initializing AnalyzerEngine...")
    analyzer = AnalyzerEngine(
        nlp_engine=provider.create_engine(),
        registry=registry,
        supported_languages=config.get("supported_languages")
    )
    
    analyzer.set_allow_list(config.get("allow_list", []))

    logger.info("--- Presidio Analyzer Service Ready ---")
    logger.info(f"Final analyzer languages: {analyzer.supported_languages}")


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
