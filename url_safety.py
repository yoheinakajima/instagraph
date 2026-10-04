import ipaddress

NAT64_WELL_KNOWN_PREFIX = ipaddress.IPv6Network("64:ff9b::/96")
IPV4_BITS = 32
IPV4_MASK = (1 << IPV4_BITS) - 1


def _embedded_ipv4(ip: ipaddress.IPv6Address) -> ipaddress.IPv4Address | None:
    if ip.ipv4_mapped is not None:
        return ip.ipv4_mapped
    if ip in NAT64_WELL_KNOWN_PREFIX:
        return ipaddress.IPv4Address(int(ip) & IPV4_MASK)
    if ip.sixtofour is not None:
        return ip.sixtofour
    if ip.teredo is not None:
        return ip.teredo[1]
    return None


def is_public_address(address: str) -> bool:
    """True only for a globally routable unicast address; anything unparsable is rejected."""
    try:
        ip = ipaddress.ip_address(address.split("%", 1)[0])
    except ValueError:
        return False
    if isinstance(ip, ipaddress.IPv6Address):
        embedded = _embedded_ipv4(ip)
        if embedded is not None:
            return is_public_address(str(embedded))
    return ip.is_global and not ip.is_multicast
