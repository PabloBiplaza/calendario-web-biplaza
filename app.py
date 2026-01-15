from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
import sys
from pathlib import Path
import uuid
import json
from datetime import datetime

# IMPORTANTE: Importar CalendarGenerator del directorio LOCAL primero
from utils.calendar_generator import CalendarGenerator

# Importar scrape_festivos_completos desde el proyecto original
from scrape_municipio import scrape_festivos_completos
print("✅ Import scrape_festivos_completos OK")

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-super-importante-cambiar-en-produccion')

# CCAA soportadas
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

# Directorio para guardar sesiones temporales
SESSION_DIR = Path('temp_sessions')
SESSION_DIR.mkdir(exist_ok=True)

@app.route('/')
def landing():
    """Landing page principal"""
    # Importar la lista de CCAA soportadas
    import scrape_municipio
    ccaa_soportadas = scrape_municipio.ccaa_soportadas if hasattr(scrape_municipio, 'ccaa_soportadas') else CCAA_SOPORTADAS
    
    # Crear lista ordenada de CCAA con nombres bonitos
    ccaas = [
        {'value': ccaa, 'nombre': CCAA_NOMBRES.get(ccaa, ccaa.title())}
        for ccaa in ccaa_soportadas
    ]
    ccaas.sort(key=lambda x: x['nombre'])  # ← Ordena por nombre visual
    return render_template('landing.html', ccaas=ccaas)

@app.route('/generar', methods=['POST'])
def generar():
    """Procesa el formulario y genera el calendario"""
    try:
        # 1. Obtener datos del formulario
        municipio = request.form.get('municipio', '').strip()
        ccaa = request.form.get('ccaa', '').strip()
        year = int(request.form.get('year', 2026))
        
        # 2. Validaciones
        if not municipio or not ccaa:
            return "Error: Faltan datos del formulario", 400
        
        if ccaa not in CCAA_SOPORTADAS:
            return f"Error: CCAA '{ccaa}' no soportada", 400
        
        # 3. Generar session_id único
        session_id = str(uuid.uuid4())
        
        # 4. Ejecutar scraping (esto puede tardar 10-30 segundos)
        print(f"🔄 Generando calendario: {municipio}, {ccaa}, {year}")
        data = scrape_festivos_completos(municipio, ccaa, year)
        
        if not data:
            return "Error: No se pudieron obtener los festivos", 500
        
        # 5. Guardar datos en archivo temporal
        session_file = SESSION_DIR / f"{session_id}.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump({
                'session_id': session_id,
                'municipio': municipio,
                'ccaa': ccaa,
                'ccaa_nombre': CCAA_NOMBRES.get(ccaa, ccaa.title()),
                'year': year,
                'data': data,
                'created_at': datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Calendario generado: {session_id}")
        
        # 6. Redirigir a página de calendario
        return redirect(url_for('calendario', session_id=session_id))
        
    except Exception as e:
        print(f"❌ Error generando calendario: {e}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", 500

@app.route('/calendario/<session_id>')
def calendario(session_id):
    """Muestra el calendario generado"""
    session_file = SESSION_DIR / f"{session_id}.json"
    
    if not session_file.exists():
        return "Error: Sesión no encontrada o expirada", 404
    
    with open(session_file, 'r', encoding='utf-8') as f:
        session_data = json.load(f)
    
    return render_template('calendario.html', **session_data)

@app.route('/download/<session_id>', methods=['POST'])
def download(session_id):
    """Genera y descarga HTML con auto-print para PDF"""
    from flask import send_file
    from utils.calendar_generator import CalendarGenerator
    import tempfile
    
    # Cargar sesión
    session_file = SESSION_DIR / f"{session_id}.json"
    if not session_file.exists():
        return "Error: Sesión no encontrada", 404
    
    with open(session_file, 'r', encoding='utf-8') as f:
        session_data = json.load(f)
    
    # Recoger datos del formulario...
    # [mantener todo el código de recogida de datos]
    
    try:
        # Crear generador
        generator = CalendarGenerator(
            year=session_data['year'],
            festivos=session_data['data']['festivos'],
            municipio=session_data['municipio'],
            ccaa=session_data['ccaa_nombre'],
            empresa=empresa,
            horario=horario,
            datos_opcionales=datos_opcionales
        )
        
        # Generar HTML
        html_content = generator.generate_html()
        
        # Añadir script de auto-print
        html_content = html_content.replace('</body>', '''
            <script>
            window.onload = function() {
                setTimeout(function() {
                    window.print();
                }, 500);
            };
            </script>
            </body>
        ''')
        
        # Guardar HTML temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as tmp:
            tmp.write(html_content)
            html_path = tmp.name
        
        # Nombre del archivo
        municipio_safe = session_data['municipio'].lower().replace(' ', '_')
        filename = f"calendario_{municipio_safe}_{session_data['year']}.html"
        
        return send_file(
            html_path,
            as_attachment=True,
            download_name=filename,
            mimetype='text/html'
        )
        
    except Exception as e:
        print(f"❌ Error generando calendario: {e}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", 500

@app.route('/download-csv/<session_id>')
def download_csv(session_id):
    """Descarga festivos en formato CSV"""
    from flask import send_file
    import pandas as pd
    import tempfile
    
    # Cargar sesión
    session_file = SESSION_DIR / f"{session_id}.json"
    if not session_file.exists():
        return "Error: Sesión no encontrada", 404
    
    with open(session_file, 'r', encoding='utf-8') as f:
        session_data = json.load(f)
    
    try:
        # Crear DataFrame
        festivos = session_data['data']['festivos']
        df = pd.DataFrame(festivos)
        
        # Seleccionar y ordenar columnas
        columnas = ['fecha', 'fecha_texto', 'descripcion', 'tipo']
        if 'ambito' in df.columns:
            columnas.append('ambito')
        
        df = df[columnas]
        
        # Guardar CSV temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w', encoding='utf-8') as tmp:
            csv_path = tmp.name
            df.to_csv(csv_path, index=False, encoding='utf-8')
        
        # Nombre del archivo
        municipio_safe = session_data['municipio'].lower().replace(' ', '_')
        filename = f"festivos_{municipio_safe}_{session_data['year']}.csv"
        
        return send_file(
            csv_path,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )
        
    except Exception as e:
        print(f"❌ Error generando CSV: {e}")
        import traceback
        traceback.print_exc()
        return f"Error generando CSV: {str(e)}", 500

@app.route('/download-xlsx/<session_id>')
def download_xlsx(session_id):
    """Descarga festivos en formato Excel"""
    from flask import send_file
    import pandas as pd
    import tempfile
    
    # Cargar sesión
    session_file = SESSION_DIR / f"{session_id}.json"
    if not session_file.exists():
        return "Error: Sesión no encontrada", 404
    
    with open(session_file, 'r', encoding='utf-8') as f:
        session_data = json.load(f)
    
    try:
        # Crear DataFrame
        festivos = session_data['data']['festivos']
        df = pd.DataFrame(festivos)
        
        # Seleccionar y ordenar columnas
        columnas = ['fecha', 'fecha_texto', 'descripcion', 'tipo']
        if 'ambito' in df.columns:
            columnas.append('ambito')
        
        df = df[columnas]
        
        # Renombrar columnas
        df.columns = ['Fecha', 'Fecha (texto)', 'Descripción', 'Tipo', 'Ámbito'] if 'ambito' in df.columns else ['Fecha', 'Fecha (texto)', 'Descripción', 'Tipo']
        
        # Guardar Excel temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            xlsx_path = tmp.name
            df.to_excel(xlsx_path, index=False, engine='openpyxl')
        
        # Nombre del archivo
        municipio_safe = session_data['municipio'].lower().replace(' ', '_')
        filename = f"festivos_{municipio_safe}_{session_data['year']}.xlsx"
        
        return send_file(
            xlsx_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        print(f"❌ Error generando Excel: {e}")
        import traceback
        traceback.print_exc()
        return f"Error generando Excel: {str(e)}", 500

@app.route('/health')
def health():
    """Health check para Railway"""
    return jsonify({'status': 'ok'})

@app.route('/api/municipios/<ccaa>')
def api_municipios(ccaa):
    """API que devuelve municipios de una CCAA"""
    import json
    from pathlib import Path
    
    # Mapeo de nombres especiales de archivos
    FILENAME_MAP = {
        'canarias': 'canarias_municipios_islas.json',
        # Añadir aquí otros casos especiales si los hay
    }
    
    # Obtener nombre del archivo
    filename = FILENAME_MAP.get(ccaa, f'{ccaa}_municipios.json')
    config_file = Path(__file__).parent / 'config' / filename
    
    if not config_file.exists():
        return jsonify({'error': 'CCAA no encontrada'}), 404
    
    with open(config_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Dependiendo del formato
    municipios = []
    if isinstance(data, list):
        municipios = sorted(data)
    elif isinstance(data, dict):
        # Aplanar dict (por islas, provincias, etc)
        for valores in data.values():
            if isinstance(valores, list):
                municipios.extend(valores)
        municipios = sorted(set(municipios))
    
    return jsonify(municipios)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)