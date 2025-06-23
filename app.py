import os
import logging
from flask import Flask, request, jsonify, make_response
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
# 3. Créer le moteur NLP, le registre de recognizers, et charger les recognizers
#    personnalisés et l'allow_list, en s'assurant que les langues sont cohérentes.

try:
    logger.info("Initializing AnalyzerEngine using configuration from environment variable...")
    analyzer = AnalyzerEngine()
    logger.info("AnalyzerEngine initialized successfully.")
    # Pour le débogage, on peut lister les recognizers pour une langue spécifique
    logger.info(f"Loaded recognizers for 'fr': {[rec.name for rec in analyzer.get_recognizers(language='fr')]}")
except Exception as e:
    logger.exception("FATAL: Error initializing AnalyzerEngine from configuration.")
    analyzer = None

@app.route('/analyze', methods=['POST'])
def analyze_text():
    if not analyzer:
        return jsonify({"error": "Analyzer engine not initialized"}), 500
    
    try:
        data = request.get_json(force=True)
        text_to_analyze = data.get("text", "")
        language = data.get("language", "en")

        if not text_to_analyze:
             return jsonify({"error": "text field is missing or empty"}), 400
        
        # On n'a plus besoin de passer l'allow_list ici, l'Analyzer l'a déjà chargée
        results = analyzer.analyze(
            text=text_to_analyze,
            language=language
        )
        
        response_data = [res.to_dict() for res in results]
        return make_response(jsonify(response_data), 200)
    except Exception as e:
        logger.exception("Error during analysis.")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
