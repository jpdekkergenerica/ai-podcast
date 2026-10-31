"""Veilig adressen ophalen die gebruikers opgeven (eigen bronnen): geen interne netwerken, beperkte omvang en tijd."""
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

import httpx

MAX_BYTES = 2_000_000
TIMEOUT = 10.0
MAX_REDIRECTS = 4


class UnsafeUrl(ValueError):
    """Het adres is geen openbaar http(s)-adres."""


def check_public_url(url: str) -> str:
    """Geeft het adres terug als het naar een openbare host wijst; anders UnsafeUrl."""
    parts = urlparse(url.strip())
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise UnsafeUrl("Gebruik een website- of RSS-adres dat met http:// of https:// begint")
    if parts.username or parts.password:
        raise UnsafeUrl("Adressen met inloggegevens zijn niet toegestaan")
    try:
        infos = socket.getaddrinfo(parts.hostname, parts.port or (443 if parts.scheme == "https" else 80), type=socket.SOCK_STREAM)
    except socket.gaierror as e:
        raise UnsafeUrl("Dit adres bestaat niet of is niet bereikbaar") from e
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global:
            raise UnsafeUrl("Dit adres wijst naar een intern netwerk en is niet toegestaan")
    return url.strip()


def fetch_public(url: str, client: httpx.Client | None = None) -> tuple[str, str, str]:
    """Haalt een pagina of feed op, met controle van elk doorverwezen adres. Geeft (eind-url, content-type, tekst)."""
    own = client is None
    client = client or httpx.Client(timeout=TIMEOUT, follow_redirects=False, headers={"User-Agent": "yourownpod/1.0"})
    try:
        current = url
        for _ in range(MAX_REDIRECTS + 1):
            check_public_url(current)
            with client.stream("GET", current) as res:
                if res.is_redirect and res.headers.get("location"):
                    current = str(httpx.URL(current).join(res.headers["location"]))
                    continue
                if res.status_code >= 400:
                    raise UnsafeUrl(f"De website antwoordde met fout {res.status_code}")
                body = b""
                for chunk in res.iter_bytes():
                    body += chunk
                    if len(body) > MAX_BYTES:
                        break
                return current, res.headers.get("content-type", ""), body[:MAX_BYTES].decode(res.encoding or "utf-8", errors="replace")
        raise UnsafeUrl("Te veel doorverwijzingen")
    except httpx.HTTPError as e:
        raise UnsafeUrl("De website is niet bereikbaar of reageert te traag") from e
    finally:
        if own:
            client.close()
