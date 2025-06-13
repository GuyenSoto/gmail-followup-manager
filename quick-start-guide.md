# 🚀 Gmail Follow-up Manager - Inicio Rápido

## ⚡ Instalación Express (5 minutos)

### 1. Preparar el entorno
```bash
# Crear directorio del proyecto
mkdir gmail-followup-manager
cd gmail-followup-manager

# Descargar archivos del proyecto
# (Copia todos los archivos de código que te proporcioné)
```

### 2. Instalar UV y dependencias
```bash
# Instalar UV (si no lo tienes)
# Windows (PowerShell):
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Inicializar proyecto e instalar dependencias
uv init
uv add streamlit pandas openpyxl python-dotenv
uv add google-api-python-client google-auth-httplib2 google-auth-oauthlib plotly
```

### 3. Configurar Google APIs (CRÍTICO)
```bash
# 1. Ve a: https://console.cloud.google.com/
# 2. Crea proyecto → Habilitar APIs (Gmail + Calendar)
# 3. Credenciales → OAuth 2.0 → Aplicación escritorio
# 4. Descargar JSON → Guardar como 'credentials.json'
```

### 4. Ejecutar la aplicación
```bash
# Modo directo
uv run streamlit run app.py

# O crear archivo run.sh/run.bat:
echo "uv run streamlit run app.py" > run.sh
chmod +x run.sh
./run.sh
```

## 📂 Estructura Mínima Requerida

```
gmail-followup-manager/
├── app.py                          # ← Aplicación principal
├── credentials.json                # ← Credenciales Google (TÚ lo descargas)
├── .env                           # ← Variables configuración
├── src/
│   ├── __init__.py
│   ├── config.py                  # ← Configuración central
│   ├── auth/
│   │   ├── __init__.py
│   │   └── gmail_auth.py          # ← Autenticación Gmail
│   └── services/
│       ├── __init__.py
│       ├── gmail_service.py       # ← Lógica Gmail
│       ├── calendar_service.py    # ← Lógica Calendar
│       └── data_service.py        # ← Gestión datos
└── data/                          # ← Se crea automáticamente
    ├── exports/
    └── backups/
```

## ⚙️ Archivo .env (Crear manualmente)

```env
# Google APIs
GOOGLE_CREDENTIALS_FILE=credentials.json

# App Configuration  
APP_NAME=Gmail Follow-up Manager
DATA_DIR=data
DEFAULT_LOOKBACK_DAYS=30
MAX_RESULTS=200

# UI
PAGE_TITLE=Gmail Follow-up Manager
PAGE_ICON=📧
LAYOUT=wide
```

## 🎯 Primer Uso

1. **Ejecutar app**: `uv run streamlit run app.py`
2. **Autorizar Google**: Se abre navegador → Permite acceso
3. **Buscar correos**: Pestaña "Búsqueda" → Configurar filtros → Buscar
4. **Gestionar**: Revisar tabla → Añadir notas → Cambiar estados
5. **Recordatorios**: Seleccionar correos → Crear en Calendar

## 🔧 Comandos UV Esenciales

```bash
# Instalar nueva librería
uv add nombre-libreria

# Ejecutar aplicación
uv run streamlit run app.py

# Ver dependencias
uv pip list

# Actualizar todo
uv sync

# Limpiar cache si hay problemas
uv cache clean
```

## 🆘 Problemas Comunes

### "No module named 'src'"
```bash
# Asegúrate de tener __init__.py en todas las carpetas src/
touch src/__init__.py
touch src/auth/__init__.py
touch src/services/__init__.py
```

### "credentials.json not found"
```bash
# Verifica que el archivo esté en la raíz del proyecto
ls -la credentials.json

# Si no existe, descárgalo desde Google Cloud Console
```

### Error de autenticación
```bash
# Eliminar tokens y re-autenticar
rm token_*.json token_*.pickle
uv run streamlit run app.py
```

### UV no encontrado
```bash
# Reinstalar UV
curl -LsSf https://astral.sh/uv/install.sh | sh
# Reiniciar terminal y probar: uv --version
```

## 💡 Tips de Uso

### Palabras clave efectivas
```
interview, follow up, proposal, meeting, quotation, 
thank you, checking in, response, feedback
```

### Filtros útiles
- **Etiquetas**: SENT (correos enviados)
- **Días atrás**: 7-30 días para seguimiento activo
- **Excluir automáticos**: Siempre activado

### Estados recomendados
- **Pending**: Esperando respuesta
- **Following Up**: Enviado seguimiento
- **Closed**: Resuelto o respondido
- **No Response Needed**: No requiere acción

## 🎉 ¡Listo!

Con estos pasos tienes un sistema completo para:
- ✅ Rastrear correos sin respuesta
- ✅ Crear recordatorios automáticos
- ✅ Analizar métricas de seguimiento
- ✅ Exportar datos a Excel
- ✅ Gestionar backups

**¿Problemas?** Revisa que tengas:
1. ✅ UV instalado (`uv --version`)
2. ✅ credentials.json descargado
3. ✅ APIs habilitadas en Google Cloud
4. ✅ Estructura de carpetas correcta