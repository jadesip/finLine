"""
finLine Database Module

SQLite database with JSON column for project data.
Uses aiosqlite for async operations.
"""

import aiosqlite
import json
import logging
from pathlib import Path
from typing import Any
from datetime import datetime
from contextlib import asynccontextmanager

from config import get_settings

logger = logging.getLogger(__name__)

# Database file path
DB_PATH = get_settings().data_dir / "finline.db"


@asynccontextmanager
async def get_db():
    """Get database connection as async context manager."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()


async def init_db() -> None:
    """Initialize database schema."""
    logger.info(f"Initializing database at {DB_PATH}")

    async with get_db() as db:
        # Users table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                last_login TEXT,
                stripe_customer_id TEXT,
                stripe_subscription_id TEXT,
                subscription_status TEXT DEFAULT 'none'
            )
        """)

        # Projects table with JSON data column
        await db.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                data JSON NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Extractions table for document processing
        await db.execute("""
            CREATE TABLE IF NOT EXISTS extractions (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                status TEXT NOT NULL,
                source_files JSON,
                extracted_data JSON,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)

        # Indexes
        await db.execute("CREATE INDEX IF NOT EXISTS idx_projects_user ON projects(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_extractions_project ON extractions(project_id)")

        await db.commit()
        logger.info("Database initialized successfully")


# ============================================================
# User Operations
# ============================================================

async def create_user(user_id: str, email: str, password_hash: str) -> dict[str, Any]:
    """Create a new user."""
    now = datetime.utcnow().isoformat()

    async with get_db() as db:
        await db.execute(
            "INSERT INTO users (id, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (user_id, email, password_hash, now)
        )
        await db.commit()

    logger.info(f"Created user: {email}")
    return {"id": user_id, "email": email, "created_at": now}


async def get_user_by_email(email: str) -> dict[str, Any] | None:
    """Get user by email."""
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = await cursor.fetchone()
        if row:
            return dict(row)
    return None


async def get_user_by_id(user_id: str) -> dict[str, Any] | None:
    """Get user by ID."""
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        if row:
            return dict(row)
    return None


async def update_user_last_login(user_id: str) -> None:
    """Update user's last login timestamp."""
    now = datetime.utcnow().isoformat()
    async with get_db() as db:
        await db.execute("UPDATE users SET last_login = ? WHERE id = ?", (now, user_id))
        await db.commit()


async def get_user(user_id: str) -> dict[str, Any] | None:
    """Get user by ID (alias for get_user_by_id)."""
    return await get_user_by_id(user_id)


async def update_user_subscription(
    user_id: str,
    stripe_customer_id: str | None = None,
    stripe_subscription_id: str | None = None,
    subscription_status: str | None = None,
) -> None:
    """Update user's subscription information."""
    async with get_db() as db:
        updates = []
        params = []

        if stripe_customer_id is not None:
            updates.append("stripe_customer_id = ?")
            params.append(stripe_customer_id)

        if stripe_subscription_id is not None:
            updates.append("stripe_subscription_id = ?")
            params.append(stripe_subscription_id)

        if subscription_status is not None:
            updates.append("subscription_status = ?")
            params.append(subscription_status)

        if updates:
            params.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            await db.execute(query, params)
            await db.commit()
            logger.info(f"Updated subscription for user {user_id}: status={subscription_status}")


# ============================================================
# Project Operations
# ============================================================

async def create_project(project_id: str, user_id: str, name: str, data: dict[str, Any]) -> dict[str, Any]:
    """Create a new project."""
    now = datetime.utcnow().isoformat()

    async with get_db() as db:
        await db.execute(
            "INSERT INTO projects (id, user_id, name, created_at, updated_at, data) VALUES (?, ?, ?, ?, ?, ?)",
            (project_id, user_id, name, now, now, json.dumps(data))
        )
        await db.commit()

    logger.info(f"Created project: {name} (id: {project_id})")
    return {"id": project_id, "user_id": user_id, "name": name, "created_at": now, "updated_at": now, "data": data}


async def get_project(project_id: str) -> dict[str, Any] | None:
    """Get project by ID."""
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = await cursor.fetchone()
        if row:
            result = dict(row)
            result["data"] = json.loads(result["data"])
            return result
    return None


async def get_projects_by_user(user_id: str) -> list[dict[str, Any]]:
    """Get all projects for a user."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT id, user_id, name, created_at, updated_at FROM projects WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def update_project(project_id: str, data: dict[str, Any], name: str | None = None) -> dict[str, Any] | None:
    """Update project data."""
    now = datetime.utcnow().isoformat()

    async with get_db() as db:
        if name:
            await db.execute(
                "UPDATE projects SET data = ?, name = ?, updated_at = ? WHERE id = ?",
                (json.dumps(data), name, now, project_id)
            )
        else:
            await db.execute(
                "UPDATE projects SET data = ?, updated_at = ? WHERE id = ?",
                (json.dumps(data), now, project_id)
            )
        await db.commit()

    logger.info(f"Updated project: {project_id}")
    return await get_project(project_id)


async def delete_project(project_id: str) -> bool:
    """Delete a project."""
    async with get_db() as db:
        cursor = await db.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        await db.commit()
        deleted = cursor.rowcount > 0

    if deleted:
        logger.info(f"Deleted project: {project_id}")
    return deleted


# ============================================================
# Extraction Operations
# ============================================================

async def create_extraction(extraction_id: str, project_id: str, source_files: list[str]) -> dict[str, Any]:
    """Create a new extraction record."""
    now = datetime.utcnow().isoformat()

    async with get_db() as db:
        await db.execute(
            "INSERT INTO extractions (id, project_id, status, source_files, created_at) VALUES (?, ?, ?, ?, ?)",
            (extraction_id, project_id, "pending", json.dumps(source_files), now)
        )
        await db.commit()

    logger.info(f"Created extraction: {extraction_id} for project {project_id}")
    return {"id": extraction_id, "project_id": project_id, "status": "pending", "source_files": source_files, "created_at": now}


async def update_extraction(extraction_id: str, status: str, extracted_data: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Update extraction status and data."""
    now = datetime.utcnow().isoformat() if status in ("completed", "failed") else None

    async with get_db() as db:
        if extracted_data and now:
            await db.execute(
                "UPDATE extractions SET status = ?, extracted_data = ?, completed_at = ? WHERE id = ?",
                (status, json.dumps(extracted_data), now, extraction_id)
            )
        elif now:
            await db.execute(
                "UPDATE extractions SET status = ?, completed_at = ? WHERE id = ?",
                (status, now, extraction_id)
            )
        else:
            await db.execute(
                "UPDATE extractions SET status = ? WHERE id = ?",
                (status, extraction_id)
            )
        await db.commit()

    logger.info(f"Updated extraction {extraction_id}: status={status}")
    return await get_extraction(extraction_id)


async def get_extraction(extraction_id: str) -> dict[str, Any] | None:
    """Get extraction by ID."""
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM extractions WHERE id = ?", (extraction_id,))
        row = await cursor.fetchone()
        if row:
            result = dict(row)
            if result.get("source_files"):
                result["source_files"] = json.loads(result["source_files"])
            if result.get("extracted_data"):
                result["extracted_data"] = json.loads(result["extracted_data"])
            return result
    return None
