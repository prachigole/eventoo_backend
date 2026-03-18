"""
mDNS service advertisement via Zeroconf.

When the backend starts it registers an _eventoo._tcp.local. service on the
LAN.  Any Flutter app running multicast_dns on the same WiFi network will
discover it and automatically use the correct IP — no hardcoded addresses.

Service name : Eventoo API._eventoo._tcp.local.
Port         : 8000  (must match the uvicorn port)
"""

import asyncio
import logging
import socket

from zeroconf import ServiceInfo
from zeroconf.asyncio import AsyncZeroconf

logger = logging.getLogger("eventoo.mdns")

_SERVICE_TYPE = "_eventoo._tcp.local."
_SERVICE_NAME = f"Eventoo API.{_SERVICE_TYPE}"
_PORT = 8000


def _lan_ip() -> str:
    """Return the machine's LAN IP by probing an external UDP destination.

    No packet is actually sent — the OS just picks the correct outbound
    interface, which gives us the LAN IP reliably even when /etc/hosts maps
    hostname → 127.0.0.1.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


async def advertise() -> AsyncZeroconf:
    """Register the service and return the Zeroconf instance so the caller
    can unregister it on shutdown."""
    ip = _lan_ip()
    info = ServiceInfo(
        _SERVICE_TYPE,
        _SERVICE_NAME,
        addresses=[socket.inet_aton(ip)],
        port=_PORT,
        properties={"version": "1"},
        server="eventoo.local.",
    )

    zc = AsyncZeroconf()
    await zc.async_register_service(info)
    logger.info(f"mDNS: advertising Eventoo API at {ip}:{_PORT} as '{_SERVICE_NAME}'")
    return zc


async def stop(zc: AsyncZeroconf) -> None:
    await zc.async_unregister_all_services()
    await zc.async_close()
    logger.info("mDNS: service unregistered")
