"""
Test específico del día 14 de octubre de 2022 (BOE de festivos 2023)
"""

import requests
import json

fecha = "20221014"  # 14 de octubre de 2022
api_url = f"https://www.boe.es/datosabiertos/api/boe/sumario/{fecha}"

print(f"🔍 Consultando: {api_url}\n")

response = requests.get(api_url, headers={'Accept': 'application/json'}, timeout=10)

if response.status_code == 200:
    data = response.json()
    
    # Guardar para inspección
    with open('data/boe_sumario_20221014.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ JSON guardado en: data/boe_sumario_20221014.json")
    
    # Buscar "fiestas laborales" en todo el JSON
    json_str = json.dumps(data, ensure_ascii=False).lower()
    
    if 'fiestas laborales' in json_str and '2023' in json_str:
        print(f"\n✅ Encontrado 'fiestas laborales 2023' en el JSON")
        
        # Buscar el ID
        import re
        pattern = r'boe-a-\d{4}-\d{5}'
        matches = re.findall(pattern, json_str)
        
        print(f"\n📋 IDs encontrados en el JSON:")
        for match in matches:
            print(f"   - {match.upper()}")
        
        # Encontrar contexto de "fiestas laborales"
        idx = json_str.find('fiestas laborales')
        context = json_str[max(0, idx-300):min(len(json_str), idx+500)]
        
        print(f"\n📄 Contexto alrededor de 'fiestas laborales':")
        print(context)
    else:
        print(f"\n❌ NO encontrado 'fiestas laborales 2023'")
        print(f"\n¿Tiene 'fiestas laborales'? {'fiestas laborales' in json_str}")
        print(f"¿Tiene '2023'? {'2023' in json_str}")
else:
    print(f"❌ Error: {response.status_code}")