import os
import logging
import yaml
from flask import Flask, request, jsonify, make_response

# Import des classes nécessaires de Presidio
from presidio_analyzer import AnalyzerEngine

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialisation de l'application Flask
app = Flask(__name__)

# --- LAISSER PRESIDIO GÉRER L'INITIALISATION ---
# L'AnalyzerEngine, lorsqu'il est initialisé sans arguments, va automatiquement :
# 1. Chercher la variable d'environnement PRESIDIO_ANALYZER_CONFIG_FILE.
# 2. Lire le fichier de configuration (votre default.yaml).
# 3. Créer et configurer tous les composants (moteur NLP, recognizers, etc.).

analyzer = None
try:
    logger.info("Initializing AnalyzerEngine using configuration from environment variable...")
    analyzer = AnalyzerEngine()
    logger.info("AnalyzerEngine initialized successfully.")
except Exception as e:
    logger.exception("FATAL: Error initializing AnalyzerEngine from configuration.")
    # On s'assure que l'analyzer est None pour que les requêtes échouent proprement
    analyzer = None

@app.route('/analyze', methods=['POST'])
def analyze_text():
    if not analyzer:
        return jsonify({"error": "Analyzer engine not initialized. Check startup logs."}), 500
    
    try:
        data = request.get_json(force=True)
        text_to_analyze = data.get("text", "")
        language = data.get("language", "en")

        if not text_to_analyze:
             return jsonify({"error": "text field is missing or empty"}), 400
        
        # L'allow list est chargée par l'AnalyzerEngine depuis le default.yaml
        results = analyzer.analyze(
            text=text_to_analyze,
            language=language
        )
        
        response_data = [res.to_dict() for res in results]
        return make_response(jsonify(response_data), 200)
    except Exception as e:
        logger.exception("Error during analysis request.")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Pour un test local sans gunicorn
    app.run(host='0.0.0.0', port=5001)
