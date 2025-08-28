# Python Script zum Scraping der Wildvogelhilfe-Daten
# Verbesserte Version basierend auf der echten Website-Struktur

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from geopy.geocoders import Nominatim
from urllib.parse import urljoin

class WildvogelhilfeScraper:
    def __init__(self):
        # URLs für alle zu scrapenden Seiten
        self.urls = [
            "https://wp.wildvogelhilfe.org/de/auffangstationen/auffangstationen-plz-gebiet-0/",
            "https://wp.wildvogelhilfe.org/de/auffangstationen/auffangstationen-plz-gebiet-1/",
            "https://wp.wildvogelhilfe.org/de/auffangstationen/auffangstationen-plz-gebiet-2/",
            "https://wp.wildvogelhilfe.org/de/auffangstationen/auffangstationen-plz-gebiet-3/",
            "https://wp.wildvogelhilfe.org/de/auffangstationen/auffangstationen-plz-gebiet-4/",
            "https://wp.wildvogelhilfe.org/de/auffangstationen/auffangstationen-plz-gebiet-5/",
            "https://wp.wildvogelhilfe.org/de/auffangstationen/auffangstationen-plz-gebiet-6/",
            "https://wp.wildvogelhilfe.org/de/auffangstationen/auffangstationen-plz-gebiet-7/",
            "https://wp.wildvogelhilfe.org/de/auffangstationen/auffangstationen-plz-gebiet-8/",
            "https://wp.wildvogelhilfe.org/de/auffangstationen/auffangstationen-plz-gebiet-9/",
            "https://wp.wildvogelhilfe.org/de/auffangstationen/auffangstationen-oesterreich/",
            "https://wp.wildvogelhilfe.org/de/auffangstationen/auffangstationen-schweiz/",
            "https://wp.wildvogelhilfe.org/de/auffangstationen/auffangstationen-italien/"
        ]
        self.geolocator = Nominatim(user_agent="wildvogelhilfe_scraper_v2")
        self.stations = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def scrape_all_plz_areas(self):
        """Scrapt alle definierten URLs"""
        for i, url in enumerate(self.urls):
            # Region aus URL extrahieren
            region = self.extract_region_from_url(url)
            print(f"\n🌍 Scraping {i+1}/{len(self.urls)}: {region}")
            
            self.scrape_plz_area(url, region)
            time.sleep(2)  # Höfliche Pause zwischen Requests
    
    def extract_region_from_url(self, url):
        """Extrahiert die Region aus der URL"""
        if 'plz-gebiet-' in url:
            return url.split('plz-gebiet-')[1].split('/')[0]
        elif 'oesterreich' in url:
            return 'österreich'
        elif 'schweiz' in url:
            return 'schweiz'
        elif 'italien' in url:
            return 'italien'
        else:
            return 'unbekannt'
            
    def scrape_plz_area(self, url, plz_prefix):
        """Scrapt eine einzelne PLZ-Bereichsseite"""
        try:
            print(f"  Lade {url}...")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Hauptinhalt finden - verschiedene mögliche Container
            content_selectors = [
                'div.entry-content',
                '.entry-content', 
                '.post-content',
                '.content',
                'main'
            ]
            
            content = None
            for selector in content_selectors:
                content = soup.select_one(selector)
                if content:
                    break
                    
            if not content:
                print(f"  ⚠️  Kein Hauptinhalt gefunden für {url}")
                return
                
            # Alle h3 Überschriften finden (Stationsnamen)
            station_headers = content.find_all('h3')
            stations_found = 0
            
            for header in station_headers:
                station_data = self.parse_station_block(header, plz_prefix)
                if station_data:
                    self.stations.append(station_data)
                    stations_found += 1
                    print(f"    ✅ {station_data['name']}")
                    
            print(f"  📍 {stations_found} Stationen gefunden in PLZ-Bereich {plz_prefix}")
                    
        except requests.RequestException as e:
            print(f"  ❌ Netzwerk-Fehler bei {url}: {e}")
        except Exception as e:
            print(f"  ❌ Unerwarteter Fehler bei {url}: {e}")
            
    def parse_station_block(self, header, plz_prefix):
        """Parst einen einzelnen Station-Block nach der neuen Struktur"""
        try:
            station_name = header.get_text().strip()
            
            if not station_name or len(station_name) < 3:
                return None
                
            # Initialisierung der Datenfelder
            specialization = ""
            address_parts = []
            phone = ""
            email = ""
            website = ""
            opening_hours = ""
            
            # Alle Geschwister-Elemente nach der Überschrift sammeln bis zur nächsten h3 oder hr
            current = header.next_sibling
            text_blocks = []
            
            while current:
                if current.name == 'h3':  # Nächste Station erreicht
                    break
                elif current.name == 'hr':  # Trennlinie erreicht
                    break
                elif hasattr(current, 'get_text'):
                    text = current.get_text().strip()
                    if text and len(text) > 2:
                        text_blocks.append((current, text))
                        
                current = current.next_sibling
            
            # Text-Blöcke analysieren
            for element, text in text_blocks:
                # E-Mail Links finden
                email_links = element.find_all('a', href=lambda x: x and x.startswith('mailto:'))
                for link in email_links:
                    email = link.get('href').replace('mailto:', '').strip()
                
                # Website Links finden
                web_links = element.find_all('a', href=lambda x: x and (x.startswith('http') or x.startswith('www')))
                for link in web_links:
                    href = link.get('href', '')
                    if not href.startswith('mailto:'):
                        website = href
                
                # Telefonnummer erkennen
                if re.search(r'[Tt]el\.?:?\s*', text):
                    phone_match = re.search(r'[Tt]el\.?:?\s*([0-9\s\-\/\(\)\+]+)', text)
                    if phone_match:
                        phone = phone_match.group(1).strip()
                
                # PLZ und Ort extrahieren (5-stellige Zahl gefolgt von Ortsnamen)
                plz_match = re.search(r'\b(\d{5})\s+([A-ZÄÖÜa-zäöüß\s\-]+)', text)
                if plz_match:
                    plz = plz_match.group(1)
                    city = plz_match.group(2).strip()
                    
                    # Adresse vor PLZ suchen
                    address_before_plz = text[:plz_match.start()].strip()
                    if address_before_plz and not any(x in address_before_plz.lower() for x in ['tel', 'telefon', 'fax', 'mail']):
                        full_address = f"{address_before_plz}, {plz} {city}".strip(', ')
                        address_parts.append(full_address)
                    else:
                        address_parts.append(f"{plz} {city}")
                
                # Spezialisierung erkennen
                specialization_indicators = [
                    'spezialisiert auf', 'alle vögel', 'alle wildvögel', 'greifvögel',
                    'singvögel', 'mauersegler', 'schwalben', 'eulen', 'falken', 'dohlen'
                ]
                
                if any(indicator in text.lower() for indicator in specialization_indicators):
                    if not specialization:  # Nur die erste Spezialisierung nehmen
                        specialization = text
                
                # Öffnungszeiten erkennen
                if re.search(r'\d+\s*[-–]\s*\d+\s*uhr|montag|dienstag|mittwoch|donnerstag|freitag|samstag|sonntag', text.lower()):
                    if 'erreichbarkeit' in text.lower() or 'uhr' in text.lower():
                        opening_hours = text
            
            # Adresse zusammenbauen
            address = ' | '.join(address_parts) if address_parts else ""
            
            # Mindestanforderungen prüfen
            if not station_name or not address:
                return None
            
            # Koordinaten ermitteln mit länderspezifischer Geocoding-Strategie
            coords = self.geocode_address(address, plz_prefix)
            
            station_data = {
                'name': station_name,
                'specialization': specialization,
                'address': address,
                'phone': phone,
                'email': email,
                'website': website,
                'opening_hours': opening_hours,
                'latitude': coords[0] if coords else None,
                'longitude': coords[1] if coords else None,
                'plz_prefix': plz_prefix
            }
            
            return station_data
            
        except Exception as e:
            print(f"    ⚠️  Fehler beim Parsen der Station '{station_name}': {e}")
            return None
        
    def geocode_address(self, address, region="deutschland"):
        """Konvertiert Adresse zu Koordinaten mit verbesserter Fehlerbehandlung"""
        try:
            # Adresse bereinigen
            clean_address = self.clean_address_for_geocoding(address)
            
            # Land basierend auf Region bestimmen
            if region == "österreich":
                country = "Österreich"
            elif region == "schweiz":
                country = "Schweiz"  
            elif region == "italien":
                country = "Italien"
            else:
                country = "Deutschland"
            
            # Land zur Suche hinzufügen
            full_address = f"{clean_address}, {country}"
            
            # Geocoding mit Retry-Mechanismus
            for attempt in range(3):
                try:
                    location = self.geolocator.geocode(full_address, timeout=10)
                    if location:
                        return (location.latitude, location.longitude)
                    break  # Kein Retry wenn kein Ergebnis gefunden
                except Exception as e:
                    if attempt < 2:  # Noch Versuche übrig
                        time.sleep(1)
                        continue
                    else:
                        print(f"    ⚠️  Geocoding fehlgeschlagen für '{address}': {e}")
                        break
            
            # Fallback: Nur PLZ und Ort versuchen
            plz_match = re.search(r'(\d{4,5})\s+([A-ZÄÖÜa-zäöüß\s\-]+)', address)
            if plz_match:
                plz_city = f"{plz_match.group(1)} {plz_match.group(2).strip()}, {country}"
                try:
                    location = self.geolocator.geocode(plz_city, timeout=10)
                    if location:
                        print(f"    📍 Fallback-Geocoding erfolgreich für PLZ/Ort")
                        return (location.latitude, location.longitude)
                except:
                    pass
            
            print(f"    ❌ Koordinaten nicht gefunden für: {address}")
            return None
                
        except Exception as e:
            print(f"    ❌ Geocoding-Fehler für '{address}': {e}")
            return None
    
    def clean_address_for_geocoding(self, address):
        """Bereinigt die Adresse für besseres Geocoding"""
        # Mehrere Adressen durch | getrennt - nur die erste nehmen
        if '|' in address:
            address = address.split('|')[0].strip()
        
        # Telefonnummern und E-Mails entfernen
        address = re.sub(r'[Tt]el\.?:?.*?(?=\d{5}|$)', '', address)
        address = re.sub(r'[Ff]ax\.?:?.*?(?=\d{5}|$)', '', address)
        address = re.sub(r'[Ee]-?[Mm]ail:.*', '', address)
        
        # Mehrfache Leerzeichen entfernen
        address = re.sub(r'\s+', ' ', address).strip()
        
        return address
    
    def save_to_json(self, filename='data/wildvogelhilfen.json'):
        """Speichert die Daten als JSON mit verbesserter Datenbereinigung"""
        # Duplikate entfernen (gleicher Name + gleiche PLZ)
        unique_stations = {}
        for station in self.stations:
            # Eindeutigen Schlüssel erstellen
            key = f"{station['name'].lower()}_{station.get('plz_prefix', '')}"
            
            # Nur Stationen mit Namen und Adresse
            if station.get('name') and station.get('address'):
                if key not in unique_stations:
                    unique_stations[key] = station
                else:
                    # Bessere Station behalten (mit Koordinaten)
                    if station.get('latitude') and not unique_stations[key].get('latitude'):
                        unique_stations[key] = station
        
        valid_stations = list(unique_stations.values())
        
        # Nach PLZ sortieren
        valid_stations.sort(key=lambda x: x.get('plz_prefix', '0'))
        
        # Daten bereinigen
        for station in valid_stations:
            # Leere Felder entfernen
            station = {k: v for k, v in station.items() if v}
            
            # Telefonnummer formatieren
            if station.get('phone'):
                station['phone'] = self.clean_phone_number(station['phone'])
        
        # JSON speichern
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(valid_stations, f, ensure_ascii=False, indent=2)
            
        # Statistiken ausgeben
        total_stations = len(valid_stations)
        stations_with_coords = len([s for s in valid_stations if s.get('latitude')])
        stations_with_phone = len([s for s in valid_stations if s.get('phone')])
        stations_with_email = len([s for s in valid_stations if s.get('email')])
        
        print(f"\n📊 SCRAPING-STATISTIKEN:")
        print(f"   📍 {total_stations} eindeutige Stationen gespeichert")
        print(f"   🌍 {stations_with_coords} Stationen mit Koordinaten ({stations_with_coords/total_stations*100:.1f}%)")
        print(f"   📞 {stations_with_phone} Stationen mit Telefon ({stations_with_phone/total_stations*100:.1f}%)")
        print(f"   📧 {stations_with_email} Stationen mit E-Mail ({stations_with_email/total_stations*100:.1f}%)")
        print(f"   💾 Datei gespeichert: {filename}")
        
        # PLZ-Verteilung anzeigen
        plz_stats = {}
        for station in valid_stations:
            plz = station.get('plz_prefix', 'unknown')
            plz_stats[plz] = plz_stats.get(plz, 0) + 1
        
        print(f"\n📍 PLZ-VERTEILUNG:")
        for plz in sorted(plz_stats.keys()):
            print(f"   PLZ {plz}: {plz_stats[plz]} Stationen")
            
    def clean_phone_number(self, phone):
        """Bereinigt Telefonnummern"""
        if not phone:
            return ""
        
        # Entferne "Tel:", "Telefon:", etc.
        phone = re.sub(r'^[Tt]el\.?:?\s*', '', phone)
        phone = re.sub(r'^[Tt]elefon\.?:?\s*', '', phone)
        
        # Entferne Fax-Nummern (alles nach "Fax")
        phone = re.split(r'[Ff]ax\.?:?', phone)[0]
        
        # Entferne Zusatzinfos in Klammern am Ende
        phone = re.sub(r'\s*\([^)]*\)\s*$', '', phone)
        
        # Bereinige Whitespace
        phone = phone.strip()
        
        return phone if phone else ""

def main():
    """Hauptfunktion mit verbesserter Benutzerführung"""
    print("🦅 WILDVOGELHILFE SCRAPER v2.0")
    print("="*50)
    
    scraper = WildvogelhilfeScraper()
    
    try:
        # Test-Verbindung
        print("🔍 Teste Verbindung zur Website...")
        test_url = "https://wp.wildvogelhilfe.org/de/auffangstationen/auffangstationen-plz-gebiet-0/"
        response = scraper.session.get(test_url, timeout=10)
        response.raise_for_status()
        print("✅ Verbindung erfolgreich!")
        
        # Alle URLs scrapen
        print(f"\n📥 Starte Scraping aller Regionen...")
        scraper.scrape_all_plz_areas()
        
        # Daten speichern
        print(f"\n💾 Speichere Daten...")
        scraper.save_to_json()
        
        print(f"\n🎉 SCRAPING ABGESCHLOSSEN!")
        print(f"   Überprüfen Sie die Datei 'data/wildvogelhilfen.json'")
        print(f"   Laden Sie die Website neu, um die neuen Daten zu sehen.")
        
    except requests.RequestException as e:
        print(f"❌ Netzwerk-Fehler: {e}")
        print("   Bitte überprüfen Sie Ihre Internetverbindung.")
    except KeyboardInterrupt:
        print(f"\n⏹️  Scraping unterbrochen durch Benutzer")
        if scraper.stations:
            print(f"💾 Speichere bereits gesammelte Daten...")
            scraper.save_to_json()
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")
        if scraper.stations:
            print(f"💾 Speichere bereits gesammelte Daten...")
            scraper.save_to_json()

if __name__ == "__main__":
    # Abhängigkeiten prüfen
    try:
        import requests
        import bs4
        import geopy
    except ImportError as e:
        print(f"❌ Fehlende Abhängigkeit: {e}")
        print("📦 Installieren Sie die Abhängigkeiten mit:")
        print("   pip install -r requirements.txt")
        exit(1)
    
    main()
