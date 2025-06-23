from flask import Flask, request, jsonify, make_response
from presidio_analyzer import AnalyzerEngine
import os
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialisation de l'application Flask
app = Flask(__name__)

# Initialisation du moteur Presidio Analyzer
analyzer = None
try:
    logger.info("Initializing AnalyzerEngine...")
    analyzer = AnalyzerEngine()
    logger.info("AnalyzerEngine initialized successfully.")
    
    # --- CORRECTION ICI ---
    # La ligne de débogage est corrigée ou commentée.
    # On va la commenter pour l'instant car elle n'est pas essentielle au fonctionnement.
    # loaded_recognizers = [r.name for r in analyzer.registry.get_recognizers(language="fr")]
    # logger.info(f"Loaded recognizers for 'fr': {loaded_recognizers}")

except Exception as e:
    # La ligne 'analyzer = None' était déjà là, mais on s'assure qu'elle est bien là.
    analyzer = None
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
    app.run(host='0.0.0.0', port=5001)
