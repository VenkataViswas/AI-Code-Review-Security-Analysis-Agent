"""Mixed: SQL injection and weak error handling."""

def search_products(cursor, term):
    try:
        sql = "SELECT * FROM products WHERE name LIKE '%" + term + "%'"
        cursor.execute(sql)
        return cursor.fetchall()
    except Exception:
        return []
