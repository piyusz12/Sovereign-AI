import asyncio
import logging
import json
from typing import Set, Dict, Any, AsyncGenerator
from backend.sovereignty.monitor import system_monitor
from backend.sovereignty.schemas import SovereigntyStatus, ConnectionEvent
from backend.audit.service import audit_service
from backend.audit.context import current_trace_id
import uuid

logger = logging.getLogger("sovereign.sovereignty.service")

class SovereigntyService:
    def __init__(self):
        self.is_running = False
        self._task = None
        self.status = SovereigntyStatus()
        self.clients: Set[asyncio.Queue] = set()
        
        # Track seen connections to avoid spamming audit log
        # key: (pid, remote_address)
        self.seen_blocked_connections: Set[tuple[int, str]] = set()
        self.blocked_attempts_count = 0

    async def start(self):
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("Sovereignty Service started.")

    async def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Sovereignty Service stopped.")

    def subscribe(self) -> asyncio.Queue:
        q = asyncio.Queue()
        self.clients.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        if q in self.clients:
            self.clients.remove(q)

    async def _broadcast(self, data: Dict[str, Any]):
        message = f"data: {json.dumps(data)}\n\n"
        # Create a list of clients to avoid set changed size during iteration
        for q in list(self.clients):
            try:
                await q.put(message)
            except Exception:
                self.unsubscribe(q)

    def _log_blocked_event(self, conn: ConnectionEvent):
        # We need a context for audit. We can generate a dummy trace id or use background
        trace_id = current_trace_id.get() or f"SOV-{uuid.uuid4().hex[:8].upper()}"
        audit_service.log(
            action="network.egress.blocked",
            status="BLOCKED",
            trace_id=trace_id,
            resource_type="network_connection",
            resource_id=f"{conn.process_name}:{conn.pid}",
            decision="blocked",
            source_ip=conn.local_address,
            destination=conn.remote_address,
            metadata={
                "process_name": conn.process_name,
                "pid": conn.pid,
                "reason": "external network prohibited"
            }
        )

    async def _monitor_loop(self):
        while self.is_running:
            try:
                connections = system_monitor.get_active_connections()
                
                # Update status
                self.status.active_connections = connections
                
                external_count = 0
                new_blocked = []

                for conn in connections:
                    # Ignore internal python connections to itself that might spam (like localhost:xxxx)
                    if conn.classification == "EXTERNAL":
                        external_count += 1
                    
                    if conn.action == "BLOCK":
                        # To avoid spamming, only log if it's a new attempt (by pid+address)
                        conn_key = (conn.pid, conn.remote_address or "")
                        if conn_key not in self.seen_blocked_connections:
                            self.seen_blocked_connections.add(conn_key)
                            self.blocked_attempts_count += 1
                            new_blocked.append(conn)
                            self._log_blocked_event(conn)
                
                self.status.external_connections = external_count
                self.status.blocked_attempts = self.blocked_attempts_count
                self.status.is_sovereign = external_count == 0

                # Broadcast status update
                await self._broadcast({
                    "type": "status_update",
                    "status": self.status.model_dump(mode='json')
                })

                if new_blocked:
                    for conn in new_blocked:
                        await self._broadcast({
                            "type": "event_blocked",
                            "event": conn.model_dump(mode='json')
                        })

                await asyncio.sleep(2.0)  # Check every 2 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                await asyncio.sleep(5.0)

sovereignty_service = SovereigntyService()
