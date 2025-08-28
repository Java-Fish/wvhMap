#!/usr/bin/env python3
"""
Automatische Erweiterung der geocode_cache.json
Dieses Script sammelt neue Orte aus wildvogelhilfen.json und erweitert den Cache automatisch.
"""

import json
import re
import time
import argparse
from pathlib import Path
from typing import Dict, Set, List, Tuple, Optional
import requests

def load_cache() -> Dict:
    """Lädt den bestehenden Geocode-Cache"""
    cache_path = Path('data/geocode_cache.json')
    if cache_path.exists():
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Fehler beim Laden des Cache: {e}")
            return {}
    return {}

def load_stations() -> List[Dict]:
    """Lädt die Wildvogelhilfe-Stationen"""
    stations_path = Path('data/wildvogelhilfen.json')
    if not stations_path.exists():
        print("❌ data/wildvogelhilfen.json nicht gefunden!")
        return []
    
    try:
        with open(stations_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Fehler beim Laden der Stationen: {e}")
        return []

def extract_plz_city_country(station: Dict) -> Optional[Tuple[str, str, str]]:
    """Extrahiert PLZ, Ort und Land aus einer Station"""
    address = station.get('address', '')
    if not address:
        return None
    
    # PLZ und Ort extrahieren
    # Für Deutschland: 5-stellige PLZ
    match = re.search(r'\b(\d{5})\s+([A-Za-zÄÖÜäöüß\s\-]+?)(?:\s*,|\s*$)', address)
    if match:
        plz = match.group(1)
        city = match.group(2).strip()
        country = "deutschland"
        
        # Land basierend auf PLZ-Prefix bestimmen
        plz_prefix = station.get('plz_prefix', '')
        if plz_prefix == 'österreich':
            country = "österreich"
        elif plz_prefix == 'schweiz':
            country = "schweiz"
        elif plz_prefix == 'italien':
            country = "italien"
        
        return plz, city, country
    
    # Für Österreich/Schweiz: 4-stellige PLZ
    match = re.search(r'\b(\d{4})\s+([A-Za-zÄÖÜäöüß\s\-]+?)(?:\s*,|\s*$)', address)
    if match:
        plz = match.group(1)
        city = match.group(2).strip()
        
        plz_prefix = station.get('plz_prefix', '')
        if plz_prefix == 'österreich':
            country = "österreich"
        elif plz_prefix == 'schweiz':
            country = "schweiz"
        else:
            country = "deutschland"  # Fallback
        
        return plz, city, country
    
    return None

def create_cache_key(plz: str, city: str, country: str) -> str:
    """Erstellt einen Cache-Schlüssel im Format des bestehenden Systems"""
    # Normalisiere Stadt-Namen (kleinbuchstaben, Leerzeichen entfernen)
    city_clean = city.lower().strip()
    city_clean = re.sub(r'\s+', ' ', city_clean)
    
    return f"{plz}|{city_clean}|{country}"

def geocode_location(plz: str, city: str, country: str, session: requests.Session) -> Optional[Tuple[float, float]]:
    """Geocodiert einen Ort mit Nominatim"""
    try:
        # Vollständige Adresse für bessere Ergebnisse
        search_query = f"{plz} {city}, {country}"
        
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': search_query,
            'format': 'json',
            'limit': 1,
            'countrycodes': get_country_code(country)
        }
        
        response = session.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data and len(data) > 0:
            result = data[0]
            lat = float(result['lat'])
            lon = float(result['lon'])
            print(f"  ✅ {plz} {city} -> {lat:.6f}, {lon:.6f}")
            return lat, lon
        else:
            print(f"  ❌ Keine Ergebnisse für: {plz} {city}, {country}")
            return None
            
    except Exception as e:
        print(f"  ⚠️  Geocoding-Fehler für {plz} {city}: {e}")
        return None

def get_country_code(country: str) -> str:
    """Konvertiert Ländernamen zu ISO-Codes für Nominatim"""
    mapping = {
        'deutschland': 'de',
        'österreich': 'at',
        'schweiz': 'ch',
        'italien': 'it'
    }
    return mapping.get(country.lower(), 'de')

def find_missing_locations(stations: List[Dict], cache: Dict) -> List[Tuple[str, str, str]]:
    """Findet Orte, die noch nicht im Cache sind"""
    missing = []
    seen = set()
    
    for station in stations:
        location_data = extract_plz_city_country(station)
        if not location_data:
            continue
            
        plz, city, country = location_data
        cache_key = create_cache_key(plz, city, country)
        
        # Vermeid Duplikate
        if cache_key in seen:
            continue
        seen.add(cache_key)
        
        # Prüfe ob im Cache
        if cache_key not in cache:
            missing.append((plz, city, country))
    
    return missing

def save_cache(cache: Dict):
    """Speichert den erweiterten Cache"""
    cache_path = Path('data/geocode_cache.json')
    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        print(f"💾 Cache gespeichert: {len(cache)} Einträge")
    except Exception as e:
        print(f"❌ Fehler beim Speichern: {e}")

def main():
    parser = argparse.ArgumentParser(description='Automatische Erweiterung des Geocode-Cache')
    parser.add_argument('--max', type=int, default=50, 
                       help='Maximale Anzahl neuer Geocode-Anfragen (Standard: 50)')
    parser.add_argument('--delay', type=float, default=1.0,
                       help='Pause zwischen Anfragen in Sekunden (Standard: 1.0)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Nur anzeigen was gemacht würde, nichts ändern')
    
    args = parser.parse_args()
    
    print("🗺️  AUTOMATISCHE CACHE-ERWEITERUNG")
    print("=" * 50)
    
    # Daten laden
    print("📂 Lade bestehende Daten...")
    cache = load_cache()
    stations = load_stations()
    
    if not stations:
        print("❌ Keine Stationen gefunden!")
        return
    
    print(f"✅ {len(cache)} Cache-Einträge geladen")
    print(f"✅ {len(stations)} Stationen geladen")
    
    # Fehlende Orte finden
    print("\n🔍 Suche fehlende Orte...")
    missing = find_missing_locations(stations, cache)
    
    if not missing:
        print("🎉 Alle Orte sind bereits im Cache!")
        return
    
    print(f"📍 {len(missing)} fehlende Orte gefunden")
    
    if args.dry_run:
        print("\n📝 DRY RUN - würde folgende Orte geocodieren:")
        for i, (plz, city, country) in enumerate(missing[:args.max]):
            print(f"  {i+1:3d}. {plz} {city}, {country}")
        return
    
    # Geocoding starten
    print(f"\n🌍 Starte Geocoding (max {args.max} Anfragen)...")
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'WildvogelhilfeApp/1.0 (Automated Cache Update)'
    })
    
    new_entries = 0
    failed_entries = 0
    
    for i, (plz, city, country) in enumerate(missing[:args.max]):
        print(f"🔍 {i+1:3d}/{min(len(missing), args.max)}: {plz} {city}, {country}")
        
        # Geocodierung
        coords = geocode_location(plz, city, country, session)
        cache_key = create_cache_key(plz, city, country)
        
        if coords:
            cache[cache_key] = list(coords)  # [lat, lon]
            new_entries += 1
        else:
            cache[cache_key] = [None, None]  # Fehlgeschlagen markieren
            failed_entries += 1
        
        # Pause zwischen Anfragen
        if i < len(missing) - 1:  # Nicht nach dem letzten Eintrag warten
            time.sleep(args.delay)
    
    # Cache speichern
    print(f"\n💾 Speichere erweiterten Cache...")
    save_cache(cache)
    
    # Statistiken
    print(f"\n📊 ERGEBNISSE:")
    print(f"   ✅ {new_entries} neue Koordinaten hinzugefügt")
    print(f"   ❌ {failed_entries} Orte nicht gefunden")
    print(f"   📍 {len(cache)} Gesamt-Einträge im Cache")
    print(f"\n🎉 Cache-Update abgeschlossen!")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Unterbrochen durch Benutzer")
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
