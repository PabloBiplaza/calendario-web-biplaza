"""
Auto-discovery de URLs del BOJA (Boletín Oficial de la Junta de Andalucía)
Busca automáticamente las resoluciones de festivos locales publicadas cada año
"""

from typing import Dict, Optional
import requests
from bs4 import BeautifulSoup
import re


def auto_discover_andalucia(year: int) -> Optional[str]:
    """
    Intenta descubrir automáticamente la URL del BOJA con festivos locales.
    
    Args:
        year: Año para el cual buscar festivos
        
    Returns:
        URL del BOJA si se encuentra, None si no
    """
    print(f"🔍 Buscando URL del BOJA para festivos locales de Andalucía {year}...")
    
    # El BOJA suele publicar en octubre del año anterior
    year_publicacion = year - 1
    
    # Provincias que DEBEN aparecer en el documento correcto
    provincias_requeridas = ['ALMERÍA', 'CÁDIZ', 'CÓRDOBA', 'GRANADA', 'HUELVA', 'JAÉN', 'MÁLAGA', 'SEVILLA']
    
    # Probar diferentes números de boletín (típicamente entre 180-210)
    for numero_boletin in range(180, 220):
        # Probar diferentes números de documento
        for num_doc in range(1, 50):
            url = f"https://www.juntadeandalucia.es/boja/{year_publicacion}/{numero_boletin}/{num_doc}"
            
            try:
                r = requests.get(url, timeout=5)
                if r.status_code == 200:
                    texto = r.text
                    
                    # VALIDACIÓN ESTRICTA:
                    # 1. Debe contener "festivos locales" o "fiestas locales"
                    if 'festivos locales' not in texto.lower() and 'fiestas locales' not in texto.lower():
                        continue
                    
                    # 2. Debe contener el año
                    if str(year) not in texto:
                        continue
                    
                    # 3. Debe contener AL MENOS 6 de las 8 provincias
                    provincias_encontradas = sum(1 for prov in provincias_requeridas if prov in texto)
                    if provincias_encontradas < 6:
                        continue
                    
                    # 4. Debe contener múltiples municipios (buscar patrón de fechas)
                    # Patrón: DD DE MES (aparece muchas veces en el documento correcto)
                    fechas_encontradas = len(re.findall(r'\d{1,2}\s+DE\s+(?:ENERO|FEBRERO|MARZO|ABRIL|MAYO|JUNIO|JULIO|AGOSTO|SEPTIEMBRE|OCTUBRE|NOVIEMBRE|DICIEMBRE)', texto))
                    
                    # El documento correcto tiene ~1500 fechas (746 municipios × 2)
                    if fechas_encontradas < 1000:
                        continue
                    
                    print(f"   ✅ URL encontrada: {url}")
                    print(f"      Provincias: {provincias_encontradas}/8")
                    print(f"      Fechas: {fechas_encontradas}")
                    return url
                    
            except Exception as e:
                continue
    
    print(f"   ❌ No se encontró URL automáticamente para {year}")
    return None


def get_cached_url(year: int, cache_file: str = 'config/andalucia_urls_cache.json') -> Optional[str]:
    """
    Obtiene URL desde el caché si existe.
    
    Args:
        year: Año
        cache_file: Archivo de caché
        
    Returns:
        URL si existe en caché, None si no
    """
    import json
    import os
    
    if not os.path.exists(cache_file):
        return None
    
    try:
        with open(cache_file, 'r') as f:
            cache = json.load(f)
        
        url = cache.get('locales', {}).get(str(year))
        if url:
            print(f"📦 URL cargada desde caché: {url}")
        return url
    except:
        return None


def save_to_cache(year: int, url: str, tipo: str = 'locales', cache_file: str = 'config/andalucia_urls_cache.json'):
    """
    Guarda URL en el caché.
    
    Args:
        year: Año
        url: URL a guardar
        tipo: Tipo de festivo (locales, autonomicos)
        cache_file: Archivo de caché
    """
    import json
    import os
    
    # Cargar caché existente
    cache = {}
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                cache = json.load(f)
        except:
            cache = {}
    
    # Actualizar caché
    if tipo not in cache:
        cache[tipo] = {}
    
    cache[tipo][str(year)] = url
    
    # Guardar
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(cache, f, indent=2)
    
    print(f"💾 URL guardada en caché: {cache_file}")


if __name__ == "__main__":
    import sys
    
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
    
    print(f"{'='*80}")
    print(f"🔍 AUTO-DISCOVERY: Andalucía Locales {year}")
    print(f"{'='*80}\n")
    
    # Intentar desde caché primero
    url = get_cached_url(year)
    
    if not url:
        # Buscar automáticamente
        url = auto_discover_andalucia(year)
        
        if url:
            # Guardar en caché
            save_to_cache(year, url)
    
    if url:
        print(f"\n✅ URL final: {url}")
    else:
        print(f"\n❌ No se pudo encontrar URL para {year}")