"""Security issue: SQL injection via string concatenation."""

def find_account(cursor, account_name):
    query = "SELECT * FROM accounts WHERE name = '" + account_name + "'"
    cursor.execute(query)
    return cursor.fetchall()
