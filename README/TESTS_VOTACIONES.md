# 🧪 MANUAL DE PRUEBA - Sistema de Votaciones Multi-Usuario

## Requisitos
- 3+ navegadores o pestañas abiertas
- Usuarios de prueba creados en admin
- Servidor ejecutándose

---

## 🔬 TEST 1: Múltiples Usuarios Votando Simultáneamente

### Paso 1: Preparación
```
1. Abre 3 navegadores (o pestañas anónimas)
   - Navegador A → Usuario: user1
   - Navegador B → Usuario: user2
   - Navegador C → Usuario: user3
```

### Paso 2: Ejecución Simultánea
```
⏱️ t=0s   Navegador A vota: Candidata #1 como REINA
⏱️ t=0.2s Navegador B vota: Candidata #1 como PRINCESA
⏱️ t=0.4s Navegador C vota: Candidata #1 como DAMA

↓ ESPERAR 30 SEGUNDOS (auto-sync)

⏱️ t=30s  Refresh en todos los navegadores
```

### Paso 3: Verificación ✅
**ESPERADO:**
- Navegador A: Candidata #1 en REINA
- Navegador B: Candidata #1 en PRINCESA  
- Navegador C: Candidata #1 en DAMA
- **TODOS LOS VOTOS PERSISTEN**

**SI FALLA:** ❌ Es la race condition original

---

## 🔬 TEST 2: Mismo Usuario, Múltiples Categorías

### Paso 1: Preparación
```
Navegador A → Usuario: admin
(Abre 2 pestañas del mismo navegador)
```

### Paso 2: Ejecución
```
Pestaña 1: Vota Candidata #5 como REINA
Pestaña 2: Vota Candidata #5 como PRINCESA

↓ Esperar auto-sync 30s ↓

Pestaña 1: Refresh
Pestaña 2: Refresh
```

### Paso 3: Verificación ✅
**ESPERADO:**
- Ambas pestañas muestran:
  - Candidata #5 en REINA
  - Candidata #5 en PRINCESA
- **No hay conflicto de categorías**

---

## 🔬 TEST 3: Cambio de Voto en Tiempo Real

### Paso 1: Preparación
```
Navegador A → Usuario: testuser
Navegador B → ADMIN (para ver ranking)
```

### Paso 2: Ejecución
```
⏱️ t=0s   Navegador A vota: Candidata #1 como REINA
⏱️ t=5s   Admin ve ranking actualizado
⏱️ t=10s  Navegador A CAMBIA a Candidata #2 como REINA
⏱️ t=15s  Admin ve cambio actualizado
⏱️ t=20s  Navegador A vota Candidata #1 como PRINCESA
⏱️ t=25s  Admin ve nuevo voto
```

### Paso 3: Verificación ✅
**ESPERADO:**
- Ranking se actualiza en vivo
- Votos previos no desaparecen
- Cambios son inmediatos en admin

---

## 🔬 TEST 4: Stress Test (Muchos Usuarios)

### Paso 1: Preparación
```
Crear 10+ usuarios en admin:
- user01, user02, user03... user10
```

### Paso 2: Ejecución
```
Abrir múltiples pestañas rápidamente:
- Todos votan simultáneamente
- Cada uno vota por diferentes candidatas
- Cada uno en diferentes categorías
```

### Paso 3: Verificación ✅
**ESPERADO:**
- No hay timeouts
- No hay errores 500
- Todos los votos se guardan
- **Servidor no colapsa**

---

## 🔬 TEST 5: Validación de Seguridad

### Paso 1: Ataque Simulado
```
Console del navegador (F12):
```
```javascript
// Intentar votar como otro usuario
fetch('/api/save-votos', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        username: 'admin',           // ❌ Usuario diferente
        votos: {'admin': {'Reina': 999}}
    })
});
```

### Paso 2: Verificación ✅
**ESPERADO:**
- **Respuesta:** `403 Forbidden` o error
- **No se guardan** los votos de otro usuario
- **Protección:** Solo el usuario autenticado puede cambiar sus votos

---

## 🔬 TEST 6: Persistencia Después de Limpiar

### Paso 1: Ejecución
```
1. Usuario A vota
2. Admin → "Eliminar Todos Los Votos"
3. Usuario B vota
4. Refresh página de Usuario A
```

### Paso 2: Verificación ✅
**ESPERADO:**
- Usuario A ve: "No has votado en esta categoría"
- Usuario B ver sus votos nuevos
- **Completamente independientes**

---

## 📊 CHECKLIST DE VALIDACIÓN

### Concurrencia
- [ ] 3+ usuarios votan simultáneamente sin conflictos
- [ ] Cambios de voto se aplican correctamente
- [ ] No hay "votos fantasma"
- [ ] El server no se cae

### Seguridad
- [ ] Un usuario no puede votar como otro
- [ ] Validación de username en servidor
- [ ] Respuesta 403 en intentos de spoofing

### Persistencia
- [ ] Los votos sobreviven a server restart
- [ ] Los votos persisten entre sesiones
- [ ] Limpiar votos realmente los elimina

### Performance
- [ ] Auto-sync cada 30s (no sobrecarga)
- [ ] Status check cada 5s en admin
- [ ] Sin timeouts ni errores

---

## 🐛 Troubleshooting

| Problema | Causa | Solución |
|----------|-------|----------|
| Votos desaparecen | Race condition | Reiniciar servidor |
| Error 403 en save | Usuario inválido | Verificar currentUser |
| Votos compartidos | Caché local | Limpiar localStorage |
| Admin no ve cambios | No sincronizado | Refrescar Ranking |
| Server lento | Muchos usuarios | Aumentar auto-save interval |

---

## ✅ RESULTADOS ESPERADOS FINALES

**SI TODOS LOS TESTS PASAN:**
- ✅ Votos completamente independientes por usuario
- ✅ Múltiples usuarios simultáneos sin conflictos
- ✅ Datos consistentes y persistentes
- ✅ **Solución implementada CORRECTAMENTE**

**SI ALGÚN TEST FALLA:**
- Revisar logs en `/logs/`
- Verificar consola del navegador (F12)
- Contactar soporte técnico
