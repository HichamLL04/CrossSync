#!/usr/bin/env python3
import sys
import os
import subprocess
import shutil

def main():
    print("=== SubSync Build Tool ===")
    
    # 1. Detect operating system
    is_windows = sys.platform.startswith("win")
    os_name = "Windows" if is_windows else "Linux/macOS"
    print(f"Sistema Operativo detectado: {os_name}")
    
    # 2. Check requirements
    print("\n[1/3] Verificando dependencias de empaquetado...")
    try:
        import PyInstaller
        print("- PyInstaller: OK")
    except ImportError:
        print("- PyInstaller no está instalado en este entorno. Instalando...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    try:
        import PyQt6
        print("- PyQt6: OK")
    except ImportError:
        print("- PyQt6 no está instalado en este entorno. Instalando...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyQt6"])

    # 3. Build Command
    print("\n[2/3] Ejecutando PyInstaller...")
    separator = ";" if is_windows else ":"
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "-y",
        "--name", "SubSync",
        "--onedir",
        "--add-data", f"src/translations{separator}src/translations",
        "sync.py"
    ]
    
    print(f"Comando: {' '.join(cmd)}")
    try:
        subprocess.check_call(cmd)
        print("\n[3/3] ¡Compilación completada exitosamente!")
        
        dist_dir = os.path.abspath("dist/SubSync")
        exe_path = os.path.join(dist_dir, "SubSync.exe" if is_windows else "SubSync")
        
        print("\n" + "="*50)
        print("¡El ejecutable está listo!")
        print(f"Ruta: {exe_path}")
        print("="*50)
        print("\nNota: Se ha utilizado la opción '--onedir' (directorio).")
        print("Para mover la aplicación, copia o comprime la carpeta entera 'dist/SubSync'.")
        print("El ejecutable no funcionará de manera aislada fuera de su carpeta.")
        
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Falló la compilación de PyInstaller: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
