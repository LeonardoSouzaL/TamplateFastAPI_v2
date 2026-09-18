"""Detecção do IP local da máquina para identificar a instância.

Usado pelo `config` para anexar o último octeto do IP ao nome do serviço
(ex.: ``MetricsAPI-213``) e para preencher ``host.name``/tag ``host``.
Nenhuma função aqui pode quebrar o startup; todas têm fallback seguro.
"""

import socket
from typing import Optional


def get_local_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return "127.0.0.1"
    finally:
        sock.close()


def get_ip_suffix(ip: Optional[str] = None) -> str:
    ip = ip or get_local_ip()
    parts = ip.split(".")
    if len(parts) == 4 and parts[-1].isdigit():
        return parts[-1]
    digits = "".join(char for char in ip if char.isdigit())
    return digits[-3:] if digits else "000"
