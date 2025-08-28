// Wildvogelhilfe Karte - Hauptskript
class WildvogelhilfeMap {
    constructor() {
        this.map = null;
        this.markers = [];
        this.stations = [];
        this.init();
    }

    async init() {
        this.initMap();
        await this.loadStations();
        this.addMarkersToMap();
        this.updateStats();
    }

    initMap() {
        // Karte auf Deutschland zentrieren
        this.map = L.map('map').setView([51.1657, 10.4515], 6);

        // OpenStreetMap Tiles hinzufügen
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 18
        }).addTo(this.map);

        // Benutzerdefinierte Icons
        this.createCustomIcons();
    }

    createCustomIcons() {
        // Standard Icon für Wildvogelhilfen
        this.defaultIcon = L.divIcon({
            className: 'custom-marker',
            html: `<div style="
                background-color: #4a7c59;
                width: 20px;
                height: 20px;
                border-radius: 50%;
                border: 3px solid white;
                box-shadow: 0 2px 5px rgba(0,0,0,0.3);
            "></div>`,
            iconSize: [26, 26],
            iconAnchor: [13, 13]
        });

        // Spezielles Icon für Greifvogel-Spezialisten
        this.greifvogelIcon = L.divIcon({
            className: 'custom-marker-greifvogel',
            html: `<div style="
                background-color: #8B4513;
                width: 20px;
                height: 20px;
                border-radius: 50%;
                border: 3px solid white;
                box-shadow: 0 2px 5px rgba(0,0,0,0.3);
            "></div>`,
            iconSize: [26, 26],
            iconAnchor: [13, 13]
        });
    }

    async loadStations() {
        try {
            console.log('🔄 Lade Stationen aus JSON-Datei...');
            const response = await fetch('data/wildvogelhilfen.json');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            this.stations = await response.json();
            console.log(`✅ ${this.stations.length} Stationen erfolgreich geladen`);
            
            // Validierung der Daten
            if (!Array.isArray(this.stations) || this.stations.length === 0) {
                throw new Error('Keine gültigen Stationsdaten gefunden');
            }
        } catch (error) {
            console.error('❌ Fehler beim Laden der Stationen:', error);
            this.showError(`Fehler beim Laden: ${error.message}`);
            // Fallback: Demo-Daten verwenden
            console.log('🔄 Verwende Demo-Daten als Fallback');
            this.loadDemoData();
        }
    }

    loadDemoData() {
        // Demo-Daten basierend auf dem Beispiel aus der Anfrage
        this.stations = [
            {
                name: "Greifvogelhilfe Sachsen e. V.",
                specialization: "Spezialisiert auf Greifvögel",
                address: "Nordstraße 4, 01689 Weinböhla",
                phone: "0171/26 45 180",
                email: "info@greifvogelhilfe-sachsen.de",
                latitude: 51.3167,
                longitude: 13.5833,
                plz: "01689"
            },
            {
                name: "Wildvogelhilfe Berlin",
                specialization: "Alle Wildvogelarten",
                address: "Musterstraße 10, 10115 Berlin",
                phone: "030/12345678",
                email: "info@wildvogelhilfe-berlin.de",
                latitude: 52.5200,
                longitude: 13.4050,
                plz: "10115"
            },
            {
                name: "Vogelschutz München",
                specialization: "Singvögel und Wasservögel",
                address: "Beispielweg 5, 80331 München",
                phone: "089/987654321",
                email: "kontakt@vogelschutz-muenchen.de",
                latitude: 48.1351,
                longitude: 11.5820,
                plz: "80331"
            }
        ];
    }

    addMarkersToMap() {
        this.stations.forEach(station => {
            // Icon basierend auf Spezialisierung wählen
            const icon = this.getIconForStation(station);
            
            // Marker erstellen
            const marker = L.marker([station.latitude, station.longitude], {
                icon: icon
            }).addTo(this.map);

            // Popup-Inhalt erstellen
            const popupContent = this.createPopupContent(station);
            marker.bindPopup(popupContent);

            // Marker zur Liste hinzufügen
            this.markers.push(marker);
        });

        // Karte so zoomen, dass alle Marker sichtbar sind
        if (this.markers.length > 0) {
            const group = new L.featureGroup(this.markers);
            this.map.fitBounds(group.getBounds().pad(0.1));
        }
    }

    getIconForStation(station) {
        // Prüfen ob es sich um eine Greifvogel-Spezialisierung handelt
        if (station.specialization && 
            station.specialization.toLowerCase().includes('greifvogel')) {
            return this.greifvogelIcon;
        }
        return this.defaultIcon;
    }

    createPopupContent(station) {
        let content = `<div class="popup-content">`;
        content += `<h4>${station.name}</h4>`;
        
        if (station.specialization) {
            content += `<div class="specialization">${station.specialization}</div>`;
        }
        
        content += `<div class="address">${station.address}</div>`;
        
        content += `<div class="contact">`;
        if (station.phone) {
            content += `<strong>Tel:</strong> <a href="tel:${station.phone.replace(/\s/g, '')}">${station.phone}</a><br>`;
        }
        if (station.email) {
            content += `<strong>E-Mail:</strong> <a href="mailto:${station.email}">${station.email}</a>`;
        }
        content += `</div>`;
        
        content += `</div>`;
        return content;
    }

    updateStats() {
        const statsElement = document.getElementById('station-count');
        if (statsElement) {
            const totalStations = this.stations.length;
            const regions = {};
            
            // Regionen zählen
            this.stations.forEach(station => {
                const region = this.getRegionName(station.plz_prefix);
                regions[region] = (regions[region] || 0) + 1;
            });
            
            let statsText = `${totalStations} Wildvogelhilfen gefunden`;
            
            // Top-Regionen anzeigen
            const sortedRegions = Object.entries(regions)
                .sort(([,a], [,b]) => b - a)
                .slice(0, 3);
            
            if (sortedRegions.length > 0) {
                const regionText = sortedRegions
                    .map(([region, count]) => `${region}: ${count}`)
                    .join(', ');
                statsText += ` | ${regionText}`;
            }
            
            statsElement.textContent = statsText;
        }
    }
    
    getRegionName(plzPrefix) {
        const regionMap = {
            '0': 'PLZ 0',
            '1': 'PLZ 1', 
            '2': 'PLZ 2',
            '3': 'PLZ 3',
            '4': 'PLZ 4',
            '5': 'PLZ 5',
            '6': 'PLZ 6',
            '7': 'PLZ 7',
            '8': 'PLZ 8',
            '9': 'PLZ 9',
            'österreich': 'Österreich',
            'schweiz': 'Schweiz',
            'italien': 'Italien'
        };
        return regionMap[plzPrefix] || 'Unbekannt';
    }

    showError(message) {
        const statsElement = document.getElementById('station-count');
        if (statsElement) {
            statsElement.innerHTML = `<span style="color: red;">⚠️ ${message}</span>`;
        }
    }
}

// Karte initialisieren wenn DOM geladen ist
document.addEventListener('DOMContentLoaded', () => {
    new WildvogelhilfeMap();
});
