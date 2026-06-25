"""
database.py — SQLite persistence layer for votes and events.
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional

from config import DB_PATH
from logger import get_logger

log = get_logger("smart_evm.database")


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they don't exist."""
    conn = _connect()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS votes (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp     TEXT    NOT NULL,
                candidate_id  INTEGER NOT NULL,
                candidate_name TEXT   NOT NULL,
                event_type    TEXT    NOT NULL
            )
            """
        )
        conn.commit()
        log.info("Database initialised at %s", DB_PATH)
    finally:
        conn.close()


def record_vote(candidate_id: int, candidate_name: str, event_type: str = "vote") -> None:
    """Insert a single vote / error record."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO votes (timestamp, candidate_id, candidate_name, event_type) VALUES (?,?,?,?)",
            (ts, candidate_id, candidate_name, event_type),
        )
        conn.commit()
    finally:
        conn.close()


def get_vote_totals() -> dict[int, int]:
    """Return {candidate_id: total_votes} for accepted votes only."""
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT candidate_id, COUNT(*) as cnt FROM votes WHERE event_type='vote' GROUP BY candidate_id"
        ).fetchall()
        return {r["candidate_id"]: r["cnt"] for r in rows}
    finally:
        conn.close()


def get_all_events(limit: Optional[int] = None) -> list[sqlite3.Row]:
    """Return all event rows, newest first."""
    conn = _connect()
    try:
        q = "SELECT * FROM votes ORDER BY id DESC"
        if limit:
            q += f" LIMIT {limit}"
        return conn.execute(q).fetchall()
    finally:
        conn.close()


def get_total_votes() -> int:
    conn = _connect()
    try:
        row = conn.execute("SELECT COUNT(*) FROM votes WHERE event_type='vote'").fetchone()
        return row[0]
    finally:
        conn.close()


def clear_all() -> None:
    """Delete every record — used when starting a fresh session."""
    conn = _connect()
    try:
        conn.execute("DELETE FROM votes")
        conn.commit()
        log.info("All vote records cleared.")
    finally:
        conn.close()
