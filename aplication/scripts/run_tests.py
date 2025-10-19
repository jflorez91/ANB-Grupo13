#!/usr/bin/env python3
"""Script para ejecutar tests"""
import subprocess
import sys

def run_tests():
    """Ejecutar todos los tests"""
    print("🚀 Ejecutando tests...")
    
    # Comando para ejecutar tests
    cmd = [
        "python", "-m", "pytest",
        "app/test/",
        "-v",
        "--cov=app",
        "--cov-report=html",
        "--cov-report=term"
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"❌ Tests fallaron con código: {e.returncode}")
        return e.returncode

if __name__ == "__main__":
    sys.exit(run_tests())