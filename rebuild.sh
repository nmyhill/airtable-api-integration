#!/usr/bin/env bash
set -euo pipefail

echo "▶ Rebuild started"

# 0) Load local secrets from .env (if present)
if [ -f ./.env ]; then
  echo "• Loading .env"
  set -a
  . ./.env
  set +a
fi

# 1) Export Airtable data → data/nodes.csv + data/edges.csv
echo "• Running Python exporter"
python3 generate_visnetwork_assets.py

# 2) Ensure required R packages are installed
echo "• Ensuring R packages"
Rscript viz/install.R || { echo "❌ R package install failed"; exit 1; }

# 3) Build visualization → index.html
echo "• Building visualization"
Rscript "viz/Network diagram.R" || { echo "❌ R visualization build failed"; exit 1; }

echo "✅ Done. Updated: index.html and data/{nodes.csv,edges.csv}"
