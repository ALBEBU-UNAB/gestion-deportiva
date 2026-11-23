"""Genera participantes sintéticos para Gestión Deportiva, sin tocar MySQL.

Instalación: pip install Faker
Ejecución: python poblar_datos.py
Salida: participantes_faker.csv
"""
import csv
from pathlib import Path
from faker import Faker

CANTIDAD = 100
SALIDA = Path(__file__).with_name("participantes_faker.csv")

def generar_participantes(cantidad=CANTIDAD):
    fake = Faker("es_CL")
    Faker.seed(2026)
    participantes = []
    for numero in range(1, cantidad + 1):
        participantes.append({
            "nombre": fake.name(),
            "correo": f"participante{numero:04d}@example.com",
            "telefono": fake.phone_number(),
        })
    return participantes

def main():
    participantes = generar_participantes()
    with SALIDA.open("w", newline="", encoding="utf-8-sig") as archivo:
        escritor = csv.DictWriter(
            archivo, fieldnames=["nombre", "correo", "telefono"]
        )
        escritor.writeheader()
        escritor.writerows(participantes)
    print(f"Se generaron {len(participantes)} participantes ficticios.")
    print(f"Archivo creado: {SALIDA}")
    print("No se modificó ninguna base de datos.")

if __name__ == "__main__":
    main()
