# clean_start.py - Inicio limpio sin warnings
import warnings
import pandas as pd
import subprocess
import sys

def setup_clean_environment():
    """Configura entorno sin warnings"""
    
    # Suprimir warnings
    warnings.filterwarnings('ignore', category=FutureWarning)
    warnings.filterwarnings('ignore', message='.*Downcasting.*')
    
    # Configurar pandas
    pd.set_option('future.no_silent_downcasting', False)
    pd.set_option('mode.chained_assignment', None)
    
    print("🔇 Warnings suprimidos")
    print("⚙️ Pandas configurado")

def run_streamlit_clean():
    """Ejecuta streamlit con configuración limpia"""
    
    setup_clean_environment()
    
    print("🚀 Iniciando aplicación...")
    
    # Ejecutar streamlit
    try:
        subprocess.run([sys.executable, '-m', 'streamlit', 'run', 'app.py'])
    except KeyboardInterrupt:
        print("\n👋 Aplicación cerrada")

if __name__ == "__main__":
    run_streamlit_clean()
