#!/bin/bash
set -e

echo "Running custom entrypoint.sh..."

# Vérifier si default.yaml est lisible (débogage)
echo "Checking default.yaml path and content:"
ls -l /usr/bin/presidio-analyzer/presidio_analyzer/conf/default.yaml
cat /usr/bin/presidio-analyzer/presidio_analyzer/conf/default.yaml

# Vérifier si custom_recognizers est présent (débogage)
echo "Checking custom_recognizers path:"
ls -l /usr/bin/presidio-analyzer/custom_recognizers

# Vérifier PYTHONPATH (débogage)
echo "Current PYTHONPATH: $PYTHONPATH"
export PYTHONPATH="/usr/bin/presidio-analyzer:$PYTHONPATH"
echo "Updated PYTHONPATH: $PYTHONPATH"

# Exécuter le ENTRYPOINT/CMD original de l'image de base.
# C'est la commande magique qui lance réellement Presidio.
# Pour l'image 'mcr.microsoft.com/presidio-analyzer:latest', son ENTRYPOINT est probablement quelque chose comme:
# CMD ["python", "-m", "presidio_analyzer.app", "--host", "0.0.0.0", "--port", "3000"]
# Ou peut-être un script shell interne qui finit par lancer gunicorn.
# La plus simple est de supposer qu'elle a un CMD final qui démarre Gunicorn.

# Pour s'assurer que l'image démarre comme elle le ferait normalement,
# nous allons appeler la CMD par défaut de l'image de base.
# Cela peut varier, mais souvent c'est le CMD spécifié dans le Dockerfile de l'image de base.
# Pour mcr.microsoft.com/presidio-analyzer, c'est probablement gunicorn comme nous l'avons utilisé.
# Si cela ne marche pas, nous devrons essayer 'exec "$@"' pour passer le ENTRYPOINT/CMD original.

# Version 1 : Relancer gunicorn manuellement (si l'image n'a pas un ENTRYPOINT compliqué)
exec gunicorn -w 1 -b 0.0.0.0:3000 presidio_analyzer.app:app

# Version 2 : Si la version 1 échoue, et si l'image de base a un ENTRYPOINT qui attend d'autres commandes.
# exec "$@"
# Ceci exécuterait la CMD qui aurait été définie dans le Dockerfile de l'image de base.
# Si votre Dockerfile.analyzer ne contient pas de CMD, alors "$@" serait vide.
# Dans ce cas, il faudrait remettre un CMD dans votre Dockerfile.analyzer:
# CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:3000", "presidio_analyzer.app:app"]
# Et dans entrypoint.sh: exec "$@"

# Commençons par la Version 1 car c'est la plus simple et la plus directe pour votre cas.
