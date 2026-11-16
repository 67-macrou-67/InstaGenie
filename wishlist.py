
from database import connect
from datetime import datetime
import secrets


# --------------------------------------------------
# WISHLIST-UL PROPRIU
# --------------------------------------------------

def get_products(user_id):
    con = connect()
    cur = con.cursor()

    cur.execute("""
        SELECT id, name, image_url, product_url
        FROM wishlist_items
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,))

    products = cur.fetchall()
    con.close()
    return products


def add_product(user_id, name, image_url, product_url):
    con = connect()
    cur = con.cursor()

    cur.execute("""
        INSERT INTO wishlist_items
        (user_id, name, image_url, product_url)
        VALUES (?, ?, ?, ?)
    """, (user_id, name.strip(), image_url.strip(), product_url.strip()))

    con.commit()
    con.close()


def update_product(product_id, user_id, name, image_url, product_url):
    con = connect()
    cur = con.cursor()

    cur.execute("""
        UPDATE wishlist_items
        SET name = ?, image_url = ?, product_url = ?
        WHERE id = ? AND user_id = ?
    """, (
        name.strip(),
        image_url.strip(),
        product_url.strip(),
        product_id,
        user_id
    ))

    con.commit()
    updated = cur.rowcount > 0
    con.close()
    return updated


def delete_product(product_id, user_id):
    con = connect()
    cur = con.cursor()

    cur.execute("""
        DELETE FROM wishlist_items
        WHERE id = ? AND user_id = ?
    """, (product_id, user_id))

    con.commit()
    deleted = cur.rowcount > 0
    con.close()
    return deleted


# --------------------------------------------------
# DISTRIBUIREA WISHLIST-ULUI
# --------------------------------------------------

def get_share_token(user_id):
    con = connect()
    cur = con.cursor()

    cur.execute(
        "SELECT share_token FROM users WHERE id = ?",
        (user_id,)
    )
    result = cur.fetchone()

    if not result:
        con.close()
        return None

    token = result[0]

    if not token:
        token = secrets.token_urlsafe(16)
        cur.execute(
            "UPDATE users SET share_token = ? WHERE id = ?",
            (token, user_id)
        )
        con.commit()

    con.close()
    return token


def get_user_by_share_token(token):
    con = connect()
    cur = con.cursor()

    cur.execute("""
        SELECT id, username, name
        FROM users
        WHERE share_token = ?
    """, (token,))

    user = cur.fetchone()
    con.close()

    if not user:
        return None

    return {
        "id": user[0],
        "username": user[1],
        "name": user[2]
    }


# --------------------------------------------------
# VIZUALIZAREA WISHLIST-ULUI ALTUI UTILIZATOR
# --------------------------------------------------

def get_products_for_viewer(owner_id, viewer_id):
    con = connect()
    cur = con.cursor()

    cur.execute("""
        SELECT id, name, image_url, product_url
        FROM wishlist_items
        WHERE user_id = ?
        ORDER BY id DESC
    """, (owner_id,))

    products = cur.fetchall()
    result = []

    for product in products:
        product_id = product[0]

        # Proprietarul nu primește informații despre cumpărători
        if owner_id == viewer_id:
            interactions = []
        else:
            cur.execute("""
                SELECT users.username, users.name,
                       wishlist_interactions.status
                FROM wishlist_interactions
                JOIN users
                    ON users.id = wishlist_interactions.user_id
                WHERE wishlist_interactions.product_id = ?
                ORDER BY wishlist_interactions.updated_at DESC
            """, (product_id,))

            interactions = [
                {
                    "username": row[0],
                    "name": row[1],
                    "status": row[2]
                }
                for row in cur.fetchall()
            ]

        result.append({
            "id": product[0],
            "name": product[1],
            "image_url": product[2],
            "product_url": product[3],
            "interactions": interactions
        })

    con.close()
    return result


# --------------------------------------------------
# URMEAZĂ SĂ-L CUMPĂR / L-AM CUMPĂRAT
# --------------------------------------------------


def set_product_status(product_id, user_id, status):
    if status not in ("planned", "bought"):
        raise ValueError("Starea selectată nu este validă.")

    con = connect()

    try:
        # Blocăm temporar alte modificări concurente
        con.execute("BEGIN IMMEDIATE")
        cur = con.cursor()

        cur.execute("""
            SELECT user_id
            FROM wishlist_items
            WHERE id = ?
        """, (product_id,))

        product = cur.fetchone()

        if not product:
            raise ValueError("Produsul nu există.")

        if product[0] == user_id:
            raise ValueError(
                "Nu poți selecta o stare pentru propriul produs."
            )

        # Verificăm dacă altcineva a cumpărat deja produsul
        cur.execute("""
            SELECT users.name
            FROM wishlist_interactions
            JOIN users
                ON users.id = wishlist_interactions.user_id
            WHERE wishlist_interactions.product_id = ?
              AND wishlist_interactions.status = 'bought'
              AND wishlist_interactions.user_id != ?
            LIMIT 1
        """, (product_id, user_id))

        bought_by = cur.fetchone()

        if bought_by:
            raise ValueError(
                f"Acest produs a fost deja cumpărat de {bought_by[0]}!"
            )

        # Salvăm sau actualizăm alegerea
        cur.execute("""
            INSERT INTO wishlist_interactions
                (product_id, user_id, status, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(product_id, user_id)
            DO UPDATE SET
                status = excluded.status,
                updated_at = excluded.updated_at
        """, (
            product_id,
            user_id,
            status,
            datetime.now().isoformat(timespec="seconds")
        ))

        con.commit()

    except Exception:
        con.rollback()
        raise

    finally:
        con.close()


def remove_product_status(product_id, user_id):
    con = connect()
    cur = con.cursor()

    cur.execute("""
        DELETE FROM wishlist_interactions
        WHERE product_id = ? AND user_id = ?
    """, (product_id, user_id))

    con.commit()
    con.close()


def get_product_interactions(product_id, viewer_id, owner_id):
    # Protecție suplimentară: proprietarul nu vede niciodată stările
    if viewer_id == owner_id:
        return []

    con = connect()
    cur = con.cursor()

    cur.execute("""
        SELECT users.username, users.name,
               wishlist_interactions.status
        FROM wishlist_interactions
        JOIN users
            ON users.id = wishlist_interactions.user_id
        WHERE wishlist_interactions.product_id = ?
    """, (product_id,))

    rows = cur.fetchall()
    con.close()

    return [
        {
            "username": row[0],
            "name": row[1],
            "status": row[2]
        }
        for row in rows
    ]
