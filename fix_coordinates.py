#!/usr/bin/env python3
"""
Skript zur Korrektur der Koordinaten basierend auf PLZ
"""

import json
import re
import hashlib
import time
import argparse
from pathlib import Path
from typing import Dict, Tuple, Optional

import requests

def extract_plz_from_address(address: str) -> str:
    """Extrahiert die PLZ (DE 5-stellig, AT/CH 4-stellig) aus der Adresse."""
    if not address:
        return None
    # Zuerst 5-stellig versuchen
    m5 = re.search(r'\b(\d{5})\b', address)
    if m5:
        return m5.group(1)
    # Dann 4-stellig (für AT / CH)
    m4 = re.search(r'\b(\d{4})\b', address)
    if m4:
        return m4.group(1)
    return None

def _hash_offset(key: str, scale: float = 0.18) -> Tuple[float, float]:
    h = hashlib.md5(key.encode('utf-8')).hexdigest()
    a = int(h[:8], 16) / 0xFFFFFFFF - 0.5
    b = int(h[8:16], 16) / 0xFFFFFFFF - 0.5
    return a * scale, b * scale

DE_CENTROIDS = {
    '0': (51.1, 13.4), '1': (52.5, 13.3), '2': (53.6, 10.0), '3': (52.3, 9.7),
    '4': (51.5, 7.5), '5': (50.8, 7.2), '6': (50.1, 8.7), '7': (48.8, 9.2),
    '8': (48.1, 11.5), '9': (49.5, 11.1)
}
AT_CENTROIDS = {
    '1': (48.21, 16.37), '2': (48.2, 15.7), '3': (48.3, 14.3), '4': (47.8, 13.0),
    '5': (47.3, 11.4), '6': (47.25, 9.6), '7': (46.7, 14.2), '8': (47.2, 15.6), '9': (47.5, 16.4)
}
CH_CENTROIDS = {
    '1': (47.38, 8.54), '2': (47.56, 7.59), '3': (46.95, 7.45), '4': (47.05, 8.31),
    '5': (47.42, 9.37), '6': (46.85, 9.53), '7': (46.23, 7.36), '8': (46.0, 8.95), '9': (46.52, 6.63)
}
IT_CENTROIDS = {
    # Nur grobe Zentren für Nord-Italien (PLZ 39xxx, 46xxx etc.)
    '39': (46.5, 11.35),  # Südtirol
    '46': (45.65, 9.7),   # Lombardei
    '04': (44.05, 12.57)  # Rimini Umgebung (fiktiv, da 479xx real wäre)
}

def get_coordinates_for_plz(plz: str, country: str = 'Deutschland') -> Tuple[Optional[float], Optional[float]]:
    if not plz:
        return None, None
    country = country.lower()
    base = None
    if country == 'deutschland' and len(plz) == 5:
        if plz[0] == '0':
            second = plz[1]
            east_map = {
                '1': (51.05, 13.74),  # Dresden
                '2': (51.16, 14.99),  # Görlitz/Bautzen
                '3': (51.75, 14.33),  # Cottbus
                '4': (51.34, 12.37),  # Leipzig
                '5': (51.48, 11.97),  # Halle (Saale)
                '6': (51.50, 11.00),  # West Sachsen-Anhalt
                '7': (50.93, 11.59),  # Jena / Weimar
                '8': (50.70, 12.50),  # Zwickau / Plauen
                '9': (50.83, 12.92),  # Chemnitz
            }
            base = east_map.get(second)
        if not base and plz[0] in DE_CENTROIDS:
            base = DE_CENTROIDS[plz[0]]
    elif country == 'österreich' and len(plz) == 4 and plz[0] in AT_CENTROIDS:
        base = AT_CENTROIDS[plz[0]]
    elif country == 'schweiz' and len(plz) == 4 and plz[0] in CH_CENTROIDS:
        base = CH_CENTROIDS[plz[0]]
    elif country == 'italien':
        # Versuche zwei Präfixlängen
        if len(plz) >= 2 and plz[:2] in IT_CENTROIDS:
            base = IT_CENTROIDS[plz[:2]]
        elif len(plz) >= 3 and plz[:3] in IT_CENTROIDS:
            base = IT_CENTROIDS[plz[:3]]
    if not base:
        return None, None
    lat_off, lon_off = _hash_offset(plz)
    return round(base[0] + lat_off, 4), round(base[1] + lon_off, 4)

def geocode_plz_city(plz: str, city: str, country: str, session: requests.Session, cache: Dict, delay: float = 1.0) -> Tuple[Optional[float], Optional[float]]:
    """Fragt Nominatim nach exakten Koordinaten (Cache genutzt)."""
    key = f"{plz}|{city.lower()}|{country.lower()}"
    if key in cache:
        return cache[key]
    url = "https://nominatim.openstreetmap.org/search"
    params = {"postalcode": plz, "city": city, "country": country, "format": "json", "limit": 1}
    headers = {"User-Agent": "wvhMap/1.0 (kontakt@example.com)"}
    try:
        resp = session.get(url, params=params, headers=headers, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            if data:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                cache[key] = (lat, lon)
                time.sleep(delay)
                return lat, lon
    except Exception:
        pass
    cache[key] = (None, None)
    return None, None

def fix_coordinates_in_json(geocode: bool = False, only_missing: bool = False, max_geocode: Optional[int] = None):
    """Korrigiert / präzisiert Koordinaten; optional exaktes Geocoding."""
    path = Path('data/wildvogelhilfen.json')
    stations = json.loads(path.read_text(encoding='utf-8'))
    print(f"🔍 Verarbeite {len(stations)} Stationen... (geocode={'on' if geocode else 'off'})")

    cache_path = Path('data/geocode_cache.json')
    if cache_path.exists():
        geocode_cache = json.loads(cache_path.read_text(encoding='utf-8'))
    else:
        geocode_cache = {}

    session = requests.Session()
    fixed_count = 0
    skipped_count = 0
    cleaned_count = 0
    geocoded = 0

    for station in stations:
        address = station.get('address', '')
        plz = extract_plz_from_address(address)
        country = station.get('country', 'Deutschland')
        if not plz:
            print(f"❌ Keine PLZ: {address[:60]}")
            skipped_count += 1
            continue

        # Stadt extrahieren (alles nach PLZ bis Komma / Ende)
        city = ''
        mcity = re.search(rf'{plz}\s+([^,]+)', address)
        if mcity:
            city = mcity.group(1).strip()

        # Optional exaktes Geocoding
        lat = lon = None
        if geocode and city and (not only_missing or not station.get('latitude')):
            if max_geocode is None or geocoded < max_geocode:
                lat, lon = geocode_plz_city(plz, city, country, session, geocode_cache)
                if lat and lon:
                    station['latitude'] = round(lat, 6)
                    station['longitude'] = round(lon, 6)
                    geocoded += 1
                    print(f"🌐 Geocoded {station['name'][:45]:<45} -> {lat:.6f},{lon:.6f}")
                    fixed_count += 1
                    # Continue to next station after exact match
                    station['plz'] = plz
                    station['plz_prefix'] = plz[0] if country.lower() == 'deutschland' and len(plz)==5 else country.lower()
                    continue

        # Fallback deterministische Koordinaten
        base_lat, base_lon = get_coordinates_for_plz(plz, country)
        if base_lat and base_lon:
            if not station.get('latitude') or not station.get('longitude') or not only_missing:
                station['latitude'] = base_lat
                station['longitude'] = base_lon
                fixed_count += 1
                print(f"✅ Fallback {station['name'][:50]:<50} -> {base_lat:.4f},{base_lon:.4f}")
        else:
            print(f"⚠️  Kein Fallback für {plz} ({station['name'][:40]})")
            skipped_count += 1

        station['plz'] = plz
        if country.lower() == 'deutschland' and len(plz) == 5:
            station['plz_prefix'] = plz[0]
        else:
            station['plz_prefix'] = country.lower()

        # Aufräumen
        spec = station.get('specialization')
        if spec and station['name'] in spec:
            new_spec = spec.replace(station['name'], '').strip()
            if new_spec:
                station['specialization'] = new_spec
                cleaned_count += 1
        addr = station.get('address')
        if addr and station['name'] in addr:
            new_addr = addr.replace(station['name'], '').strip(', ') or addr
            if new_addr != addr:
                station['address'] = new_addr
                cleaned_count += 1

    # Speichern
    path.write_text(json.dumps(stations, ensure_ascii=False, indent=2), encoding='utf-8')
    cache_path.write_text(json.dumps(geocode_cache, ensure_ascii=False, indent=2), encoding='utf-8')

    print("\n📊 Zusammenfassung:")
    print(f"   🌐 Geocoded exakt: {geocoded}")
    print(f"   ✅ Koordinaten gesetzt/aktualisiert: {fixed_count}")
    print(f"   ⚠️  Übersprungen: {skipped_count}")
    print(f"   🧹 Bereinigt: {cleaned_count}")
    print(f"   📁 Datei: data/wildvogelhilfen.json")
    print(f"   💾 Cache: data/geocode_cache.json ({len(geocode_cache)} Keys)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Koordinaten fixer mit optionalem Geocoding (Nominatim)")
    parser.add_argument('--geocode', action='store_true', help='Exakte Koordinaten via Nominatim (langsam)')
    parser.add_argument('--only-missing', action='store_true', help='Nur fehlende Koordinaten geocoden / setzen')
    parser.add_argument('--max', type=int, default=None, help='Maximale Anzahl Geocode-Anfragen (z.B. zum Testen)')
    args = parser.parse_args()
    fix_coordinates_in_json(geocode=args.geocode, only_missing=args.only_missing, max_geocode=args.max)
