# ataques.py  — funciones reutilizables (las de loadtest, sin cambios en su lógica)
import time
from loadtest import worker_udp, worker_tcp_connect, worker_http, worker_icmp
import threading

def lanzar_ataque(tipo, ip, puerto, duracion, hilos=4, tam=1024, ruta="/"):
    fin = time.time() + duracion
    if tipo == "udp":
        fn = lambda: worker_udp(ip, puerto, fin, tam)
    elif tipo == "tcp":
        fn = lambda: worker_tcp_connect(ip, puerto, fin)
    elif tipo == "http":
        fn = lambda: worker_http(ip, puerto, fin, ruta)
    elif tipo == "icmp":
        hilos = 1
        fn = lambda: worker_icmp(ip, fin)
    else:
        return
    hs = [threading.Thread(target=fn, daemon=True) for _ in range(hilos)]
    for t in hs: t.start()
    for t in hs: t.join()