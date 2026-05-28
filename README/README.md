# 🎓 Elecciones Reina - Sistema de Votación Seguro

Sistema de votación digital diseñado para entornos educativos, con enfoque en **seguridad, control de sesiones y uso en red local**.

---

## 📊 Estado del Proyecto

✅ Completo y funcional  
🚀 Listo para implementación  

---

## 🔐 Características de Seguridad

- Acceso restringido a **red local**
- Bloqueo de accesos desde internet
- Login obligatorio
- Validación de sesión en todas las páginas
- **Un dispositivo por usuario**
- Expiración automática de sesiones

---

## 📁 Estructura del Proyecto

```
ProgramaEleccionReina/
├── index.html        # Login
├── admin.html        # Panel de administrador
├── user.html         # Interfaz de votación
├── css/
│   └── style.css     # Estilos
├── server.py         # Servidor y APIs
```

---

## 👨‍💼 Panel de Administrador

- Gestión de candidatas
- Gestión de usuarios
- Visualización de resultados en tiempo real
- Eliminación de datos

---

## 🗳️ Sistema de Votación

- Búsqueda de candidatas
- Visualización de información
- Votación por categorías:
  - Reina
  - Princesa
  - Dama de Honor
- Edición de votos
- Ranking en vivo

---

## 🔒 Sistema de Sesiones

### Funcionamiento

Cada usuario al iniciar sesión genera:

- `device_id` → Identificador único del dispositivo  
- `session_id` → Identificador de sesión en el servidor  

El servidor registra:

```
usuario → device_id + session_id + IP
```

---

### Reglas

- ❌ No se puede acceder sin login  
- ❌ No se permite más de un dispositivo por usuario  
- ❌ Sesiones inválidas redirigen al login  
- ⏱️ Timeout de sesión: 1 hora  

---

## 🔌 API

### Login
```
POST /api/login
```

### Verificar sesión
```
POST /api/verify-session
```

### Logout
```
POST /api/logout
```

---

## 💾 Almacenamiento

**Cliente (navegador):**
- Usuarios
- Candidatas
- Votos

**Servidor:**
- Sesiones activas (en memoria)

---

## 👥 Usuario Inicial

| Usuario | Contraseña | Rol |
|--------|-----------|-----|
| admin  | admin     | Administrador |

⚠️ Se recomienda cambiar la contraseña en el primer uso.

---

## 📋 Flujo de Uso

1. Usuario accede al sistema
2. Inicia sesión en `index.html`
3. Accede según rol:
   - `admin.html`
   - `user.html`
4. Interactúa con el sistema
5. La sesión es validada continuamente

---

## ⚠️ Problemas Comunes

**Acceso denegado**
- Fuera de red local
- Sesión inválida

**Usuario ya conectado**
- Otro dispositivo está usando esa cuenta

**Redirección al login**
- Sesión expirada o inexistente

---

## 🎯 Objetivo del Proyecto

Garantizar un sistema de votación:

- Seguro
- Controlado
- Simple de usar
- Sin dependencia de internet

---

## 📌 Notas

- Sistema pensado para uso en eventos escolares
- No utiliza base de datos externa
- Arquitectura ligera y fácil de desplegar

---

## 📄 Licencia

ISC
