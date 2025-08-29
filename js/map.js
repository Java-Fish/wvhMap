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
        this.initDownloadButton();
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
    
    let markerCount = 0;
    let skippedCount = 0;
    
        this.stations.forEach(station => {
            // Koordinaten validieren
            const lat = parseFloat(station.latitude);
            const lng = parseFloat(station.longitude);
            
            // Debug: Ungültige Koordinaten protokollieren
            if (isNaN(lat) || isNaN(lng) || lat === 0 || lng === 0) {
                console.warn('Station ohne gültige Koordinaten:', station.name, 'lat:', station.latitude, 'lng:', station.longitude);
                skippedCount++;
                return;
            }
            
            // Icon basierend auf Spezialisierung wählen
            const icon = this.getIconForStation(station);
            
            try {
                // Marker erstellen
                const marker = L.marker([lat, lng], {
                    icon: icon
                }).addTo(this.map);
                
                // Referenz für Highlighting / Suche
                marker._station = station;

                // Popup-Inhalt erstellen
                const popupContent = this.createPopupContent(station);
                marker.bindPopup(popupContent);

                // Marker zur Liste hinzufügen
                this.markers.push(marker);
                markerCount++;
            } catch (error) {
                console.error('Fehler beim Erstellen des Markers für:', station.name, error);
                skippedCount++;
            }
        });

        console.log(`Marker erstellt: ${markerCount}, Übersprungen: ${skippedCount}, Total Stationen: ${this.stations.length}`);

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

    initDownloadButton() {
        const downloadBtn = document.getElementById('download-btn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => {
                this.downloadJsonData();
            });
        }
    }

    downloadJsonData() {
        try {
            // JSON-Daten vorbereiten
            const jsonData = JSON.stringify(this.stations, null, 2);
            
            // Blob erstellen
            const blob = new Blob([jsonData], { type: 'application/json' });
            
            // Download-URL erstellen
            const url = window.URL.createObjectURL(blob);
            
            // Temporären Download-Link erstellen
            const downloadLink = document.createElement('a');
            downloadLink.href = url;
            downloadLink.download = `wildvogelhilfen-${new Date().toISOString().split('T')[0]}.json`;
            downloadLink.style.display = 'none';
            
            // Link zum DOM hinzufügen, klicken und wieder entfernen
            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);
            
            // URL wieder freigeben
            window.URL.revokeObjectURL(url);
            
            // Feedback für den Benutzer
            const originalText = document.getElementById('download-btn').textContent;
            document.getElementById('download-btn').textContent = '✅ Download gestartet!';
            document.getElementById('download-btn').style.background = 'linear-gradient(135deg, #28a745, #20c997)';
            
            setTimeout(() => {
                document.getElementById('download-btn').textContent = originalText;
                document.getElementById('download-btn').style.background = '';
            }, 2000);
            
        } catch (error) {
            console.error('Fehler beim Download:', error);
            
            // Fallback: Daten in neuem Tab anzeigen
            const jsonData = JSON.stringify(this.stations, null, 2);
            const newWindow = window.open();
            newWindow.document.write('<pre>' + jsonData + '</pre>');
            newWindow.document.title = 'Wildvogelhilfen JSON-Daten';
            
            // Feedback für den Benutzer
            const originalText = document.getElementById('download-btn').textContent;
            document.getElementById('download-btn').textContent = '📋 In neuem Tab geöffnet';
            
            setTimeout(() => {
                document.getElementById('download-btn').textContent = originalText;
            }, 3000);
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
        const pts = stations.filter(s => {
            const lat = parseFloat(s.latitude);
            const lng = parseFloat(s.longitude);
            return !isNaN(lat) && !isNaN(lng) && lat !== 0 && lng !== 0;
        }).map(s => [parseFloat(s.latitude), parseFloat(s.longitude)]);
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
    
    // Widget-Funktionalität nur auf der Hauptseite
    if (document.getElementById('widget-toggle-btn')) {
        new WidgetManager();
    }
});

// Widget-Manager Klasse
class WidgetManager {
    constructor() {
        this.currentConfig = {
            width: '800',
            height: '600',
            includeSearch: true
        };
        this.baseUrl = window.location.origin + window.location.pathname.replace('index.html', '');
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.updateWidgetCode();
    }

    setupEventListeners() {
        // Toggle-Button
        const toggleBtn = document.getElementById('widget-toggle-btn');
        const widgetContent = document.getElementById('widget-content');
        const toggleIcon = document.getElementById('widget-toggle-icon');

        toggleBtn.addEventListener('click', () => {
            const isVisible = widgetContent.style.display !== 'none';
            widgetContent.style.display = isVisible ? 'none' : 'block';
            toggleIcon.textContent = isVisible ? '▼' : '▲';
        });

        // Größen-Buttons
        document.querySelectorAll('.size-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                // Alle Buttons deaktivieren
                document.querySelectorAll('.size-btn').forEach(b => b.classList.remove('active'));
                // Aktuellen Button aktivieren
                e.target.classList.add('active');
                
                // Konfiguration aktualisieren
                this.currentConfig.width = e.target.dataset.width;
                this.currentConfig.height = e.target.dataset.height;
                this.updateWidgetCode();
            });
        });

        // Suchfunktion Checkbox
        document.getElementById('include-search').addEventListener('change', (e) => {
            this.currentConfig.includeSearch = e.target.checked;
            this.updateWidgetCode();
        });

        // Code kopieren
        document.getElementById('copy-widget-code').addEventListener('click', () => {
            this.copyToClipboard();
        });

        // Vorschau anzeigen
        document.getElementById('preview-widget').addEventListener('click', () => {
            this.showPreview();
        });
    }

    updateWidgetCode() {
        const { width, height, includeSearch } = this.currentConfig;
        
        const searchParam = !includeSearch ? '?hideSearch=true' : '';
        const widgetUrl = `${this.baseUrl}widget.html${searchParam}`;
        
        const code = `<!-- Wildvogelhilfe Karte Widget -->
<iframe 
    src="${widgetUrl}"
    width="${width}" 
    height="${height}"
    frameborder="0"
    style="border: 1px solid #ddd; border-radius: 8px; max-width: 100%;"
    title="Wildvogelhilfe Karte"
    loading="lazy">
    <p>Ihr Browser unterstützt keine iframes. 
    <a href="${widgetUrl}" target="_blank">Karte in neuem Fenster öffnen</a></p>
</iframe>`;

        document.getElementById('widget-code').value = code;
    }

    async copyToClipboard() {
        const codeTextarea = document.getElementById('widget-code');
        const copyBtn = document.getElementById('copy-widget-code');
        const originalText = copyBtn.textContent;

        try {
            await navigator.clipboard.writeText(codeTextarea.value);
            copyBtn.textContent = '✅ Kopiert!';
            copyBtn.style.background = '#28a745';
            
            setTimeout(() => {
                copyBtn.textContent = originalText;
                copyBtn.style.background = '#4a7c59';
            }, 2000);
        } catch (err) {
            // Fallback für ältere Browser
            codeTextarea.select();
            document.execCommand('copy');
            copyBtn.textContent = '✅ Kopiert!';
            
            setTimeout(() => {
                copyBtn.textContent = originalText;
            }, 2000);
        }
    }

    showPreview() {
        const previewContainer = document.getElementById('widget-preview-container');
        const previewFrame = document.getElementById('widget-preview');
        const { width, height, includeSearch } = this.currentConfig;
        
        const searchParam = !includeSearch ? '?hideSearch=true' : '';
        const widgetUrl = `${this.baseUrl}widget.html${searchParam}`;
        
        // Vorschau-Container anzeigen
        previewContainer.style.display = 'block';
        
        // Preview-Frame Größe setzen
        const previewWidth = width === '100%' ? '100%' : Math.min(parseInt(width), 800) + 'px';
        const previewHeight = Math.min(parseInt(height), 500) + 'px';
        
        previewFrame.style.width = previewWidth;
        previewFrame.style.height = previewHeight;
        previewFrame.src = widgetUrl;
        
        // Scroll zur Vorschau
        previewContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}
