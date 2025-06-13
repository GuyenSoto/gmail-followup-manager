@echo off
echo 🚀 Iniciando Gmail Follow-up Manager...
echo.

REM Desactivar conda si está activo
echo 🔄 Desactivando entorno conda...
call conda deactivate 2>nul
echo ✅ Entorno conda desactivado

REM Activar el entorno virtual del proyecto
echo 📦 Activando entorno virtual del proyecto...
call .\.venv\Scripts\activate
if errorlevel 1 (
    echo ❌ Error: No se pudo activar el entorno virtual
    echo 💡 Asegúrate de que .venv existe en este directorio
    pause
    exit /b 1
)
echo ✅ Entorno virtual activado

REM Verificar que existe credentials.json
if not exist "credentials.json" (
    echo ❌ Error: No se encontró credentials.json
    echo 📋 Descarga el archivo desde Google Cloud Console
    echo    y guárdalo en este directorio.
    pause
    exit /b 1
)
echo ✅ Archivo credentials.json encontrado

REM Verificar que existe app.py
if not exist "app.py" (
    echo ❌ Error: No se encontró app.py
    echo 📁 Asegúrate de estar en el directorio correcto
    pause
    exit /b 1
)
echo ✅ Archivo app.py encontrado

echo.
echo ✅ Iniciando aplicación...
echo 🌐 La aplicación se abrirá en tu navegador
echo.
uv run streamlit run app.py
pause