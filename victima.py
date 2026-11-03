#!/usr/bin/env python3
"""
Victima - simple receptor UDP para la PoC.

No es obligatorio: puedes observar el ataque directamente en Wireshark.
Este script solo abre un puerto UDP y cuenta los paquetes que recibe,
para ver el efecto del flood sin herramientas extra.

Uso solo en un laboratorio aislado y controlado.
"""
import socket
import time

PUERTO = 9999  # el mismo que le pases al C&C


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("", PUERTO))
    print(f"[VICTIMA] Escuchando en el puerto {PUERTO}...")

    recibidos = 0
    t0 = time.time()
    while True:
        s.recvfrom(2048)
        recibidos += 1
        # Cada segundo mostramos cuantos paquetes por segundo llegan
        if time.time() - t0 >= 1:
            print(f"[VICTIMA] {recibidos} paquetes/s")
            recibidos = 0
            t0 = time.time()


if __name__ == "__main__":
    main()
