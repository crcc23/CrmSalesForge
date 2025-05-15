"""
Script para actualizar el esquema de la base de datos.
Usa este script para aplicar cambios al esquema después de modificar modelos.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db

def migrate_database():
    """Actualiza las tablas en la base de datos usando los modelos definidos"""
    with app.app_context():
        # Crear todas las tablas
        db.create_all()
        print("Se han actualizado las tablas de la base de datos.")

if __name__ == "__main__":
    migrate_database()