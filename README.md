# 🦅 Wildvogelhilfen Deutschland - Interaktive Karte

Eine interaktive Webkarte aller Wildvogelhilfen und Auffangstationen in Deutschland.

## 🎯 Über das Projekt

Diese Webseite bietet eine benutzerfreundliche, interaktive Karte, die alle Wildvogelhilfen in Deutschland anzeigt. Die Daten basieren auf den Informationen von [wildvogelhilfe.org](https://wp.wildvogelhilfe.org/auffangstationen/karte-der-auffangstationen/).

### ✨ Features

- 🗺️ **Interaktive Karte** mit Leaflet.js
- 📍 **Detaillierte Marker** für jede Wildvogelhilfe
- 💬 **Informative Popups** mit Kontaktdaten
- 🎨 **Responsive Design** für alle Geräte
- 🚀 **Schnelle Ladezeiten** durch statisches Hosting

## 🛠️ Technologie

- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Kartenbibliothek**: Leaflet.js
- **Hosting**: Netlify
- **Datenformat**: JSON

## 📁 Projektstruktur

```
wvhMap/
├── index.html              # Hauptseite
├── css/
│   └── style.css          # Styling
├── js/
│   └── map.js             # Karten-Logik
├── data/
│   └── wildvogelhilfen.json # Stationsdaten
├── netlify.toml           # Netlify-Konfiguration
└── README.md              # Diese Datei
```

## 🚀 Deployment auf Netlify

### Automatisches Deployment

1. Repository auf GitHub erstellen
2. Bei [Netlify](https://netlify.app) anmelden
3. "New site from Git" wählen
4. GitHub Repository verbinden
5. Build-Einstellungen:
   - **Build command**: (leer lassen)
   - **Publish directory**: `/` (Root-Verzeichnis)

### Manuelles Deployment

1. Projekt-Ordner als ZIP-Datei komprimieren
2. Auf [Netlify](https://netlify.app) ziehen und fallenlassen

## 📊 Datenaktualisierung

Die Wildvogelhilfe-Daten befinden sich in `data/wildvogelhilfen.json`. 

### Datenformat

```json
{
  "name": "Name der Einrichtung",
  "specialization": "Spezialisierung (optional)",
  "address": "Vollständige Adresse",
  "phone": "Telefonnummer",
  "email": "E-Mail-Adresse",
  "latitude": 51.1234,
  "longitude": 10.5678,
  "plz": "12345"
}
```

### Geocoding

Für neue Einträge müssen die Koordinaten (latitude/longitude) hinzugefügt werden. 
Dies kann über verschiedene Geocoding-Services erfolgen:

- [OpenStreetMap Nominatim](https://nominatim.openstreetmap.org/)
- [Google Geocoding API](https://developers.google.com/maps/documentation/geocoding)
- [MapBox Geocoding](https://docs.mapbox.com/api/search/geocoding/)

## 🔧 Lokale Entwicklung

```bash
# Repository klonen
git clone https://github.com/USERNAME/wvhMap.git
cd wvhMap

# Lokalen Server starten (Python)
python -m http.server 8000

# Oder mit Node.js
npx serve .

# Im Browser öffnen
open http://localhost:8000
```

## 📝 Web Scraping Script

Für die Datenextraktion von der Original-Webseite kann ein Python-Script verwendet werden:

```python
# scraper.py (Beispiel-Struktur)
import requests
from bs4 import BeautifulSoup
import json

def scrape_wildvogelhilfen():
    # PLZ-Bereiche 0-9 durchgehen
    stations = []
    for plz_start in range(10):
        url = f"https://wp.wildvogelhilfe.org/auffangstationen/auffangstationen-plz-gebiet-{plz_start}/"
        # Scraping-Logik hier implementieren
        
    return stations

if __name__ == "__main__":
    data = scrape_wildvogelhilfen()
    with open('data/wildvogelhilfen.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
```

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
