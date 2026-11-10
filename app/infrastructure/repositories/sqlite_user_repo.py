from typing import List, Optional, Any
from app.core.entities.user import User
from app.core.interfaces.repositories import IUserRepository
from app.infrastructure.db.sqlite_client import SQLiteClient

class SQLiteUserRepository(IUserRepository):
    """
    Implementasi konkret IUserRepository menggunakan SQLite.
    Menyediakan operasi CRUD dan pencarian akun pengguna / admin.
    """

    def __init__(self, client: SQLiteClient):
        self.client = client

    def _row_to_entity(self, row) -> User:
        return User(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            password_hash=row["password_hash"],
            full_name=row["full_name"],
            role=row["role"],
            division=row["division"] if "division" in row.keys() else "Pusat Riset PBL",
            created_at=str(row["created_at"]) if "created_at" in row.keys() else None
        )

    def save(self, user: User) -> User:
        with self.client.get_connection() as conn:
            cursor = conn.cursor()
            if user.id is not None:
                cursor.execute("""
                    UPDATE users
                    SET username = ?, email = ?, password_hash = ?, full_name = ?, role = ?, division = ?
                    WHERE id = ?
                """, (
                    user.username,
                    user.email,
                    user.password_hash,
                    user.full_name,
                    user.role,
                    user.division,
                    user.id
                ))
            else:
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, full_name, role, division)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    user.username,
                    user.email,
                    user.password_hash,
                    user.full_name,
                    user.role,
                    user.division
                ))
                user.id = cursor.lastrowid
            conn.commit()
            return user

    def find_by_id(self, user_id: Any) -> Optional[User]:
        with self.client.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_entity(row)

    def find_by_identifier(self, identifier: str) -> Optional[User]:
        clean_id = identifier.strip().lower()
        with self.client.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM users 
                WHERE LOWER(username) = ? OR LOWER(email) = ?
                LIMIT 1
            """, (clean_id, clean_id))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_entity(row)

    def find_all(self) -> List[User]:
        with self.client.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users ORDER BY id ASC")
            rows = cursor.fetchall()
            return [self._row_to_entity(r) for r in rows]

    def count(self) -> int:
        with self.client.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            return cursor.fetchone()[0]
