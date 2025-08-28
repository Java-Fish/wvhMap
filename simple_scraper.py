#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Wildvogelhilfe Scraper
Funktioniert auch ohne Geocoding-API
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
import logging
from datetime import datetime
import os
import hashlib
from typing import List, Optional, Tuple

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimpleWildvogelhilfeScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.data = []
        
        # URLs aller zu scrapenden Seiten
        self.urls = [
            ("PLZ 0", "https://wp.wildvogelhilfe.org/de/auffangstationen/auffangstationen-plz-gebiet-0/"),
            ("PLZ 1", "https://wp.wildvogelhilfe.org/de/auffangstationen/auffangstationen-plz-gebiet-1/"),
            ("PLZ 2", "https://wp.wildvogelhilfe.org/de/auffangstationen/auffangstationen-plz-gebiet-2/"),
            ("PLZ 3", "https://wp.wildvogelhilfe.org/de/auffangstationen/auffangstationen-plz-gebiet-3/"),
            ("PLZ 4", "https://wp.wildvogelhilfe.org/de/auffangstationen/auffangstationen-plz-gebiet-4/"),
            ("PLZ 5", "https://wp.wildvogelhilfe.org/de/auffangstationen/auffangstationen-plz-gebiet-5/"),
            ("PLZ 6", "https://wp.wildvogelhilfe.org/de/auffangstationen/auffangstationen-plz-gebiet-6/"),
            ("PLZ 7", "https://wp.wildvogelhilfe.org/de/auffangstationen/auffangstationen-plz-gebiet-7/"),
            ("PLZ 8", "https://wp.wildvogelhilfe.org/de/auffangstationen/auffangstationen-plz-gebiet-8/"),
            ("PLZ 9", "https://wp.wildvogelhilfe.org/de/auffangstationen/auffangstationen-plz-gebiet-9/"),
            ("Österreich", "https://wp.wildvogelhilfe.org/de/auffangstationen/auffangstationen-oesterreich/"),
            ("Schweiz", "https://wp.wildvogelhilfe.org/de/auffangstationen/auffangstationen-schweiz/"),
            ("Italien", "https://wp.wildvogelhilfe.org/de/auffangstationen/auffangstationen-italien/")
        ]
        
        # Basis-Koordinaten für deutsche PLZ-Bereiche (erste Ziffer)
        self.de_plz_centroids = {
            '0': (51.1, 13.4),
            '1': (52.5, 13.3),
            '2': (53.6, 10.0),
            '3': (52.3, 9.7),
            '4': (51.5, 7.5),
            '5': (50.8, 7.2),
            '6': (50.1, 8.7),
            '7': (48.8, 9.2),
            '8': (48.1, 11.5),
            '9': (49.5, 11.1),
        }

        # Basis-Koordinaten für Österreich (erste Ziffer 4-stellige PLZ)
        self.at_plz_centroids = {
            '1': (48.21, 16.37),  # Wien
            '2': (48.2, 15.7),    # NÖ
            '3': (48.3, 14.3),    # OÖ
            '4': (47.8, 13.0),    # Salzburg
            '5': (47.3, 11.4),    # Tirol
            '6': (47.25, 9.6),    # Vorarlberg
            '7': (46.7, 14.2),    # Kärnten
            '8': (47.2, 15.6),    # Steiermark
            '9': (47.5, 16.4),    # Burgenland
        }

        # Schweiz (erste Ziffer 4-stellige PLZ)
        self.ch_plz_centroids = {
            '1': (47.38, 8.54),   # Zürich
            '2': (47.56, 7.59),   # Basel
            '3': (46.95, 7.45),   # Bern
            '4': (47.05, 8.31),   # Luzern
            '5': (47.42, 9.37),   # St. Gallen
            '6': (46.85, 9.53),   # Chur
            '7': (46.23, 7.36),   # Wallis
            '8': (46.0, 8.95),    # Tessin
            '9': (46.52, 6.63),   # Lausanne / Genf
        }
    
    def _deterministic_offset(self, key: str, scale: float = 0.25) -> Tuple[float, float]:
        """Deterministische Streuung (±scale/2) basierend auf Hash."""
        h = hashlib.md5(key.encode('utf-8')).hexdigest()
        a = int(h[:8], 16) / 0xFFFFFFFF - 0.5  # -0.5..0.5
        b = int(h[8:16], 16) / 0xFFFFFFFF - 0.5
        return a * scale, b * scale

    def get_coordinates_for_plz(self, plz_code: Optional[str], country: str = "Deutschland"):
        """Gibt deterministische Koordinaten für PLZ (verfeinert) zurück."""
        if not plz_code:
            return None, None
        country_l = country.lower()
        base = None
        if country_l == 'deutschland' and len(plz_code) == 5:
            if plz_code[0] == '0':
                east_map = {
                    '01': (51.05, 13.74), '02': (51.16, 14.99), '03': (51.75, 14.33),
                    '04': (51.34, 12.37), '05': (51.48, 11.97), '06': (51.50, 11.0),
                    '07': (50.93, 11.59), '08': (50.70, 12.50), '09': (50.83, 12.92)
                }
                base = east_map.get(plz_code[:2])
            if not base and plz_code[0] in self.de_plz_centroids:
                base = self.de_plz_centroids[plz_code[0]]
        elif country_l == 'österreich' and len(plz_code) == 4 and plz_code[0] in self.at_plz_centroids:
            base = self.at_plz_centroids[plz_code[0]]
        elif country_l == 'schweiz' and len(plz_code) == 4 and plz_code[0] in self.ch_plz_centroids:
            base = self.ch_plz_centroids[plz_code[0]]
        else:
            return None, None

        # Feinere Offsets: Verwende letzte 3 Ziffern um lokales Gitter zu verteilen
        core = plz_code[-3:]
        try:
            tail_int = int(core)
        except ValueError:
            tail_int = 0
        # Hash-basierte Streuung plus deterministische proportionale Komponente
        h_lat, h_lon = self._deterministic_offset(plz_code, 0.12)  # kleinere Hash-Streuung
        frac = (tail_int / 999.0) - 0.5  # -0.5..0.5
        lat = base[0] + h_lat + frac * 0.05  # ±0.025 zusätzlich
        lon = base[1] + h_lon + ((tail_int % 97)/97 - 0.5) * 0.07
        return round(lat, 5), round(lon, 5)
    
    def extract_station_info(self, station_html, region):
        """Extrahiert Informationen aus einem Stations-HTML-Block basierend auf einzelnen <p>-Elementen."""
        try:
            name_elem = station_html.find('h3')
            if not name_elem:
                return None
            name = name_elem.get_text(strip=True)

            paragraphs = []
            for p in station_html.find_all('p'):
                txt = p.get_text(" ", strip=True)
                if txt:
                    paragraphs.append((p, txt))

            specialization = None
            address = None
            phone = None
            note = None
            plz = None
            plz_re = re.compile(r'^\s*(\d{4,5})\s+([A-Za-zÄÖÜäöüß .\-]+)$')
            phone_re = re.compile(r'(?:(?:Tel|Telefon|Vogelnotruf|Mobil)\s*:?)\s*([+0-9][0-9 \-/()]{5,})', re.IGNORECASE)

            for p, txt in paragraphs:
                # Spezialisation via class or keywords
                if not specialization:
                    if p.find(class_=re.compile('stationsinfo', re.I)):
                        specialization = txt
                    else:
                        low = txt.lower()
                        if any(k in low for k in ['greifvögel', 'singvögel', 'mauersegler', 'schwalben', 'eulen', 'alle wildvogelarten', 'dohlen', 'falken']):
                            specialization = txt
                # Address
                if not address:
                    m_addr = plz_re.match(txt)
                    if m_addr:
                        plz = m_addr.group(1)
                        city = m_addr.group(2).strip()
                        address = f"{plz} {city}".strip()
                # Phone
                if not phone:
                    m_phone = phone_re.search(txt)
                    if m_phone:
                        raw_phone = m_phone.group(1)
                        # Abschneiden vor evtl. nachfolgendem '(' Hinweis
                        raw_phone = raw_phone.split('(')[0].strip()
                        phone = raw_phone
                # Note
                if not note and (txt.startswith('(') or 'bitte' in txt.lower()):
                    note = txt

            if not plz and address:
                # fallback extraction
                pm = re.search(r'\b(\d{4,5})\b', address)
                if pm:
                    plz = pm.group(1)
            if not plz:
                # try any paragraph
                for _p, t in paragraphs:
                    pm = re.search(r'\b(\d{4,5})\b', t)
                    if pm:
                        plz = pm.group(1)
                        if not address:
                            # attempt to reconstruct city after PLZ
                            rest = t.split(plz, 1)[1].strip()
                            city = rest.split()[0] if rest else ''
                            address = f"{plz} {city}".strip()
                        break

            if not plz:
                logger.warning(f"⚠️  Keine PLZ gefunden für {name}")
                return None

            if not specialization:
                specialization = 'Alle Wildvogelarten'

            # Country
            country = 'Deutschland'
            if region in ('Österreich', 'Schweiz', 'Italien'):
                country = region

            lat, lon = self.get_coordinates_for_plz(plz, country)

            if country != 'Deutschland':
                plz_prefix = country.lower()
            else:
                plz_prefix = plz[0]

            station = {
                'name': name,
                'specialization': specialization,
                'address': address,
                'phone': phone,
                'note': note,
                'latitude': lat,
                'longitude': lon,
                'plz': plz,
                'plz_prefix': plz_prefix,
                'region': region,
                'country': country
            }
            return {k: v for k, v in station.items() if v}
        except Exception as e:
            logger.error(f"❌ Fehler beim Parsen der Station: {e}")
            return None
    
    def _fetch_with_retries(self, url: str, retries: int = 3, backoff: float = 2.0) -> Optional[requests.Response]:
        for attempt in range(1, retries + 1):
            try:
                resp = self.session.get(url, timeout=30)
                resp.raise_for_status()
                return resp
            except Exception as e:
                logger.warning(f"⚠️  Request fehlgeschlagen (Versuch {attempt}/{retries}) {e}")
                if attempt < retries:
                    time.sleep(backoff * attempt)
        return None

    def scrape_page(self, region, url):
        """Scrapt eine einzelne Seite mit robustem Block-Paser."""
        try:
            logger.info(f"🔍 Scraping {region}: {url}")
            response = self._fetch_with_retries(url)
            if response is None:
                logger.error(f"❌ Abbruch {region}: Seite nicht erreichbar")
                return []

            soup = BeautifulSoup(response.content, 'html.parser')
            content = soup.find('div', class_='entry-content') or soup.find('main')
            if not content:
                logger.warning(f"⚠️  Kein Hauptinhalt gefunden für {region}")
                return []

            stations = []
            current_station = []
            elements = content.find_all(['h3', 'p', 'hr', 'div'])
            for el in elements:
                if el.name == 'h3':
                    if current_station:
                        station_soup = BeautifulSoup(''.join(str(e) for e in current_station), 'html.parser')
                        st = self.extract_station_info(station_soup, region)
                        if st:
                            stations.append(st)
                            logger.info(f"✅ {st['name']}")
                    current_station = [el]
                elif el.name in ('p', 'div'):
                    if current_station:
                        current_station.append(el)
                elif el.name == 'hr':
                    if current_station:
                        station_soup = BeautifulSoup(''.join(str(e) for e in current_station), 'html.parser')
                        st = self.extract_station_info(station_soup, region)
                        if st:
                            stations.append(st)
                            logger.info(f"✅ {st['name']}")
                        current_station = []
            if current_station:
                station_soup = BeautifulSoup(''.join(str(e) for e in current_station), 'html.parser')
                st = self.extract_station_info(station_soup, region)
                if st:
                    stations.append(st)
                    logger.info(f"✅ {st['name']}")
            logger.info(f"📊 {region}: {len(stations)} Stationen gefunden")
            return stations
        except Exception as e:
            logger.error(f"❌ Fehler beim Scraping von {region}: {e}")
            return []
    
    def run(self, test_mode=False):
        """Führt den kompletten Scraping-Prozess aus"""
        logger.info("🚀 Starte Simple Wildvogelhilfe-Scraper")
        start_time = datetime.now()
        
        # Im Testmodus nur erste 2 Seiten
        urls_to_process = self.urls[:2] if test_mode else self.urls
        
        for i, (region, url) in enumerate(urls_to_process, 1):
            logger.info(f"📑 Bearbeite Seite {i}/{len(urls_to_process)}: {region}")
            
            stations = self.scrape_page(region, url)
            self.data.extend(stations)
            
            # Fortschritt speichern nach jeder Seite
            self.save_progress()
            
            logger.info(f"🎯 Fortschritt: {i}/{len(urls_to_process)} Seiten | {len(self.data)} Stationen total")
            
            # Kurze Pause zwischen Seiten
            if i < len(urls_to_process):
                logger.info("⏸️  Pause 2 Sekunden...")
                time.sleep(2)
        
        # Finale Statistiken
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("=" * 50)
        logger.info("🎉 SCRAPING ABGESCHLOSSEN!")
        logger.info(f"⏱️  Dauer: {duration}")
        logger.info(f"📊 Gesamtanzahl Stationen: {len(self.data)}")
        
        # Statistiken nach Regionen
        region_stats = {}
        coord_count = 0
        
        for station in self.data:
            region = station.get('region', 'Unknown')
            region_stats[region] = region_stats.get(region, 0) + 1
            if station.get('latitude') and station.get('longitude'):
                coord_count += 1
        
        logger.info(f"🌍 Stationen mit Koordinaten: {coord_count}/{len(self.data)} ({coord_count/len(self.data)*100:.1f}%)")
        logger.info("\n📍 Verteilung nach Regionen:")
        for region, count in sorted(region_stats.items()):
            logger.info(f"  {region}: {count} Stationen")
        
        self.save_progress()
        logger.info("💾 Finale Daten gespeichert in data/wildvogelhilfen.json")
        
        return len(self.data)

    def save_progress(self):
        """Speichert aktuellen Zwischenstand in JSON."""
        try:
            with open('data/wildvogelhilfen.json', 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern: {e}")

def main():
    """Hauptfunktion"""
    import sys
    
    scraper = SimpleWildvogelhilfeScraper()
    
    # Prüfe Kommandozeilen-Argumente
    test_mode = '--test' in sys.argv
    
    if test_mode:
        logger.info("🧪 TESTMODUS: Nur erste 2 Seiten werden gescrapt")
    
    try:
        total_stations = scraper.run(test_mode=test_mode)
        logger.info(f"✅ Erfolgreich abgeschlossen! {total_stations} Stationen gesammelt.")
        
    except KeyboardInterrupt:
        logger.info("\n⏹️  Scraping durch Benutzer unterbrochen")
        scraper.save_progress()
        
    except Exception as e:
        logger.error(f"❌ Unerwarteter Fehler: {e}")
        scraper.save_progress()

if __name__ == "__main__":
    main()
