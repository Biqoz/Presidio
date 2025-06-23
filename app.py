import os
import logging
from flask import Flask, request, jsonify, make_response

# On importe UNIQUEMENT le Provider, c'est lui qui gère tout.
from presidio_analyzer import AnalyzerEngineProvider

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialisation de l'application Flask
app = Flask(__name__)

# --- Initialisation Globale de l'Analyseur via le Provider ---
analyzer = None
try:
    logger.info("--- Presidio Analyzer Service Starting ---")
    
    # Le chemin vers le fichier de configuration est toujours défini par la variable d'environnement
    CONFIG_FILE_PATH = os.environ.get("PRESIDIO_ANALYZER_CONFIG_FILE", "conf/default.yaml")
    
    # On utilise le Provider pour lire le fichier et créer le moteur
    # C'est la méthode officielle et robuste.
    provider = AnalyzerEngineProvider(analyzer_engine_conf_file=CONFIG_FILE_PATH)
    analyzer = provider.create_engine()
    
    # L'allow_list est aussi gérée par le provider, mais on peut la surcharger si besoin
    # from presidio_analyzer.store import AllowListStore
    # allow_list_store = AllowListStore()
    # allow_list_store.set_allow_list(provider.get_configuration().get("allow_list", []))
    # analyzer.allow_list_store = allow_list_store

    logger.info("--- Presidio Analyzer Service Ready ---")
    logger.info(f"Analyzer created successfully, supporting languages: {analyzer.supported_languages}")

except Exception as e:
    logger.exception("FATAL: Error during AnalyzerEngine initialization.")
    analyzer = None 

# Le reste du fichier Flask est identique
@app.route('/analyze', methods=['POST'])
def analyze_text():
    if not analyzer:
        return jsonify({"error": "Analyzer engine is not available. Check startup logs."}), 500
    
    try:
        data = request.get_json(force=True)
        text_to_analyze = data.get("text", "")
        language = data.get("language", "fr")

        if not text_to_analyze:
             return jsonify({"error": "text field is missing or empty"}), 400
        
        results = analyzer.analyze(
            text=text_to_analyze,
            language=language
        )
        
        response_data = [res.to_dict() for res in results]
        return make_response(jsonify(response_data), 200)

    except Exception as e:
        logger.exception(f"Error during analysis for language '{language}'.")
        if "No matching recognizers" in str(e):
             return jsonify({"error": f"No recognizers available for language '{language}'."}), 400
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
