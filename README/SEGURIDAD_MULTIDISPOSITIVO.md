# 🔒 Sistema de Múltiples Dispositivos - Documentación

## Descripción

El sistema implementa una nueva capa de seguridad que **permite solo UN dispositivo conectado por usuario**. Si un usuario intenta conectarse desde otro dispositivo mientras ya está conectado desde otro, el acceso será rechazado.

---

## 🚀 Características

### 1. **Identificación de Dispositivo**
- Cada dispositivo recibe un ID único basado en:
  - Un identificador aleatorio
  - Timestamp del primer acceso
  - Se almacena en `localStorage` del navegador
- ID Formato: `dev_[8 caracteres aleatorios]_[timestamp]`

### 2. **Validación de Sesión**
- Cuando se carga `admin.html` o `user.html`, se valida automáticamente:
  - Que el usuario esté autenticado
  - Que el dispositivo sea el correcto
  - Que la sesión no haya expirado

### 3. **Rechazo de Conexiones Múltiples**
- El servidor mantiene registro de:
  - Usuario conectado
  - ID de dispositivo
  - Información de IP
  - Timestamp de la sesión
- Si otro dispositivo intenta conectarse con el mismo usuario:
  - **Login es rechazado** con código HTTP 403
  - Mensaje de error: "Este usuario ya está conectado desde otro dispositivo"
  - Se muestran detalles del dispositivo actual

### 4. **Cierre de Sesión Seguro**
- Al cerrar sesión, se comunica con el servidor
- La sesión se limpia en el servidor y el cliente
- Nuevo acceso es permitido desde otros dispositivos

### 5. **Fallback Mode**
- Si el servidor no responde, el sistema funciona en modo local
- Las validaciones se hacen en el navegador
- Se mantiene funcionalidad básica

---

## 🔐 Flujo de Seguridad

### 1. **Primer Acceso - Login**
```
Usuario A (Dispositivo 1)
    ↓
Completa credenciales en index.html
    ↓
JavaScript genera ID único del dispositivo
    ↓
Envía POST /api/login con usuario + device_id
    ↓
Servidor valida credenciales
    ↓
Servidor genera session_id
    ↓
Servidor almacena: usuario → {session_id, device_id, ip, timestamp}
    ↓
✓ Acceso concedido → Redirige a admin.html o user.html
```

### 2. **Intento de Acceso desde Otro Dispositivo**
```
Usuario A (Dispositivo 2)
    ↓
Completa credenciales en index.html
    ↓
Genera nuevo device_id (diferente)
    ↓
Envía POST /api/login con usuario + nuevo device_id
    ↓
Servidor ve que usuario A ya existe pero device_id es diferente
    ↓
❌ Acceso rechazado (HTTP 403)
Mensaje: "Usuario conectado desde otro dispositivo"
```

### 3. **Carga de Página Protegida**
```
Usuario accede a admin.html o user.html
    ↓
JavaScript llama verifySession()
    ↓
Envía POST /api/verify-session con {username, session_id, device_id}
    ↓
Servidor verifica que coinciden
    ↓
✓ Si es válido → Carga página normalmente
✗ Si es inválido → Redirige a index.html
```

---

## 📊 Ejemplo de Sesión en el Servidor

```python
ACTIVE_SESSIONS = {
    'admin': {
        'session_id': 'b04b09a2-3757-42bc-991d-7c752e08ad59',
        'device_id': 'dev_abc12345_1712973000',
        'ip': '192.168.100.50',
        'timestamp': 1712973000.123
    },
    'usuario1': {
        'session_id': 'd8e2f3c5-9876-54a2-bc11-e8d7c6b5a4f3',
        'device_id': 'dev_xyz78901_1712973010',
        'ip': '192.168.100.51',
        'timestamp': 1712973010.456
    }
}
```

---

## 🕐 Timeout de Sesión

- **Duración**: 1 hora (3600 segundos)
- **Actualización**: Cada vez que se verifica la sesión
- **Expiración automática**: Si la sesión expira, nuevo login desde otro dispositivo es permitido

---

## 🔌 Endpoints API

### 1. **POST /api/login**
Solicitud:
```json
{
  "username": "admin",
  "device_id": "dev_abc12345_1712973000"
}
```

Respuesta exitosa (200):
```json
{
  "success": true,
  "username": "admin",
  "role": "admin",
  "session_id": "b04b09a2-3757-42bc-991d-7c752e08ad59",
  "device_id": "dev_abc12345_1712973000",
  "allowed_devices": 1
}
```

Respuesta error - usuario conectado (403):
```json
{
  "error": "Este usuario ya está conectado desde otro dispositivo",
  "current_device": "dev_abc12345_1712973000",
  "current_ip": "192.168.100.50",
  "allowed_devices": 0
}
```

### 2. **POST /api/verify-session**
Solicitud:
```json
{
  "username": "admin",
  "session_id": "b04b09a2-3757-42bc-991d-7c752e08ad59",
  "device_id": "dev_abc12345_1712973000"
}
```

Respuesta válida (200):
```json
{
  "valid": true,
  "message": "Sesión válida"
}
```

Respuesta inválida (403):
```json
{
  "valid": false,
  "error": "Sesión inválida: Tu usuario está conectado desde otro dispositivo"
}
```

### 3. **POST /api/logout**
Solicitud:
```json
{
  "username": "admin"
}
```

Respuesta (200):
```json
{
  "success": true,
  "message": "Sesión cerrada"
}
```

---

## 💻 Almacenamiento en el Cliente

Cada dispositivo guarda en `localStorage`:

```javascript
{
  "deviceId": "dev_abc12345_1712973000",
  "currentUser": {
    "username": "admin",
    "role": "admin",
    "session_id": "b04b09a2-3757-42bc-991d-7c752e08ad59",
    "device_id": "dev_abc12345_1712973000"
  }
}
```

---

## 🛡️ Medidas de Seguridad Implementadas

| Medida | Descripción |
|--------|------------|
| **Device ID único** | Cada navegador recibe un identificador único |
| **Session ID** | Token de sesión generado por el servidor |
| **IP Tracking** | Se registra la IP del primer acceso |
| **Timestamp** | Se valida la antigüedad de la sesión |
| **Single Connection** | Solo 1 dispositivo por usuario simultáneamente |
| **Logout Server-side** | Limpieza de sesión en el servidor |
| **Verification API** | Validación continua de sesión activa |

---

## 🚨 Escenarios de Uso

### Escenario 1: Uso Normal
1. Usuario abre `index.html` en su teléfono
2. Inicia sesión exitosamente
3. Accede a `user.html` y vota
4. Sesión se mantiene activa

### Escenario 2: Múltiples Dispositivos (Bloqueado)
1. Usuario abre `index.html` en teléfono → Sesión activa ✓
2. User intenta acceder desde tablet → Rechazado ❌
3. Mensaje: "Usuario ya conectado desde otro dispositivo"
4. Opción: Cerrar sesión en teléfono primero

### Escenario 3: Cambio de Dispositivo
1. Usuario cierra sesión en teléfono
2. Servidor limpia la sesión
3. Puede acceder desde tablet inmediatamente ✓

### Escenario 4: Sesión Expirada
1. Usuario con sesión inactiva por >1 hora
2. Intenta acceder desde tablet
3. Sesión antigua expira automáticamente
4. Nuevo login desde tablet permitido ✓

---

## 📝 Logs del Servidor

El servidor muestra información de sesiones:

```
✓ Login exitoso - Usuario: admin, Dispositivo: deva1234...
❌ Intento de conexión múltiple - Usuario: admin, Nuevo dispositivo: devb5678
❌ Sesión rechazada - Usuario: username
✓ Logout - Usuario: admin
```

---

## ⚕️ Casos Especiales

### 1. **Pérdida de Dispositivo**
Si un usuario pierde su dispositivo:
- La sesión permanece activa hasta expirar (1 hora)
- El administrador puede eliminar el usuario para limpiar sesiones
- Recrear el usuario permite nuevas sesiones

### 2. **Cambio de Navegador**
Si el usuario abre otro navegador en el MISMO dispositivo:
- Recibe un `deviceId` diferente
- Será tratado como otro dispositivo
- Login será rechazado desde el segundo navegador

### 3. **Borrar Datos del Navegador**
Si el usuario limpia `localStorage`:
- Pierde el `deviceId`
- Se genera uno nuevo al próximo acceso
- Será tratado como nuevo dispositivo
- Si había sesión activa, será rechazado

---

## 🔧 Configuración

Para ajustar el timeout de sesión, edita `server.py`:

```python
SESSION_TIMEOUT = 3600  # Cambiar este valor (en segundos)
```

Ejemplos:
- 1800 = 30 minutos
- 3600 = 1 hora
- 7200 = 2 horas
- 86400 = 1 día

---

## ✅ Testing Manual

### Probar desde terminal:

```bash
# Dispositivo 1 - Login exitoso
curl -X POST http://192.168.100.1:3000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","device_id":"device_1"}'

# Dispositivo 2 - Debe rechazarse
curl -X POST http://192.168.100.1:3000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","device_id":"device_2"}'

# Resultado esperado:
# {"error": "Este usuario ya está conectado desde otro dispositivo", ...}
```

---
