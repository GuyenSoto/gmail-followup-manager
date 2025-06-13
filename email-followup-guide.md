# Gmail Follow-up Manager - Sistema Completo

## 🚀 Configuración del Entorno con UV

### 1. Instalar UV (si no lo tienes)
```bash
# En macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# En Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Verificar instalación
uv --version
```

### 2. Crear el proyecto y entorno
```bash
# Crear directorio del proyecto
mkdir gmail-followup-manager
cd gmail-followup-manager

# Inicializar proyecto con uv
uv init
```

### 3. Instalar dependencias con UV
```bash
# Instalar todas las dependencias de una vez
uv add streamlit pandas openpyxl python-dotenv
uv add google-api-python-client google-auth-httplib2 google-auth-oauthlib
uv add plotly # Para gráficos mejorados
```

## 📁 Estructura del Proyecto Mejorada

```
gmail-followup-manager/
├── .env                    # Variables de entorno
├── .gitignore             # Archivos a ignorar en git
├── pyproject.toml         # Configuración del proyecto (uv la crea)
├── README.md              # Documentación
├── requirements.txt       # Para compatibilidad (opcional)
├── src/
│   ├── __init__.py
│   ├── config.py          # Configuración centralizada
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── gmail_auth.py  # Autenticación Gmail
│   │   └── calendar_auth.py # Autenticación Calendar
│   ├── services/
│   │   ├── __init__.py
│   │   ├── gmail_service.py # Lógica Gmail
│   │   ├── calendar_service.py # Lógica Calendar
│   │   └── data_service.py # Gestión de datos
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── helpers.py     # Funciones auxiliares
│   │   └── validators.py  # Validaciones
│   └── ui/
│       ├── __init__.py
│       ├── components.py  # Componentes UI reutilizables
│       └── pages.py       # Páginas de la app
├── app.py                 # Punto de entrada principal
├── credentials.json       # Credenciales Google (no versionar)
└── data/                  # Directorio para datos locales
    └── exports/           # Exportaciones Excel
```

## 🔧 Configuración de Google APIs

### 1. Google Cloud Console Setup
1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita estas APIs:
   - Gmail API
   - Google Calendar API
4. Ve a "Credenciales" → "Crear credenciales" → "ID de cliente OAuth 2.0"
5. Selecciona "Aplicación de escritorio"
6. Descarga el JSON y guárdalo como `credentials.json`

### 2. Archivo .env
```env
# Google APIs
GOOGLE_CREDENTIALS_FILE=credentials.json
GMAIL_SCOPES=https://www.googleapis.com/auth/gmail.readonly
CALENDAR_SCOPES=https://www.googleapis.com/auth/calendar.events

# App Configuration
APP_NAME=Gmail Follow-up Manager
DATA_DIR=data
EXPORTS_DIR=data/exports
DEFAULT_LOOKBACK_DAYS=30
MAX_RESULTS=200

# UI Configuration
PAGE_TITLE=Gmail Follow-up Manager
PAGE_ICON=📧
LAYOUT=wide
```

## 📝 Implementación del Código

### config.py
```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / os.getenv('DATA_DIR', 'data')
    EXPORTS_DIR = BASE_DIR / os.getenv('EXPORTS_DIR', 'data/exports')
    CREDENTIALS_FILE = BASE_DIR / os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
    
    # Google APIs
    GMAIL_SCOPES = [os.getenv('GMAIL_SCOPES', 'https://www.googleapis.com/auth/gmail.readonly')]
    CALENDAR_SCOPES = [os.getenv('CALENDAR_SCOPES', 'https://www.googleapis.com/auth/calendar.events')]
    
    # App settings
    APP_NAME = os.getenv('APP_NAME', 'Gmail Follow-up Manager')
    DEFAULT_LOOKBACK_DAYS = int(os.getenv('DEFAULT_LOOKBACK_DAYS', '30'))
    MAX_RESULTS = int(os.getenv('MAX_RESULTS', '200'))
    
    # UI
    PAGE_TITLE = os.getenv('PAGE_TITLE', 'Gmail Follow-up Manager')
    PAGE_ICON = os.getenv('PAGE_ICON', '📧')
    LAYOUT = os.getenv('LAYOUT', 'wide')
    
    @classmethod
    def ensure_directories(cls):
        """Crear directorios necesarios si no existen"""
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.EXPORTS_DIR.mkdir(exist_ok=True)
```

## 🚀 Ejecución del Proyecto

### Usando UV (Recomendado)
```bash
# Activar el entorno de uv y ejecutar
uv run streamlit run app.py

# O si prefieres activar manualmente el entorno
uv shell
streamlit run app.py
```

### Primera ejecución
1. La app abrirá tu navegador automáticamente
2. Te pedirá autorizar acceso a Gmail y Calendar
3. Se crearán archivos `token_gmail.json` y `token_calendar.json`
4. ¡Ya puedes usar la aplicación!

## ✨ Características Mejoradas

### 🔍 Búsqueda Inteligente
- Filtros avanzados por fecha, remitente, asunto
- Detección automática de correos sin respuesta
- Soporte para múltiples etiquetas de Gmail

### 📊 Dashboard Visual
- Estadísticas de seguimiento con gráficos
- Métricas de respuesta y productividad
- Timeline de actividad

### 🗂️ Gestión de Datos
- Exportación automática a Excel
- Importación de datos existentes
- Backup automático de cambios

### 📅 Integración Calendar
- Creación masiva de recordatorios
- Templates personalizables de eventos
- Sincronización bidireccional

### 🚨 Sistema de Alertas
- Notificaciones por correos pendientes
- Recordatorios automáticos
- Reportes semanales

## 🛠️ Comandos Útiles con UV

```bash
# Ver dependencias instaladas
uv pip list

# Agregar nueva dependencia
uv add nueva-libreria

# Actualizar dependencias
uv pip upgrade --all

# Generar requirements.txt (para compatibilidad)
uv pip freeze > requirements.txt

# Ejecutar con variables de entorno específicas
uv run --env-file .env.prod streamlit run app.py

# Ejecutar tests (cuando los agregues)
uv run pytest

# Linting y formateo
uv add black flake8 --dev
uv run black src/
uv run flake8 src/
```

## 📋 Próximos Pasos

1. **Configurar el entorno**: Sigue los pasos de instalación con UV
2. **Configurar Google APIs**: Obtén tus credenciales
3. **Ejecutar la aplicación**: `uv run streamlit run app.py`
4. **Personalizar**: Ajusta filtros y configuraciones según tus necesidades

## 🔒 Seguridad y Buenas Prácticas

- Nunca subas `credentials.json` a repositorios públicos
- Usa `.env` para configuraciones sensibles
- Implementa rotación de tokens para producción
- Considera usar Google Service Accounts para despliegues

## 🆘 Solución de Problemas

### Error de autenticación
```bash
# Eliminar tokens existentes y re-autenticar
rm token_*.json
uv run streamlit run app.py
```

### Problemas con UV
```bash
# Reinstalar UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Limpiar cache de UV
uv cache clean
```

### Dependencias faltantes
```bash
# Sincronizar dependencias
uv sync

# Reinstalar todo desde cero
rm -rf .venv
uv venv
uv sync
```

¿Te gustaría que proceda a crear los archivos de código completos para este sistema mejorado?