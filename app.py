import os
import logging
import yaml
from flask import Flask, request, jsonify, make_response

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider

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

    # 2. Créer le fournisseur de moteur NLP avec TOUTE la configuration
    logger.info("Creating NLP engine provider...")
    provider = NlpEngineProvider(nlp_configuration=config)
    
    # 3. Créer le registre de recognizers
    logger.info("Creating and populating recognizer registry...")
    registry = RecognizerRegistry()
    # On charge les recognizers par défaut pour les langues supportées
    registry.load_predefined_recognizers(languages=config.get("supported_languages"))
    
    # 4. Charger les recognizers personnalisés depuis la configuration
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
        registry.add_recognizer(custom_recognizer)
        logger.info(f"Loaded custom recognizer: {custom_recognizer.name}")

    # 5. Créer l'AnalyzerEngine avec tous les composants
    logger.info("Initializing AnalyzerEngine with custom components...")
    analyzer = AnalyzerEngine(
        nlp_engine=provider.create_engine(),
        registry=registry,
        supported_languages=config.get("supported_languages")
    )
    logger.info("--- Presidio Analyzer Service Ready ---")

except Exception as e:
    logger.exception("FATAL: Error during AnalyzerEngine initialization.")
    analyzer = None # S'assurer que l'analyzer est None en cas d'échec

@app.route('/analyze', methods=['POST'])
def analyze_text():
    if not analyzer:
        return jsonify({"error": "Analyzer engine is not available. Check startup logs for errors."}), 500
    
    try:
        data = request.get_json(force=True)
        text_to_analyze = data.get("text", "")
        language = data.get("language", "fr") # Mettre 'fr' par défaut

        if not text_to_analyze:
             return jsonify({"error": "text field is missing or empty"}), 400
        
        # L'allow list est chargée directement depuis la configuration de l'Analyzer
        # car c'est une fonctionnalité intégrée.
        results = analyzer.analyze(
            text=text_to_analyze,
            language=language
        )
        
        response_data = [res.to_dict() for res in results]
        return make_response(jsonify(response_data), 200)
    except Exception as e:
        logger.exception(f"Error during analysis request for language '{language}'.")
        # Renvoyer l'erreur spécifique de Presidio si elle est informative
        if "No matching recognizers" in str(e):
             return jsonify({"error": f"No recognizers available for language '{language}'. Please ensure the language model and recognizers are configured."}), 400
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
