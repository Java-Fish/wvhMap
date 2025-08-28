// Wildvogelhilfe Karte - Hauptskript
class WildvogelhilfeMap {
    constructor() {
        this.map = null;
        this.markers = [];
        this.stations = [];
    this.filteredMarkers = [];
    this.index = { plz: new Map(), city: new Map() };
    this.lastQuery = '';
        this.init();
    }

    async init() {
        this.initMap();
        await this.loadStations();
    this.buildIndex();
    this.initSearchUI();
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
    // Entferne vorhandene Marker (bei Re-Render nach Filter)
    this.markers.forEach(m => this.map.removeLayer(m));
    this.markers = [];
        this.stations.forEach(station => {
            // Icon basierend auf Spezialisierung wählen
            const icon = this.getIconForStation(station);
            
            // Marker erstellen
            const marker = L.marker([station.latitude, station.longitude], {
                icon: icon
            }).addTo(this.map);
            // Referenz für Highlighting / Suche
            marker._station = station;

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
        if (station.note) {
            content += `<div class="note" style="margin-top:6px;font-size:0.85rem;color:#444;line-height:1.2;">${station.note}</div>`;
        }
        
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

    // --- Suche ---
    buildIndex() {
        this.stations.forEach(st => {
            if (st.plz) {
                this.index.plz.set(st.plz, st);
            }
            // Stadt aus Adresse heuristisch: alles nach PLZ
            if (st.address) {
                const m = st.address.match(/\b(\d{4,5})\s+([^,]+)(?:,|$)/);
                if (m) {
                    const city = m[2].trim().toLowerCase();
                    if (!this.index.city.has(city)) this.index.city.set(city, []);
                    this.index.city.get(city).push(st);
                    st._city = city; // cache
                }
            }
        });
    }

    initSearchUI() {
        this.searchInput = document.getElementById('search-input');
        this.searchBtn = document.getElementById('search-btn');
        this.clearBtn = document.getElementById('clear-btn');
        this.resultsBox = document.getElementById('search-results');
        if (!this.searchInput) return;

        const handle = () => {
            const q = this.searchInput.value.trim();
            this.performSearch(q);
        };
        this.searchBtn?.addEventListener('click', handle);
        this.searchInput.addEventListener('input', (e) => {
            const q = e.target.value.trim();
            if (q.length === 0) {
                this.clearSearch();
            } else {
                this.performSearch(q, true);
            }
        });
        this.searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') { e.preventDefault(); handle(); }
            if (e.key === 'Escape') { this.clearSearch(); }
            if (['ArrowDown','ArrowUp'].includes(e.key)) { this.navigateResults(e.key); e.preventDefault(); }
        });
        this.clearBtn?.addEventListener('click', () => this.clearSearch());
        document.addEventListener('click', (e) => {
            if (!this.resultsBox.contains(e.target) && e.target !== this.searchInput) {
                this.hideResults();
            }
        });
    }

    performSearch(query, live=false) {
        this.lastQuery = query;
        if (!query) { this.clearSearch(); return; }
        const qLower = query.toLowerCase();
        // Sammle Treffer
        const exactPlz = this.index.plz.get(query);
        let candidates = [];
        if (exactPlz) candidates.push(exactPlz);
        // PLZ-Prefix Match
        if (!exactPlz && /^(\d{2,5})$/.test(query)) {
            candidates = this.stations.filter(s => s.plz && s.plz.startsWith(query));
        }
        // Stadt substring
        const cityMatches = this.stations.filter(s => s._city && s._city.includes(qLower));
        cityMatches.forEach(st => { if (!candidates.includes(st)) candidates.push(st); });
        // Name fallback
        if (candidates.length === 0) {
            // Name
            candidates = this.stations.filter(s => s.name.toLowerCase().includes(qLower));
        }
        if (candidates.length === 0) {
            // Address fallback
            candidates = this.stations.filter(s => s.address && s.address.toLowerCase().includes(qLower));
        }
    console.log('🔎 Suche', query, 'Treffer:', candidates.length);
        this.renderResults(candidates.slice(0, 25));
        if (!live && candidates.length > 0) {
            this.focusStations(candidates);
        }
    }

    focusStations(stations) {
        // Bounds über ausgewählte Stationen
        const pts = stations.filter(s => s.latitude && s.longitude).map(s => [s.latitude, s.longitude]);
        if (pts.length === 1) {
            this.map.flyTo(pts[0], 11, { duration: 0.8 });
        } else if (pts.length > 1) {
            const group = L.featureGroup(pts.map(p => L.marker(p)));
            this.map.fitBounds(group.getBounds().pad(0.2));
        }
        // Marker hervorheben
        this.highlightMarkers(stations);
    }

    highlightMarkers(selected) {
        const set = new Set(selected.map(s => s.name+':'+s.plz));
        this.markers.forEach(m => {
            const st = m._station;
            if (st && set.has(st.name+':'+st.plz)) {
                m.getElement()?.classList.add('marker-highlight');
            } else {
                m.getElement()?.classList.remove('marker-highlight');
            }
        });
    }

    renderResults(list) {
        if (!this.resultsBox) return;
        if (this.lastQuery.length === 0) { this.resultsBox.innerHTML=''; this.hideResults(); return; }
        if (list.length === 0) {
            this.resultsBox.innerHTML = '<div style="padding:0.6rem;">Keine Treffer</div>';
            this.showResults();
            return;
        }
        const html = '<ul>' + list.map((st,i) => {
            const city = st._city ? st._city.charAt(0).toUpperCase()+st._city.slice(1) : '';
            return `<li data-idx="${i}"><strong>${st.plz||''}</strong> ${city} <span class="meta">${st.name}</span></li>`;
        }).join('') + '</ul>';
        this.resultsBox.innerHTML = html;
        this.showResults();
        this.resultsBox.querySelectorAll('li').forEach((li,i) => {
            li.addEventListener('click', () => {
                const st = list[i];
                this.focusStations([st]);
                this.hideResults();
            });
        });
    }

    navigateResults(direction) {
        const items = Array.from(this.resultsBox.querySelectorAll('li'));
        if (items.length === 0) return;
        let idx = items.findIndex(li => li.classList.contains('active'));
        if (direction === 'ArrowDown') idx = (idx + 1) % items.length; else idx = (idx - 1 + items.length) % items.length;
        items.forEach(li => li.classList.remove('active'));
        items[idx].classList.add('active');
        const clickEvt = new Event('click');
        items[idx].dispatchEvent(clickEvt);
    }

    clearSearch() {
        if (this.searchInput) this.searchInput.value='';
        this.lastQuery='';
        this.hideResults();
        this.highlightMarkers([]);
    }
    hideResults(){ this.resultsBox?.classList.add('hidden'); }
    showResults(){ this.resultsBox?.classList.remove('hidden'); }
    
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
