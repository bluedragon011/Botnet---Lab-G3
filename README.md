# Botnet PoC (laboratorio)

Prueba de concepto muy sencilla de una botnet para la parte de seguridad
ofensiva. Son tres piezas:

- `cc.py` — **C&C (Command and Control)**: el equipo del atacante. Manda la
  orden de ataque por UDP broadcast (IP victima, puerto, duracion).
- `bot.py` — **bot / zombie**: escucha la orden del C&C y, al recibirla,
  lanza un flood UDP contra la victima.
- `victima.py` — **victima** (opcional): cuenta los paquetes que recibe por
  segundo. Puedes usar Wireshark en su lugar.

> Uso exclusivo en un laboratorio aislado y controlado (maquinas tuyas o VMs
> en una red privada). No lo uses contra equipos o redes de terceros.

## Como probarlo

1. En la maquina victima (o una VM):
   ```
   python3 victima.py
   ```

2. En cada equipo zombie (1, 2, 3... puedes abrir varias terminales/VMs):
   ```
   python3 bot.py
   ```

3. En el C&C, lanza la orden (IP de la victima, puerto 9999, 10 segundos):
   ```
   python3 cc.py 192.168.1.50 9999 10
   ```

Todos los bots reciben el broadcast y atacan a la vez.

## Demostracion con Wireshark

- Filtra por `udp.port == 9999` en la interfaz de la victima.
- En *Statistics > IO Graph* veras subir los paquetes/s.
- Repite con 1 zombie, luego 2, luego 3, y compara las graficas: el trafico
  crece de forma acumulada con cada zombie.

## Notas tecnicas

- El broadcast (`255.255.255.255`) solo llega a la red local, por eso todo
  esto va en la misma LAN/VLAN de laboratorio.
- Para probar varios bots en una misma maquina se usa `SO_REUSEADDR`.
- La orden es texto plano `IP;PUERTO;DURACION`. Mas adelante se puede
  complicar (cifrado, mas tipos de ataque, registro de zombies, etc.).
