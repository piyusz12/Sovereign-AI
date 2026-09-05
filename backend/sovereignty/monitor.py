import psutil
import logging
from backend.sovereignty.schemas import ConnectionEvent
from backend.sovereignty.classifier import classify_destination
from backend.sovereignty.policy import evaluate_network_policy

logger = logging.getLogger("sovereign.sovereignty.monitor")

class SystemMonitor:
    def __init__(self):
        # Cache for process names to avoid repeated lookups for the same PID
        self._process_cache = {}

    def get_process_name(self, pid: int) -> str:
        if pid in self._process_cache:
            try:
                # Check if process is still alive
                p = psutil.Process(pid)
                if p.name() == self._process_cache[pid]:
                    return self._process_cache[pid]
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        try:
            p = psutil.Process(pid)
            name = p.name()
            self._process_cache[pid] = name
            return name
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return "unknown"

    def get_active_connections(self) -> list[ConnectionEvent]:
        events = []
        try:
            # We use 'inet' to get IPv4 and IPv6
            connections = psutil.net_connections(kind="inet")
            for conn in connections:
                # We need a remote address to classify external/internal
                if not conn.raddr:
                    # It's likely a LISTEN socket, which is LOCAL conceptually
                    remote_ip = ""
                    remote_port = ""
                else:
                    remote_ip = conn.raddr.ip
                    remote_port = conn.raddr.port
                
                local_ip = conn.laddr.ip if conn.laddr else ""
                local_port = conn.laddr.port if conn.laddr else ""

                if remote_ip:
                    classification = classify_destination(remote_ip)
                else:
                    classification = classify_destination(local_ip)

                policy_decision = evaluate_network_policy(remote_ip or local_ip, classification)

                pid = conn.pid
                if pid:
                    process_name = self.get_process_name(pid)
                else:
                    process_name = "system"

                event = ConnectionEvent(
                    pid=pid or 0,
                    process_name=process_name,
                    local_address=f"{local_ip}:{local_port}" if local_ip else "",
                    remote_address=f"{remote_ip}:{remote_port}" if remote_ip else None,
                    status=conn.status,
                    classification=classification,
                    action=policy_decision.decision,
                    bytes_sent=0, # psutil doesn't give per-connection bytes easily
                    bytes_recv=0
                )
                events.append(event)
                
        except Exception as e:
            logger.error(f"Error fetching network connections: {e}")

        return events

system_monitor = SystemMonitor()
