#!/bin/bash

# Script para crear una red WiFi ad-hoc en Linux
# Requiere priviligios de root

echo "================================"
echo "Configurar Red WiFi Ad-Hoc"
echo "================================"
echo ""
echo "Este script configura una red ad-hoc para la aplicación de Elecciones Reina."
echo "Requiere conexión WiFi y acceso de administrador."
echo ""

# Verificar si se ejecuta con sudo
if [[ $EUID -ne 0 ]]; then
   echo "❌ Este script debe ejecutarse con sudo"
   echo "Ejecuta: sudo bash crear_red_adhoc.sh"
   exit 1
fi

# Encontrar la interfaz WiFi
echo "Buscando interfaces WiFi disponibles..."
WIFI_INTERFACE=$(iwconfig 2>/dev/null | grep -i "ESSID\|802.11" | head -1 | awk '{print $1}')

if [ -z "$WIFI_INTERFACE" ]; then
    echo "❌ No se encontró interfaz WiFi disponible"
    echo "Verifica que tu tarjeta WiFi esté habilitada."
    exit 1
fi

echo "✓ Interfaz WiFi encontrada: $WIFI_INTERFACE"
echo ""

# Configuración de la red
SSID="EleccionesReina"
PASSWORD="votacion2026"
CHANNEL="1"
IP_SERVER="192.168.100.1"
NETMASK="255.255.255.0"

echo "Configuración de la red ad-hoc:"
echo "  SSID: $SSID"
echo "  Contraseña: $PASSWORD"
echo "  IP del servidor: $IP_SERVER"
echo "  Máscara: $NETMASK"
echo ""

# Detener Network Manager si está activo
echo "Deteniendo NetworkManager..."
systemctl stop NetworkManager 2>/dev/null

# Traer la interfaz hacia arriba
echo "Activando interfaz $WIFI_INTERFACE..."
ip link set $WIFI_INTERFACE up

# Crear la red ad-hoc con iwconfig (método antiguo pero confiable)
echo "Creando red ad-hoc..."
iwconfig $WIFI_INTERFACE mode ad-hoc
iwconfig $WIFI_INTERFACE essid "$SSID"
iwconfig $WIFI_INTERFACE channel $CHANNEL

# Asignar IP al servidor
echo "Asignando IP al servidor..."
ip addr flush dev $WIFI_INTERFACE 2>/dev/null
ip addr add $IP_SERVER/24 dev $WIFI_INTERFACE

# Configurar firewall para permitir conexiones locales
echo "Configurando firewall..."
iptables -A INPUT -s 192.168.100.0/24 -p tcp --dport 3000 -j ACCEPT 2>/dev/null
iptables -A INPUT -s 127.0.0.0/8 -p tcp --dport 3000 -j ACCEPT 2>/dev/null

echo ""
echo "================================"
echo "✓ Red ad-hoc configurada:"
echo "================================"
echo ""
echo "SSID: $SSID"
echo "IP del servidor: $IP_SERVER"
echo "Otros dispositivos pueden conectarse a esta red"
echo ""
echo "Para conectarse desde otro dispositivo:"
echo "  1. Abre WiFi disponibles"
echo "  2. Busca '$SSID'"
echo "  3. Conecta con la contraseña: $PASSWORD"
echo "  4. Abre el navegador en: http://$IP_SERVER:8000"
echo ""
echo "Para restaurar la configuración normal:"
echo "  sudo systemctl start NetworkManager"
echo ""
