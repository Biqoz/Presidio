from flask import Flask, request, jsonify, make_response
from presidio_analyzer import AnalyzerEngine
import os
import logging

# Configuration du logging pour un meilleur débogage
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialisation de l'application Flask
app = Flask(__name__)

# Initialisation du moteur Presidio Analyzer
analyzer = None
try:
    logger.info("Initializing AnalyzerEngine...")
    # L'AnalyzerEngine va chercher la configuration via la variable d'environnement
    analyzer = AnalyzerEngine()
    logger.info("AnalyzerEngine initialized successfully.")
    # Affiche les recognizers chargés pour confirmer que la config est bien lue
    loaded_recognizers = [r.name for r in analyzer.registry.get_recognizers()]
    logger.info(f"Loaded recognizers: {loaded_recognizers}")
except Exception as e:
    logger.exception("FATAL: Error initializing AnalyzerEngine.")

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
        
        results = analyzer.analyze(text=text_to_analyze, language=language)
        response_data = [res.to_dict() for res in results]
        
        return make_response(jsonify(response_data), 200)
    except Exception as e:
        logger.exception("Error during analysis.")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Pour un test local sans gunicorn
    app.run(host='0.0.0.0', port=5001)
