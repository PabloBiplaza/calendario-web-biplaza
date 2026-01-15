"""Scraper para festivos locales del País Vasco / Euskadi"""

from scrapers.core.base_scraper import BaseScraper
from typing import List, Dict, Optional
import requests
import json


class PaisVascoLocalesScraper(BaseScraper):
    """Scraper para festivos locales del País Vasco desde OpenData Euskadi"""
    
    CACHE_FILE = "config/pais_vasco_urls_cache.json"
    
    def __init__(self, year: int, municipio: Optional[str] = None):
        super().__init__(year=year, ccaa='pais_vasco', tipo='locales')
        self._load_cache()
        
        # Si se especifica municipio, hacer fuzzy matching
        if municipio:
            import json
            from utils.normalizer import find_municipio
            
            # Cargar todos los municipios del País Vasco
            with open('config/pais_vasco_municipios.json', 'r', encoding='utf-8') as f:
                territorios_data = json.load(f)
            
            # Crear lista plana
            todos_municipios = []
            for munis in territorios_data.values():
                todos_municipios.extend(munis)
            
            # Buscar mejor match
            mejor_match = find_municipio(municipio, todos_municipios, threshold=85)
            
            if mejor_match:
                self.municipio = mejor_match
                if mejor_match.lower() != municipio.lower():
                    print(f"   🔍 Fuzzy match: '{municipio}' → '{mejor_match}'")
            else:
                self.municipio = municipio
        else:
            self.municipio = None
    
    def _load_cache(self):
        """Carga URLs del cache"""
        import os
        import json
        
        self.cached_urls = {}
        
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                    self.cached_urls = json.load(f)
                print(f"📦 Cache cargado: {len(self.cached_urls)} URLs")
            except:
                self.cached_urls = {}
        else:
            self.cached_urls = {}
    
    def _save_to_cache(self, year_str: str, url: str):
        """Guarda URL en el cache"""
        import os
        import json
        
        # Cargar cache actual
        cache = {}
        if os.path.exists(self.CACHE_FILE):
            with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
        
        # Añadir nueva URL
        cache[year_str] = url
        
        # Guardar
        with open(self.CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
        
        print(f"💾 URL guardada en cache: {self.CACHE_FILE}")
    
    def get_source_url(self) -> str:
        """Devuelve la URL del JSON de OpenData Euskadi"""
        year_str = str(self.year)
        
        # 1. Cache
        if year_str in self.cached_urls:
            url = self.cached_urls[year_str]
            print(f"📦 URL en cache para {self.year}: {url}")
            return url
        
        # 2. Auto-discovery
        print(f"🔍 Auto-discovery para {self.year} (no está en cache)...")
        
        from scrapers.discovery.ccaa.pais_vasco_discovery import auto_discover_pais_vasco
        url = auto_discover_pais_vasco(self.year)
        
        if url:
            print(f"✅ URL encontrada via discovery: {url}")
            
            # Guardar en cache
            self._save_to_cache(year_str, url)
            
            return url
        
        raise ValueError(
            f"No se encontró URL para País Vasco {self.year}.\n"
            f"Añade la URL a {self.CACHE_FILE}"
        )
    
    def parse_festivos(self, content: str) -> List[Dict]:
        """Parsea festivos desde el JSON de OpenData Euskadi"""
        
        print("🔍 Parseando festivos locales del País Vasco...")
        
        try:
            datos = json.loads(content)
        except:
            print("   ❌ Error parseando JSON")
            return []
        
        if self.municipio:
            print(f"   🎯 Filtrando por municipio: {self.municipio}")
        
        festivos = []
        
        # Provincias y generales a excluir
        provincias = ['CAE', 'EAE', 'Bizkaia', 'Gipuzkoa', 'Araba', 'Álava']
        
        for item in datos:
            municipio_es = item.get('municipalityEs', '')
            territorio = item.get('territory', '')
            
            # CASO 1: Festivos generales (CAE/EAE) - los ignora, vienen del BOE
            if municipio_es in ['CAE', 'EAE']:
                continue
            
            # CASO 2: Festivo del municipio específico
            es_del_municipio = False
            
            if self.municipio:
                from utils.normalizer import MunicipioNormalizer
                es_del_municipio = MunicipioNormalizer.are_equivalent(self.municipio, municipio_es, threshold=85)
            
            # CASO 3: Festivo provincial - si el municipio está en esa provincia
            es_provincial = False
            
            if self.municipio and municipio_es in ['Bizkaia', 'Gipuzkoa', 'Araba', 'Álava']:
                # Necesitamos saber la provincia del municipio solicitado
                # La inferimos del 'territory' de sus festivos municipales
                if not hasattr(self, '_territorio_municipio'):
                    # Buscar territorio del municipio
                    for item_temp in datos:
                        if MunicipioNormalizer.are_equivalent(self.municipio, item_temp.get('municipalityEs', ''), threshold=85):
                            self._territorio_municipio = item_temp.get('territory', '')
                            break
                    else:
                        self._territorio_municipio = ''
                
                # Si el festivo provincial coincide con el territorio del municipio
                es_provincial = (municipio_es == self._territorio_municipio or 
                               territorio == self._territorio_municipio)
            
            # Solo incluir si es del municipio o es provincial aplicable
            if not es_del_municipio and not es_provincial:
                continue
            
            # Parsear fecha (formato: YYYY/MM/DD)
            fecha_raw = item.get('date', '')
            try:
                fecha_iso = fecha_raw.replace('/', '-')  # 2026/01/01 → 2026-01-01
            except:
                continue
            
            descripcion = item.get('descripcionEs', 'Festivo local')
            
            festivos.append({
                'fecha': fecha_iso,
                'fecha_texto': fecha_iso,
                'descripcion': descripcion,
                'tipo': 'local',
                'ambito': 'local',
                'municipio': municipio_es,
                'territorio': territorio,
                'year': self.year
            })
        
        print(f"   ✅ Festivos locales extraídos: {len(festivos)}")
        
        return festivos
    
    def fetch_content(self, url: str) -> str:
        """Descarga el JSON desde OpenData Euskadi"""
        try:
            print(f"📥 Descargando JSON: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            print(f"✅ JSON descargado ({len(response.text)} caracteres)")
            
            return response.text
            
        except Exception as e:
            print(f"❌ Error descargando {url}: {e}")
            return ""
