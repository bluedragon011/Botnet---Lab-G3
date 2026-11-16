#!/usr/bin/env python3
"""
loadtest.py - Herramienta de generacion de carga para pruebas de red (laboratorio).

Analoga a herramientas estandar de la industria como hping3 / iperf3 / locust:
UN solo operador, ejecutando UN proceso, contra UN host que tu controlas,
para medir como se comporta ese host/red bajo distintos tipos y volumenes
de trafico.

Lo que esta herramienta NO es ni hace, a proposito:
  - No tiene componente de mando remoto ("C&C"): no escucha ordenes de nadie,
    no se registra en ningun sitio, no coordina otras maquinas.
  - No se auto-instala, no se auto-arranca, no persiste tras reiniciar.
  - No se disfraza ni oculta su actividad: imprime claramente lo que hace.
  - Solo ataca el host que indiques explicitamente en la linea de comandos,
    y solo mientras el proceso esta corriendo en primer plano.

Uso pensado: tu mismo, en tu VM victima (o la de un companero, con permiso,
dentro del laboratorio), ejecutas este script a mano para generar trafico
medible y comparar con 1 instancia, 2 instancias en paralelo, etc., igual
que harias con `hping3 --flood` o `locust`.

Requiere permisos de root/administrador para los modos TCP-SYN e ICMP
(usan raw sockets). El modo UDP y HTTP no los necesitan.

Uso:
    sudo python3 loadtest.py <ip> <puerto> --tipo udp   --duracion 10 --hilos 4
    sudo python3 loadtest.py <ip> <puerto> --tipo synack --duracion 10
    python3  loadtest.py <ip> <puerto> --tipo http  --duracion 10 --hilos 8
    sudo python3 loadtest.py <ip>        --tipo icmp --duracion 10
"""
import argparse
import ipaddress
import os
import random
import socket
import struct
import sys
import threading
import time
import urllib.request

# ---------------------------------------------------------------------------
# Salvaguarda: solo se permite apuntar a direcciones privadas / de laboratorio
# (RFC1918, loopback, link-local). Esto obliga a que la herramienta se use
# dentro de tu propia red de pruebas y no contra internet.
# ---------------------------------------------------------------------------
def validar_objetivo_privado(ip_str):
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        print(f"[ERROR] '{ip_str}' no es una IP valida.")
        sys.exit(1)

    if not (ip.is_private or ip.is_loopback or ip.is_link_local):
        print(
            f"[BLOQUEADO] {ip_str} no es una direccion privada/de laboratorio "
            f"(RFC1918, loopback o link-local).\n"
            f"Esta herramienta esta limitada a redes de laboratorio propias. "
            f"Usa una IP tipo 192.168.x.x, 10.x.x.x, 172.16-31.x.x o 127.0.0.1."
        )
        sys.exit(1)
    return str(ip)


def confirmar(ip, puerto, tipo, duracion):
    print("=" * 70)
    print(" AVISO: esto va a generar trafico de red de forma deliberada.")
    print(f"  Objetivo : {ip}" + (f":{puerto}" if puerto else ""))
    print(f"  Tipo     : {tipo}")
    print(f"  Duracion : {duracion}s")
    print(" Usa esto SOLO contra equipos de tu laboratorio, con permiso.")
    print("=" * 70)
    resp = input("Escribe EXACTAMENTE 'confirmo' para continuar: ")
    if resp.strip() != "confirmo":
        print("Cancelado.")
        sys.exit(0)


# ---------------------------------------------------------------------------
# Contadores compartidos (para ver throughput real logrado, no solo el pedido)
# ---------------------------------------------------------------------------
contador_lock = threading.Lock()
paquetes_enviados = 0
errores = 0


def sumar(ok=True, n=1):
    global paquetes_enviados, errores
    with contador_lock:
        if ok:
            paquetes_enviados += n
        else:
            errores += n


# ---------------------------------------------------------------------------
# Modo UDP: envio de datagramas de tamano configurable
# ---------------------------------------------------------------------------
def worker_udp(ip, puerto, fin, tam_payload):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    payload = os.urandom(tam_payload)
    while time.time() < fin:
        try:
            s.sendto(payload, (ip, puerto))
            sumar(True)
        except OSError:
            sumar(False)
    s.close()


# ---------------------------------------------------------------------------
# Modo HTTP: peticiones GET repetidas (como un mini locust de un solo tipo)
# ---------------------------------------------------------------------------
def worker_http(ip, puerto, fin, ruta):
    url = f"http://{ip}:{puerto}{ruta}"
    while time.time() < fin:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                r.read(0)
            sumar(True)
        except Exception:
            sumar(False)


# ---------------------------------------------------------------------------
# Modo TCP "handshake" (SYN+ACK normal, sin raw sockets, sin spoofing):
# abre y cierra conexiones TCP reales a repeticion. Mide coste de
# gestionar muchas conexiones nuevas, pero usando sockets normales
# (no construye paquetes a mano ni falsea la IP de origen).
# ---------------------------------------------------------------------------
def worker_tcp_connect(ip, puerto, fin):
    while time.time() < fin:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect((ip, puerto))
            s.close()
            sumar(True)
        except OSError:
            sumar(False)


# ---------------------------------------------------------------------------
# Modo ICMP echo (ping) repetido usando el comando del sistema, que ya
# respeta los permisos y limites normales del SO (no raw socket a mano).
# ---------------------------------------------------------------------------
def worker_icmp(ip, fin):
    import subprocess
    plat_cmd = ["ping", "-c", "1", "-W", "1", ip] if sys.platform != "win32" \
        else ["ping", "-n", "1", "-w", "1000", ip]
    while time.time() < fin:
        try:
            subprocess.run(plat_cmd, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, timeout=2)
            sumar(True)
        except Exception:
            sumar(False)


# ---------------------------------------------------------------------------
# Lanzador
# ---------------------------------------------------------------------------
def lanzar(ip, puerto, tipo, duracion, hilos, tam_payload, ruta):
    fin = time.time() + duracion
    hilos_lista = []

    if tipo == "udp":
        fn = lambda: worker_udp(ip, puerto, fin, tam_payload)
    elif tipo == "http":
        fn = lambda: worker_http(ip, puerto, fin, ruta)
    elif tipo == "tcp":
        fn = lambda: worker_tcp_connect(ip, puerto, fin)
    elif tipo == "icmp":
        hilos = 1  # un solo hilo basta, ping ya es bloqueante por si mismo
        fn = lambda: worker_icmp(ip, fin)
    else:
        print(f"[ERROR] tipo desconocido: {tipo}")
        sys.exit(1)

    print(f"[LOADTEST] Lanzando {hilos} hilo(s), tipo={tipo}, {duracion}s...")
    t0 = time.time()
    for _ in range(hilos):
        t = threading.Thread(target=fn, daemon=True)
        t.start()
        hilos_lista.append(t)

    # Barra de progreso simple con contador en vivo
    try:
        while time.time() < fin:
            time.sleep(1)
            transcurrido = time.time() - t0
            with contador_lock:
                print(f"\r[LOADTEST] t={transcurrido:5.1f}s  "
                    f"enviados={paquetes_enviados}  errores={errores}",
                    end="", flush=True)
    except KeyboardInterrupt:
        print("\n[LOADTEST] Interrumpido por el usuario.")

    for t in hilos_lista:
        t.join(timeout=2)

    duracion_real = time.time() - t0
    print()
    print("-" * 70)
    print(f"[LOADTEST] Terminado en {duracion_real:.1f}s")
    print(f"  Total enviados : {paquetes_enviados}")
    print(f"  Total errores  : {errores}")
    if duracion_real > 0:
        print(f"  Tasa media     : {paquetes_enviados / duracion_real:.1f} /s")
    print("-" * 70)


def main():
    p = argparse.ArgumentParser(
        description="Generador de carga de un solo nodo para pruebas de laboratorio."
    )
    p.add_argument("ip", help="IP del objetivo (debe ser privada/de laboratorio)")
    p.add_argument("puerto", nargs="?", type=int, default=0,
                    help="Puerto del objetivo (no aplica a icmp)")
    p.add_argument("--tipo", choices=["udp", "tcp", "http", "icmp"],
                    default="udp", help="Tipo de trafico a generar")
    p.add_argument("--duracion", type=int, default=10,
                    help="Duracion en segundos")
    p.add_argument("--hilos", type=int, default=4,
                    help="Hilos en paralelo dentro de este mismo proceso")
    p.add_argument("--tam", type=int, default=1024,
                    help="Tamano del payload UDP en bytes")
    p.add_argument("--ruta", default="/",
                    help="Ruta HTTP a solicitar (modo http)")
    p.add_argument("--si", action="store_true",
                    help="Omite la confirmacion interactiva (usar con cuidado)")
    args = p.parse_args()

    if args.tipo != "icmp" and args.puerto == 0:
        print("[ERROR] este tipo de trafico necesita un puerto.")
        sys.exit(1)

    ip = validar_objetivo_privado(args.ip)

    if (args.tipo in ("tcp", "icmp")) and os.name != "nt" and os.geteuid() != 0:
        print(f"[AVISO] el modo '{args.tipo}' puede necesitar permisos de root "
            f"para abrir sockets rapido / usar ping sin restricciones. "
            f"Si falla mucho, prueba con sudo.")

    if not args.si:
        confirmar(ip, args.puerto, args.tipo, args.duracion)

    lanzar(ip, args.puerto, args.tipo, args.duracion, args.hilos,
        args.tam, args.ruta)


if __name__ == "__main__":
    main()
