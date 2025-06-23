#!/bin/bash
set -e

echo "Running debug entrypoint.sh..."

# Trouver où le package presidio-analyzer est réellement installé par pip
echo "--- Finding presidio-analyzer package location ---"
pip show presidio-analyzer

# Lister le contenu du répertoire 'Location' trouvé ci-dessus
# Vous devrez copier-coller le chemin de 'Location:' dans la commande 'ls' manuellement si nécessaire
# Mais on peut aussi essayer de le faire dynamiquement
LOCATION=$(pip show presidio-analyzer | grep Location | awk '{print $2}')
echo "Presidio-analyzer is at: $LOCATION"

echo "--- Listing files in the presidio-analyzer package ---"
ls -l "$LOCATION/presidio_analyzer"

echo "--- Checking for app.py in the presidio-analyzer package ---"
ls -l "$LOCATION/presidio_analyzer/app.py"

echo "--- Listing content of 'conf' directory ---"
ls -l "$LOCATION/presidio_analyzer/conf/"

echo "Debug session started. The container will stay alive. Connect via Coolify terminal."
# Garder le conteneur en vie indéfiniment
while true; do
  sleep 3600;
done
