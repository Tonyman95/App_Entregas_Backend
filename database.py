import os
import sys
from urllib.parse import quote_plus
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import pyodbc

# Helper para imprimir en stderr, más visible en logs de Azure
def print_err(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

load_dotenv()
print_err("--- 📝 Cargando configuración de base de datos ---")

DB_SERVER = os.getenv("DB_SERVER")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", "1433")
DB_ENCRYPT = os.getenv("DB_ENCRYPT", "yes")
DB_TRUST = os.getenv("DB_TRUST_SERVER_CERTIFICATE", "yes")

# Log de configuración (sin password)
print_err(f"  - Servidor: {DB_SERVER}:{DB_PORT}")
print_err(f"  - Base de datos: {DB_DATABASE}")
print_err(f"  - Usuario: {DB_USERNAME}")
print_err(f"  - Password: {'Sí' if DB_PASSWORD else 'No'}")
print_err(f"  - Encrypt: {DB_ENCRYPT}, TrustServerCertificate: {DB_TRUST}")

if not all([DB_SERVER, DB_DATABASE, DB_USERNAME, DB_PASSWORD]):
    error_msg = "❌ Faltan variables de entorno críticas para la DB. Revisa la configuración de la App Service."
    print_err(error_msg)
    raise RuntimeError(error_msg)

print_err("\n--- 🔍 Buscando driver ODBC ---")
PREFERRED = ["ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server"]
try:
    installed = sorted(list(set(pyodbc.drivers())))
    print_err("  - Drivers instalados en el sistema:", installed)
except Exception as e:
    print_err(f"  - ❌ Error al listar drivers ODBC: {e}")
    installed = []

driver = next((d for d in PREFERRED if d in installed), None)

if not driver:
    error_msg = f"❌ No se encontró un driver ODBC compatible. Se buscaron {PREFERRED}."
    print_err(error_msg)
    raise RuntimeError(error_msg)

print_err(f"  - ✅ Driver seleccionado: {driver}")


print_err("\n--- 🛠️  Construyendo cadena de conexión ---")
try:
    odbc_raw = (
        f"DRIVER={{{driver}}};"
        f"SERVER={DB_SERVER},{DB_PORT};"
        f"DATABASE={DB_DATABASE};"
        f"UID={DB_USERNAME};PWD={DB_PASSWORD};"
        f"Encrypt={DB_ENCRYPT};TrustServerCertificate={DB_TRUST};"
    )
    
    # Log de la cadena sin password
    odbc_safe = (
        f"DRIVER={{{driver}}};"
        f"SERVER={DB_SERVER},{DB_PORT};"
        f"DATABASE={DB_DATABASE};"
        f"UID={DB_USERNAME};PWD=***;"
        f"Encrypt={DB_ENCRYPT};TrustServerCertificate={DB_TRUST};"
    )
    print_err("  - Cadena de conexión (sin password):", odbc_safe)

    conn_str = f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc_raw)}"
    
    print_err("\n--- 🚀 Creando motor de SQLAlchemy ---")
    engine = create_engine(conn_str, pool_pre_ping=True)
    SessionLocal = scoped_session(sessionmaker(bind=engine, autocommit=False, autoflush=False))
    print_err("  - ✅ Motor de SQLAlchemy creado exitosamente.")

except Exception as e:
    print_err(f"  - ❌ Error fatal al crear la conexión a la base de datos: {e}")
    raise

print_err("\n--- 🎉 Conexión a base de datos configurada ---")
