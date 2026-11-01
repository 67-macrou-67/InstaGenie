
import flet as ft

from datetime import date
from urllib.parse import urlparse

from database import create_tables
from users import register_user, login_user
from wishlist import (
    get_products,
    add_product,
    update_product,
    delete_product
)


def main(page: ft.Page):
    page.title = "InstaGenie"

    create_tables()

    def show_message(message):
        print(message)

        snack_bar = ft.SnackBar(content=ft.Text(message))
        page.snack_bar = snack_bar
        snack_bar.open = True
        page.update()

    def valid_url(url):
        try:
            parsed = urlparse(url.strip())
            return parsed.scheme in ("http", "https") and bool(parsed.netloc)
        except ValueError:
            return False

    def show_home(user):
        page.clean()

        page.add(
            ft.Text(f"Bun venit, {user['name']}!", size=25),
            ft.Text(f"Username: @{user['username']}"),
            ft.Text(f"Data nașterii: {user['birth_date']}"),
            ft.Button(
                "Lista mea de dorințe",
                on_click=lambda e: show_wishlist(user)
            ),
            ft.Button(
                "Deconectare",
                on_click=show_login
            )
        )

        page.update()

    def show_wishlist(user):
        page.clean()

        products = get_products(user["id"])

        page.add(
            ft.Text("Lista mea de dorințe", size=25),
            ft.Button(
                "Adaugă produs",
                on_click=lambda e: show_product_form(user)
            )
        )

        if not products:
            page.add(ft.Text("Nu ai adăugat încă niciun produs."))

        for product in products:
            product_id, name, image_url, product_url = product

            page.add(
                ft.Divider(),
                ft.Text(name, size=20),
                ft.Image(
                    src=image_url,
                    width=180,
                    height=180
                ),
                ft.Text(f"Link magazin: {product_url}"),
                ft.Row(
                    controls=[
                        ft.Button(
                            "Deschide magazinul",
                            on_click=lambda e, url=product_url:
                                page.launch_url(url)
                        ),
                        ft.Button(
                            "Modifică",
                            on_click=lambda e, p=product:
                                show_product_form(user, p)
                        ),
                        ft.Button(
                            "Șterge",
                            on_click=lambda e, pid=product_id:
                                remove_product(user, pid)
                        )
                    ],
                    wrap=True
                )
            )

        page.add(
            ft.Divider(),
            ft.TextButton(
                "Înapoi la profil",
                on_click=lambda e: show_home(user)
            )
        )

        page.update()

    def remove_product(user, product_id):
        delete_product(product_id, user["id"])
        show_message("Produsul a fost șters.")
        show_wishlist(user)

    def show_product_form(user, product=None):
        page.clean()

        editing = product is not None

        name = ft.TextField(
            label="Numele produsului",
            value=product[1] if editing else ""
        )

        image_url = ft.TextField(
            label="Link către imagine",
            value=product[2] if editing else ""
        )

        product_url = ft.TextField(
            label="Link către magazin",
            value=product[3] if editing else ""
        )

        def submit(e):
            product_name = (name.value or "").strip()
            image = (image_url.value or "").strip()
            link = (product_url.value or "").strip()

            if not product_name or not image or not link:
                show_message("Completează toate câmpurile.")
                return

            if not valid_url(image):
                show_message("Linkul imaginii trebuie să înceapă cu http:// sau https://.")
                return

            if not valid_url(link):
                show_message("Linkul magazinului nu este valid.")
                return

            try:
                if editing:
                    update_product(
                        product[0],
                        user["id"],
                        product_name,
                        image,
                        link
                    )
                    show_message("Produsul a fost modificat.")
                else:
                    add_product(
                        user["id"],
                        product_name,
                        image,
                        link
                    )
                    show_message("Produsul a fost adăugat.")

                show_wishlist(user)

            except Exception as ex:
                print("Eroare la salvarea produsului:", repr(ex))
                show_message("Nu am putut salva produsul.")

        page.add(
            ft.Text(
                "Modifică produsul" if editing else "Adaugă produs",
                size=25
            ),
            name,
            image_url,
            product_url,
            ft.Button(
                "Salvează",
                on_click=submit
            ),
            ft.TextButton(
                "Înapoi la listă",
                on_click=lambda e: show_wishlist(user)
            )
        )

        page.update()

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
            nume = (name.value or "").strip()
            user_name = (username.value or "").strip()
            data_nasterii = (birth_date.value or "").strip()
            parola = password.value or ""

            if not all([nume, user_name, data_nasterii, parola]):
                show_message("Completează toate câmpurile.")
                return

            try:
                date.fromisoformat(data_nasterii)
            except ValueError:
                show_message("Data trebuie să fie YYYY-MM-DD.")
                return

            if len(parola) < 8:
                show_message("Parola trebuie să aibă minimum 8 caractere.")
                return

            try:
                success, message = register_user(
                    user_name,
                    nume,
                    data_nasterii,
                    parola
                )

                show_message(message)

                if success:
                    show_login()

            except Exception as ex:
                print("Eroare la înregistrare:", repr(ex))
                show_message("Eroare la crearea contului.")

        page.add(
            ft.Text("Creare cont", size=25),
            name,
            username,
            birth_date,
            password,
            ft.Button("Creează cont", on_click=submit),
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
                show_message("Eroare la autentificare.")

        page.add(
            ft.Text("InstaGenie", size=30),
            ft.Text("Autentificare", size=20),
            username,
            password,
            ft.Button("Intră în cont", on_click=submit),
            ft.TextButton(
                "Nu ai cont? Înregistrează-te",
                on_click=show_register
            )
        )

        page.update()

    show_login()


ft.run(main)
