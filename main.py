
import flet as ft

from datetime import date
from database import create_tables
from users import register_user, login_user

from wishlist import (
    get_products,
    add_product,
    update_product,
    delete_product,
    get_share_token,
    get_user_by_share_token,
    get_products_for_viewer,
    set_product_status,
    remove_product_status
)


def main(page: ft.Page):
    page.title = "InstaGenie"
    print("open_url:", hasattr(page, "open_url"))
    print("launch_url:", hasattr(page, "launch_url"))
    print("launch_url:", hasattr(ft, "UrlLauncher"))
    page.scroll = ft.ScrollMode.AUTO

    create_tables()

    current_user = None

    def show_message(message):
        print(message)
        snack_bar = ft.SnackBar(content=ft.Text(message))
        page.snack_bar = snack_bar
        snack_bar.open = True
        page.update()

    # --------------------------------------------------
    # PAGINA PRINCIPALA
    # --------------------------------------------------

    def show_home(user):
        nonlocal current_user
        current_user = user

        page.clean()

        page.add(
            ft.Text(f"Bun venit, {user['name']}!", size=25),
            ft.Text(f"Username: @{user['username']}"),
            ft.Text(f"Data nașterii: {user['birth_date']}"),
            ft.Text("Profilul tău InstaGenie"),
            ft.Button(
                "Lista mea de dorințe",
                on_click=lambda e: show_wishlist(user)
            ),
            ft.Button(
                "Vezi wishlist-ul unui prieten",
                on_click=show_enter_share_code
            ),
            ft.Button(
                "Deconectare",
                on_click=show_login
            )
        )

        page.update()

    # --------------------------------------------------
    # AUTENTIFICARE
    # --------------------------------------------------

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

            if not nume or not user_name or not data_nasterii or not parola:
                show_message("Completează toate câmpurile.")
                return

            try:
                date.fromisoformat(data_nasterii)
            except ValueError:
                show_message("Data trebuie să fie în format YYYY-MM-DD.")
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
                show_message("A apărut o eroare la salvarea contului.")

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
        nonlocal current_user
        current_user = None

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
                show_message("A apărut o eroare la autentificare.")

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

    # --------------------------------------------------
    # WISHLIST-UL PROPRIU
    # --------------------------------------------------

    def show_wishlist(user):
        page.clean()

        products = get_products(user["id"])

        controls = [
            ft.Text("Wishlist-ul meu", size=25),
            ft.Text("Produsele pe care ți le dorești")
        ]

        controls.append(
            ft.Button(
                "Adaugă produs",
                on_click=lambda e: show_product_form(user)
            )
        )

        controls.append(
            ft.Button(
                "Distribuie wishlist-ul meu",
                on_click=lambda e: show_share_code(user)
            )
        )

        if not products:
            controls.append(ft.Text("Nu ai adăugat încă niciun produs."))

        for product in products:
            product_id, name, image_url, product_url = product

            controls.append(
                ft.Divider()
            )

            controls.append(ft.Text(name, size=20))

            if image_url:
                controls.append(
                    ft.Image(
                        src=image_url,
                        width=180,
                        height=180,

                    )
                )

            if product_url and product_url.strip():
                controls.append(
                    ft.Button(
                        "Mergi la magazin",
                        action=ft.OpenUrl(
                            product_url,
                            target=ft.UrlTarget.BLANK
                        )
                    )
                )

            controls.append(
                ft.Row(
                    controls=[
                        ft.Button(
                            "Modifică",
                            on_click=lambda e, p=product:
                                show_product_form(user, p)
                        ),
                        ft.Button(
                            "Șterge",
                            on_click=lambda e, pid=product_id:
                                remove_product(pid, user)
                        )
                    ],
                    wrap=True
                )
            )

        controls.append(
            ft.Button(
                "Înapoi la profil",
                on_click=lambda e: show_home(user)
            )
        )

        page.add(
            ft.Column(
                controls,
                scroll=ft.ScrollMode.AUTO,
                expand=True
            )
        )
        page.update()

    def show_product_form(user, product=None):
        page.clean()

        editing = product is not None

        name = ft.TextField(
            label="Numele produsului",
            value=product[1] if editing else ""
        )

        image_url = ft.TextField(
            label="Link imagine",
            value=product[2] if editing else ""
        )

        product_url = ft.TextField(
            label="Link magazin",
            value=product[3] if editing else ""
        )

        def submit(e):
            product_name = (name.value or "").strip()
            image = (image_url.value or "").strip()
            url = (product_url.value or "").strip()

            if not product_name:
                show_message("Numele produsului este obligatoriu.")
                return

            try:
                if editing:
                    update_product(
                        product[0],
                        user["id"],
                        product_name,
                        image,
                        url
                    )
                    show_message("Produs modificat!")
                else:
                    add_product(
                        user["id"],
                        product_name,
                        image,
                        url
                    )
                    show_message("Produs adăugat!")

                show_wishlist(user)

            except Exception as ex:
                print("Eroare produs:", repr(ex))
                show_message("Nu am putut salva produsul.")

        page.add(
            ft.Text(
                "Modifică produsul" if editing else "Adaugă produs",
                size=25
            ),
            name,
            image_url,
            product_url,
            ft.Button("Salvează", on_click=submit),
            ft.TextButton(
                "Înapoi",
                on_click=lambda e: show_wishlist(user)
            )
        )

        page.update()

    def remove_product(product_id, user):
        try:
            delete_product(product_id, user["id"])
            show_message("Produs șters.")
            show_wishlist(user)
        except Exception as ex:
            print("Eroare ștergere:", repr(ex))
            show_message("Nu am putut șterge produsul.")

    # --------------------------------------------------
    # DISTRIBUIREA WISHLIST-ULUI
    # --------------------------------------------------

    def show_share_code(user):
        page.clean()

        token = get_share_token(user["id"])

        page.add(
            ft.Text("Distribuie wishlist-ul", size=25),
            ft.Text(
                "Acesta este codul tău personal. "
                "Trimite-l prietenilor tăi."
            ),
            ft.Text(token, size=20, selectable=True),
            ft.Text(
                "Prietenii trebuie să fie autentificați "
                "și să introducă acest cod în aplicație."
            ),
            ft.Button(
                "Înapoi la wishlist",
                on_click=lambda e: show_wishlist(user)
            )
        )

        page.update()

    # --------------------------------------------------
    # ACCESAREA WISHLIST-ULUI UNUI PRIETEN
    # --------------------------------------------------

    def show_enter_share_code(e=None):
        page.clean()

        token_field = ft.TextField(
            label="Introdu codul wishlist-ului"
        )

        def submit(e):
            token = (token_field.value or "").strip()

            if not token:
                show_message("Introdu codul primit de la prieten.")
                return

            owner = get_user_by_share_token(token)

            if not owner:
                show_message("Cod invalid. Verifică și încearcă din nou.")
                return

            if owner["id"] == current_user["id"]:
                show_message("Acesta este propriul tău wishlist.")
                show_wishlist(current_user)
                return

            show_friend_wishlist(owner, current_user)

        page.add(
            ft.Text("Wishlist-ul unui prieten", size=25),
            token_field,
            ft.Button("Accesează wishlist-ul", on_click=submit),
            ft.TextButton(
                "Înapoi la profil",
                on_click=lambda e: show_home(current_user)
            )
        )

        page.update()

    # --------------------------------------------------
    # AFIȘAREA WISHLIST-ULUI PRIETENULUI
    # --------------------------------------------------

    def show_friend_wishlist(owner, viewer):
        page.clean()

        products = get_products_for_viewer(
            owner["id"],
            viewer["id"]
        )

        controls = [
            ft.Text(
                f"Wishlist-ul lui {owner['name']}",
                size=25
            ),
            ft.Text("Vezi ce cadouri își dorește!")
        ]

        if not products:
            controls.append(ft.Text("Acest wishlist este momentan gol."))

        for product in products:
            product_id = product["id"]
            interactions = product["interactions"]

            controls.append(ft.Divider())
            controls.append(ft.Text(product["name"], size=20))

            if product["image_url"]:
                controls.append(
                    ft.Image(
                        src=product["image_url"],
                        width=180,
                        height=180,

                    )
                )

            if product["product_url"] and product["product_url"].strip():
                controls.append(
                    ft.Button(
                        "Mergi la magazin",
                        action=ft.OpenUrl(
                            product["product_url"],
                            target=ft.UrlTarget.BLANK
                        )
                    )
                )


            bought = [
                item for item in interactions
                if item["status"] == "bought"
            ]

            planned = [
                item for item in interactions
                if item["status"] == "planned"
            ]

            # Verificăm dacă produsul a fost cumpărat
            if bought:
                buyer = bought[0]

                controls.append(
                    ft.Text(
                        f"A FOST CUMPĂRAT DEJA DE {buyer['name'].upper()}!",
                        size=20,
                        color=ft.Colors.RED,
                        weight=ft.FontWeight.BOLD
                    )
                )

            else:
                # Afișăm persoanele interesate
                if planned:
                    controls.append(
                        ft.Text(
                            "Urmează să-l cumpere: "
                            + ", ".join(
                                item["name"] for item in planned
                            )
                        )
                    )

            my_status = next(
                (
                    item["status"]
                    for item in interactions
                    if item["username"] == viewer["username"]
                ),
                None
            )

            if bought and bought[0]["username"] == viewer["username"]:
                controls.append(
                    ft.Text("Tu ai marcat acest produs ca fiind cumpărat.")
                )

            elif bought:
                # Produsul este cumpărat de altcineva.
                # Nu mai afișăm butoanele de cumpărare.
                pass

            else:
                if my_status == "planned":
                    controls.append(
                        ft.Text("Tu ai ales: Urmează să-l cumpăr.")
                    )

                controls.append(
                    ft.Row(
                        controls=[
                            ft.Button(
                                "Urmează să-l cumpăr",
                                on_click=lambda e, pid=product_id:
                                    change_product_status(
                                        pid, viewer, owner, "planned"
                                    )
                            ),
                            ft.Button(
                                "L-am cumpărat deja",
                                on_click=lambda e, pid=product_id:
                                    change_product_status(
                                        pid, viewer, owner, "bought"
                                    )
                            ),
                            ft.TextButton(
                                "Anulează alegerea",
                                on_click=lambda e, pid=product_id:
                                    cancel_product_status(
                                        pid, viewer, owner
                                    )
                            )
                        ],
                        wrap=True
                    )
                )


        controls.append(
            ft.Button(
                "Înapoi la profil",
                on_click=lambda e: show_home(viewer)
            )
        )

        page.add(
            ft.Column(
                controls,
                scroll=ft.ScrollMode.AUTO,
                expand=True
            )
        )
        page.update()

    def change_product_status(product_id, viewer, owner, status):
        try:
            set_product_status(
                product_id,
                viewer["id"],
                status
            )

            show_message("Alegerea ta a fost salvată!")

            show_friend_wishlist(owner, viewer)

        except Exception as ex:
            print("Eroare la actualizarea stării:", repr(ex))
            show_message(str(ex))

    def cancel_product_status(product_id, viewer, owner):
        try:
            remove_product_status(
                product_id,
                viewer["id"]
            )

            show_message("Alegerea ta a fost anulată.")

            show_friend_wishlist(owner, viewer)

        except Exception as ex:
            print("Eroare la anulare:", repr(ex))
            show_message("Nu am putut anula alegerea.")

    show_login()


ft.run(main)
