"""Clean example: safe parameterized query."""
import sqlite3

def get_user_by_id(connection: sqlite3.Connection, user_id: int) -> list[tuple]:
    """Fetch a user using a parameterized query."""
    cursor = connection.execute(
        "SELECT id, username FROM users WHERE id = ?",
        (user_id,),
    )
    return cursor.fetchall()
