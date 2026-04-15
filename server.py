#!/usr/bin/env python3
import http.server
import socketserver
import socket
import os
import json
import ipaddress
import uuid
import time
import cgi
import shutil
from urllib.parse import urlparse
import sys

PORT = 3000
ALLOWED_EXTENSIONS = {'.html', '.css', '.js', '.json', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico'}
ACTIVE_SESSIONS = {}
SESSION_TIMEOUT = 3600

# Crear directorio datos
DATA_DIR = 'datos'
os.makedirs(DATA_DIR, exist_ok=True)

CANDIDATAS_FILE = os.path.join(DATA_DIR, 'candidatas.json')
USUARIOS_FILE = os.path.join(DATA_DIR, 'usuarios.json')
VOTOS_FILE = os.path.join(DATA_DIR, 'votos.json')

def load_candidatas():
    if os.path.exists(CANDIDATAS_FILE):
        try:
            with open(CANDIDATAS_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_candidatas(candidatas):
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
    with open(VOTOS_FILE, 'w') as f:
        json.dump(votos, f, indent=2)

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
                self.send_json(200, {
                    'success': True, 
                    'candidatas': candidatas,
                    'votos': votos
                })
                return True
            except Exception as e:
                self.send_json(400, {'error': str(e)})
                return True
        
        return False
    
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
        if not self.is_local_ip(client_ip):
            self.send_json(403, {'error': 'Acceso denegado'})
            return
        
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        data = json.loads(body) if body else {}
        
        if path == '/api/save-candidatas':
            try:
                save_candidatas(data.get('candidatas', []))
                self.send_json(200, {'success': True})
                print(f"✓ Candidatas guardadas")
            except Exception as e:
                self.send_json(400, {'error': str(e)})
        
        elif path == '/api/save-usuarios':
            try:
                save_usuarios(data.get('usuarios', []))
                self.send_json(200, {'success': True})
                print(f"✓ Usuarios guardados")
            except Exception as e:
                self.send_json(400, {'error': str(e)})
        
        elif path == '/api/save-votos':
            try:
                save_votos(data.get('votos', {}))
                self.send_json(200, {'success': True})
            except Exception as e:
                self.send_json(400, {'error': str(e)})

        elif path == '/api/upload-candidata-foto':
            try:
                ctype, pdict = cgi.parse_header(self.headers.get('Content-Type', ''))
                if ctype != 'multipart/form-data':
                    self.send_json(400, {'error': 'Content-Type debe ser multipart/form-data'})
                    return
                pdict['boundary'] = bytes(pdict['boundary'], 'utf-8')
                pdict['CONTENT-LENGTH'] = int(self.headers.get('Content-Length', 0))
                form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD':'POST'}, keep_blank_values=True)
                file_field = form['foto'] if 'foto' in form else None
                numero = form.getvalue('numero')
                if not file_field or not numero:
                    self.send_json(400, {'error': 'Falta foto o número de candidata'})
                    return
                filename = file_field.filename
                ext = os.path.splitext(filename)[1].lower()
                if ext not in ['.png', '.jpg', '.jpeg', '.gif', '.svg']:
                    self.send_json(400, {'error': 'Extensión de imagen no permitida'})
                    return
                safe_filename = f"{numero}{ext}"
                img_dir = os.path.join(os.getcwd(), 'img')
                os.makedirs(img_dir, exist_ok=True)
                output_path = os.path.join(img_dir, safe_filename)
                with open(output_path, 'wb') as out_file:
                    shutil.copyfileobj(file_field.file, out_file)
                self.send_json(200, {'success': True, 'foto': f'img/{safe_filename}'})
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
                    # Eliminar sesiones anteriores del mismo usuario
                    sessions_to_remove = [sid for sid, s in ACTIVE_SESSIONS.items() if s['username'] == username]
                    for sid in sessions_to_remove:
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
                    print(f"✓ Usuario {username} inició sesión")
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
                    # Verificar timeout
                    if time.time() - session['timestamp'] > SESSION_TIMEOUT:
                        del ACTIVE_SESSIONS[session_id]
                        self.send_json(200, {'valid': False})
                        return
                    else:
                        session['timestamp'] = time.time()  # Actualizar timestamp
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
                print(f"✓ Usuario {username} cerró sesión")
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

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Obtener IP local
    local_ip = get_local_ip()
    
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", PORT), SecureHandler) as httpd:
        print("=" * 60)
        print("🎓 SERVIDOR DE ELECCIONES (v2)")
        print("=" * 60)
        print(f"\n✓ Escuchando en puerto {PORT}")
        print(f"✓ Solo redes locales permitidas")
        print(f"✓ Datos persistentes en carpeta 'datos/'")
        print(f"\n🌐 Acceso local: http://localhost:{PORT}")
        print(f"📱 Acceso desde red: http://{local_ip}:{PORT}")
        print(f"\n💡 Comparte la URL de red con otros dispositivos en la misma red WiFi\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n✓ Servidor detenido")
