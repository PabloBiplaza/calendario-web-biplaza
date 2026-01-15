"""
Orchestrator - Ejecuta todos los scrapers y combina los resultados
Genera el calendario laboral completo para una CCAA y año específicos
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

from scrapers.core.boe_scraper import BOEScraper
from scrapers.ccaa.canarias.autonomicos import CanariasAutonomicosScraper
from scrapers.ccaa.canarias.locales import CanariasLocalesScraper


class CalendarioOrchestrator:
    """
    Orquesta la ejecución de todos los scrapers necesarios
    para generar un calendario laboral completo
    """
    
    def __init__(self, year: int, ccaa: str = 'canarias'):
        self.year = year
        self.ccaa = ccaa
        self.festivos_nacionales = []
        self.festivos_autonomicos = []
        self.festivos_locales = []
    
    def run_all(self):
        """Ejecuta todos los scrapers necesarios"""
        print(f"\n{'='*80}")
        print(f"🚀 ORQUESTADOR - Calendario Laboral {self.year}")
        print(f"📍 Comunidad Autónoma: {self.ccaa.upper()}")
        print(f"{'='*80}\n")
        
        # 1. Festivos nacionales (BOE)
        print("1️⃣  FASE 1: Festivos Nacionales (BOE)")
        print("-" * 80)
        boe_scraper = BOEScraper(year=self.year)
        self.festivos_nacionales = boe_scraper.scrape()
        print()
        
        # 2. Festivos autonómicos
        if self.ccaa == 'canarias':
            print("2️⃣  FASE 2: Festivos Autonómicos (BOC - Decreto)")
            print("-" * 80)
            auto_scraper = CanariasAutonomicosScraper(year=self.year)
            self.festivos_autonomicos = auto_scraper.scrape()
            print()
            
            print("3️⃣  FASE 3: Festivos Locales (BOC - Orden)")
            print("-" * 80)
            locales_scraper = CanariasLocalesScraper(year=self.year)
            self.festivos_locales = locales_scraper.scrape()
            print()
        
        # Resumen final
        self._print_summary()
        
        # Guardar resultados combinados
        self._save_combined()
    
    def _print_summary(self):
        """Imprime resumen de todos los festivos extraídos"""
        print(f"\n{'='*80}")
        print(f"📊 RESUMEN FINAL - {self.ccaa.upper()} {self.year}")
        print(f"{'='*80}")
        print(f"✅ Festivos nacionales: {len(self.festivos_nacionales)}")
        print(f"✅ Festivos autonómicos/insulares: {len(self.festivos_autonomicos)}")
        print(f"✅ Festivos locales: {len(self.festivos_locales)}")
        print(f"➡️  TOTAL: {len(self.festivos_nacionales) + len(self.festivos_autonomicos) + len(self.festivos_locales)} festivos extraídos")
        print(f"{'='*80}\n")
    
    def _save_combined(self):
        """Guarda todos los festivos en un único archivo combinado"""
        output_dir = Path('data/combined')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        combined = {
            'metadata': {
                'year': self.year,
                'ccaa': self.ccaa,
                'fecha_generacion': datetime.now().isoformat(),
                'fuentes': {
                    'nacionales': 'BOE',
                    'autonomicos': 'BOC' if self.ccaa == 'canarias' else None,
                    'locales': 'BOC' if self.ccaa == 'canarias' else None
                },
                'total_festivos': {
                    'nacionales': len(self.festivos_nacionales),
                    'autonomicos': len(self.festivos_autonomicos),
                    'locales': len(self.festivos_locales)
                }
            },
            'festivos': {
                'nacionales': self.festivos_nacionales,
                'autonomicos': self.festivos_autonomicos,
                'locales': self.festivos_locales
            }
        }
        
        filepath = output_dir / f'{self.ccaa}_{self.year}_completo.json'
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(combined, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Calendario completo guardado: {filepath}")
    
    def get_festivos_municipio(self, municipio: str) -> List[Dict]:
        """
        Obtiene todos los festivos aplicables a un municipio específico
        
        Args:
            municipio: Nombre del municipio en mayúsculas
            
        Returns:
            Lista de festivos ordenados por fecha
        """
        festivos_totales = []
        
        # 1. Festivos nacionales (aplican a todos)
        festivos_totales.extend(self.festivos_nacionales)
        
        # 2. Festivos autonómicos aplicables
        # Para Canarias: el autonómico de toda Canarias + el insular de su isla
        if self.ccaa == 'canarias':
            auto_scraper = CanariasAutonomicosScraper(year=self.year)
            isla = auto_scraper.get_isla_municipio(municipio)
            
            for festivo in self.festivos_autonomicos:
                # Si es autonómico (toda Canarias)
                if festivo.get('ambito') == 'autonomico' and festivo.get('islas') == 'Todas':
                    festivos_totales.append(festivo)
                # Si es insular y aplica a esta isla
                elif festivo.get('ambito') == 'insular' and isla:
                    municipios_aplicables = festivo.get('municipios_aplicables', [])
                    if isinstance(municipios_aplicables, list) and isla in municipios_aplicables:
                        festivos_totales.append(festivo)
        
        # 3. Festivos locales del municipio
        festivos_municipio = [f for f in self.festivos_locales if f.get('municipio') == municipio]
        festivos_totales.extend(festivos_municipio)
        
        # Ordenar por fecha
        festivos_totales.sort(key=lambda x: x['fecha'])
        
        return festivos_totales


def main():
    """Función principal"""
    import sys
    
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
    ccaa = sys.argv[2] if len(sys.argv) > 2 else 'canarias'
    
    orchestrator = CalendarioOrchestrator(year=year, ccaa=ccaa)
    orchestrator.run_all()
    
    # Ejemplo: obtener festivos de un municipio
    if ccaa == 'canarias':
        print("\n" + "="*80)
        print("🔍 EJEMPLO: Festivos de San Cristóbal de La Laguna")
        print("="*80)
        festivos = orchestrator.get_festivos_municipio('SAN CRISTÓBAL DE LA LAGUNA')
        print(f"Total festivos aplicables: {len(festivos)}\n")
        for f in festivos:
            print(f"  • {f['fecha']} - {f['descripcion']} ({f['tipo']})")


if __name__ == "__main__":
    main()