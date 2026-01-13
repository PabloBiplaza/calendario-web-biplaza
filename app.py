from flask import Flask, render_template, request, jsonify
import os
import sys
from pathlib import Path

# Añadir el directorio del proyecto original al path
proyecto_original = str(Path(__file__).parent.parent / 'calendario-laboral-espana')
sys.path.insert(0, proyecto_original)

# Importar desde el proyecto original
from scrape_municipio import scrape_festivos_completos

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# CCAA soportadas (hardcoded por ahora, luego lo haremos dinámico)
CCAA_SOPORTADAS = ['andalucia', 'baleares', 'canarias', 'cataluna', 'galicia', 'madrid', 'pais_vasco', 'valencia']

# Mapeo de nombres técnicos a nombres visuales
CCAA_NOMBRES = {
    'andalucia': 'Andalucía',
    'baleares': 'Baleares',
    'canarias': 'Canarias',
    'cataluna': 'Cataluña',
    'galicia': 'Galicia',
    'madrid': 'Madrid',
    'pais_vasco': 'País Vasco',
    'valencia': 'C. Valenciana',
}

@app.route('/')
def landing():
    """Landing page principal"""
    # Crear lista ordenada de CCAA con nombres bonitos
    ccaas = [
        {'value': ccaa, 'nombre': CCAA_NOMBRES.get(ccaa, ccaa.title())}
        for ccaa in sorted(CCAA_SOPORTADAS)
    ]
    return render_template('landing.html', ccaas=ccaas)

@app.route('/health')
def health():
    """Health check para Railway"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)