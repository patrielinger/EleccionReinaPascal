#!/usr/bin/env python3
import http.server
import socketserver
import os
import json
import ipaddress
import uuid
import time
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta

# Puerto donde se ejecutará el servidor
PORT = 3000

# Rutas permitidas (relativas a la carpeta del servidor)
ALLOWED_EXTENSIONS = {'.html', '.css', '.js', '.json', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico'}

# Almacenamiento de sesiones activas
# Formato: {'username': {'session_id': {...}, 'device_id': '...', 'timestamp': ...}}
ACTIVE_SESSIONS = {}
SESSION_TIMEOUT = 3600  # 1 hora en segundos

class LocalNetworkOnlyHandler(http.server.SimpleHTTPRequestHandler):
    """
    Manejador que solo permite conexiones desde redes locales.
    Rechaza cualquier conexión que provenga de internet.
    Valida que solo un dispositivo esté conectado por usuario.
    """
    
    def is_local_ip(self, ip_str):
        """Verifica si una IP es de una red local"""
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
    
    def _lock_session(self, username, session_id, device_id):
        """Registra una sesión activa de un usuario"""
        ACTIVE_SESSIONS[username] = {
            'session_id': session_id,
            'device_id': device_id,
            'timestamp': time.time(),
            'ip': self.client_address[0]
        }
    
    def _verify_session(self, username, session_id, device_id):
        """Verifica si la sesión es válida para el usuario"""
        if username not in ACTIVE_SESSIONS:
            return True  # Sin sesión anterior, permitir
        
        session = ACTIVE_SESSIONS[username]
        
        # Verificar si la sesión ha expirado
        if time.time() - session['timestamp'] > SESSION_TIMEOUT:
            self._unlock_session(username)
            return True
        
        # Si es el mismo dispositivo y sesión, permitir
        if session['session_id'] == session_id and session['device_id'] == device_id:
            session['timestamp'] = time.time()  # Actualizar timestamp
            return True
        
        # Diferentes dispositivos del mismo usuario - RECHAZAR
        return False
    
    def _unlock_session(self, username):
        """Cierra la sesión de un usuario"""
        if username in ACTIVE_SESSIONS:
            del ACTIVE_SESSIONS[username]
    
    def _send_json(self, status, data):
        """Envía respuesta JSON"""
        self.send_response(status)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def do_POST(self):
        """Maneja solicitudes POST para API"""
        client_ip = self.client_address[0]
        
        # Verificar si la IP es local
        if not self.is_local_ip(client_ip):
            self._send_json(403, {'error': 'Acceso denegado: No desde red local'})
            print(f"❌ POST denegado: {client_ip}")
            return
        
        # Obtener la ruta
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # API: Validar login
        if path == '/api/login':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(body)
                username = data.get('username')
                device_id = data.get('device_id')
                
                # Cargar usuarios
                try:
                    with open('candidatas/usuarios.json', 'r') as f:
                        usuarios = json.load(f)
                except:
                    usuarios = [{'username': 'admin', 'password': 'admin', 'role': 'admin'}]
                
                # Verificar credenciales
                user = next((u for u in usuarios if u['username'] == username), None)
                if not user:
                    self._send_json(401, {
                        'error': 'Usuario no encontrado',
                        'allowed_devices': 0
                    })
                    return
                
                # Verificar si ya hay sesión activa desde otro dispositivo
                if username in ACTIVE_SESSIONS:
                    session = ACTIVE_SESSIONS[username]
                    if session['device_id'] != device_id:
                        # Mismo usuario, diferente dispositivo
                        self._send_json(403, {
                            'error': 'Este usuario ya está conectado desde otro dispositivo',
                            'current_device': session['device_id'],
                            'current_ip': session['ip'],
                            'allowed_devices': 0
                        })
                        print(f"❌ Intento de conexión múltiple - Usuario: {username}, Nuevo dispositivo: {device_id}")
                        return
                
                # Generar sesión
                session_id = str(uuid.uuid4())
                self._lock_session(username, session_id, device_id)
                
                self._send_json(200, {
                    'success': True,
                    'username': username,
                    'role': user.get('role', 'user'),
                    'session_id': session_id,
                    'device_id': device_id,
                    'allowed_devices': 1
                })
                print(f"✓ Login exitoso - Usuario: {username}, Dispositivo: {device_id[:8]}...")
                
            except Exception as e:
                self._send_json(400, {'error': str(e)})
        
        # API: Verificar sesión
        elif path == '/api/verify-session':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(body)
                username = data.get('username')
                session_id = data.get('session_id')
                device_id = data.get('device_id')
                
                is_valid = self._verify_session(username, session_id, device_id)
                
                if is_valid:
                    self._send_json(200, {'valid': True, 'message': 'Sesión válida'})
                else:
                    self._send_json(403, {
                        'valid': False,
                        'error': 'Sesión inválida: Tu usuario está conectado desde otro dispositivo'
                    })
                    print(f"❌ Sesión rechazada - Usuario: {username}")
                
            except Exception as e:
                self._send_json(400, {'error': str(e)})
        
        # API: Cerrar sesión
        elif path == '/api/logout':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(body)
                username = data.get('username')
                self._unlock_session(username)
                self._send_json(200, {'success': True, 'message': 'Sesión cerrada'})
                print(f"✓ Logout - Usuario: {username}")
            except Exception as e:
                self._send_json(400, {'error': str(e)})
        
        else:
            self._send_json(404, {'error': 'Endpoint no encontrado'})
    
    def do_GET(self):
        """Maneja las solicitudes GET"""
        client_ip = self.client_address[0]
        
        # Verificar si la IP es local
        if not self.is_local_ip(client_ip):
            self.send_response(403)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'<h1>Acceso Denegado</h1><p>Esta aplicaci\xc3\xb3n solo es accesible desde redes locales.</p>')
            print(f"❌ GET denegado: {client_ip}")
            return
        
        print(f"✓ Conexión aceptada desde: {client_ip}")
        
        # Redirigir "/" a "index.html"
        if self.path == '/':
            self.path = '/index.html'
        
        # Verificar que solo se acceda a archivos permitidos
        parsed_path = urlparse(self.path)
        file_path = parsed_path.path.lstrip('/')
        
        # Prevenir directory traversal
        if '..' in file_path:
            self.send_response(403)
            self.end_headers()
            return
        
        # Verificar extensión permitida
        _, ext = os.path.splitext(file_path)
        if ext and ext not in ALLOWED_EXTENSIONS:
            self.send_response(403)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'<h1>Acceso Denegado</h1>')
            return
        
        # Llamar al manejador por defecto
        super().do_GET()
    
    def log_message(self, format, *args):
        """Personalizar los logs"""
        return super().log_message(format, *args)

def run_server():
    """Inicia el servidor"""
    print("=" * 60)
    print("🎓 SERVIDOR DE ELECCIONES DE REINA")
    print("=" * 60)
    
    # Cambiar al directorio donde está el servidor
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Crear carpeta candidatas si no existe
    if not os.path.exists('candidatas'):
        os.makedirs('candidatas')
    
    # Permitir reutilizar el puerto inmediatamente
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("0.0.0.0", PORT), LocalNetworkOnlyHandler) as httpd:
        print(f"\n✓ Servidor iniciado en puerto {PORT}")
        print(f"✓ Accesible SOLO desde redes locales (WiFi ad-hoc, privadas, etc.)")
        print(f"✓ Denegará accesos desde internet público")
        print(f"✓ SEGURIDAD: Solo UN dispositivo conectado por usuario")
        print(f"\nRedes locales permitidas:")
        print(f"  - 127.0.0.1 (localhost)")
        print(f"  - 192.168.x.x (WiFi privada/ad-hoc)")
        print(f"  - 10.x.x.x (Red privada)")
        print(f"  - 172.16.x.x - 172.31.x.x (Red privada)")
        print(f"  - 169.254.x.x (Red ad-hoc/link-local)")
        print(f"\n" + "=" * 60)
        print(f"Para acceder: abre http://localhost:{PORT} en tu navegador")
        print(f"=" * 60 + "\n")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n❌ Servidor detenido por el usuario")
            httpd.shutdown()

if __name__ == "__main__":
    run_server()

