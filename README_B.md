# Parte B — Generador de carga de un solo nodo

`loadtest.py` es el equivalente de laboratorio a herramientas estándar como
`hping3`, `iperf3` o `locust`: un único script que tú ejecutas a mano, desde
una única máquina, contra un host que controlas, para generar tráfico
medible y ver cómo reacciona (y luego, en la Parte C, cómo se mitiga).

## Qué incluye

- **4 tipos de tráfico**, seleccionables con `--tipo`:
  - `udp` — datagramas UDP de tamaño configurable (`--tam`)
  - `tcp` — apertura/cierre repetido de conexiones TCP reales (sockets
    normales, sin construir paquetes a mano)
  - `http` — peticiones GET repetidas a una ruta (`--ruta`)
  - `icmp` — ping repetido usando el comando `ping` del sistema
- **Hilos configurables** (`--hilos`) para simular más carga desde el mismo
  proceso.
- **Duración configurable** (`--duracion`).
- Contador en vivo de paquetes/peticiones enviadas, errores y tasa media al
  terminar — para comparar entre pruebas (1 hilo vs 4 hilos, UDP vs HTTP, etc.)
  igual que harías con las capturas de Wireshark de la Parte C.

## Qué NO incluye, a propósito

Esto es deliberado, no una limitación técnica que se pueda "arreglar" luego:

- **No escucha órdenes de nadie.** No hay bot, no hay C&C, no hay registro
  de "zombies". Lo ejecutas tú, a mano, cuando quieres medir algo.
- **No se auto-arranca ni persiste.** No se instala como servicio, no se
  pone en el arranque. Es un script que corre mientras lo tienes abierto.
- **Solo acepta IPs privadas** (`192.168.x.x`, `10.x.x.x`, `172.16-31.x.x`,
  `127.0.0.1`): si le das una IP pública, se niega a ejecutarse. Esto obliga
  a que el uso quede dentro de tu red de laboratorio.
- **Pide confirmación explícita** antes de lanzar nada (`escribe 'confirmo'`),
  salvo que pases `--si` a propósito.
- No falsea direcciones de origen ni construye paquetes "a mano" a nivel de
  bytes (no hay spoofing ni fragmentación manual): usa la pila de red normal
  del sistema operativo.

## Uso

```bash
# UDP flood con 4 hilos durante 10s contra tu VM víctima
sudo python3 loadtest.py 192.168.1.50 9999 --tipo udp --duracion 10 --hilos 4

# Peticiones HTTP repetidas contra un servidor web de prueba en el puerto 8080
python3 loadtest.py 192.168.1.50 8080 --tipo http --duracion 10 --hilos 8

# Conexiones TCP repetidas
sudo python3 loadtest.py 192.168.1.50 9999 --tipo tcp --duracion 10 --hilos 4

# Ping repetido (ICMP), no necesita puerto
sudo python3 loadtest.py 192.168.1.50 --tipo icmp --duracion 10
```

## Cómo encaja con la Parte C (defensa)

La idea es la misma que planteaba el enunciado original: lanzas tráfico con
esto desde 1, luego 2, luego 3 máquinas/terminales en paralelo (cada una
ejecutando su propio `loadtest.py` de forma independiente — no hay
coordinación automática entre ellas, cada persona lo lanza a mano), y en la
víctima tu compañero de la Parte C:

- captura con `tshark`/Wireshark y compara los *IO Graphs* de paquetes/s,
- activa su IDS casero o Suricata para que salte la alerta,
- aplica sus reglas de `iptables`/rate-limiting y vuelve a medir con esta
  misma herramienta para demostrar que el tráfico efectivo baja.

Esa comparación "antes/después de la mitigación" es la métrica real del
trabajo, y no necesita que `loadtest.py` tenga mando remoto para funcionar.