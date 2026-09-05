import ipaddress
import logging

logger = logging.getLogger("sovereign.sovereignty.classifier")

def classify_destination(ip: str) -> str:
    """
    Classify an IP address as LOCAL, PRIVATE, or EXTERNAL.
    Handles IPv4 and IPv6.
    """
    if not ip or ip == "::":
        return "LOCAL"  # Treat unmapped/all-interfaces as local listen

    try:
        # Strip IPv6 zone index if present (e.g. fe80::1%11)
        if "%" in ip:
            ip = ip.split("%")[0]

        ip_obj = ipaddress.ip_address(ip)

        if ip_obj.is_loopback:
            return "LOCAL"
        
        if ip_obj.is_private or ip_obj.is_link_local or ip_obj.is_reserved:
            return "PRIVATE"
            
        if ip_obj.is_multicast:
            return "PRIVATE" # Treat multicast as private/local network

        return "EXTERNAL"
    except ValueError:
        # If it's not a valid IP (e.g., a domain name, though netstat usually gives IPs)
        # fallback to basic string checking or just flag as EXTERNAL if unparseable to be safe
        if ip.startswith("127.") or ip == "localhost":
            return "LOCAL"
        logger.warning(f"Could not parse IP address for classification: {ip}")
        return "UNKNOWN"
