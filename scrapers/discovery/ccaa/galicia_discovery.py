"""
Auto-discovery para Galicia usando el catálogo de datos abiertos
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional
import re


def auto_discover_galicia(year: int) -> Optional[str]:
    """
    Descubre automáticamente la URL de festivos locales de Galicia
    usando el catálogo de datos abiertos de la Xunta.
    
    Estrategia:
    1. Descargar RDF del catálogo
    2. Buscar dataset calendario-laboral-{year}
    3. Extraer URL del DOG desde el dataset
    
    Returns:
        URL del DOG o None
    """
    
    print("=" * 80)
    print(f"🔎 AUTO-DISCOVERY GALICIA {year} (via RDF)")
    print("=" * 80)
    print()
    
    try:
        # PASO 1: Descargar RDF
        print("📥 Descargando catálogo RDF...")
        url_rdf = "https://abertos.xunta.gal/busca-de-datos.rdf"
        
        r = requests.get(url_rdf, timeout=15)
        
        if r.status_code != 200:
            print(f"   ❌ Error descargando RDF: {r.status_code}")
            return None
        
        print(f"   ✅ RDF descargado: {len(r.text)} caracteres\n")
        
        # PASO 2: Parsear y buscar dataset
        print(f"🔍 Buscando dataset calendario-laboral-{year}...")
        
        soup = BeautifulSoup(r.text, 'xml')
        
        # Buscar dataset con URL que contenga calendario-laboral-{year}
        dataset_url = None
        for dataset in soup.find_all('dcat:Dataset'):
            about = dataset.get('rdf:about', '')
            
            if f'calendario-laboral-{year}' in about:
                dataset_url = about
                print(f"   ✅ Dataset encontrado: {dataset_url}\n")
                break
        
        if not dataset_url:
            print(f"   ❌ No se encontró dataset para {year}")
            print(f"   💡 Puede que aún no esté publicado\n")
            return None
        
        # PASO 3: Descargar página del dataset
        print("📄 Descargando página del dataset...")
        
        r_dataset = requests.get(dataset_url, timeout=10)
        
        if r_dataset.status_code != 200:
            print(f"   ❌ Error: {r_dataset.status_code}")
            return None
        
        print(f"   ✅ Página descargada\n")
        
        # PASO 4: Extraer URL del DOG
        print("🔗 Extrayendo URL del DOG...")
        
        soup_dataset = BeautifulSoup(r_dataset.text, 'html.parser')
        
        # Buscar enlace al DOG con "festivos locales" o "fiestas locales"
        dog_url = None
        for enlace in soup_dataset.find_all('a', href=True):
            href = enlace['href']
            texto = enlace.get_text().lower()
            
            if 'xunta.gal/dog' in href and ('festivos locales' in texto or 'fiestas locales' in texto or 'local' in texto):
                dog_url = href
                print(f"   ✅ URL encontrada: {dog_url}\n")
                break
        
        if not dog_url:
            print(f"   ⚠️  No se encontró enlace al DOG en el dataset")
            print(f"   💡 Puedes buscar manualmente en: {dataset_url}\n")
            return None
        
        # PASO 5: Convertir de gallego a castellano si es necesario
        if dog_url.endswith('_gl.html'):
            dog_url_es = dog_url.replace('_gl.html', '_es.html')
            
            # Verificar que la versión en castellano existe
            r_test = requests.head(dog_url_es, timeout=5)
            if r_test.status_code == 200:
                print(f"   🔄 Convirtiendo a versión en castellano")
                dog_url = dog_url_es
        
        print("=" * 80)
        print(f"✅ URL ENCONTRADA VIA AUTO-DISCOVERY")
        print("=" * 80)
        
        return dog_url
        
    except Exception as e:
        print(f"\n❌ Error en auto-discovery: {e}")
        print("\n📋 Búsqueda manual:")
        print(f"   1. Visita: https://abertos.xunta.gal/busca-de-datos")
        print(f"   2. Busca: 'calendario laboral {year}'")
        print(f"   3. Encuentra el enlace al DOG para festivos locales")
        print(f"   4. Añádelo a: config/galicia_urls_cache.json")
        
        return None


if __name__ == "__main__":
    import sys
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2027
    
    url = auto_discover_galicia(year)
    
    if url:
        print(f"\n🎯 Resultado: {url}")
    else:
        print(f"\n❌ No se pudo encontrar URL para {year}")
