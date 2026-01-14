from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
import sys
from pathlib import Path
import uuid
import json
from datetime import datetime

# IMPORTANTE: Importar CalendarGenerator del directorio LOCAL primero
from utils.calendar_generator import CalendarGenerator

# Luego añadir el directorio del proyecto original al path para scrapers
proyecto_original = str(Path(__file__).parent.parent / 'calendario-laboral-espana')
sys.path.insert(0, proyecto_original)

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
    ccaas = [
        {'value': ccaa, 'nombre': CCAA_NOMBRES.get(ccaa, ccaa.title())}
        for ccaa in sorted(CCAA_SOPORTADAS)
    ]
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
    """Genera y descarga el PDF del calendario"""
    from flask import send_file
    import utils.calendar_generator
    print("=" * 80)
    print(f"📍 Importando CalendarGenerator desde: {utils.calendar_generator.__file__}")
    print("=" * 80)
    from weasyprint import HTML
    from datetime import datetime
    import tempfile
    
    # Cargar sesión
    session_file = SESSION_DIR / f"{session_id}.json"
    if not session_file.exists():
        return "Error: Sesión no encontrada", 404
    
    with open(session_file, 'r', encoding='utf-8') as f:
        session_data = json.load(f)
    
    # === RECOGER DATOS DEL FORMULARIO ===
    
    # Obligatorios
    empresa = request.form.get('empresa', '').strip()
    direccion = request.form.get('direccion', '').strip()
    horario_invierno = request.form.get('horario_invierno', '').strip()
    
    # Horario (con verano opcional)
    horario = {
        'invierno': horario_invierno,
        'tiene_verano': bool(request.form.get('tiene_verano'))
    }
    
    if horario['tiene_verano']:
        horario['verano'] = request.form.get('horario_verano', '').strip()
        
        # Fechas de verano
        verano_inicio = request.form.get('verano_inicio', '').strip()
        verano_fin = request.form.get('verano_fin', '').strip()
        
        if verano_inicio:
            horario['verano_inicio'] = datetime.strptime(verano_inicio, '%Y-%m-%d')
        if verano_fin:
            horario['verano_fin'] = datetime.strptime(verano_fin, '%Y-%m-%d')
    
    # Datos opcionales
    datos_opcionales = {
        'direccion': direccion,
    }
    
    # Añadir solo si tienen valor
    convenio = request.form.get('convenio', '').strip()
    if convenio:
        datos_opcionales['convenio'] = convenio
    
    num_patronal = request.form.get('num_patronal', '').strip()
    if num_patronal:
        datos_opcionales['num_patronal'] = num_patronal
    
    mutua = request.form.get('mutua', '').strip()
    if mutua:
        datos_opcionales['mutua'] = mutua
    
    try:
        # Crear generador con todos los parámetros
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

        # Crear PDF desde HTML
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', mode='wb') as tmp:
            pdf_path = tmp.name
            HTML(string=html_content).write_pdf(pdf_path)
        
        # Nombre del archivo para descarga
        municipio_safe = session_data['municipio'].lower().replace(' ', '_')
        filename = f"calendario_{municipio_safe}_{session_data['year']}.pdf"
        
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"❌ Error generando PDF: {e}")
        import traceback
        traceback.print_exc()
        return f"Error generando PDF: {str(e)}", 500

@app.route('/health')
def health():
    """Health check para Railway"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)