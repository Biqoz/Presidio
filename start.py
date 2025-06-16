import os
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import SpacyNlpEngine
from presidio_analyzer.predefined_recognizers import EmailRecognizer, IbanRecognizer, PhoneRecognizer, CreditCardRecognizer, DateRecognizer, UrlRecognizer, IpRecognizer
from presidio_config.custom_recognizers import custom_recognizers as my_custom_rules

# Cette classe est une adaptation pour lancer le serveur Flask de Presidio avec Gunicorn
from gunicorn.app.base import BaseApplication

# 1. Créer le moteur NLP pour le français
nlp_engine = SpacyNlpEngine(models={"fr": "fr_core_news_sm"})

# 2. Créer le registre des règles
registry = RecognizerRegistry()

# 3. Charger les règles par défaut que nous voulons IMPÉRATIVEMENT
# C'est ici que nous forçons le chargement du détecteur d'emails
registry.load_predefined_recognizers(
    languages=["fr"],
    recognizers=[
        EmailRecognizer,
        DateRecognizer,
        PhoneRecognizer,
        UrlRecognizer,
        IpRecognizer,
        CreditCardRecognizer,
    ]
)

# 4. Ajouter nos règles personnalisées par-dessus
registry.add_recognizers(my_custom_rules)

# 5. Créer le moteur d'analyse final avec notre registre personnalisé
analyzer_engine = AnalyzerEngine(nlp_engine=nlp_engine, registry=registry)

# 6. Préparer l'application Flask de Presidio
from presidio_analyzer.main import app
app.config["analyzer_engine"] = analyzer_engine

# 7. Définir une classe pour lancer Gunicorn
class StandaloneApplication(BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

# 8. Point de démarrage du serveur
if __name__ == "__main__":
    options = {
        "bind": "%s:%s" % ("0.0.0.0", "3000"),
        "workers": int(os.environ.get("GUNICORN_WORKERS", "1")),
        "threads": int(os.environ.get("GUNICORN_THREADS", "1")),
    }
    StandaloneApplication(app, options).run()
