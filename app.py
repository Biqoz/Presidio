import os
import logging
import yaml
from flask import Flask, request, jsonify, make_response

# Import des classes nécessaires de Presidio
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_analyzer.recognizer_registry.recognizer_registry import RecognizerRegistry
from presidio_analyzer.recognizer_registry.deny_list_recognizer import DenyListRecognizer

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CHARGEMENT MANUEL ET EXPLICITE DE LA CONFIGURATION ---
CONFIG_FILE_PATH = os.environ.get("PRESIDIO_ANALYZER_CONFIG_FILE", "conf/default.yaml")
logger.info(f"Loading configuration from: {CONFIG_FILE_PATH}")

config = {}
try:
    with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    logger.info("Configuration file loaded successfully.")
except FileNotFoundError:
    logger.error(f"Configuration file not found at {CONFIG_FILE_PATH}. Using default empty config.")
except yaml.YAMLError as e:
    logger.error(f"Error parsing YAML configuration file: {e}. Using default empty config.")

# Création du fournisseur de moteur NLP
logger.info("Creating NLP engine provider...")
nlp_engine_provider = NlpEngineProvider(nlp_configuration=config.get("nlp_engine_configuration"))
nlp_engine = nlp_engine_provider.create_engine()
logger.info(f"NLP engine created with models for: {nlp_engine.get_supported_languages()}")

# Création du registre de recognizers
logger.info("Creating and populating recognizer registry...")
registry = RecognizerRegistry()
registry.load_predefined_recognizers(languages=config.get("supported_languages", ["en"]))

# Ajout des recognizers personnalisés définis dans le YAML
custom_recognizers_conf = config.get("recognizers", [])
for recognizer_conf in custom_recognizers_conf:
    patterns = [Pattern(name=p['name'], regex=p['regex'], score=p['score']) for p in recognizer_conf['patterns']]
    
    # On crée une instance de PatternRecognizer
    custom_recognizer = PatternRecognizer(
        supported_entity=recognizer_conf['entity_name'],
        name=recognizer_conf['name'],
        supported_language=recognizer_conf['supported_language'],
        patterns=patterns,
        context=recognizer_conf.get('context')
    )
    
    # --- CORRECTION DE LA LIGNE D'ERREUR ---
    # La méthode correcte est 'add_recognizer', pas 'add_pattern_recognizer'
    registry.add_recognizer(custom_recognizer)
    logger.info(f"Loaded custom recognizer: {custom_recognizer.name}")


# Ajout de l'allow_list (DenyListRecognizer)
allow_list_terms = [item['text'] for item in config.get("allow_list", []) if isinstance(item, dict) and 'text' in item]
if allow_list_terms:
    deny_list_recognizer = DenyListRecognizer(supported_entity="GENERIC_PII", deny_list=allow_list_terms)
    registry.add_recognizer(deny_list_recognizer)
    logger.info(f"Loaded {len(allow_list_terms)} terms into the allow list (as a deny list recognizer).")

# Initialisation de l'application Flask
app = Flask(__name__)

# Initialisation du moteur Presidio Analyzer avec nos composants créés
logger.info("Initializing AnalyzerEngine with custom configuration...")
analyzer = AnalyzerEngine(
    nlp_engine=nlp_engine,
    registry=registry,
    supported_languages=config.get("supported_languages", ["en"]),
    default_score_threshold=config.get("ner_model_configuration", {}).get("confidence_threshold", {}).get("default", 0.35)
)
logger.info("AnalyzerEngine initialized successfully.")

@app.route('/analyze', methods=['POST'])
def analyze_text():
    try:
        data = request.get_json(force=True)
        text_to_analyze = data.get("text", "")
        language = data.get("language", "en")

        if not text_to_analyze:
             return jsonify({"error": "text field is missing or empty"}), 400
        
        results = analyzer.analyze(text=text_to_analyze, language=language)
        response_data = [res.to_dict() for res in results]
        return make_response(jsonify(response_data), 200)
    except Exception as e:
        logger.exception("Error during analysis.")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
