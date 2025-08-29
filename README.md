# 🦅 Wildvogelhilfen Deutschland - Interaktive Karte

Eine interaktive Webkarte aller Wildvogelhilfen und Auffangstationen in Deutschland mit automatisierten Scraping-Tools für Datenaktualisierung.

## 🎯 Über das Projekt

Diese Webseite bietet eine benutzerfreundliche, interaktive Karte, die alle Wildvogelhilfen in Deutschland anzeigt. Die Daten werden automatisch von verschiedenen Quellen gesammelt:
- [wildvogelhilfe.org](https://wp.wildvogelhilfe.org/auffangstationen/karte-der-auffangstationen/)
- [NABU Google Maps Karte](https://www.google.com/maps/d/viewer?mid=1FtYeDfRtJF_nUIuBt0WQkRnIRM4)

### ✨ Features

- 🗺️ **Interaktive Karte** mit Leaflet.js
- 📍 **Detaillierte Marker** für jede Wildvogelhilfe
- 💬 **Informative Popups** mit Kontaktdaten und E-Mail-Adressen
- 🎨 **Responsive Design** für alle Geräte
- 🤖 **Automatisierte Datensammlung** mit Python-Scripts
- 🌐 **Präzise Geocodierung** über OpenStreetMap Nominatim API

## 🛠️ Technologie

- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Kartenbibliothek**: Leaflet.js
- **Backend**: Python-Scripts für Web-Scraping
- **APIs**: OpenStreetMap Nominatim für Geocodierung
- **Datenformat**: JSON

## 📁 Projektstruktur

```
wvhMap/
├── index.html                     # Hauptseite
├── css/
│   └── style.css                 # Styling
├── js/
│   └── map.js                    # Karten-Logik
├── data/
│   ├── wildvogelhilfen.json      # Stationsdaten (157+ Einträge)
│   └── geocode_cache.json        # Cache für exakte Koordinaten
├── scraper_wildvogelhilfe_org.py # Scraper für wildvogelhilfe.org
├── scraper_nabu_wvh.py          # Scraper für NABU Google Maps
├── fix_coordinates.py           # Geocodierung & Koordinaten-Fix
├── manual_update.py             # Manueller Update-Workflow
├── auto_update_cache.py         # Automatische Cache-Updates
├── requirements.txt             # Python-Abhängigkeiten
└── README.md                    # Diese Datei
```

## 🤖 Automatisierte Datensammlung

### 📋 Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

### 1. Wildvogelhilfe.org Scraper

**Script**: `scraper_wildvogelhilfe_org.py`

Sammelt Daten von allen PLZ-Bereichen der offiziellen Wildvogelhilfe-Website:

```bash
python3 scraper_wildvogelhilfe_org.py
```

**Features:**
- Scannt PLZ-Bereiche 0-9 plus Österreich, Schweiz, Italien
- Extrahiert Namen, Adressen, Telefonnummern, Spezialisierungen
- Generiert deterministische Fallback-Koordinaten basierend auf PLZ
- Erstellt Backup der bestehenden Daten

### 2. NABU Google Maps Scraper

**Script**: `scraper_nabu_wvh.py`

Extrahiert zusätzliche Wildvogelhilfen aus der NABU Google Maps Karte:

```bash
python3 scraper_nabu_wvh.py
```

**Features:**
- Scannt [NABU Google Maps Karte](https://www.google.com/maps/d/viewer?mid=1FtYeDfRtJF_nUIuBt0WQkRnIRM4)
- Extrahiert E-Mail-Adressen und Websites (zusätzlich zu Standarddaten)
- Duplikatserkennung verhindert doppelte Einträge
- Parst JavaScript-Kartendaten direkt aus der Webseite

### 3. Koordinaten-Geocodierung

**Script**: `fix_coordinates.py`

Verbessert die Koordinatengenauigkeit mit der OpenStreetMap Nominatim API:

```bash
# Nur fehlende Koordinaten geocodieren
python3 fix_coordinates.py --geocode --only-missing

# Maximal 50 API-Anfragen für Tests
python3 fix_coordinates.py --geocode --max 50

# Alle Koordinaten neu berechnen (ohne API)
python3 fix_coordinates.py
```

**Features:**
- **Cache-System**: Speichert API-Ergebnisse in `geocode_cache.json`
- **API-Limitierung**: Verhindert Überlastung der Nominatim API
- **Fallback-Koordinaten**: Generiert PLZ-basierte Koordinaten wenn API fehlschlägt
- **Duplikatbereinigung**: Entfernt redundante Informationen automatisch

### 4. Manueller Update-Workflow

**Script**: `manual_update.py`

Kompletter Workflow für Datenaktualisierung:

```bash
python3 manual_update.py
```

**Ablauf:**
1. Führt alle Scraper-Scripts aus
2. Bereinigt und konsolidiert Daten
3. Geocodiert neue Einträge
4. Zeigt Zusammenfassung der Änderungen

## 📊 Datenstruktur

Die Wildvogelhilfe-Daten befinden sich in `data/wildvogelhilfen.json` mit **157+ aktiven Einträgen**.

### JSON-Format

```json
{
  "name": "Name der Einrichtung",
  "specialization": "Spezialisierung (z.B. 'Greifvögel und Eulen')",
  "address": "Vollständige Adresse mit PLZ",
  "phone": "Telefonnummer",
  "email": "E-Mail-Adresse (falls verfügbar)",
  "website": "Website-URL (falls verfügbar)", 
  "note": "Zusätzliche Informationen (falls verfügbar)",
  "plz": "12345",
  "plz_prefix": "1",
  "region": "PLZ 1",
  "country": "Deutschland",
  "latitude": 51.123456,
  "longitude": 10.567890
}
```

### Geocoding-Cache

Exakte Koordinaten werden in `data/geocode_cache.json` gespeichert:

```json
{
  "12345|stadtname|deutschland": [51.123456, 10.567890],
  "67890|anderestadt|deutschland": [52.987654, 11.123456]
}
```

**Cache-Vorteile:**
- ⚡ Schnelle wiederholte Abfragen
- 🌐 Reduziert API-Aufrufe an Nominatim
- 🔄 Konsistente Koordinaten bei mehrfachen Ausführungen

## 🔧 Lokale Entwicklung

```bash
# Repository klonen
git clone https://github.com/USERNAME/wvhMap.git
cd wvhMap

# Python-Abhängigkeiten installieren
pip install -r requirements.txt

# Lokalen Server starten
python3 -m http.server 8000

# Im Browser öffnen
open http://localhost:8000
```

### Entwicklungsworkflow

1. **Daten aktualisieren**:
   ```bash
   # Alle Quellen scrapen
   python3 scraper_wildvogelhilfe_org.py
   python3 scraper_nabu_wvh.py
   
   # Koordinaten verbessern
   python3 fix_coordinates.py --geocode --only-missing --max 20
   ```

2. **Lokale Vorschau**:
   ```bash
   python3 -m http.server 8000
   ```

3. **Datenqualität prüfen**:
   ```bash
   # Anzahl Einträge
   jq length data/wildvogelhilfen.json
   
   # Cache-Größe  
   jq length data/geocode_cache.json
   ```

## � Regelmäßige Updates

### Automatisierte Pipeline

Für regelmäßige Datenaktualisierung kann ein Cron-Job eingerichtet werden:

```bash
#!/bin/bash
# update_data.sh
cd /path/to/wvhMap

# Backup erstellen
cp data/wildvogelhilfen.json "data/backup_$(date +%Y%m%d).json"

# Daten aktualisieren
python3 scraper_wildvogelhilfe_org.py
python3 scraper_nabu_wvh.py

# Neue Einträge geocodieren (max 50 pro Tag wegen API-Limits)
python3 fix_coordinates.py --geocode --only-missing --max 50

echo "Update completed: $(date)"
```

### Monitoring

**Aktuelle Statistiken (Stand: August 2025)**:
- 📍 **157 Wildvogelhilfen** in der Datenbank
- 🏥 **Deutschland**: 110 ursprüngliche + 47 NABU-Einträge  
- 🌍 **International**: Österreich, Schweiz, Italien
- 🎯 **149 exakte Koordinaten** durch Nominatim API
- 📞 **Kontaktdaten**: Telefon, E-Mail, Websites

## 🤝 Beitragen

1. Fork des Projekts erstellen
2. Feature-Branch erstellen (`git checkout -b feature/AmazingFeature`)
3. Änderungen committen (`git commit -m 'Add some AmazingFeature'`)
4. Branch pushen (`git push origin feature/AmazingFeature`)
5. Pull Request erstellen

## 📄 Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe `LICENSE` Datei für Details.

## 🙏 Danksagungen

- [Wildvogelhilfe.org](https://wp.wildvogelhilfe.org/) für die ursprünglichen Daten
- [Leaflet.js](https://leafletjs.com/) für die exzellente Kartenbibliothek
- [OpenStreetMap](https://www.openstreetmap.org/) für die Kartendaten

## 📞 Kontakt

Bei Fragen oder Anregungen können Sie gerne ein Issue erstellen oder einen Pull Request einreichen.

---

**Hinweis**: Diese Karte dient ausschließlich informativen Zwecken. Bitte kontaktieren Sie die jeweiligen Einrichtungen direkt, um aktuelle Informationen zu Öffnungszeiten und Verfügbarkeit zu erhalten.
