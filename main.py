
import flet as ft

from datetime import date
from database import create_tables
from users import register_user, login_user


def main(page: ft.Page):
    page.title = "InstaGenie"

    create_tables()

    def show_message(message):
        print(message)

        snack_bar = ft.SnackBar(
            content=ft.Text(message)
        )
        page.snack_bar = snack_bar
        snack_bar.open = True
        page.update()

    def show_home(user):
        page.clean()

        page.add(
            ft.Text(
                f"Bun venit, {user['name']}!",
                size=25
            ),
            ft.Text(f"Username: @{user['username']}"),
            ft.Text(f"Data nașterii: {user['birth_date']}"),
            ft.Text("Profilul tău InstaGenie"),
            ft.Button(
                "Lista mea de dorințe",
                on_click=lambda e: show_wishlist(user)
            ),
            ft.Button(
                "Deconectare",
                on_click=show_login
            )
        )

    def show_register(e=None):
        page.clean()

        name = ft.TextField(label="Nume complet")
        username = ft.TextField(label="Username")
        birth_date = ft.TextField(
            label="Data nașterii (YYYY-MM-DD)"
        )
        password = ft.TextField(
            label="Parolă",
            password=True,
            can_reveal_password=True
        )

        def submit(e):
            print("Butonul de creare cont a fost apăsat.")

            nume = (name.value or "").strip()
            user_name = (username.value or "").strip()
            data_nasterii = (birth_date.value or "").strip()
            parola = password.value or ""

            if not nume or not user_name or not data_nasterii or not parola:
                show_message("Completează toate câmpurile.")
                return

            try:
                date.fromisoformat(data_nasterii)
            except ValueError:
                show_message(
                    "Data trebuie să fie în format YYYY-MM-DD."
                )
                return

            if len(parola) < 8:
                show_message(
                    "Parola trebuie să aibă minimum 8 caractere."
                )
                return

            try:
                success, message = register_user(
                    user_name,
                    nume,
                    data_nasterii,
                    parola
                )

                print("Rezultat înregistrare:", success)
                print("Mesaj:", message)

                show_message(message)

                if success:
                    show_login()

            except Exception as ex:
                print("Eroare la înregistrare:", repr(ex))
                show_message("A apărut o eroare la salvarea contului.")

        page.add(
            ft.Text("Creare cont", size=25),
            name,
            username,
            birth_date,
            password,
            ft.Button(
                "Creează cont",
                on_click=submit
            ),
            ft.TextButton(
                "Ai deja cont? Autentifică-te",
                on_click=show_login
            )
        )

        page.update()

    def show_login(e=None):
        page.clean()

        username = ft.TextField(label="Username")
        password = ft.TextField(
            label="Parolă",
            password=True,
            can_reveal_password=True
        )

        def submit(e):
            print("Butonul de autentificare a fost apăsat.")

            user_name = (username.value or "").strip()
            parola = password.value or ""

            if not user_name or not parola:
                show_message("Completează username-ul și parola.")
                return

            try:
                user = login_user(user_name, parola)

                if user:
                    show_home(user)
                else:
                    show_message("Username sau parolă incorectă.")

            except Exception as ex:
                print("Eroare la autentificare:", repr(ex))
                show_message("A apărut o eroare la autentificare.")

        page.add(
            ft.Text("InstaGenie", size=30),
            ft.Text("Autentificare", size=20),
            username,
            password,
            ft.Button(
                "Intră în cont",
                on_click=submit
            ),
            ft.TextButton(
                "Nu ai cont? Înregistrează-te",
                on_click=show_register
            )
        )

        page.update()

    show_login()


ft.run(main)
