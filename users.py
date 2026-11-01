
import sqlite3
import hashlib
import secrets

from database import connect


def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)

    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        bytes.fromhex(salt),
        200000
    )

    return salt + ":" + hashed.hex()


def verify_password(password, stored_password):
    salt, _ = stored_password.split(":", 1)
    return hash_password(password, salt) == stored_password


def register_user(username, name, birth_date, password):
    con = connect()
    cur = con.cursor()

    try:
        cur.execute("""
            INSERT INTO users (username, name, birth_date, password)
            VALUES (?, ?, ?, ?)
        """, (
            username.strip(),
            name.strip(),
            birth_date,
            hash_password(password)
        ))

        con.commit()
        return True, "Cont creat cu succes!"

    except sqlite3.IntegrityError:
        return False, "Acest username este deja folosit."

    finally:
        con.close()


def login_user(username, password):
    con = connect()
    cur = con.cursor()

    cur.execute("""
        SELECT id, username, name, birth_date, password
        FROM users
        WHERE username = ?
    """, (username.strip(),))

    user = cur.fetchone()
    con.close()

    if user and verify_password(password, user[4]):
        return {
            "id": user[0],
            "username": user[1],
            "name": user[2],
            "birth_date": user[3]
        }

    return None
