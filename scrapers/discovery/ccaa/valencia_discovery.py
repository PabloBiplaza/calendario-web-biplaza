"""
Auto-discovery de URLs del DOGV (Diari Oficial de la Generalitat Valenciana)
Busca automáticamente las resoluciones de festivos locales desde la página oficial
"""

from typing import Dict, Optional
import requests
from bs4 import BeautifulSoup
import re


def auto_discover_valencia(year: int) -> Optional[str]:
    """
    Intenta descubrir automáticamente la URL del DOGV con festivos locales.
    
    Estrategia:
    1. Buscar en la página oficial: https://ceice.gva.es/es/web/dg-trabajo/calendario-laboral
    2. Encontrar el enlace a la resolución de festivos locales para el año
    3. Seguir el enlace al DOGV
    4. Extraer el PDF y validar
    
    Args:
        year: Año para el cual buscar festivos
        
    Returns:
        URL del DOGV si se encuentra, None si no
    """
    print(f"🔍 Buscando URL del DOGV para festivos locales de Valencia {year}...")
    
    url_oficial = "https://ceice.gva.es/es/web/dg-trabajo/calendario-laboral"
    
    try:
        r = requests.get(url_oficial, timeout=15)
        if r.status_code != 200:
            print(f"   ⚠️  No se pudo acceder a {url_oficial}")
            return None
        
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Buscar enlaces que contengan el año y "resolución" o "fiestas locales"
        enlaces = soup.find_all('a', href=True)
        
        for enlace in enlaces:
            href = enlace['href']
            texto = enlace.text.strip()
            
            # Filtrar: debe contener el año y "resolución" + "fiestas locales"
            if str(year) in texto:
                if 'resolución' in texto.lower() or 'resolució' in texto.lower():
                    if 'fiestas locales' in texto.lower() or 'festes locals' in texto.lower():
                        
                        # Construir URL completa
                        if href.startswith('http'):
                            url_resolucion = href
                        elif href.startswith('/'):
                            url_resolucion = f"https://ceice.gva.es{href}"
                        else:
                            # URL relativa
                            url_resolucion = f"https://ceice.gva.es/es/web/dg-trabajo/{href}"
                        
                        print(f"   🔍 Probando: {texto[:80]}...")
                        print(f"   📍 URL resolución: {url_resolucion}")
                        
                        # Seguir el enlace
                        url_pdf = _extraer_url_pdf_desde_enlace(url_resolucion, year)
                        if url_pdf:
                            print(f"   ✅ URL encontrada: {url_pdf}")
                            return url_pdf
        
        print(f"   ❌ No se encontró URL automáticamente para {year}")
        return None
        
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
        return None


def _extraer_url_pdf_desde_enlace(url_enlace: str, year: int) -> Optional[str]:
    """
    Sigue un enlace y extrae la URL del PDF.
    Puede ser que el enlace apunte directamente al DOGV o necesite redirecciones.
    
    Args:
        url_enlace: URL del enlace a seguir
        year: Año para validar
        
    Returns:
        URL del PDF si se encuentra y valida, None si no
    """
    try:
        # Seguir el enlace (permitir redirecciones)
        r = requests.get(url_enlace, timeout=15, allow_redirects=True)
        if r.status_code != 200:
            return None
        
        # Si la URL final es del DOGV, buscar el PDF ahí
        if 'dogv.gva.es' in r.url:
            return _extraer_url_pdf_desde_dogv(r.url, year, r.text)
        else:
            # Si no, parsear la página actual buscando enlaces al DOGV
            soup = BeautifulSoup(r.text, 'html.parser')
            enlaces_dogv = soup.find_all('a', href=re.compile(r'dogv\.gva\.es', re.I))
            
            for enlace in enlaces_dogv:
                href = enlace['href']
                if href.startswith('http'):
                    url_dogv = href
                else:
                    url_dogv = f"https:{href}" if href.startswith('//') else f"https://dogv.gva.es{href}"
                
                print(f"      🔗 Siguiendo enlace a DOGV: {url_dogv[:80]}...")
                
                # Intentar extraer PDF desde esa URL del DOGV
                url_pdf = _extraer_url_pdf_desde_dogv(url_dogv, year)
                if url_pdf:
                    return url_pdf
        
        return None
        
    except Exception as e:
        print(f"      ⚠️  Error siguiendo enlace: {e}")
        return None


def _extraer_url_pdf_desde_dogv(url_dogv: str, year: int, contenido_html: str = None) -> Optional[str]:
    """
    Extrae la URL del PDF desde una página del DOGV.
    Prueba diferentes fechas de publicación en nov-dic del año anterior.
    
    Args:
        url_dogv: URL de la página del DOGV
        year: Año para validar
        contenido_html: HTML ya descargado (opcional)
        
    Returns:
        URL del PDF si se encuentra y valida, None si no
    """
    try:
        # Extraer signatura de la URL (ej: 2025/46326)
        match_signatura = re.search(r'signatura=([^&]+)', url_dogv)
        if not match_signatura:
            return None
        
        signatura = match_signatura.group(1)
        signatura_underscore = signatura.replace('/', '_')
        año_publicacion = year - 1  # Generalmente se publica el año anterior
        
        print(f"      📋 Signatura: {signatura}")
        print(f"      🔍 Buscando PDF en {año_publicacion}...")
        
        # Probar solo noviembre (mes más común para festivos locales)
        # Luego diciembre, luego octubre
        meses_probar = [11, 12, 10]
        
        for mes in meses_probar:
            dias_mes = 31 if mes in [10, 12] else 30
            
            for dia in range(1, dias_mes + 1):
                # Probar primero español, luego valenciano
                for idioma in ['es', 'va']:
                    url_pdf = f"https://dogv.gva.es/datos/{año_publicacion}/{mes:02d}/{dia:02d}/pdf/{signatura_underscore}_{idioma}.pdf"
                    
                    # HEAD request para ver si existe
                    try:
                        r_pdf = requests.head(url_pdf, timeout=2)
                        if r_pdf.status_code == 200:
                            print(f"      ✅ PDF encontrado: {año_publicacion}-{mes:02d}-{dia:02d}")
                            
                            # Validar contenido rápido (solo verificar que es PDF válido)
                            if _validar_pdf_valencia(url_pdf, year):
                                return url_pdf
                    except:
                        continue
        
        print(f"      ❌ No se encontró PDF para {signatura}")
        return None
        
    except Exception as e:
        print(f"      ⚠️  Error: {e}")
        return None


def _validar_pdf_valencia(url_pdf: str, year: int) -> bool:
    """
    Valida que el PDF contenga festivos locales de Valencia.
    
    Validación:
    - Debe contener al menos 2 de las 3 provincias
    - Debe contener múltiples municipios (>50 líneas con formato MUNICIPIO:)
    - Debe mencionar el año
    """
    try:
        import tempfile
        import os
        from pypdf import PdfReader
        
        r = requests.get(url_pdf, timeout=30)
        if r.status_code != 200:
            return False
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            tmp.write(r.content)
            tmp_path = tmp.name
        
        try:
            reader = PdfReader(tmp_path)
            texto = ""
            # Extraer TODAS las páginas (no solo las primeras 5)
            for page in reader.pages:
                texto += page.extract_text()
            
            # Validar provincias
            provincias_encontradas = sum([
                'ALICANTE' in texto,
                'CASTELLÓN' in texto or 'CASTELLÓ' in texto,
                'VALENCIA' in texto or 'VALÈNCIA' in texto
            ])
            
            if provincias_encontradas < 2:
                return False
            
            # Validar año
            if str(year) not in texto:
                return False
            
            # Validar múltiples municipios (patrón MUNICIPIO:)
            municipios = len(re.findall(r'^[A-ZÁÉÍÓÚÑÜ\',\s]+:', texto, re.MULTILINE))
            
            if municipios < 50:  # Al menos 50 municipios
                return False
            
            print(f"      ✅ PDF validado: {provincias_encontradas}/3 provincias, {municipios} municipios")
            return True
            
        finally:
            os.unlink(tmp_path)
            
    except Exception as e:
        print(f"      ⚠️  Error validando PDF: {e}")
        return False


def get_cached_url(year: int, cache_file: str = 'config/valencia_urls_cache.json') -> Optional[str]:
    """Obtiene URL desde el caché si existe"""
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


def save_to_cache(year: int, url: str, tipo: str = 'locales', cache_file: str = 'config/valencia_urls_cache.json'):
    """Guarda URL en el caché"""
    import json
    import os
    
    cache = {}
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                cache = json.load(f)
        except:
            cache = {}
    
    if tipo not in cache:
        cache[tipo] = {}
    
    cache[tipo][str(year)] = url
    
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(cache, f, indent=2)
    
    print(f"💾 URL guardada en caché: {cache_file}")


if __name__ == "__main__":
    import sys
    
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
    
    print(f"{'='*80}")
    print(f"🔍 AUTO-DISCOVERY: Valencia Locales {year}")
    print(f"{'='*80}\n")
    
    # Intentar desde caché primero
    url = get_cached_url(year)
    
    if not url:
        # Buscar automáticamente
        url = auto_discover_valencia(year)
        
        if url:
            # Guardar en caché
            save_to_cache(year, url)
    
    if url:
        print(f"\n✅ URL final: {url}")
    else:
        print(f"\n❌ No se pudo encontrar URL para {year}")