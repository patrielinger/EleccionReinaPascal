#!/usr/bin/env python3
import http.server
import socketserver
import socket
import os
import json
import ipaddress
import uuid
import time
import shutil
from urllib.parse import urlparse
import sys
import re
import logging
from datetime import datetime
from io import StringIO

PORT = 3000
ALLOWED_EXTENSIONS = {'.html', '.css', '.js', '.json', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico'}
ACTIVE_SESSIONS = {}
CONNECTED_IPS = set()  # Para rastrear IPs conectadas
VOTING_ENABLED = True


# Crear directorio datos
DATA_DIR = 'datos'
os.makedirs(DATA_DIR, exist_ok=True)

CANDIDATAS_FILE = os.path.join(DATA_DIR, 'candidatas.json')
USUARIOS_FILE = os.path.join(DATA_DIR, 'usuarios.json')
VOTOS_FILE = os.path.join(DATA_DIR, 'votos.json')
CATEGORIES_FILE = os.path.join(DATA_DIR, 'categorias.json')
DEFAULT_CATEGORIES = [
    {'name': 'Reina', 'color': '#ff6fe7'},
    {'name': 'Primera Princesa', 'color': '#e6fa33'},
    {'name': 'Segunda Princesa', 'color': '#e6fa33'},
    {'name': 'Primera Dama de Honor', 'color': '#1fff40'},
    {'name': 'Segunda Dama de Honor', 'color': '#1fff40'}
]

def load_candidatas():
    if os.path.exists(CANDIDATAS_FILE):
        try:
            with open(CANDIDATAS_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_candidatas(candidatas):
    # Cargar candidatas anteriores para comparar
    anteriores = load_candidatas()
    anteriores_dict = {c['id']: c for c in anteriores}
    nuevas_dict = {c['id']: c for c in candidatas}
    
    # Detectar candidatas agregadas
    for cid, candidata in nuevas_dict.items():
        if cid not in anteriores_dict:
            logging.info(f"➕ Candidata AGREGADA: ID={cid}, Nombre='{candidata.get('nombre', 'N/A')}'")
    
    # Detectar candidatas eliminadas
    for cid, candidata in anteriores_dict.items():
        if cid not in nuevas_dict:
            logging.info(f"➖ Candidata ELIMINADA: ID={cid}, Nombre='{candidata.get('nombre', 'N/A')}'")
    
    with open(CANDIDATAS_FILE, 'w') as f:
        json.dump(candidatas, f, indent=2)

def load_usuarios():
    if os.path.exists(USUARIOS_FILE):
        try:
            with open(USUARIOS_FILE, 'r') as f:
                return json.load(f)
        except:
            return [{'username': 'admin', 'password': 'admin', 'role': 'admin'}]
    return [{'username': 'admin', 'password': 'admin', 'role': 'admin'}]

def save_usuarios(usuarios):
    # Cargar usuarios anteriores para comparar
    anteriores = load_usuarios()
    anteriores_dict = {u['username']: u for u in anteriores}
    nuevas_dict = {u['username']: u for u in usuarios}
    
    # Detectar usuarios agregados
    for username, usuario in nuevas_dict.items():
        if username not in anteriores_dict:
            logging.info(f"👤 Usuario AGREGADO: '{username}' (Rol: {usuario.get('role', 'user')})")
    
    # Detectar usuarios eliminados
    for username, usuario in anteriores_dict.items():
        if username not in nuevas_dict:
            logging.info(f"👤 Usuario ELIMINADO: '{username}' (Rol: {usuario.get('role', 'user')})")
    
    with open(USUARIOS_FILE, 'w') as f:
        json.dump(usuarios, f, indent=2)

def load_votos():
    if os.path.exists(VOTOS_FILE):
        try:
            with open(VOTOS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_votos(votos):
    # Cargar votos anteriores para comparar
    anteriores = load_votos()
    
    # Detectar nuevos votos o cambios
    for username, user_votes in votos.items():
        prev_user_votes = anteriores.get(username, {})
        
        for categoria, candidata_id in user_votes.items():
            prev_candidata_id = prev_user_votes.get(categoria)
            
            if prev_candidata_id != candidata_id:
                # Encontrar nombre de la candidata
                candidatas = load_candidatas()
                candidata = next((c for c in candidatas if c['id'] == candidata_id), None)
                candidata_nombre = candidata['nombre'] if candidata else f"ID:{candidata_id}"
                
                if prev_candidata_id is None:
                    logging.info(f"🗳️ VOTO NUEVO: Usuario '{username}' votó en '{categoria}' → Candidata '{candidata_nombre}'")
                else:
                    # Encontrar nombre de la candidata anterior
                    prev_candidata = next((c for c in candidatas if c['id'] == prev_candidata_id), None)
                    prev_candidata_nombre = prev_candidata['nombre'] if prev_candidata else f"ID:{prev_candidata_id}"
                    
                    logging.info(f"🔄 VOTO CAMBIADO: Usuario '{username}' cambió voto en '{categoria}' de '{prev_candidata_nombre}' → '{candidata_nombre}'")
    
    with open(VOTOS_FILE, 'w') as f:
        json.dump(votos, f, indent=2)

def load_categorias():
    def normalize(categoria):
        if isinstance(categoria, str):
            return {'name': categoria, 'color': '#ff6fe7'}
        if isinstance(categoria, dict) and categoria.get('name'):
            return {'name': str(categoria['name']).strip(), 'color': categoria.get('color', '#ff6fe7')}
        return None

    if os.path.exists(CATEGORIES_FILE):
        try:
            with open(CATEGORIES_FILE, 'r') as f:
                categorias = json.load(f)
                if isinstance(categorias, list) and categorias:
                    normalized = [normalize(c) for c in categorias]
                    return [c for c in normalized if c]
        except:
            pass
    return DEFAULT_CATEGORIES.copy()


def save_categorias(categorias):
    anteriores = load_categorias()
    anteriores_names = {c['name'] for c in anteriores}
    nuevas_names = {c['name'] for c in categorias if isinstance(c, dict) and c.get('name')}

    for categoria in categorias:
        if isinstance(categoria, dict) and categoria.get('name') and categoria['name'] not in anteriores_names:
            logging.info(f"➕ Categoría AGREGADA: '{categoria['name']}'")
    for categoria in anteriores:
        if categoria['name'] not in nuevas_names:
            logging.info(f"➖ Categoría ELIMINADA: '{categoria['name']}'")

    with open(CATEGORIES_FILE, 'w') as f:
        json.dump(categorias, f, indent=2)

def clear_all_votes():
    logging.info("🧹 Todos los votos han sido eliminados por el administrador")
    with open(VOTOS_FILE, 'w') as f:
        json.dump({}, f, indent=2)

class SecureHandler(http.server.SimpleHTTPRequestHandler):
    
    def is_local_ip(self, ip_str):
        try:
            ip = ipaddress.ip_address(ip_str)
            local_networks = [
                ipaddress.ip_network('127.0.0.0/8'),
                ipaddress.ip_network('192.168.0.0/16'),
                ipaddress.ip_network('10.0.0.0/8'),
                ipaddress.ip_network('172.16.0.0/12'),
                ipaddress.ip_network('169.254.0.0/16'),
            ]
            return any(ip in network for network in local_networks)
        except ValueError:
            return False
    
    def send_json(self, status, data):
        json_data = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(json_data)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json_data)
    
    def handle_api_get(self, path):
        """Maneja GET para APIs"""
        if path == '/api/load-candidatas':
            try:
                candidatas = load_candidatas()
                self.send_json(200, {'success': True, 'candidatas': candidatas})
                return True
            except Exception as e:
                self.send_json(400, {'error': str(e)})
                return True
        
        elif path == '/api/load-usuarios':
            try:
                usuarios = load_usuarios()
                self.send_json(200, {'success': True, 'usuarios': usuarios})
                return True
            except Exception as e:
                self.send_json(400, {'error': str(e)})
                return True
        
        elif path == '/api/load-categorias':
            try:
                categorias = load_categorias()
                self.send_json(200, {'success': True, 'categorias': categorias})
                return True
            except Exception as e:
                self.send_json(400, {'error': str(e)})
                return True
        
        elif path == '/api/load-votos':
            try:
                votos = load_votos()
                self.send_json(200, {'success': True, 'votos': votos})
                return True
            except Exception as e:
                self.send_json(400, {'error': str(e)})
                return True
        
        elif path == '/api/load-data':
            try:
                candidatas = load_candidatas()
                votos = load_votos()
                categorias = load_categorias()
                self.send_json(200, {
                    'success': True, 
                    'candidatas': candidatas,
                    'votos': votos,
                    'categorias': categorias
                })
                return True
            except Exception as e:
                self.send_json(400, {'error': str(e)})
                return True
        
        elif path == '/api/get-voting-status':
            try:
                self.send_json(200, {
                    'success': True,
                    'voting_enabled': VOTING_ENABLED
                })
                return True
            except Exception as e:
                self.send_json(400, {'error': str(e)})
                return True
        
        elif path == '/api/get-network-info':
            try:
                client_ip = self.client_address[0]
                server_ip = get_local_ip()
                self.send_json(200, {
                    'success': True,
                    'server_ip': server_ip,
                    'client_ip': client_ip,
                    'port': PORT
                })
                return True
            except Exception as e:
                self.send_json(400, {'error': str(e)})
                return True
        
        return False
    
    def handle_upload_candidata_foto(self, content_type, content_length):
        """Maneja carga de archivo de foto de candidata"""
        try:
            if 'multipart/form-data' not in content_type:
                self.send_json(400, {'error': 'Content-Type debe ser multipart/form-data'})
                return
            
            # Extraer boundary
            boundary_match = re.search(r'boundary=([^\s;]+)', content_type)
            if not boundary_match:
                self.send_json(400, {'error': 'Boundary no encontrado en Content-Type'})
                return
            boundary = boundary_match.group(1).strip('"')
            
            # Leer datos
            body = self.rfile.read(content_length)
            
            # Parsear campos multipart simple
            parts = body.split(f'--{boundary}'.encode())
            numero = None
            file_data = None
            filename = None
            
            for part in parts:
                if b'Content-Disposition:' not in part:
                    continue
                    
                headers_end = part.find(b'\r\n\r\n')
                if headers_end == -1:
                    headers_end = part.find(b'\n\n')
                    if headers_end == -1:
                        continue
                    payload = part[headers_end+2:]
                else:
                    payload = part[headers_end+4:]
                
                # Remover trailing boundary
                if payload.endswith(b'\r\n'):
                    payload = payload[:-2]
                elif payload.endswith(b'\n'):
                    payload = payload[:-1]
                
                # Extraer nombre del campo
                name_match = re.search(rb'name="([^"]+)"', part[:headers_end])
                if not name_match:
                    continue
                    
                field_name = name_match.group(1).decode('utf-8')
                
                if field_name == 'numero':
                    numero = payload.decode('utf-8').strip()
                elif field_name == 'foto':
                    filename_match = re.search(rb'filename="([^"]+)"', part[:headers_end])
                    if filename_match:
                        filename = filename_match.group(1).decode('utf-8')
                        file_data = payload
            
            if not filename or not numero or not file_data:
                self.send_json(400, {'error': 'Falta foto o número de candidata'})
                return
            
            ext = os.path.splitext(filename)[1].lower()
            if ext not in ['.png', '.jpg', '.jpeg', '.gif', '.svg']:
                self.send_json(400, {'error': 'Extensión de imagen no permitida'})
                return
            
            safe_filename = f"{numero}{ext}"
            img_dir = os.path.join(os.getcwd(), 'img')
            os.makedirs(img_dir, exist_ok=True)
            output_path = os.path.join(img_dir, safe_filename)
            
            with open(output_path, 'wb') as f:
                f.write(file_data)
            
            self.send_json(200, {'success': True, 'foto': f'img/{safe_filename}'})
        except Exception as e:
            self.send_json(400, {'error': str(e)})
    
    def do_HEAD(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Verificar permisos para admin.html
        if path == '/admin.html':
            query_params = dict(qc.split('=') for qc in parsed_path.query.split('&') if '=' in qc) if parsed_path.query else {}
            session_id = query_params.get('session_id')
            device_id = query_params.get('device_id')
            
            if not session_id or not device_id:
                # Redirigir a login si no hay parámetros de sesión
                self.send_response(302)
                self.send_header('Location', '/index.html')
                self.end_headers()
                return
            
            # Verificar sesión y permisos
            session = ACTIVE_SESSIONS.get(session_id)
            if not session or session.get('device_id') != device_id or session.get('role') != 'admin':
                # Usuario no autorizado - redirigir a user.html
                self.send_response(302)
                self.send_header('Location', '/user.html')
                self.end_headers()
                return
        
    def do_GET(self):
        client_ip = self.client_address[0]
        
        # Registrar nueva conexión IP
        if client_ip not in CONNECTED_IPS:
            CONNECTED_IPS.add(client_ip)
            logging.info(f"🌐 IP CONECTADA: {client_ip}")
        
        if not self.is_local_ip(client_ip):
            self.send_response(403)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'<h1>Acceso Denegado</h1>')
            return
        
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Intentar manejar API
        if self.handle_api_get(path):
            return
        
        # Verificar permisos para admin.html
        if path == '/admin.html':
            query_params = dict(qc.split('=') for qc in parsed_path.query.split('&') if '=' in qc) if parsed_path.query else {}
            session_id = query_params.get('session_id')
            device_id = query_params.get('device_id')
            
            if not session_id or not device_id:
                # Redirigir a login si no hay parámetros de sesión
                self.send_response(302)
                self.send_header('Location', '/index.html')
                self.end_headers()
                return
            
            # Verificar sesión y permisos
            session = ACTIVE_SESSIONS.get(session_id)
            if not session or session.get('device_id') != device_id or session.get('role') != 'admin':
                # Usuario no autorizado - redirigir a user.html
                self.send_response(302)
                self.send_header('Location', '/user.html')
                self.end_headers()
                return
        
        # Si "/"  ir a index.html
        if self.path == '/':
            self.path = '/index.html'
        
        # Servir archivo normalmente
        file_path = parsed_path.path.lstrip('/')
        
        if '..' in file_path:
            self.send_response(403)
            self.end_headers()
            return
        
        _, ext = os.path.splitext(file_path)
        if ext and ext not in ALLOWED_EXTENSIONS:
            self.send_response(403)
            self.end_headers()
            return
        
        super().do_GET()
    
    def do_POST(self):
        client_ip = self.client_address[0]
        
        # Registrar nueva conexión IP
        if client_ip not in CONNECTED_IPS:
            CONNECTED_IPS.add(client_ip)
            logging.info(f"🌐 IP CONECTADA: {client_ip}")
        
        if not self.is_local_ip(client_ip):
            self.send_json(403, {'error': 'Acceso denegado'})
            return
        
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        content_type = self.headers.get('Content-Type', '')
        content_length = int(self.headers.get('Content-Length', 0))
        
        # Manejo especial para upload multipart
        if path == '/api/upload-candidata-foto':
            self.handle_upload_candidata_foto(content_type, content_length)
            return
        
        # Para otros POST, decodificar como JSON
        body = self.rfile.read(content_length).decode('utf-8')
        data = json.loads(body) if body else {}
        
        if path == '/api/save-candidatas':
            try:
                save_candidatas(data.get('candidatas', []))
                self.send_json(200, {'success': True})
                logging.info(f"✓ Candidatas guardadas")
            except Exception as e:
                self.send_json(400, {'error': str(e)})
        
        elif path == '/api/save-usuarios':
            try:
                save_usuarios(data.get('usuarios', []))
                self.send_json(200, {'success': True})
                logging.info(f"✓ Usuarios guardados")
            except Exception as e:
                self.send_json(400, {'error': str(e)})
        
        elif path == '/api/save-votos':
            try:
                save_votos(data.get('votos', {}))
                self.send_json(200, {'success': True})
            except Exception as e:
                self.send_json(400, {'error': str(e)})
        
        elif path == '/api/save-categorias':
            try:
                save_categorias(data.get('categorias', []))
                self.send_json(200, {'success': True})
                logging.info('✓ Categorías guardadas')
            except Exception as e:
                self.send_json(400, {'error': str(e)})
        
        elif path == '/api/clear-all-votes':
            try:
                clear_all_votes()
                self.send_json(200, {'success': True})
            except Exception as e:
                self.send_json(400, {'error': str(e)})
        
        elif path == '/api/set-voting-status':
            try:
                global VOTING_ENABLED
                VOTING_ENABLED = bool(data.get('enabled', False))
                state = 'activadas' if VOTING_ENABLED else 'bloqueadas'
                logging.info(f"🔒 Votaciones {state} por el administrador")
                self.send_json(200, {'success': True, 'voting_enabled': VOTING_ENABLED})
            except Exception as e:
                self.send_json(400, {'error': str(e)})
        
        elif path == '/api/login':
            try:
                usuarios = load_usuarios()
                username = data.get('username')
                password = data.get('password')
                device_id = data.get('device_id')
                
                user = next((u for u in usuarios if u['username'] == username and u['password'] == password), None)
                if user:
                    # Comprobar sesiones activas del mismo usuario
                    active_sessions = [(sid, s) for sid, s in ACTIVE_SESSIONS.items() if s['username'] == username]
                    
                    # Si ya hay otra sesión en dispositivo distinto, bloquear
                    other_device_sessions = [s for sid, s in active_sessions if s['device_id'] != device_id]
                    if other_device_sessions:
                        self.send_json(403, {
                            'success': False,
                            'error': 'Este usuario ya está conectado desde otro dispositivo',
                            'allowed_devices': 0
                        })
                        return
                    
                    # Si existe sesión con el mismo dispositivo, eliminarla para crear nueva
                    same_device_sessions = [sid for sid, s in active_sessions if s['device_id'] == device_id]
                    for sid in same_device_sessions:
                        del ACTIVE_SESSIONS[sid]
                    
                    # Generar session_id único
                    session_id = str(uuid.uuid4())
                    ACTIVE_SESSIONS[session_id] = {
                        'username': username,
                        'device_id': device_id,
                        'timestamp': time.time(),
                        'role': user.get('role', 'user')
                    }
                    
                    self.send_json(200, {
                        'success': True,
                        'username': username,
                        'device_id': device_id,
                        'session_id': session_id,
                        'role': user.get('role', 'user')
                    })
                    logging.info(f"✓ Usuario {username} inició sesión")
                    return
                else:
                    self.send_json(401, {'error': 'Credenciales inválidas'})
                    return
            except Exception as e:
                self.send_json(400, {'error': str(e)})
                return
        
        elif path == '/api/verify-session':
            try:
                username = data.get('username')
                session_id = data.get('session_id')
                device_id = data.get('device_id')
                
                session = ACTIVE_SESSIONS.get(session_id)
                if session and session['username'] == username and session['device_id'] == device_id:
                    session['timestamp'] = time.time()
                    self.send_json(200, {'valid': True, 'role': session.get('role', 'user')})
                    return
                else:
                    self.send_json(200, {'valid': False})
                    return
            except Exception as e:
                self.send_json(400, {'error': str(e)})
                return
        
        elif path == '/api/logout':
            try:
                username = data.get('username')
                # Buscar y eliminar la sesión del usuario
                sessions_to_remove = [sid for sid, s in ACTIVE_SESSIONS.items() if s['username'] == username]
                for sid in sessions_to_remove:
                    del ACTIVE_SESSIONS[sid]
                self.send_json(200, {'success': True})
                logging.info(f"✓ Usuario {username} cerró sesión")
                return
            except Exception as e:
                self.send_json(400, {'error': str(e)})
                return
        
        else:
            self.send_json(404, {'error': 'Not found'})

def get_local_ip():
    """Obtiene la dirección IP local de la máquina"""
    try:
        # Crear un socket para conectarse a un servidor externo
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Conectar a Google DNS
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"  # Fallback a localhost

def setup_logging():
    """Configura el sistema de logging con archivo y consola"""
    # Crear directorio de logs si no existe
    logs_dir = 'logs'
    os.makedirs(logs_dir, exist_ok=True)
    
    # Generar nombre de archivo con fecha y hora (DD_MM_YY_HH_MM)
    log_filename = datetime.now().strftime('%d_%m_%y_%H_%M.log')
    log_path = os.path.join(logs_dir, log_filename)
    
    # Configurar logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Formato de logs
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    date_format = '%d/%m/%y %H:%M:%S'
    formatter = logging.Formatter(log_format, datefmt=date_format)
    
    # Handler para archivo
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return log_path

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Configurar logging
    log_path = setup_logging()
    
    # Obtener IP local
    local_ip = get_local_ip()
    
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", PORT), SecureHandler) as httpd:
        logging.info("=" * 60)
        logging.info("🎓 SERVIDOR DE ELECCIONES (v2)")
        logging.info("=" * 60)
        logging.info(f"\n✓ Escuchando en puerto {PORT}")
        logging.info(f"✓ Solo redes locales permitidas")
        logging.info(f"✓ Datos persistentes en carpeta 'datos/'")
        logging.info(f"✓ Logs guardados en: {log_path}")
        logging.info(f"\n🌐 Acceso local: http://localhost:{PORT}")
        logging.info(f"📱 Acceso desde red: http://{local_ip}:{PORT}")
        logging.info(f"\n💡 Comparte la URL de red con otros dispositivos en la misma red WiFi\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logging.info("\n✓ Servidor detenido")