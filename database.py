
import sqlite3
import secrets
from pathlib import Path

# Baza de date rămâne în folderul proiectului
DB_PATH = Path(__file__).resolve().parent / "instagenie.db"


def connect():
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    return con


def create_tables():
    con = connect()
    cur = con.cursor()

    # Utilizatori
    # Un singur cumpărător pentru fiecare produs
    # Păstrăm doar cea mai recentă înregistrare dacă există duplicate vechi.
    cur.execute("""
                DELETE
                FROM wishlist_interactions
                WHERE status = 'bought'
                  AND id NOT IN (SELECT MAX(id)
                                 FROM wishlist_interactions
                                 WHERE status = 'bought'
                                 GROUP BY product_id)
                """)

    cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS
                    idx_one_buyer_per_product
                    ON wishlist_interactions(product_id)
                    WHERE status = 'bought'
                """)

    # Migrare: adăugăm codul unic de distribuire
    columns = [
        row[1] for row in cur.execute("PRAGMA table_info(users)").fetchall()
    ]

    if "share_token" not in columns:
        cur.execute("ALTER TABLE users ADD COLUMN share_token TEXT")

    cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_users_share_token
        ON users(share_token)
    """)

    # Generăm coduri pentru utilizatorii existenți
    users_without_token = cur.execute("""
        SELECT id FROM users WHERE share_token IS NULL OR share_token = ''
    """).fetchall()

    for user in users_without_token:
        token = secrets.token_urlsafe(16)
        cur.execute(
            "UPDATE users SET share_token = ? WHERE id = ?",
            (token, user[0])
        )

    # Interacțiunile cu produsele
    cur.execute("""
        CREATE TABLE IF NOT EXISTS wishlist_interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            status TEXT NOT NULL CHECK (
                status IN ('planned', 'bought')
            ),
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(product_id, user_id),

            FOREIGN KEY (product_id)
                REFERENCES wishlist_items(id) ON DELETE CASCADE,

            FOREIGN KEY (user_id)
                REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    con.commit()
    con.close()


if __name__ == "__main__":
    create_tables()
    print("Baza de date a fost actualizată cu succes!")
