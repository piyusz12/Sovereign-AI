import json
import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from backend.audit.context import (
    current_role,
    current_session_id,
    current_trace_id,
    current_user_id,
)
from backend.audit.schemas import AuditEvent
from backend.settings import settings

logger = logging.getLogger("sovereign.audit.service")


class AuditService:
    def __init__(self, db_path: str = settings.audit_db_path, log_path: str = settings.audit_log_path):
        self.db_path = Path(db_path)
        self.log_path = Path(log_path)
        
        # Ensure directories exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database with audit_events table."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    trace_id TEXT,
                    timestamp TEXT,
                    user_id TEXT,
                    session_id TEXT,
                    action TEXT NOT NULL,
                    resource_type TEXT,
                    resource_id TEXT,
                    project_id TEXT,
                    role TEXT,
                    permission TEXT,
                    decision TEXT,
                    model TEXT,
                    tool TEXT,
                    sandbox_job_id TEXT,
                    source_ip TEXT,
                    destination TEXT,
                    status TEXT NOT NULL,
                    error_code TEXT,
                    metadata_json TEXT
                )
            """)
            
            # Indexes for faster queries
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_trace ON audit_events(trace_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_events(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_events(action)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events(timestamp)")
            
            conn.commit()

    def log(
        self,
        action: str,
        status: str,
        user_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        session_id: Optional[str] = None,
        role: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        project_id: Optional[str] = None,
        permission: Optional[str] = None,
        decision: Optional[str] = None,
        model: Optional[str] = None,
        tool: Optional[str] = None,
        sandbox_job_id: Optional[str] = None,
        source_ip: Optional[str] = None,
        destination: Optional[str] = None,
        error_code: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> AuditEvent:
        """
        Record a new audit event. Context vars are automatically injected if not provided explicitly.
        """
        # Resolve from context if not provided
        resolved_user_id = user_id or current_user_id.get()
        resolved_trace_id = trace_id or current_trace_id.get()
        resolved_session_id = session_id or current_session_id.get()
        resolved_role = role or current_role.get()
        
        event = AuditEvent(
            event_id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
            trace_id=resolved_trace_id,
            timestamp=datetime.now(timezone.utc),
            user_id=resolved_user_id,
            session_id=resolved_session_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            project_id=project_id,
            role=resolved_role,
            permission=permission,
            decision=decision,
            model=model,
            tool=tool,
            sandbox_job_id=sandbox_job_id,
            source_ip=source_ip,
            destination=destination,
            status=status,
            error_code=error_code,
            metadata_info=metadata or {},
        )
        
        # Async writing would be better for high throughput, but for SQLite prototype synchronous is fine.
        self._write_to_db(event)
        self._write_to_file(event)
        
        logger.info(f"AUDIT [{event.action}]: {event.user_id} → {event.status} {f'({event.decision})' if event.decision else ''}")
        return event

    def _write_to_db(self, event: AuditEvent):
        """Insert event into SQLite."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO audit_events (
                        event_id, trace_id, timestamp, user_id, session_id, action,
                        resource_type, resource_id, project_id, role, permission,
                        decision, model, tool, sandbox_job_id, source_ip, destination,
                        status, error_code, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.event_id,
                    event.trace_id,
                    event.timestamp.isoformat(),
                    event.user_id,
                    event.session_id,
                    event.action,
                    event.resource_type,
                    event.resource_id,
                    event.project_id,
                    event.role,
                    event.permission,
                    event.decision,
                    event.model,
                    event.tool,
                    event.sandbox_job_id,
                    event.source_ip,
                    event.destination,
                    event.status,
                    event.error_code,
                    json.dumps(event.metadata_info)
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to write audit event to DB: {e}")

    def _write_to_file(self, event: AuditEvent):
        """Append event to JSONL file."""
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                # Need to handle datetime serialization
                event_dict = event.model_dump()
                event_dict["timestamp"] = event.timestamp.isoformat()
                f.write(json.dumps(event_dict) + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit event to file: {e}")

    def get_events(self, limit: int = 100, offset: int = 0, **filters) -> list[AuditEvent]:
        """Fetch audit events from SQLite, optionally filtered."""
        query = "SELECT * FROM audit_events"
        conditions = []
        params = []
        
        for k, v in filters.items():
            if v is not None:
                conditions.append(f"{k} = ?")
                params.append(v)
                
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                events = []
                for r in rows:
                    row_dict = dict(r)
                    if row_dict.get("metadata_json"):
                        row_dict["metadata_info"] = json.loads(row_dict["metadata_json"])
                        del row_dict["metadata_json"]
                    else:
                        row_dict["metadata_info"] = {}
                        if "metadata_json" in row_dict:
                            del row_dict["metadata_json"]
                    
                    # SQLite stores datetime as string, we need to parse it for Pydantic if needed, 
                    # but Pydantic handles ISO format strings gracefully in init.
                    events.append(AuditEvent(**row_dict))
                return events
        except Exception as e:
            logger.error(f"Failed to read audit events from DB: {e}")
            return []


# Global singleton instance
audit_service = AuditService()
