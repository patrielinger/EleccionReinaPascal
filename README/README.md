# 🎓 Elecciones Reina de Colegios - Sistema de Votación Seguro

Sistema de votación digital para escuelas con acceso **exclusivamente desde red WiFi ad-hoc local**.

---

## 🚀 Inicio Rápido

### 1. Configurar la red ad-hoc (primera vez)

```bash
sudo bash crear_red_adhoc.sh
```

### 2. Iniciar el servidor

```bash
python3 server.py
```

### 3. Conectarse desde otros dispositivos

- **WiFi**: `EleccionesReina`
- **Contraseña**: `votacion2026`
- **URL**: `http://192.168.100.1:3000`

---

## 📚 Documentación Completa

Para instrucciones detalladas, ver [CONFIGURACION_RED.md](CONFIGURACION_RED.md)

---

## 🔐 Características de Seguridad

✓ **Acceso solo desde red local** - Sin acceso desde internet público  
✓ **Autenticación obligatoria** - Login requerido para ingresar  
✓ **Red ad-hoc aislada** - Conexión privada sin conectarse a internet  
✓ **Verificación de IP** - El servidor rechaza IPs externas  

---

## 📋 Características del Sistema

### 👨‍💼 Panel de Administrador
- Agregar/eliminar candidatas con foto y descripción
- Gestionar usuarios del sistema
- Ver ranking en tiempo real
- Eliminar usuarios registrados

### 🗳️ Interfaz de Votación
- Buscar candidatas por nombre o número
- Ver detalles de cada candidata
- Votar por categorías: Reina, Princesa, Dama de Honor
- Cambiar voto en cualquier momento
- Ver ranking actualizado en vivo

### 🔒 Sistema de Login
- Autenticación de usuarios
- Roles de administrador y usuario
- Sesiones persistentes
- Botón de cerrar sesión

---

## 📁 Estructura del Proyecto

```
ProgramaEleccionReina/
├── index.html              # Página de login
├── admin.html              # Panel de administración
├── user.html               # Interfaz de votación
├── css/
│   └── style.css           # Estilos responsivos
├── server.py               # Servidor seguro local
├── iniciar_servidor.sh     # Script para iniciar servidor
├── crear_red_adhoc.sh      # Script para crear red WiFi
├── CONFIGURACION_RED.md    # Guía detallada de configuración
└── README.md               # Este archivo
```

---

## 💻 Requisitos del Sistema

- **Sistema Operativo**: Linux, Windows o macOS
- **Python**: 3.6 o superior
- **Navegador web**: Moderno (Chrome, Firefox, Edge, Safari)
- **Tarjeta WiFi**: Compatible con modo ad-hoc (Linux)
- **Acceso de administrador**: Para crear la red ad-hoc

---

## ⚙️ Configuración Avanzada

### Cambiar puerto del servidor

Edita `server.py`:
```python
PORT = 3000  # Cambiar número
```

### Cambiar SSID o contraseña WiFi

Edita `crear_red_adhoc.sh`:
```bash
SSID="NuevoSSID"
PASSWORD="NuevaContraseña"
```

### Cambiar IP del servidor

Edita `crear_red_adhoc.sh`:
```bash
IP_SERVER="192.168.50.1"  # Nueva IP
```

---

## 🆘 Solución de Problemas

**P: La red ad-hoc no aparece**  
R: Verifica que tu tarjeta WiFi esté habilitada y soporta modo ad-hoc. Ejecuta el script con `sudo`.

**P: "Acceso Denegado" al abrir el sitio**  
R: El servidor solo acepta conexiones desde IPs locales. Asegúrate de estar conectado a `EleccionesReina` y usando la IP correcta: `192.168.100.1:3000`

**P: El servidor no inicia**  
R: Verifica que Python 3 esté instalado y que el puerto 3000 no esté en uso.

**P: ¿Cómo restauro la configuración de WiFi normal?**  
R: Ejecuta `sudo systemctl start NetworkManager` en Linux.

---

## 📝 Notas de Uso

- **Datos guardados**: Se almacenan en el navegador (localStorage)
- **Usuario predeterminado**: admin / admin
- **Primer login**: Recomendado cambiar contraseña del admin
- **Datos persistentes**: Los votos y candidatas se guardan automáticamente
- **Multi-dispositivo**: Múltiples usuarios pueden votar simultáneamente

---

## 👥 Usuarios de Ejemplo

Al iniciar, el sistema crea un usuario administrador:

| Usuario | Contraseña | Rol         |
|---------|-----------|-------------|
| admin   | admin     | Administrador |

---

**Versión**: 1.0  
**Última actualización**: Abril 2026  
**Licencia**: ISC