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
import threading
import webbrowser
from urllib.parse import urlparse
from urllib.parse import parse_qs
import sys
import re
import logging
from datetime import datetime
from io import StringIO

PORT = 3000
ALLOWED_EXTENSIONS = {'.html', '.css', '.js', '.json', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico'}
ACTIVE_SESSIONS = {}
CONNECTED_IPS = set()
VOTING_ENABLED = True

# Datos en memoria
CANDIDATAS = []
USUARIOS = []
VOTOS = {}
CATEGORIAS = []

# Lock único para todas las estructuras compartidas
DATA_LOCK = threading.RLock()

# Archivos de datos
DATA_DIR = 'datos'
os.makedirs(DATA_DIR, exist_ok=True)
CANDIDATAS_FILE = os.path.join(DATA_DIR, 'candidatas.json')
USUARIOS_FILE  = os.path.join(DATA_DIR, 'usuarios.json')
VOTOS_FILE     = os.path.join(DATA_DIR, 'votos.json')
CATEGORIES_FILE = os.path.join(DATA_DIR, 'categorias.json')

DEFAULT_CATEGORIES = [
    {'name': 'Reina',                 'color': '#ff6fe7'},
    {'name': 'Primera Princesa',      'color': '#e6fa33'},
    {'name': 'Segunda Princesa',      'color': '#e6fa33'},
    {'name': 'Primera Dama de Honor', 'color': '#1fff40'},
    {'name': 'Segunda Dama de Honor', 'color': '#1fff40'},
]

# ---------------------------------------------------------------------------
# Carga y guardado
# ---------------------------------------------------------------------------

def load_data():
    global CANDIDATAS, USUARIOS, VOTOS, CATEGORIAS
    with DATA_LOCK:
        try:
            if os.path.exists(CANDIDATAS_FILE):
                with open(CANDIDATAS_FILE, 'r', encoding='utf-8') as f:
                    CANDIDATAS = json.load(f)
        except Exception:
            CANDIDATAS = []

        try:
            if os.path.exists(USUARIOS_FILE):
                with open(USUARIOS_FILE, 'r', encoding='utf-8') as f:
                    USUARIOS = json.load(f)
                for user in USUARIOS:
                    if 'id' not in user:
                        user['id'] = f"user_{uuid.uuid4().hex}"
        except Exception:
            USUARIOS = [{'id': 'user_admin_001', 'username': 'admin',
                         'password': 'admin', 'role': 'admin'}]

        try:
            if os.path.exists(VOTOS_FILE):
                with open(VOTOS_FILE, 'r', encoding='utf-8') as f:
                    VOTOS = json.load(f)
        except Exception:
            VOTOS = {}

        try:
            if os.path.exists(CATEGORIES_FILE):
                with open(CATEGORIES_FILE, 'r', encoding='utf-8') as f:
                    raw = json.load(f)
                    CATEGORIAS = _normalize_categorias(raw)
        except Exception:
            CATEGORIAS = DEFAULT_CATEGORIES.copy()


def _normalize_categorias(raw):
    result = []
    for c in raw:
        if isinstance(c, str):
            result.append({'name': c, 'color': '#ff6fe7'})
        elif isinstance(c, dict) and c.get('name'):
            result.append({'name': str(c['name']).strip(), 'color': c.get('color', '#ff6fe7')})
    return result or DEFAULT_CATEGORIES.copy()


def _flush_to_disk():
    """Escribe todos los datos a disco. Debe llamarse con DATA_LOCK tomado."""
    try:
        with open(CANDIDATAS_FILE, 'w', encoding='utf-8') as f:
            json.dump(CANDIDATAS, f, indent=2, ensure_ascii=False)
        with open(USUARIOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(USUARIOS, f, indent=2, ensure_ascii=False)
        with open(VOTOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(VOTOS, f, indent=2, ensure_ascii=False)
        with open(CATEGORIES_FILE, 'w', encoding='utf-8') as f:
            json.dump(CATEGORIAS, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Error guardando datos: {e}")


def periodic_save():
    """Guarda datos y limpia sesiones expiradas (llamado cada 30 s)."""
    with DATA_LOCK:
        _flush_to_disk()
        current_time = time.time()
        expired = [sid for sid, s in list(ACTIVE_SESSIONS.items())
                   if current_time - s['timestamp'] > 3600]
        for sid in expired:
            del ACTIVE_SESSIONS[sid]
        if expired:
            logging.info(f"Limpiadas {len(expired)} sesiones expiradas")

# ---------------------------------------------------------------------------
# Funciones de negocio (todas con DATA_LOCK)
# ---------------------------------------------------------------------------

def load_candidatas():
    with DATA_LOCK:
        return list(CANDIDATAS)

def save_candidatas(candidatas):
    global CANDIDATAS
    with DATA_LOCK:
        CANDIDATAS = candidatas
    logging.info(f"✓ Candidatas actualizadas: {len(candidatas)}")

def load_usuarios():
    with DATA_LOCK:
        return list(USUARIOS)

def save_usuarios(usuarios):
    global USUARIOS
    with DATA_LOCK:
        USUARIOS = usuarios
    logging.info(f"✓ Usuarios actualizados: {len(usuarios)}")

def load_votos():
    with DATA_LOCK:
        return dict(VOTOS)

def save_votos(votos_patch):
    """Actualiza solo los votos del/los usuarios incluidos en votos_patch."""
    global VOTOS
    with DATA_LOCK:
        for username, user_votes in votos_patch.items():
            VOTOS[username] = user_votes if isinstance(user_votes, dict) else {}
        total = sum(len(v) for v in VOTOS.values())
        try:
            with open(VOTOS_FILE, 'w', encoding='utf-8') as f:
                json.dump(VOTOS, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Error persistiendo votos: {e}")
            raise
    logging.info(f"✓ Votos actualizados: {total} totales")

def clear_all_votes():
    global VOTOS
    with DATA_LOCK:
        VOTOS = {}
        try:
            with open(VOTOS_FILE, 'w', encoding='utf-8') as f:
                json.dump({}, f)
        except Exception as e:
            logging.error(f"Error limpiando votos: {e}")
    logging.info("🧹 Todos los votos eliminados")

def load_categorias():
    with DATA_LOCK:
        return list(CATEGORIAS)

def save_categorias(categorias):
    global CATEGORIAS
    normalized = _normalize_categorias(categorias)
    with DATA_LOCK:
        anteriores = {c['name'] for c in CATEGORIAS}
        nuevas     = {c['name'] for c in normalized}
        for n in nuevas - anteriores:
            logging.info(f"➕ Categoría AGREGADA: '{n}'")
        for n in anteriores - nuevas:
            logging.info(f"➖ Categoría ELIMINADA: '{n}'")
        CATEGORIAS = normalized
        try:
            with open(CATEGORIES_FILE, 'w', encoding='utf-8') as f:
                json.dump(CATEGORIAS, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Error guardando categorías: {e}")


def get_admin_status():
    with DATA_LOCK:
        active_sessions = []
        for session_id, session in ACTIVE_SESSIONS.items():
            active_sessions.append({
                'session_id': session_id,
                'username': session.get('username'),
                'role': session.get('role', 'user'),
                'device_id': session.get('device_id'),
                'timestamp': session.get('timestamp'),
            })

    latest_log_path = None
    logs_dir = 'logs'
    if os.path.isdir(logs_dir):
        candidates = [
            os.path.join(logs_dir, filename)
            for filename in os.listdir(logs_dir)
            if filename.endswith('.log')
        ]
        if candidates:
            latest_log_path = max(candidates, key=os.path.getmtime)

    logs_content = ''
    if latest_log_path and os.path.exists(latest_log_path):
        try:
            with open(latest_log_path, 'r', encoding='utf-8') as f:
                logs_content = f.read()
        except Exception:
            logs_content = ''

    return {
        'success': True,
        'active_sessions': active_sessions,
        'connected_ips': sorted(list(CONNECTED_IPS)),
        'logs': logs_content or 'No hay logs disponibles aún.',
    }

# ---------------------------------------------------------------------------
# Handler HTTP
# ---------------------------------------------------------------------------

class SecureHandler(http.server.SimpleHTTPRequestHandler):

    # --- silenciar logs verbosos de acceso (opcional, reduce ruido en consola)
    def log_message(self, format, *args):
        pass  # Comentar esta línea si querés ver todos los accesos

    def is_local_ip(self, ip_str):
        try:
            ip = ipaddress.ip_address(ip_str)
            for net in ('127.0.0.0/8', '192.168.0.0/16', '10.0.0.0/8',
                        '172.16.0.0/12', '169.254.0.0/16'):
                if ip in ipaddress.ip_network(net):
                    return True
        except ValueError:
            pass
        return False

    def send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    # --- GET APIs -----------------------------------------------------------

    def handle_api_get(self, path):
        if path == '/api/load-candidatas':
            self.send_json(200, {'success': True, 'candidatas': load_candidatas()})
            return True

        if path == '/api/load-usuarios':
            self.send_json(200, {'success': True, 'usuarios': load_usuarios()})
            return True

        if path == '/api/load-categorias':
            self.send_json(200, {'success': True, 'categorias': load_categorias()})
            return True

        if path == '/api/load-votos':
            self.send_json(200, {'success': True, 'votos': load_votos()})
            return True

        if path == '/api/load-data':
            # Un solo endpoint en lugar de 3 llamadas separadas
            self.send_json(200, {
                'success': True,
                'candidatas': load_candidatas(),
                'votos':      load_votos(),
                'categorias': load_categorias(),
            })
            return True

        if path == '/api/admin-status':
            self.send_json(200, get_admin_status())
            return True

        if path == '/api/get-voting-status':
            self.send_json(200, {'success': True, 'voting_enabled': VOTING_ENABLED})
            return True

        if path == '/api/get-network-info':
            self.send_json(200, {
                'success':   True,
                'server_ip': get_local_ip(),
                'client_ip': self.client_address[0],
                'port':      PORT,
            })
            return True

        return False

    # --- POST ---------------------------------------------------------------

    def do_HEAD(self):
        parsed = urlparse(self.path)
        if parsed.path == '/admin.html':
            params = dict(qc.split('=') for qc in parsed.query.split('&') if '=' in qc) if parsed.query else {}
            session = ACTIVE_SESSIONS.get(params.get('session_id'))
            if not session or session.get('device_id') != params.get('device_id') or session.get('role') != 'admin':
                self.send_response(302)
                self.send_header('Location', '/index.html')
                self.end_headers()
                return

    def do_GET(self):
        client_ip = self.client_address[0]
        if client_ip not in CONNECTED_IPS:
            CONNECTED_IPS.add(client_ip)
            logging.info(f"🌐 Nueva IP: {client_ip}")

        if not self.is_local_ip(client_ip):
            self.send_response(403)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'<h1>Acceso Denegado</h1>')
            return

        parsed = urlparse(self.path)
        path   = parsed.path

        if self.handle_api_get(path):
            return

        if path == '/admin.html':
            self.send_response(302)
            self.send_header('Location', '/admin-dashboard')
            self.end_headers()
            return

        if path == '/admin-dashboard':
            self.path = '/admin_dashboard.html'

        if self.path == '/':
            self.path = '/index.html'

        file_path = parsed.path.lstrip('/')
        if '..' in file_path:
            self.send_response(403); self.end_headers(); return
        _, ext = os.path.splitext(file_path)
        if ext and ext not in ALLOWED_EXTENSIONS:
            self.send_response(403); self.end_headers(); return

        super().do_GET()

    def do_POST(self):
        client_ip = self.client_address[0]
        if client_ip not in CONNECTED_IPS:
            CONNECTED_IPS.add(client_ip)
            logging.info(f"🌐 Nueva IP: {client_ip}")

        if not self.is_local_ip(client_ip):
            self.send_json(403, {'error': 'Acceso denegado'})
            return

        parsed  = urlparse(self.path)
        path    = parsed.path
        ctype   = self.headers.get('Content-Type', '')
        clen    = int(self.headers.get('Content-Length', 0))

        if path == '/api/upload-candidata-foto':
            self.handle_upload_candidata_foto(ctype, clen)
            return

        body = self.rfile.read(clen).decode('utf-8') if clen else '{}'
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_json(400, {'error': 'JSON inválido'})
            return

        # --- rutas POST -----------------------------------------------------
        if path == '/api/save-candidatas':
            save_candidatas(data.get('candidatas', []))
            self.send_json(200, {'success': True})

        elif path == '/api/save-usuarios':
            save_usuarios(data.get('usuarios', []))
            self.send_json(200, {'success': True})

        elif path == '/api/save-votos':
            username   = data.get('username')
            votos_data = data.get('votos', {})
            with DATA_LOCK:
                user = next((u for u in USUARIOS if u['username'] == username), None)
            if not user:
                self.send_json(403, {'error': 'Usuario no autenticado'})
                return
            save_votos({username: votos_data.get(username, {})})
            self.send_json(200, {'success': True})

        elif path == '/api/save-categorias':
            save_categorias(data.get('categorias', []))
            self.send_json(200, {'success': True})

        elif path == '/api/clear-all-votes':
            clear_all_votes()
            self.send_json(200, {'success': True})

        elif path == '/api/set-voting-status':
            global VOTING_ENABLED
            VOTING_ENABLED = bool(data.get('enabled', False))
            estado = 'activadas' if VOTING_ENABLED else 'bloqueadas'
            logging.info(f"🔒 Votaciones {estado}")
            self.send_json(200, {'success': True, 'voting_enabled': VOTING_ENABLED})

        elif path == '/api/login':
            self._handle_login(data)

        elif path == '/api/verify-session':
            self._handle_verify_session(data)

        elif path == '/api/logout':
            self._handle_logout(data)

        else:
            self.send_json(404, {'error': 'Not found'})

    # --- helpers de sesión --------------------------------------------------

    def _handle_login(self, data):
        username  = data.get('username')
        password  = data.get('password')
        device_id = data.get('device_id')

        with DATA_LOCK:
            user = next((u for u in USUARIOS
                         if u['username'] == username and u['password'] == password), None)
            if not user:
                self.send_json(401, {'error': 'Credenciales inválidas'})
                return

            active = [(sid, s) for sid, s in ACTIVE_SESSIONS.items() if s['username'] == username]
            other  = [s for _, s in active if s['device_id'] != device_id]
            if other:
                self.send_json(403, {
                    'success': False,
                    'error': 'Este usuario ya está conectado desde otro dispositivo',
                    'allowed_devices': 0,
                })
                return

            # Eliminar sesiones anteriores del mismo dispositivo
            for sid, s in active:
                if s['device_id'] == device_id:
                    del ACTIVE_SESSIONS[sid]

            session_id = str(uuid.uuid4())
            ACTIVE_SESSIONS[session_id] = {
                'username':  username,
                'device_id': device_id,
                'timestamp': time.time(),
                'role':      user.get('role', 'user'),
            }

        self.send_json(200, {
            'success':    True,
            'username':   username,
            'device_id':  device_id,
            'session_id': session_id,
            'role':       user.get('role', 'user'),
        })
        logging.info(f"✓ Login: {username} ({device_id[:8]}…)")

    def _handle_verify_session(self, data):
        username   = data.get('username')
        session_id = data.get('session_id')
        device_id  = data.get('device_id')

        with DATA_LOCK:
            session = ACTIVE_SESSIONS.get(session_id)
            if session and session['username'] == username and session['device_id'] == device_id:
                session['timestamp'] = time.time()
                self.send_json(200, {'valid': True, 'role': session.get('role', 'user')})
            else:
                self.send_json(200, {'valid': False})

    def _handle_logout(self, data):
        username = data.get('username')
        with DATA_LOCK:
            to_remove = [sid for sid, s in ACTIVE_SESSIONS.items() if s['username'] == username]
            for sid in to_remove:
                del ACTIVE_SESSIONS[sid]
        self.send_json(200, {'success': True})
        logging.info(f"✓ Logout: {username}")

    # --- upload foto --------------------------------------------------------

    def handle_upload_candidata_foto(self, content_type, content_length):
        try:
            if 'multipart/form-data' not in content_type:
                self.send_json(400, {'error': 'Content-Type debe ser multipart/form-data'})
                return
            m = re.search(r'boundary=([^\s;]+)', content_type)
            if not m:
                self.send_json(400, {'error': 'Boundary no encontrado'})
                return
            boundary = m.group(1).strip('"')
            body     = self.rfile.read(content_length)
            parts    = body.split(f'--{boundary}'.encode())
            numero = file_data = filename = None

            for part in parts:
                if b'Content-Disposition:' not in part:
                    continue
                he = part.find(b'\r\n\r\n')
                if he == -1:
                    he = part.find(b'\n\n')
                    payload = part[he+2:] if he != -1 else b''
                else:
                    payload = part[he+4:]
                payload = payload.rstrip(b'\r\n')

                nm = re.search(rb'name="([^"]+)"', part[:he] if he != -1 else part)
                if not nm:
                    continue
                field = nm.group(1).decode('utf-8')
                if field == 'numero':
                    numero = payload.decode('utf-8').strip()
                elif field == 'foto':
                    fm = re.search(rb'filename="([^"]+)"', part[:he] if he != -1 else part)
                    if fm:
                        filename  = fm.group(1).decode('utf-8')
                        file_data = payload

            if not all([filename, numero, file_data]):
                self.send_json(400, {'error': 'Falta foto o número de candidata'})
                return
            ext = os.path.splitext(filename)[1].lower()
            if ext not in {'.png', '.jpg', '.jpeg', '.gif', '.svg'}:
                self.send_json(400, {'error': 'Extensión no permitida'})
                return

            img_dir = os.path.join(os.getcwd(), 'img')
            os.makedirs(img_dir, exist_ok=True)
            safe_name = f"{numero}{ext}"
            with open(os.path.join(img_dir, safe_name), 'wb') as f:
                f.write(file_data)
            self.send_json(200, {'success': True, 'foto': f'img/{safe_name}'})
        except Exception as e:
            self.send_json(400, {'error': str(e)})


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def setup_logging():
    logs_dir = 'logs'
    os.makedirs(logs_dir, exist_ok=True)
    log_path = os.path.join(logs_dir, datetime.now().strftime('%d_%m_%y_%H_%M.log'))

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%d/%m/%y %H:%M:%S')

    fh = logging.FileHandler(log_path, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    try:
        cs = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1, closefd=False)
    except Exception:
        cs = sys.stdout
    ch = logging.StreamHandler(cs)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    return log_path


# ---------------------------------------------------------------------------
# Servidor con Threading  ← CORRECCIÓN PRINCIPAL
# ---------------------------------------------------------------------------

class ThreadingServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Atiende cada request en su propio hilo, sin bloquear a los demás."""
    allow_reuse_address = True
    daemon_threads      = True   # los hilos mueren con el proceso principal


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    log_path = setup_logging()
    load_data()
    logging.info("✓ Datos cargados en memoria")

    def _periodic():
        while True:
            time.sleep(30)
            periodic_save()

    threading.Thread(target=_periodic, daemon=True).start()
    logging.info("✓ Guardado automático cada 30 s")

    local_ip = get_local_ip()

    dashboard_url = f"http://localhost:{PORT}/admin-dashboard"
    threading.Timer(1.0, lambda: webbrowser.open(dashboard_url)).start()

    with ThreadingServer(("0.0.0.0", PORT), SecureHandler) as httpd:
        logging.info("=" * 60)
        logging.info("🎓 SERVIDOR DE ELECCIONES (v3 - Threading)")
        logging.info("=" * 60)
        logging.info(f"✓ Puerto: {PORT}")
        logging.info(f"✓ Modo: multi-hilo (hasta 50+ usuarios simultáneos)")
        logging.info(f"✓ Logs: {log_path}")
        logging.info(f"🌐 Local:  http://localhost:{PORT}")
        logging.info(f"📱 Red:    http://{local_ip}:{PORT}")
        logging.info(f"🖥️  Panel admin abierto automáticamente: {dashboard_url}")
        logging.info("")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logging.info("✓ Servidor detenido")
