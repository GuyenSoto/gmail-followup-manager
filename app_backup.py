# app.py - Gmail Follow-up Manager
import streamlit as st
import sys
from pathlib import Path

# Agregar src al path
sys.path.append(str(Path(__file__).parent / 'src'))

try:
    from config import Config
    config_loaded = True
except ImportError:
    config_loaded = False

# Configuración de página
st.set_page_config(
    page_title="Gmail Follow-up Manager",
    page_icon="📧",
    layout="wide"
)

def main():
    st.title("📧 Gmail Follow-up Manager")
ECHO is off.
    if config_loaded:
        st.success("✅ Configuración cargada correctamente")
        Config.ensure_directories()
    else:
        st.warning("⚠️ No se pudo cargar la configuración")
ECHO is off.
    st.markdown("""
    ### 🚀 Sistema de Seguimiento de Correos
ECHO is off.
    **Estado de configuración:**
    """^)
ECHO is off.
    # Verificaciones
    checks = [
        ("credentials.json", Path("credentials.json").exists()),
        ("Directorio src", Path("src").exists()),
        ("Archivo config.py", Path("src/config.py").exists()),
        ("Directorio data", Path("data").exists())
    ]
ECHO is off.
    all_ok = True
    for name, status in checks:
        if status:
            st.success(f"✅ {name}")
        else:
            st.error(f"❌ {name}")
            all_ok = False
ECHO is off.
    if all_ok:
        st.balloons()
        st.success("🎉 ¡Todo configurado! Listo para usar.")
    else:
        st.info("""
        📋 **Próximos pasos:**
        1. Ejecuta install_complete.bat
        2. Descarga credentials.json de Google Cloud Console
        3. Reinicia la aplicación
        """^)

if __name__ == "__main__":
    main()
