# cripto.py — cifrado simetrico de las ordenes (Fernet)
import json
from cryptography.fernet import Fernet

CLAVE = b"hnlGlKsO9vNaxS3FuHzQ8WGjYuHGk6RBlR0PjFtRzug="
fernet = Fernet(CLAVE)

def cifrar(datos):
    texto = json.dumps(datos).encode()
    return fernet.encrypt(texto)

def descifrar(cifrado):
    texto = fernet.decrypt(cifrado)
    return json.loads(texto.decode())