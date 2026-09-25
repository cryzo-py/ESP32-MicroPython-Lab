"""
Module 'urequests' et 'requests' émulé pour l'environnement MicroPython virtuel de l'ESP32.
Permet d'exécuter des requêtes HTTP/HTTPS réelles vers des serveurs Web, Cloud IoT, API REST.
"""

import json as _json
import urllib.error
import urllib.parse
import urllib.request


class Response:
    """Objet réponse HTTP conforme à l'API urequests de MicroPython."""

    def __init__(self, status_code: int, reason: str, content: bytes, headers: dict):
        self.status_code = status_code
        self.reason = reason
        self._content = content
        self.headers = headers

    @property
    def content(self) -> bytes:
        """Données brutes de la réponse en octets."""
        return self._content

    @property
    def text(self) -> str:
        """Contenu de la réponse décodé sous forme de chaîne de caractères."""
        return self._content.decode("utf-8", errors="replace")

    def json(self):
        """Parse le corps de la réponse au format JSON."""
        return _json.loads(self.text)

    def close(self):
        """Ferme la réponse."""
        pass


def request(method: str, url: str, data=None, json=None, headers: dict | None = None, timeout: float = 10.0) -> Response:
    """Exécute une requête HTTP/HTTPS via la connexion réseau hôte."""
    if headers is None:
        headers = {}

    req_headers = {
        "User-Agent": "ESP32-MicroPython-Lab/2.0",
        **headers
    }

    body = None
    if json is not None:
        req_headers["Content-Type"] = "application/json"
        body = _json.dumps(json).encode("utf-8")
    elif data is not None:
        if isinstance(data, str):
            body = data.encode("utf-8")
        elif isinstance(data, bytes):
            body = data
        elif isinstance(data, dict):
            req_headers["Content-Type"] = "application/x-www-form-urlencoded"
            body = urllib.parse.urlencode(data).encode("utf-8")

    req = urllib.request.Request(url, data=body, headers=req_headers, method=method.upper())

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read()
            resp_headers = dict(resp.headers)
            return Response(resp.status, resp.reason, content, resp_headers)
    except urllib.error.HTTPError as e:
        err_content = e.read() if hasattr(e, "read") else b""
        return Response(e.code, e.reason, err_content, dict(e.headers) if hasattr(e, "headers") else {})
    except Exception as e:
        raise OSError(f"Erreur de communication réseau : {e}")


def get(url: str, **kwargs) -> Response:
    return request("GET", url, **kwargs)


def post(url: str, **kwargs) -> Response:
    return request("POST", url, **kwargs)


def put(url: str, **kwargs) -> Response:
    return request("PUT", url, **kwargs)


def patch(url: str, **kwargs) -> Response:
    return request("PATCH", url, **kwargs)


def delete(url: str, **kwargs) -> Response:
    return request("DELETE", url, **kwargs)


def head(url: str, **kwargs) -> Response:
    return request("HEAD", url, **kwargs)
