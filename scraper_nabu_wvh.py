#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NABU Wildvogelhilfe Google Maps Scraper
Scannt die NABU Google Maps Karte für Wildvogelhilfen
Verwendet KML-Export und Google Maps API Aufrufe
"""

import requests
import json
import time
import re
import logging
from datetime import datetime
import os
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from urllib.parse import parse_qs, urlparse

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper_nabu.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NABUGoogleMapsScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.data = []
        self.existing_data = []
        self.json_file = 'data/wildvogelhilfen.json'
        
        # Google Maps URL und KML-Export URLs
        self.maps_url = "https://www.google.com/maps/d/viewer?mid=1FtYeDfRtJF_nUIuBt0WQkRnIRM4&femb=1&ll=51.099256809569006%2C10.42040625&z=6"
        self.kml_url = "https://www.google.com/maps/d/kml?mid=1FtYeDfRtJF_nUIuBt0WQkRnIRM4"
        
    def load_existing_data(self):
        """Lädt die bestehenden Daten aus der JSON-Datei"""
        try:
            if os.path.exists(self.json_file):
                with open(self.json_file, 'r', encoding='utf-8') as f:
                    self.existing_data = json.load(f)
                logger.info(f"Bestehende Daten geladen: {len(self.existing_data)} Einträge")
            else:
                logger.warning(f"JSON-Datei {self.json_file} nicht gefunden")
        except Exception as e:
            logger.error(f"Fehler beim Laden der bestehenden Daten: {e}")
            
    def is_duplicate(self, name: str, address: str) -> bool:
        """Prüft ob ein Eintrag bereits existiert"""
        for existing in self.existing_data:
            if (existing.get('name', '').lower() == name.lower() or 
                (existing.get('address', '').lower() in address.lower() and 
                 len(existing.get('address', '')) > 10)):
                return True
        return False
        
    def extract_plz_info(self, address: str) -> tuple:
        """Extrahiert PLZ-Informationen aus der Adresse"""
        # Deutsche PLZ suchen (5 Ziffern)
        de_plz_match = re.search(r'\b(\d{5})\b', address)
        if de_plz_match:
            plz = de_plz_match.group(1)
            plz_prefix = plz[0]
            region = f"PLZ {plz_prefix}"
            country = "Deutschland"
            return plz, plz_prefix, region, country
            
        # Österreichische PLZ suchen (4 Ziffern)
        at_plz_match = re.search(r'\b(\d{4})\b', address)
        if at_plz_match and any(word in address.lower() for word in ['österreich', 'austria', 'wien', 'salzburg', 'graz']):
            plz = at_plz_match.group(1)
            plz_prefix = "österreich"
            region = "Österreich"
            country = "Österreich"
            return plz, plz_prefix, region, country
            
        # Schweizer PLZ suchen (4 Ziffern)
        ch_plz_match = re.search(r'\b(\d{4})\b', address)
        if ch_plz_match and any(word in address.lower() for word in ['schweiz', 'switzerland', 'zürich', 'basel', 'bern']):
            plz = ch_plz_match.group(1)
            plz_prefix = "schweiz"
            region = "Schweiz"
            country = "Schweiz"
            return plz, plz_prefix, region, country
            
        # Fallback
        return "", "", "Unbekannt", "Deutschland"
        
    def clean_text(self, text: str) -> str:
        """Bereinigt Text von unnötigen Zeichen"""
        if not text:
            return ""
        # Entferne führende/nachfolgende Leerzeichen und normalisiere Leerzeichen
        text = re.sub(r'\s+', ' ', text.strip())
        # Entferne HTML-Tags falls vorhanden
        text = re.sub(r'<[^>]+>', '', text)
        return text
        
    def extract_contact_info(self, text: str) -> dict:
        """Extrahiert Kontaktinformationen aus Text"""
        contact_info = {
            'phone': '',
            'email': '',
            'website': ''
        }
        
        # Telefonnummer suchen
        phone_patterns = [
            r'(?:Tel\.?|Telefon|Phone|Mobil|Mobile)?\s*:?\s*(\+?\d{1,4}[\s\-/]?\d{1,4}[\s\-/]?\d{1,10}[\s\-/]?\d{0,10})',
            r'(\d{2,5}[\s\-/]\d{1,10}[\s\-/]?\d{0,10})',
            r'(\+\d{1,4}\s?\d{1,4}\s?\d{1,10})',
        ]
        
        for pattern in phone_patterns:
            phone_match = re.search(pattern, text)
            if phone_match:
                contact_info['phone'] = self.clean_text(phone_match.group(1))
                break
                
        # E-Mail suchen
        email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text)
        if email_match:
            contact_info['email'] = email_match.group(1)
            
        # Website suchen
        website_match = re.search(r'(https?://[^\s]+|www\.[^\s]+)', text)
        if website_match:
            contact_info['website'] = website_match.group(1)
            
        return contact_info
        
    def scrape_kml_data(self):
        """Versucht KML-Daten von der Google Maps Karte zu laden"""
        try:
            logger.info("Versuche KML-Daten zu laden...")
            response = self.session.get(self.kml_url, timeout=30)
            
            if response.status_code == 200:
                # Parse KML XML
                try:
                    root = ET.fromstring(response.content)
                    self.parse_kml_data(root)
                except ET.ParseError as e:
                    logger.error(f"Fehler beim Parsen der KML-Daten: {e}")
            else:
                logger.warning(f"KML-URL nicht erreichbar: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Fehler beim Laden der KML-Daten: {e}")
            
    def parse_kml_data(self, root):
        """Parst KML-XML-Daten und extrahiert Wildvogelhilfe-Informationen"""
        # KML-Namespaces
        namespaces = {
            'kml': 'http://www.opengis.net/kml/2.2',
            'gx': 'http://www.google.com/kml/ext/2.2'
        }
        
        # Suche nach Placemark-Elementen
        placemarks = root.findall('.//kml:Placemark', namespaces)
        logger.info(f"Gefunden: {len(placemarks)} Placemarks in KML")
        
        for placemark in placemarks:
            try:
                # Name extrahieren
                name_elem = placemark.find('kml:name', namespaces)
                name = name_elem.text if name_elem is not None else ""
                
                # Beschreibung extrahieren
                desc_elem = placemark.find('kml:description', namespaces)
                description = desc_elem.text if desc_elem is not None else ""
                
                # Koordinaten extrahieren (werden später durch fix_coordinates.py ersetzt)
                coordinates_elem = placemark.find('.//kml:coordinates', namespaces)
                coordinates = coordinates_elem.text if coordinates_elem is not None else ""
                
                if name and description:
                    entry = self.parse_kml_description(name, description)
                    if entry and not self.is_duplicate(entry['name'], entry['address']):
                        self.data.append(entry)
                        logger.info(f"KML-Eintrag hinzugefügt: {entry['name']}")
                        
            except Exception as e:
                logger.warning(f"Fehler beim Parsen eines Placemarks: {e}")
                
    def parse_kml_description(self, name: str, description: str) -> Optional[Dict]:
        """Parst die KML-Beschreibung und erstellt einen JSON-Eintrag"""
        if not name or not description:
            return None
            
        # HTML aus Beschreibung entfernen
        soup = BeautifulSoup(description, 'html.parser')
        clean_description = soup.get_text()
        
        # Kontaktinformationen extrahieren
        contact_info = self.extract_contact_info(clean_description)
        
        # Adresse suchen
        address = ""
        lines = [line.strip() for line in clean_description.split('\n') if line.strip()]
        
        for line in lines:
            if re.search(r'\d{4,5}', line):  # Zeile mit PLZ
                address = self.clean_text(line)
                break
                
        # Spezialisierung suchen
        specialization = ""
        spec_keywords = ['spezialisiert', 'aufnahme', 'pflege', 'arten', 'vögel', 'greif', 'eule', 'sing', 'schwalben', 'mauersegler']
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in spec_keywords):
                specialization = self.clean_text(line)
                break
                
        # PLZ-Informationen extrahieren
        plz, plz_prefix, region, country = self.extract_plz_info(address or clean_description)
        
        entry = {
            'name': self.clean_text(name),
            'specialization': specialization,
            'address': address or self.clean_text(lines[0] if lines else ""),
            'phone': contact_info['phone'],
            'plz': plz,
            'plz_prefix': plz_prefix,
            'region': region,
            'country': country
        }
        
        # Zusätzliche Felder hinzufügen
        if contact_info['email']:
            entry['email'] = contact_info['email']
        if contact_info['website']:
            entry['website'] = contact_info['website']
            
        # Note für zusätzliche Informationen
        if len(clean_description) > 200:
            entry['note'] = clean_description[:200] + "..."
            
        return entry
        
    def scrape_maps_page(self):
        """Versucht Daten direkt von der Google Maps Seite zu extrahieren"""
        try:
            logger.info("Versuche direkte Extraktion von der Maps-Seite...")
            response = self.session.get(self.maps_url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Suche nach JavaScript-Variablen mit Kartendaten
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string and 'var _pageData' in script.string:
                        self.extract_from_page_data(script.string)
                        break
                        
            else:
                logger.warning(f"Maps-Seite nicht erreichbar: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Fehler beim Scrapen der Maps-Seite: {e}")
            
    def extract_from_page_data(self, script_content: str):
        """Extrahiert Daten aus JavaScript _pageData Variable"""
        try:
            # Verschiedene Regex-Patterns für Google Maps Daten
            patterns = [
                r'\["Beschreibung",\s*\["([^"]*(?:\\.[^"]*)*)"\]',  # Original mit Escapes
                r'"Beschreibung",\s*\["([^"]*(?:\\.[^"]*)*)"\]',    # Ohne führende Klammer
                r'Beschreibung.*?"([^"]*(?:Tel|Fon|Mobile|E-Mail|wildvogel)[^"]*)"',  # Freiere Suche
            ]
            
            all_matches = []
            for pattern in patterns:
                matches = re.findall(pattern, script_content, re.IGNORECASE | re.DOTALL)
                all_matches.extend(matches)
                logger.info(f"Pattern {pattern[:30]}... fand {len(matches)} Treffer")
            
            # Entferne Duplikate
            unique_matches = list(set(all_matches))
            logger.info(f"Gefunden: {len(unique_matches)} eindeutige Einträge in den Kartendaten")
            
            # Zusätzliche Suche nach JavaScript-Arrays mit Wildvogel-Daten
            if not unique_matches:
                # Suche nach allen Strings, die wildvogel-relevante Begriffe enthalten
                wildvogel_pattern = r'"([^"]*(?:wildvogel|vogelstation|auffangstation|pflegestation|greifvogel)[^"]*)"'
                wildvogel_matches = re.findall(wildvogel_pattern, script_content, re.IGNORECASE)
                
                for match in wildvogel_matches:
                    if len(match) > 50:  # Nur längere Beschreibungen
                        unique_matches.append(match)
                        
                logger.info(f"Zusätzlich gefunden: {len(wildvogel_matches)} Wildvogel-bezogene Strings")
            
            for match in unique_matches:
                # Escape-Sequenzen auflösen
                description = match.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                
                if len(description) > 30:  # Mindestlänge für sinnvolle Einträge
                    entry = self.parse_description_text(description)
                    if entry and not self.is_duplicate(entry['name'], entry['address']):
                        self.data.append(entry)
                        logger.info(f"Neuer Eintrag aus Kartendaten: {entry['name']}")
                        
        except Exception as e:
            logger.warning(f"Fehler beim Extrahieren von PageData: {e}")
            
        # Debug: Zeige auch rohe Daten an
        if not self.data:
            logger.info("Zeige Debug-Informationen...")
            # Suche nach allen Arrays die Adressen oder Telefonnummern enthalten könnten
            debug_pattern = r'\[([^\[\]]*(?:\d{4,5}|Tel|Fon|Mobile)[^\[\]]*)\]'
            debug_matches = re.findall(debug_pattern, script_content)
            logger.info(f"Debug: Gefunden {len(debug_matches)} Arrays mit Adressen/Telefon")
            for i, match in enumerate(debug_matches[:5]):  # Zeige nur erste 5
                logger.info(f"Debug {i+1}: {match[:100]}...")
            
    def parse_description_text(self, description: str) -> Optional[Dict]:
        """Parst Beschreibungstext und erstellt JSON-Eintrag"""
        lines = [line.strip() for line in description.split('\n') if line.strip()]
        
        if len(lines) < 2:
            return None
            
        # Erster Ansatz: Name ist die erste Zeile oder aus der ersten Zeile extrahierbar
        name = self.clean_text(lines[0])
        
        # Falls erste Zeile zu lang ist, versuche Organisation zu finden
        if len(name) > 100:
            # Suche nach Organisationsnamen in den ersten Zeilen
            for line in lines[:3]:
                if any(keyword in line.lower() for keyword in ['e.v.', 'verein', 'station', 'hilfe', 'nabu', 'tierschutz']):
                    name = self.clean_text(line)
                    break
        
        # Kontaktinformationen extrahieren
        contact_info = self.extract_contact_info(description)
        
        # Adresse suchen - meist zweite oder dritte Zeile
        address = ""
        for line in lines[1:4]:
            if re.search(r'\d{4,5}', line):  # PLZ gefunden
                address = self.clean_text(line)
                break
                
        if not address and len(lines) > 1:
            address = self.clean_text(lines[1])
            
        # Spezialisierung suchen
        specialization = ""
        spec_keywords = ['spezialisiert', 'aufnahme', 'pflege', 'arten', 'vögel', 'greif', 'eule', 'sing', 'schwalben', 'mauersegler', 'alle']
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in spec_keywords) and len(line) > 10:
                specialization = self.clean_text(line)
                break
                
        # PLZ-Informationen extrahieren
        plz, plz_prefix, region, country = self.extract_plz_info(address or description)
        
        # Zusätzliche Informationen als Note
        note = ""
        if len(description) > 300:
            # Kürze sehr lange Beschreibungen
            note = description[:300] + "..."
        elif len(lines) > 5:
            # Sammle zusätzliche Informationen
            additional_info = []
            for line in lines[3:]:
                if line and not any(info in line for info in [contact_info['phone'], contact_info['email']]):
                    additional_info.append(line)
            if additional_info:
                note = " | ".join(additional_info[:3])
        
        entry = {
            'name': name,
            'specialization': specialization,
            'address': address,
            'phone': contact_info['phone'],
            'plz': plz,
            'plz_prefix': plz_prefix,
            'region': region,
            'country': country
        }
        
        # Zusätzliche Felder hinzufügen
        if contact_info['email']:
            entry['email'] = contact_info['email']
        if contact_info['website']:
            entry['website'] = contact_info['website']
        if note:
            entry['note'] = note
            
        return entry
            
    def parse_marker_info(self, info_text: str) -> Optional[Dict]:
        """Parst die Marker-Informationen in ein JSON-Format"""
        if not info_text or len(info_text.strip()) < 10:
            return None
            
        lines = [line.strip() for line in info_text.split('\n') if line.strip()]
        
        if not lines:
            return None
            
        # Name ist meist die erste Zeile
        name = self.clean_text(lines[0])
        
        # Suche nach Adresse, Spezialisierung, etc.
        address = ""
        specialization = ""
        note = ""
        
        # Extrahiere Kontaktinformationen
        contact_info = self.extract_contact_info(info_text)
        
        # Versuche Adresse zu finden (enthält meist PLZ)
        for line in lines[1:]:
            if re.search(r'\d{4,5}', line):  # Zeile mit PLZ
                address = self.clean_text(line)
                break
                
        # Wenn keine Adresse mit PLZ gefunden, nimm die zweite Zeile
        if not address and len(lines) > 1:
            address = self.clean_text(lines[1])
            
        # Suche nach Spezialisierung
        spec_keywords = ['spezialisiert', 'aufnahme', 'pflege', 'arten', 'vögel', 'greif', 'eule', 'sing']
        for line in lines:
            if any(keyword in line.lower() for keyword in spec_keywords):
                specialization = self.clean_text(line)
                break
                
        # Extrahiere PLZ-Informationen
        plz, plz_prefix, region, country = self.extract_plz_info(address)
        
        entry = {
            'name': name,
            'specialization': specialization,
            'address': address,
            'phone': contact_info['phone'],
            'plz': plz,
            'plz_prefix': plz_prefix,
            'region': region,
            'country': country
        }
        
        # Füge zusätzliche Felder hinzu wenn vorhanden
        if contact_info['email']:
            entry['email'] = contact_info['email']
        if contact_info['website']:
            entry['website'] = contact_info['website']
        if note:
            entry['note'] = note
            
        return entry
        
    def save_data(self):
        """Speichert die gesammelten Daten"""
        if not self.data:
            logger.warning("Keine neuen Daten zum Speichern gefunden")
            return
            
        # Füge neue Daten zu bestehenden hinzu
        combined_data = self.existing_data + self.data
        
        # Erstelle Backup der bestehenden Datei
        if os.path.exists(self.json_file):
            backup_file = f"{self.json_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.rename(self.json_file, backup_file)
            logger.info(f"Backup erstellt: {backup_file}")
            
        # Speichere kombinierte Daten
        try:
            with open(self.json_file, 'w', encoding='utf-8') as f:
                json.dump(combined_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Daten gespeichert: {len(self.data)} neue Einträge, {len(combined_data)} total")
        except Exception as e:
            logger.error(f"Fehler beim Speichern: {e}")
            
    def run(self):
        """Hauptmethode zum Ausführen des Scrapers"""
        logger.info("Starte NABU Google Maps Scraper")
        
        self.load_existing_data()
        
        # Versuche verschiedene Methoden zum Datensammeln
        self.scrape_kml_data()
        
        if not self.data:
            logger.info("Keine Daten über KML gefunden, versuche direkte Seitenextraktion...")
            self.scrape_maps_page()
        
        if self.data:
            self.save_data()
            logger.info(f"Scraping abgeschlossen. {len(self.data)} neue Einträge hinzugefügt.")
        else:
            logger.info("Keine neuen Einträge gefunden")


def main():
    scraper = NABUGoogleMapsScraper()
    scraper.run()


if __name__ == "__main__":
    main()
