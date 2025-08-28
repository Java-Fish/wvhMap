#!/bin/bash
# Automatisches Update-Script für Wildvogelhilfe-Daten und Cache
# Kann als Cron-Job eingerichtet werden

set -e  # Bei Fehlern stoppen

# Verzeichnis des Scripts
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Logging
LOG_FILE="logs/update_$(date +%Y%m%d_%H%M%S).log"
mkdir -p logs

echo "🦅 WILDVOGELHILFE AUTO-UPDATE $(date)" | tee "$LOG_FILE"
echo "===========================================" | tee -a "$LOG_FILE"

# Python-Umgebung aktivieren (falls vorhanden)
if [ -f "venv/bin/activate" ]; then
    echo "🐍 Aktiviere Python Virtual Environment..." | tee -a "$LOG_FILE"
    source venv/bin/activate
fi

# 1. Aktuelle Daten scrapen
echo "📥 Scrape neue Daten von der Website..." | tee -a "$LOG_FILE"
if python scraper.py >> "$LOG_FILE" 2>&1; then
    echo "✅ Scraping erfolgreich" | tee -a "$LOG_FILE"
else
    echo "❌ Scraping fehlgeschlagen" | tee -a "$LOG_FILE"
    exit 1
fi

# 2. Cache automatisch erweitern
echo "🗺️  Erweitere Geocode-Cache..." | tee -a "$LOG_FILE"
if python auto_update_cache.py --max 20 --delay 1.5 >> "$LOG_FILE" 2>&1; then
    echo "✅ Cache-Update erfolgreich" | tee -a "$LOG_FILE"
else
    echo "⚠️  Cache-Update mit Fehlern (fortfahren)" | tee -a "$LOG_FILE"
fi

# 3. Koordinaten korrigieren/ergänzen
echo "📍 Korrigiere fehlende Koordinaten..." | tee -a "$LOG_FILE"
if python fix_coordinates.py --only-missing --max 10 >> "$LOG_FILE" 2>&1; then
    echo "✅ Koordinaten-Korrektur erfolgreich" | tee -a "$LOG_FILE"
else
    echo "⚠️  Koordinaten-Korrektur mit Fehlern (fortfahren)" | tee -a "$LOG_FILE"
fi

# 4. Git-Commit (optional - falls Repository automatisch aktualisiert werden soll)
if command -v git >/dev/null 2>&1 && [ -d ".git" ]; then
    echo "📝 Git-Status prüfen..." | tee -a "$LOG_FILE"
    
    if git diff --quiet && git diff --cached --quiet; then
        echo "ℹ️  Keine Änderungen für Git-Commit" | tee -a "$LOG_FILE"
    else
        echo "💾 Committe Änderungen..." | tee -a "$LOG_FILE"
        git add data/wildvogelhilfen.json data/geocode_cache.json
        git commit -m "Automatisches Update: $(date +%Y-%m-%d)"
        echo "✅ Git-Commit erfolgreich" | tee -a "$LOG_FILE"
        
        # Optional: Push (nur wenn Remote konfiguriert)
        if git remote get-url origin >/dev/null 2>&1; then
            echo "📤 Push zu Remote Repository..." | tee -a "$LOG_FILE"
            if git push; then
                echo "✅ Git-Push erfolgreich" | tee -a "$LOG_FILE"
            else
                echo "⚠️  Git-Push fehlgeschlagen" | tee -a "$LOG_FILE"
            fi
        fi
    fi
fi

# 5. Statistiken
echo "" | tee -a "$LOG_FILE"
echo "📊 FINAL-STATISTIKEN:" | tee -a "$LOG_FILE"

# Anzahl Stationen
if [ -f "data/wildvogelhilfen.json" ]; then
    STATION_COUNT=$(python -c "import json; print(len(json.load(open('data/wildvogelhilfen.json'))))")
    echo "   📍 $STATION_COUNT Wildvogelhilfe-Stationen" | tee -a "$LOG_FILE"
fi

# Cache-Größe
if [ -f "data/geocode_cache.json" ]; then
    CACHE_COUNT=$(python -c "import json; print(len(json.load(open('data/geocode_cache.json'))))")
    echo "   🗺️  $CACHE_COUNT Geocode-Cache-Einträge" | tee -a "$LOG_FILE"
fi

echo "🎉 AUTO-UPDATE ABGESCHLOSSEN: $(date)" | tee -a "$LOG_FILE"

# Alte Logs aufräumen (behalte nur die letzten 10)
find logs -name "update_*.log" -type f | sort | head -n -10 | xargs rm -f 2>/dev/null || true
