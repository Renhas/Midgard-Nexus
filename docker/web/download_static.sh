#!/bin/bash
set -e

if [ -d "/app/src/static" ]; then
    # Запуск внутри Docker-контейнера (образ собран с /app/src)
    BASE_DIR="/app"
    echo "🔧 Running inside Docker"
else
    # Запуск локально, из корня проекта (там где лежит src/)
    BASE_DIR="."
    echo "🔧 Running locally"
fi

VENDOR_DIR="$BASE_DIR/src/static/vendor"
BOOTSTRAP_ICONS_VERSION="1.13.1"
LUCIDE_VERSION="latest"

mkdir -p "$VENDOR_DIR/bootstrap/css" "$VENDOR_DIR/bootstrap/js" \
         "$VENDOR_DIR/bootstrap/css/fonts" \
         "$VENDOR_DIR/lucide/css" "$VENDOR_DIR/lucide/fonts" \
         "$VENDOR_DIR/htmx" "$VENDOR_DIR/alpine" \
         "$VENDOR_DIR/chart" "$VENDOR_DIR/wordcloud" \
         "$VENDOR_DIR/sortable"

echo "Скачивание библиотек..."
echo "Bootstrap"
curl -L -o "$VENDOR_DIR/bootstrap/css/bootstrap.min.css" \
    https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css
echo "Bootstrap Icons"
curl -L -o "$VENDOR_DIR/bootstrap/css/bootstrap-icons.css" \
    https://cdn.jsdelivr.net/npm/bootstrap-icons@${BOOTSTRAP_ICONS_VERSION}/font/bootstrap-icons.css

curl -L -o "$VENDOR_DIR/bootstrap/css/fonts/bootstrap-icons.woff2" \
    "https://cdn.jsdelivr.net/npm/bootstrap-icons@${BOOTSTRAP_ICONS_VERSION}/font/fonts/bootstrap-icons.woff2"

curl -L -o "$VENDOR_DIR/bootstrap/css/fonts/bootstrap-icons.woff" \
    "https://cdn.jsdelivr.net/npm/bootstrap-icons@${BOOTSTRAP_ICONS_VERSION}/font/fonts/bootstrap-icons.woff"

curl -L -o "$VENDOR_DIR/bootstrap/js/bootstrap.bundle.min.js" \
    https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js
echo "Licude Icons"
curl -L -o "$VENDOR_DIR/lucide/css/lucide.min.css" \
    "https://cdn.jsdelivr.net/npm/lucide-static@${LUCIDE_VERSION}/font/lucide.min.css"

curl -L -o "$VENDOR_DIR/lucide/css/lucide.woff2" \
    "https://cdn.jsdelivr.net/npm/lucide-static@${LUCIDE_VERSION}/font/lucide.woff2"

curl -L -o "$VENDOR_DIR/lucide/css/lucide.woff" \
    "https://cdn.jsdelivr.net/npm/lucide-static@${LUCIDE_VERSION}/font/lucide.woff"
echo "HTMX"
curl -L -o "$VENDOR_DIR/htmx/htmx.min.js" \
    https://unpkg.com/htmx.org@1.9.10/dist/htmx.min.js
echo "Alpine"
curl -L -o "$VENDOR_DIR/alpine/alpine.min.js" \
    https://unpkg.com/alpinejs@3.14.1/dist/cdn.min.js
echo "Chart"
curl -L -o "$VENDOR_DIR/chart/chart.min.js" \
    https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js
echo "Chart WordCloud"
curl -L -o "$VENDOR_DIR/wordcloud/chartjs-chart-wordcloud.min.js" \
    https://cdn.jsdelivr.net/npm/chartjs-chart-wordcloud@4.4.5/build/index.umd.min.js
echo "Sortable"
curl -L -o "$VENDOR_DIR/sortable/Sortable.min.js" \
    https://cdn.jsdelivr.net/npm/sortablejs@1.15.2/Sortable.min.js

echo "✅ Static libraries downloaded to $VENDOR_DIR"
