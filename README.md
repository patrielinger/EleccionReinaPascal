# 🎓 Sistema de Votación - Elección Reina Pascal

Sistema web de votación digital para eventos escolares, pensado para funcionar en una red local segura y sencilla. Permite administrar candidatas, usuarios, categorías de votación, bloquear o reactivar votaciones y visualizar resultados en tiempo real.

## ✅ Qué hace el sistema

- Autenticación obligatoria mediante login.
- Separación entre usuarios administradores y usuarios normales.
- Votación directa por puestos o por puntaje según el modo configurado.
- Gestión de candidatas, usuarios y categorías.
- Bloqueo de votaciones desde el panel administrativo.
- Persistencia de datos en archivos JSON.
- Acceso restringido a redes locales.

---

## 🧰 Requisitos

### Software necesario
- Python 3.8 o superior (recomendado 3.10/3.11)
- Un navegador moderno: Chrome, Edge, Firefox o Safari

### Dependencias
El proyecto no requiere librerías externas. Usa únicamente la biblioteca estándar de Python.

No es necesario ejecutar `pip install` salvo que quieras instalar herramientas adicionales para desarrollo.

### Opcional (solo para red ad-hoc en Linux)
- `sudo`
- `iwconfig`
- `NetworkManager` o soporte para crear redes Wi-Fi ad-hoc

---

## 📁 Estructura del proyecto

```text
.
├── admin_dashboard.html   # Panel administrativo
├── index.html             # Pantalla de inicio de sesión
├── user.html              # Interfaz de votación para usuarios
├── server.py              # Servidor principal
├── css/                   # Estilos del sistema
├── datos/                 # Archivos JSON de datos
├── img/                   # Imágenes de candidatas
├── README/                # Documentación adicional del proyecto
└── logs/                  # Registros del servidor
```

---

## 🚀 Procedimiento para arrancar el programa

### Opción 1: Inicio básico

1. Abrir el buscador de archivos e ir a la carpeta donde esta alojada el programa.
2. Hacer doble click en el archivo *server.py*
3. Al iniciar debera de aparecer una terminal en la cual debera aparecer un enlace 
    "https://localhost:3000" o una direccion ip, por ejemplo "192.168.0.1:3000". La direccion ip es para ingresar desde otro dispositivo conectado a la misma red.
---

### Opción 2: Usar la red local / ad-hoc (recomendado para eventos)

Si quieres que el sistema sea accesible desde otros dispositivos, puedes crear una red local ad-hoc o tambien conocidas como hotspot o punto de enlace. 

#### En Linux
Ejecuta:
```bash
sudo bash README/crear_red_adhoc.sh
```

Luego inicia el servidor:
```bash
python3 server.py
```

Y en otros dispositivos conecta al Wi-Fi generado y abre:
```text
http://192.168.100.1:3000
```

> El script crea una red Wi-Fi local con SSID `EleccionesReina` y contraseña `votacion2026`.

#### En Windows o Mac
Puedes usar un hotspot o una red Wi-Fi local compartida. Asegúrate de que todos los dispositivos estén en la misma red local y accedan mediante la IP del equipo que ejecuta el servidor.

---

## 🔐 Credenciales por defecto

Al iniciar por primera vez, el sistema crea un usuario administrador con:

- Usuario: `admin`
- Contraseña: `admin`

Se recomienda cambiar esa contraseña después del primer acceso.
Al arrancar el programa este abrira una ventana en su buscador por defecto con el panel de administrador del programa con este usuario `admin` ya logeado, bloqueando el acceso a esta cuenta desde otro dispositivo

---

## 🗳️ Cómo usar el sistema

### 1. Iniciar sesión
Abre la página principal y entra con tus credenciales.

### 2. Cerrar votaciones y exportar resultados
Cuando el administrador cierre las votaciones desde el panel de administración, aparecerá un botón nuevo llamado "Exportar votos (.csv)".

Este exportador genera un archivo compatible con Excel o Google Sheets y ofrece dos formatos según el modo activo:

- En modo directo: muestra por cada usuario el puesto, la candidata elegida y el identificador de la candidata.
- En modo por puntaje: muestra por cada usuario la candidata, los puntajes asignados en cada categoría y el total acumulado para generar el ranking final.

El archivo se descarga automáticamente y puede usarse para análisis, registro o presentación de resultados.

### 2. Para usuarios normales
- Verán la interfaz de votación.
- Podrán buscar candidatas y ver su información.
- Podrán votar según el modo activo del sistema.

### 3. Para administradores
- Accederán al panel administrativo.
- Podrán agregar o eliminar usuarios.
- Podrán agregar o eliminar candidatas.
- Podrán gestionar categorías de votación.
- Podrán bloquear o reactivar votaciones.
- Podrán limpiar votos y ver el ranking en tiempo real.

---

## ⚙️ Modos de votación

El sistema soporta dos modos:

### Modo directo
- Un voto por puesto.
- Se elige una candidata para cada categoría o puesto.

### Modo por puntaje
- Se asignan puntajes del 1 al 100 por categoría de votación.
- El sistema suma los puntos y genera un ranking final.

El administrador puede cambiar entre modos desde el panel de votos.

---

## 💾 Almacenamiento de datos

Los datos se guardan en archivos JSON dentro de la carpeta `datos/`:

- `candidatas.json`
- `usuarios.json`
- `votos.json`
- `categorias.json`
- `voting_categories.json`
- `config.json`

El servidor guarda automáticamente los cambios periódicamente y también al cerrar.

---

## 🔒 Seguridad del sistema

El proyecto está pensado para funcionar en entornos locales, no en internet abierto.

### Medidas incluidas
- Login obligatorio.
- Validación de sesión.
- Bloqueo de acceso desde redes no autorizadas.
- Limitación de un dispositivo conectado por usuario.
- Manejo de sesiones con expiración.

---

## 🧪 Verificación rápida

Puedes comprobar que el servidor está bien con:

```bash
python3 -m py_compile server.py
```

Si no muestra errores, la sintaxis del servidor es válida.

---

## 🛠️ Solución de problemas

### El servidor no inicia
- Verifica que Python esté instalado correctamente.
- Revisa que el puerto 3000 no esté ocupado.
- Prueba con otra terminal y confirma que no haya otro proceso escuchando ese puerto.

### No puedo acceder desde otros dispositivos
- Asegúrate de estar en la misma red local.
- Verifica que el firewall permita conexiones locales.
- Si tu navegador trae problemas para ingresa intenta usando Firefox sin ninguna extencion de adblock o desactivando antivirus externos al sistema en tu dispositivo
- Usa la IP del equipo que ejecuta el servidor en vez de `localhost`.

### No puedo entrar al sistema
- Revisa las credenciales.
- Asegúrate de que la sesión no haya expirado.
- Si usas otro dispositivo, confirma que no haya sido abierto con una sesión previa.

---

## 📌 Resumen rápido

Para usar el sistema:

1. Instala Python 3.
2. Abre la carpeta del proyecto.
3. Ejecuta `python server.py` o `py server.py`.
4. Abre `http://localhost:3000`.
5. Inicia sesión con `admin/admin`.
6. Configura candidatas, usuarios y votaciones desde el panel administrativo.
