#!/usr/bin/env python3
"""
Einfaches Manual-Update Script für Wildvogelhilfe-Daten
Führt alle notwendigen Schritte in der richtigen Reihenfolge aus.
"""

import subprocess
import sys
import argparse
from pathlib import Path

def run_command(cmd, description):
    """Führt einen Befehl aus und zeigt den Status"""
    print(f"\n🔄 {description}...")
    print(f"   Ausführe: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {description} erfolgreich")
        if result.stdout.strip():
            print("📋 Ausgabe:")
            for line in result.stdout.strip().split('\n')[-10:]:  # Nur letzte 10 Zeilen
                print(f"   {line}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} fehlgeschlagen")
        if e.stdout:
            print("📋 Stdout:")
            print(f"   {e.stdout}")
        if e.stderr:
            print("📋 Stderr:")
            print(f"   {e.stderr}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Manual Update für Wildvogelhilfe-Daten')
    parser.add_argument('--skip-scraping', action='store_true',
                       help='Überspringe das Scraping (nutze vorhandene Daten)')
    parser.add_argument('--cache-max', type=int, default=20,
                       help='Maximale Anzahl Cache-Updates (Standard: 20)')
    parser.add_argument('--fix-max', type=int, default=10,
                       help='Maximale Anzahl Koordinaten-Korrekturen (Standard: 10)')
    
    args = parser.parse_args()
    
    print("🦅 WILDVOGELHILFE MANUAL UPDATE")
    print("=" * 50)
    
    # Stelle sicher, dass wir im richtigen Verzeichnis sind
    script_dir = Path(__file__).parent
    if script_dir != Path.cwd():
        print(f"📁 Wechsle zu Projektverzeichnis: {script_dir}")
        import os
        os.chdir(script_dir)
    
    success_count = 0
    total_steps = 3 if not args.skip_scraping else 2
    
    # Schritt 1: Scraping (optional)
    if not args.skip_scraping:
        if run_command([sys.executable, 'scraper.py'], 'Neue Daten scrapen'):
            success_count += 1
    else:
        print("⏭️  Scraping übersprungen")
        success_count += 1
    
    # Schritt 2: Cache erweitern
    cache_cmd = [sys.executable, 'auto_update_cache.py', '--max', str(args.cache_max)]
    if run_command(cache_cmd, f'Cache erweitern (max {args.cache_max} Orte)'):
        success_count += 1
    
    # Schritt 3: Koordinaten korrigieren
    fix_cmd = [sys.executable, 'fix_coordinates.py', '--only-missing', '--max', str(args.fix_max)]
    if run_command(fix_cmd, f'Koordinaten korrigieren (max {args.fix_max})'):
        success_count += 1
    
    # Zusammenfassung
    print(f"\n📊 UPDATE ABGESCHLOSSEN")
    print(f"   ✅ {success_count}/{total_steps} Schritte erfolgreich")
    
    if success_count == total_steps:
        print("🎉 Alle Updates erfolgreich!")
        
        # Statistiken anzeigen
        try:
            import json
            
            if Path('data/wildvogelhilfen.json').exists():
                with open('data/wildvogelhilfen.json') as f:
                    stations = json.load(f)
                print(f"   📍 {len(stations)} Wildvogelhilfe-Stationen")
            
            if Path('data/geocode_cache.json').exists():
                with open('data/geocode_cache.json') as f:
                    cache = json.load(f)
                print(f"   🗺️  {len(cache)} Geocode-Cache-Einträge")
                
        except Exception as e:
            print(f"   ⚠️  Konnte Statistiken nicht laden: {e}")
    else:
        print("⚠️  Einige Updates sind fehlgeschlagen")
        return 1
    
    return 0

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  Unterbrochen durch Benutzer")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
        sys.exit(1)
