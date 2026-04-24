# Guía: Ejecutar Elecciones Reina en Red Ad-Hoc

## Descripción

Este programa solo es accesible desde una **red local ad-hoc** creada en tu computadora. No se puede acceder desde internet. Solo los dispositivos conectados a la red ad-hoc podrán usar la aplicación.

---

## ⚙️ Paso 1: Configurar la Red Ad-Hoc

### En Linux (Recomendado):

```bash
cd /home/patrielinger/Documentos/ProgramaEleccionReina
sudo bash crear_red_adhoc.sh
```

El script creará una red WiFi con:
- **SSID**: `EleccionesReina`
- **Contraseña**: `votacion2026`
- **IP del servidor**: `192.168.100.1:3000`

### En Windows o MacOS:

Busca en la documentación de tu sistema operativo cómo crear una red ad-hoc o hotspot WiFi local.

---

## 🚀 Paso 2: Iniciar el Servidor

En la carpeta del proyecto, ejecuta:

```bash
python3 server.py
```

Deberías ver algo como:

```
============================================================
🎓 SERVIDOR DE ELECCIONES DE REINA
============================================================

✓ Servidor iniciado en puerto 3000
✓ Accesible SOLO desde redes locales (WiFi ad-hoc, privadas, etc.)
✓ Denegará accesos desde internet público

Redes locales permitidas:
  - 127.0.0.1 (localhost)
  - 192.168.x.x (WiFi privada)
  - 10.x.x.x (Red privada)
  - 172.16.x.x - 172.31.x.x (Red privada)
  - 169.254.x.x (Red ad-hoc/link-local)

============================================================
Para acceder: abre http://localhost:3000 en tu navegador
============================================================
```

---

## 📱 Paso 3: Conectarse desde Otros Dispositivos

1. **Ve a WiFi disponibles** en tu otro dispositivo (teléfono, tablet, etc.)
2. **Busca**: `EleccionesReina`
3. **Contraseña**: `votacion2026`
3. **Abre tu navegador** y ve a: `http://192.168.100.1:3000`

---

## 🔐 Seguridad

El servidor rechazará cualquier conexión que NO sea desde una red local:

✓ **Permitidas**:
- `127.0.0.1` (localhost)
- `192.168.x.x` (redes privadas/ad-hoc)
- `10.x.x.x` (redes privadas)
- `169.254.x.x` (redes ad-hoc)

❌ **Rechazadas**:
- Conexiones desde internet público
- IPs externas
- Accesos desde fuera de la red local

---

## 📋 Flujo de Uso

1. **Servidor iniciado** → `python3 server.py`
2. **Red ad-hoc activa** → `sudo bash crear_red_adhoc.sh`
3. **Dispositivos conectados** a `EleccionesReina`
4. **Abren** `http://192.168.100.1:3000`
5. **Login obligatorio** en `index.html`
6. **Acceso a admin.html o user.html** una vez autenticados

---

## 🛑 Detener el Servidor

Presiona `Ctrl + C` en la terminal donde corre el servidor.

---

## 🔧 Restaurar Configuración de Red (Linux)

Si quieres volver a la configuración normal de wifi:

```bash
sudo systemctl start NetworkManager
```

---

## ⚠️ Requisitos

- Python 3.6+
- Acceso de administrador (para crear la red ad-hoc)
- Tarjeta WiFi compatible con modo ad-hoc
- Navegador web moderno en los dispositivos cliente

---

## 🆘 Problemas Comunes

### "No encuentro la red ad-hoc"
- Verifica que el script se ejecutó correctamente
- Revisa que tu tarjeta WiFi esté habilitada
- Intenta reiniciar el servidor

### "Conexión denegada"
- Asegúrate de estar conectado a `EleccionesReina`
- Verifica que uses `http://` (no `https://`)
- La dirección debe ser `http://192.168.100.1:3000`

### "Error de puerto"
- Verifica que no hay otro servidor en puerto 3000
- Cambia el puerto en el archivo `server.py` si es necesario

---

## 📝 Personalización

Para cambiar la SSID o contraseña, edita `crear_red_adhoc.sh`:

```bash
SSID="TuSSID"
PASSWORD="TuContraseña"
IP_SERVER="192.168.100.1"
```

---
