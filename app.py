import os
import logging
import yaml
from flask import Flask, request, jsonify, make_response

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider

# Configuration du logging pour un meilleur débogage
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CHARGEMENT MANUEL ET EXPLICITE DE LA CONFIGURATION ---

# Chemin vers le fichier de configuration, défini par la variable d'environnement
CONFIG_FILE_PATH = os.environ.get("PRESIDIO_ANALYZER_CONFIG_FILE", "conf/default.yaml")
logger.info(f"Loading configuration from: {CONFIG_FILE_PATH}")

try:
    with open(CONFIG_FILE_PATH, 'r') as f:
        config = yaml.safe_load(f)
    logger.info("Configuration file loaded successfully.")
except FileNotFoundError:
    logger.error(f"Configuration file not found at {CONFIG_FILE_PATH}. Exiting.")
    config = {}
except yaml.YAMLError as e:
    logger.error(f"Error parsing YAML configuration file: {e}. Exiting.")
    config = {}

# Création du fournisseur de moteur NLP basé sur la configuration
logger.info("Creating NLP engine provider...")
nlp_engine_provider = NlpEngineProvider(nlp_configuration=config.get("nlp_engine_configuration"))
nlp_engine = nlp_engine_provider.create_engine()
logger.info(f"NLP engine created with models for: {nlp_engine.get_supported_languages()}")

# Création du registre de recognizers basé sur la configuration
logger.info("Creating and populating recognizer registry...")
registry = RecognizerRegistry()
registry.load_predefined_recognizers(languages=config.get("supported_languages", ["en"]))

# Ajout des recognizers personnalisés définis dans le YAML
custom_recognizers_conf = config.get("recognizers", [])
for recognizer_conf in custom_recognizers_conf:
    registry.add_pattern_recognizer(
        name=recognizer_conf['name'],
        patterns=recognizer_conf['patterns'],
        context=recognizer_conf.get('context'),
        supported_language=recognizer_conf['supported_language'],
        supported_entity=recognizer_conf['entity_name']
    )
    logger.info(f"Loaded custom recognizer: {recognizer_conf['name']}")

# --- FIN DU CHARGEMENT DE LA CONFIGURATION ---

# Initialisation de l'application Flask
app = Flask(__name__)

# Initialisation du moteur Presidio Analyzer avec les composants que nous avons créés
logger.info("Initializing AnalyzerEngine with custom configuration...")
analyzer = AnalyzerEngine(
    nlp_engine=nlp_engine,
    registry=registry,
    supported_languages=config.get("supported_languages", ["en"])
)

# On ajoute l'allow_list manuellement
allow_list = config.get("allow_list", [])
if allow_list:
    registry.add_recognizer(DenyListRecognizer(supported_entity="GENERIC_PII", deny_list=allow_list))
    logger.info(f"Loaded {len(allow_list)} terms into the allow list (deny list recognizer).")

logger.info("AnalyzerEngine initialized successfully.")

@app.route('/analyze', methods=['POST'])
def analyze_text():
    try:
        data = request.get_json(force=True)
        text_to_analyze = data.get("text", "")
        language = data.get("language", "en")

        if not text_to_analyze:
             return jsonify({"error": "text field is missing or empty"}), 400
        
        # Le seuil de confiance est appliqué ici, à la volée
        score_threshold = data.get("score_threshold", config.get("ner_model_configuration", {}).get("confidence_threshold", {}).get("default", 0.35))
        
        results = analyzer.analyze(
            text=text_to_analyze,
            language=language,
            score_threshold=score_threshold,
            allow_list=allow_list # On passe la allow list ici aussi
        )
        
        response_data = [res.to_dict() for res in results]
        return make_response(jsonify(response_data), 200)
    except Exception as e:
        logger.exception("Error during analysis.")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
