#!/usr/bin/env python3
"""
Script zum Entfernen der groben Koordinaten aus wildvogelhilfen.json
Damit fix_coordinates.py die exakten Koordinaten aus dem Cache einfügen kann.
"""

import json
from pathlib import Path

def remove_rough_coordinates():
    """Entfernt die groben Koordinaten aus allen Stationen"""
    
    stations_path = Path('data/wildvogelhilfen.json')
    if not stations_path.exists():
        print("❌ data/wildvogelhilfen.json nicht gefunden!")
        return False
    
    print("🧹 Entferne grobe Koordinaten aus wildvogelhilfen.json...")
    
    try:
        # Stationen laden
        with open(stations_path, 'r', encoding='utf-8') as f:
            stations = json.load(f)
        
        print(f"📍 {len(stations)} Stationen geladen")
        
        # Koordinaten entfernen
        removed_count = 0
        for station in stations:
            had_coords = False
            
            # Latitude und Longitude entfernen falls vorhanden
            if 'latitude' in station:
                del station['latitude']
                had_coords = True
            
            if 'longitude' in station:
                del station['longitude']
                had_coords = True
            
            if had_coords:
                removed_count += 1
        
        # Zurück speichern
        with open(stations_path, 'w', encoding='utf-8') as f:
            json.dump(stations, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Koordinaten von {removed_count} Stationen entfernt")
        print(f"💾 Datei gespeichert: {stations_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False

if __name__ == '__main__':
    print("🗺️  KOORDINATEN-BEREINIGUNG")
    print("=" * 50)
    
    if remove_rough_coordinates():
        print("\n🎉 Bereinigung abgeschlossen!")
        print("   Führen Sie jetzt 'python3 fix_coordinates.py --geocode' aus")
        print("   um die exakten Koordinaten aus dem Cache einzufügen.")
    else:
        print("\n❌ Bereinigung fehlgeschlagen!")
