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
        
        # Manuelle Koordinaten für PLZ-Bereiche (Zentren der Regionen)
        self.plz_coordinates = {
            '0': (51.2, 13.0),   # Sachsen/Thüringen
            '1': (52.5, 13.4),   # Berlin/Brandenburg
            '2': (53.6, 10.0),   # Hamburg/Schleswig-Holstein
            '3': (52.3, 9.7),    # Niedersachsen
            '4': (51.5, 7.5),    # NRW
            '5': (50.7, 7.1),    # NRW/Rheinland-Pfalz
            '6': (49.9, 8.4),    # Baden-Württemberg/Hessen
            '7': (48.8, 9.2),    # Baden-Württemberg
            '8': (48.1, 11.6),   # Bayern
            '9': (49.4, 11.1),   # Bayern/Thüringen
        }
    
    def get_coordinates_for_plz(self, plz_code):
        """Gibt Koordinaten basierend auf PLZ zurück"""
        if not plz_code:
            return None, None
            
        # Erste Ziffer der PLZ
        first_digit = plz_code[0] if plz_code else '0'
        
        if first_digit in self.plz_coordinates:
            lat, lon = self.plz_coordinates[first_digit]
            # Kleine zufällige Abweichung für bessere Verteilung
            import random
            lat += random.uniform(-0.1, 0.1)
            lon += random.uniform(-0.1, 0.1)
            return round(lat, 4), round(lon, 4)
        
        return None, None
    
    def save_progress(self):
        """Speichert den aktuellen Fortschritt"""
        try:
            os.makedirs('data', exist_ok=True)
            with open('data/wildvogelhilfen.json', 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 Fortschritt gespeichert: {len(self.data)} Einträge")
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern: {e}")
    
    def extract_station_info(self, station_html, region):
        """Extrahiert Informationen aus einem Stations-HTML-Block"""
        try:
            # Name aus h3
            name_elem = station_html.find('h3')
            if not name_elem:
                return None
            
            name = name_elem.get_text(strip=True)
            text_content = station_html.get_text()
            
            # PLZ und Ort extrahieren
            plz_match = re.search(r'(\d{4,5})\s+([A-ZÄÖÜa-zäöüß][A-ZÄÖÜa-zäöüß\s\-]*)', text_content)
            if not plz_match:
                logger.warning(f"⚠️  Keine PLZ gefunden für {name}")
                return None
            
            plz = plz_match.group(1)
            city = plz_match.group(2).strip()
            
            # Straße suchen (vor der PLZ)
            before_plz = text_content[:plz_match.start()]
            street_match = re.search(r'([A-ZÄÖÜa-zäöüß][A-ZÄÖÜa-zäöüß\s\-\.]*\d+[a-z]?)\s*$', before_plz)
            
            if street_match:
                address = f"{street_match.group(1).strip()}, {plz} {city}"
            else:
                address = f"{plz} {city}"
            
            # Telefon extrahieren
            phone_patterns = [
                r'Tel\.?\s*:?\s*([0-9\s\-\/\(\)\+]{8,})',
                r'Telefon\.?\s*:?\s*([0-9\s\-\/\(\)\+]{8,})',
                r'Vogelnotruf\.?\s*:?\s*([0-9\s\-\/\(\)\+]{8,})'
            ]
            
            phone = ""
            for pattern in phone_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    phone = match.group(1).strip()
                    # Entferne Fax-Nummer falls vorhanden
                    phone = re.split(r'[Ff]ax', phone)[0].strip()
                    break
            
            # E-Mail extrahieren
            email = ""
            email_elem = station_html.find('a', href=lambda x: x and x.startswith('mailto:'))
            if email_elem:
                email = email_elem.get('href').replace('mailto:', '')
            
            # Website extrahieren
            website = ""
            web_elem = station_html.find('a', href=lambda x: x and (x.startswith('http') or x.startswith('www')))
            if web_elem and 'mailto:' not in web_elem.get('href', ''):
                website = web_elem.get('href')
            
            # Spezialisierung extrahieren
            specialization = "Alle Wildvogelarten"
            spec_indicators = [
                'Spezialisiert auf', 'Greifvögel', 'Singvögel', 'Mauersegler', 
                'Schwalben', 'Alle Vögel', 'Dohlen', 'Eulen', 'Falken'
            ]
            
            for indicator in spec_indicators:
                if indicator.lower() in text_content.lower():
                    # Finde den Satz mit der Spezialisierung
                    lines = text_content.split('\n')
                    for line in lines:
                        if indicator.lower() in line.lower():
                            specialization = line.strip()
                            break
                    break
            
            # Koordinaten basierend auf PLZ
            lat, lon = self.get_coordinates_for_plz(plz)
            
            # Land bestimmen
            country = "Deutschland"
            if region == "Österreich":
                country = "Österreich"
            elif region == "Schweiz":
                country = "Schweiz"
            elif region == "Italien":
                country = "Italien"
            
            station = {
                "name": name,
                "specialization": specialization,
                "address": address,
                "phone": phone,
                "email": email,
                "website": website,
                "latitude": lat,
                "longitude": lon,
                "plz_prefix": plz[0] if len(plz) == 5 else plz[:2],
                "region": region,
                "country": country
            }
            
            # Leere Felder entfernen
            station = {k: v for k, v in station.items() if v}
            
            return station
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Parsen der Station: {e}")
            return None
    
    def scrape_page(self, region, url):
        """Scrapt eine einzelne Seite"""
        try:
            logger.info(f"🔍 Scraping {region}: {url}")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Hauptinhalt finden
            content = soup.find('div', class_='entry-content')
            if not content:
                content = soup.find('main')
            
            if not content:
                logger.warning(f"⚠️  Kein Hauptinhalt gefunden für {region}")
                return []
            
            stations = []
            
            # Finde alle Stations-Blöcke (zwischen h3 und hr oder nächster h3)
            current_station = []
            elements = content.find_all(['h3', 'p', 'hr'])
            
            for element in elements:
                if element.name == 'h3':
                    # Vorherige Station verarbeiten
                    if current_station:
                        station_soup = BeautifulSoup(''.join(str(e) for e in current_station), 'html.parser')
                        station = self.extract_station_info(station_soup, region)
                        if station:
                            stations.append(station)
                            logger.info(f"✅ {station['name']}")
                    
                    # Neue Station beginnen
                    current_station = [element]
                    
                elif element.name == 'p':
                    if current_station:  # Nur hinzufügen wenn wir in einer Station sind
                        current_station.append(element)
                        
                elif element.name == 'hr':
                    # Station beenden
                    if current_station:
                        station_soup = BeautifulSoup(''.join(str(e) for e in current_station), 'html.parser')
                        station = self.extract_station_info(station_soup, region)
                        if station:
                            stations.append(station)
                            logger.info(f"✅ {station['name']}")
                        current_station = []
            
            # Letzte Station verarbeiten falls kein abschließendes hr
            if current_station:
                station_soup = BeautifulSoup(''.join(str(e) for e in current_station), 'html.parser')
                station = self.extract_station_info(station_soup, region)
                if station:
                    stations.append(station)
                    logger.info(f"✅ {station['name']}")
            
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
