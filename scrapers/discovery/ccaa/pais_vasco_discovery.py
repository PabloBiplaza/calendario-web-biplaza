"""
Auto-discovery para País Vasco / Euskadi usando OpenData Euskadi
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional


def auto_discover_pais_vasco(year: int) -> Optional[str]:
    """
    Descubre automáticamente la URL del JSON de calendario laboral del País Vasco.
    
    Estrategia:
    1. Probar URL predecible del JSON
    2. Si falla, buscar en el catálogo de OpenData Euskadi
    
    Returns:
        URL del JSON o None
    """
    
    print("=" * 80)
    print(f"🔎 AUTO-DISCOVERY PAÍS VASCO {year}")
    print("=" * 80)
    print()
    
    # ESTRATEGIA 1: URL predecible
    url_predecible = f"https://opendata.euskadi.eus/contenidos/ds_eventos/calendario_laboral_{year}/opendata/calendario_laboral_{year}.json"
    
    print(f"🔍 Probando URL predecible...")
    print(f"   {url_predecible}")
    
    try:
        r = requests.head(url_predecible, timeout=5)
        
        if r.status_code == 200:
            print(f"   ✅ URL válida\n")
            print("=" * 80)
            print(f"✅ URL ENCONTRADA (patrón predecible)")
            print("=" * 80)
            return url_predecible
        else:
            print(f"   ❌ No existe ({r.status_code})\n")
    except:
        print(f"   ❌ Error de conexión\n")
    
    # ESTRATEGIA 2: Buscar en el catálogo
    print(f"🔍 Buscando en catálogo de OpenData Euskadi...")
    
    try:
        url_catalogo = "https://opendata.euskadi.eus/catalogo-datos/"
        
        params = {
            'r01kQry': f'tC:euskadi;m:documentLanguage.EQ.es;mO:documentName.LIKE.calendario%20laboral,documentDescription.LIKE.calendario%20laboral',
            'r01SearchEngine': 'meta'
        }
        
        r_catalogo = requests.get(url_catalogo, params=params, timeout=15)
        
        if r_catalogo.status_code != 200:
            print(f"   ❌ Error en catálogo: {r_catalogo.status_code}")
            return None
        
        print(f"   ✅ Catálogo descargado\n")
        
        soup = BeautifulSoup(r_catalogo.text, 'html.parser')
        
        # Buscar enlace al dataset del año
        for enlace in soup.find_all('a', href=True):
            texto = enlace.get_text().lower()
            href = enlace['href']
            
            if 'calendario laboral' in texto and str(year) in texto:
                print(f"   ✅ Dataset encontrado: {texto[:60]}")
                
                # Construir URL completa
                if not href.startswith('http'):
                    href = f"https://opendata.euskadi.eus{href}"
                
                print(f"   📄 Descargando página del dataset...")
                
                r_dataset = requests.get(href, timeout=10)
                
                if r_dataset.status_code != 200:
                    continue
                
                # Buscar enlace al JSON
                soup_dataset = BeautifulSoup(r_dataset.text, 'html.parser')
                
                for enlace_json in soup_dataset.find_all('a', href=True):
                    href_json = enlace_json['href']
                    
                    if '.json' in href_json.lower() and 'calendario_laboral' in href_json:
                        # Construir URL completa
                        if not href_json.startswith('http'):
                            url_json = f"https://opendata.euskadi.eus{href_json}"
                        else:
                            url_json = href_json
                        
                        print(f"   ✅ JSON encontrado: {url_json}\n")
                        print("=" * 80)
                        print(f"✅ URL ENCONTRADA VIA CATÁLOGO")
                        print("=" * 80)
                        
                        return url_json
        
        print(f"   ❌ No se encontró dataset para {year}\n")
        return None
        
    except Exception as e:
        print(f"\n❌ Error en auto-discovery: {e}")
        print("\n📋 Búsqueda manual:")
        print(f"   1. Visita: https://opendata.euskadi.eus/catalogo-datos/")
        print(f"   2. Busca: 'calendario laboral {year}'")
        print(f"   3. Descarga el JSON")
        print(f"   4. Añade la URL a: config/pais_vasco_urls_cache.json")
        
        return None


if __name__ == "__main__":
    import sys
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
    
    url = auto_discover_pais_vasco(year)
    
    if url:
        print(f"\n🎯 Resultado: {url}")
    else:
        print(f"\n❌ No se pudo encontrar URL para {year}")
