import os
import logging
import yaml
from flask import Flask, request, jsonify, make_response

# Import des classes nécessaires de Presidio
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider

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
except Exception as e:
    logger.exception(f"Could not load or parse configuration file at {CONFIG_FILE_PATH}")
    # En cas d'échec, on continue avec une config vide pour ne pas planter, mais le service sera limité.
    config = {}

# On récupère les langues supportées depuis la config pour les utiliser partout
supported_languages_from_config = config.get("supported_languages", ["en"])
logger.info(f"Languages supported according to config: {supported_languages_from_config}")

# Création du fournisseur de moteur NLP
logger.info("Creating NLP engine provider...")
nlp_engine_provider = NlpEngineProvider(nlp_configuration=config.get("nlp_engine_configuration"))
nlp_engine = nlp_engine_provider.create_engine()
logger.info(f"NLP engine created with models for: {nlp_engine.get_supported_languages()}")

# Création du registre de recognizers
logger.info("Creating and populating recognizer registry...")
registry = RecognizerRegistry()
# On initialise le registre avec TOUTES les langues supportées
registry.load_predefined_recognizers(languages=supported_languages_from_config)

# Ajout des recognizers personnalisés définis dans le YAML
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

# Préparation de l'allow_list (simple liste de mots)
allow_list_config = config.get("allow_list", [])
allow_list_terms = [item if isinstance(item, str) else item.get('text') for item in allow_list_config if item]
if allow_list_terms:
    logger.info(f"Prepared {len(allow_list_terms)} terms for the allow list.")

# Initialisation de l'application Flask
app = Flask(__name__)

# Initialisation du moteur Presidio Analyzer
logger.info("Initializing AnalyzerEngine with custom configuration...")
analyzer = AnalyzerEngine(
    nlp_engine=nlp_engine,
    registry=registry,
    supported_languages=supported_languages_from_config, # On s'assure de la cohérence ici aussi
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
        
        # On passe directement la liste de mots à ignorer au paramètre 'allow_list'
        results = analyzer.analyze(
            text=text_to_analyze,
            language=language,
            allow_list=allow_list_terms
        )
        
        response_data = [res.to_dict() for res in results]
        return make_response(jsonify(response_data), 200)
    except Exception as e:
        logger.exception("Error during analysis.")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
