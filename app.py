import os
import logging
import yaml
from flask import Flask, request, jsonify, make_response

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider
# On importe les classes des détecteurs prédéfinis que l'on veut pouvoir utiliser depuis le YAML
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
    supported_languages = config.get("supported_languages", ["en"])

    # === DÉBUT DE LA CORRECTION MAJEURE ===

    # Étape A: On pré-construit tous les détecteurs personnalisés ("custom") définis dans la section 'recognizers'
    custom_recognizers = {}
    for recognizer_conf in config.get("recognizers", []):
        patterns = [Pattern(name=p['name'], regex=p['regex'], score=p['score']) for p in recognizer_conf['patterns']]
        custom_recognizer = PatternRecognizer(
            supported_entity=recognizer_conf['entity_name'],
            name=recognizer_conf['name'],
            supported_language=recognizer_conf['supported_language'],
            patterns=patterns,
            context=recognizer_conf.get('context')
        )
        custom_recognizers[recognizer_conf['name']] = custom_recognizer
    
    # Étape B: On parcourt la liste 'recognizer_registry' pour activer les détecteurs demandés
    for recognizer_name in config.get("recognizer_registry", []):
        # Cas 1: Le détecteur est dans notre liste de détecteurs personnalisés
        if recognizer_name in custom_recognizers:
            registry.add_recognizer(custom_recognizers[recognizer_name])
            logger.info(f"Loaded custom recognizer from registry list: {recognizer_name}")
        
        # Cas 2: Le détecteur est un détecteur prédéfini connu
        elif recognizer_name in PREDEFINED_RECOGNIZERS_MAP:
            recognizer_class = PREDEFINED_RECOGNIZERS_MAP[recognizer_name]
            # On crée une instance pour chaque langue supportée (en, fr)
            for lang in supported_languages:
                # CORRECTION : On utilise le mot-clé au singulier 'supported_language'
                instance = recognizer_class(supported_language=lang)
                registry.add_recognizer(instance)
            logger.info(f"Loaded predefined recognizer '{recognizer_name}' for languages: {supported_languages}")
        else:
            logger.warning(f"Recognizer '{recognizer_name}' from registry list was not found in custom or predefined lists.")

    # === FIN DE LA CORRECTION MAJEURE ===

    # 4. Créer l'AnalyzerEngine avec tous les composants
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

# Le reste du fichier Flask reste identique...
@app.route('/analyze', methods=['POST'])
def analyze_text():
    if not analyzer:
        return jsonify({"error": "Analyzer engine is not available. Check startup logs for errors."}), 500
    
    try:
        data = request.get_json(force=True)
        text_to_analyze = data.get("text", "")
        default_lang = analyzer.supported_languages[0] if analyzer.supported_languages else "en"
        language = data.get("language", default_lang)

        if not text_to_analyze:
             return jsonify({"error": "text field is missing or empty"}), 400
        
        results = analyzer.analyze(text=text_to_analyze, language=language)
        
        response_data = [res.to_dict() for res in results]
        return make_response(jsonify(response_data), 200)
    except Exception as e:
        logger.exception(f"Error during analysis request for language '{language}'.")
        if "No matching recognizers" in str(e):
             return jsonify({"error": f"No recognizers available for language '{language}'. Please ensure the language model and recognizers are configured."}), 400
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
