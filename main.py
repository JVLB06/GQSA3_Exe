import flet as ft
import json
import os


DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        data = {"users": []}

        
        admin = {
            "id": "admin",
            "name": "Administrador",
            "email": "admin@local",
            "password": "admin"
        }
        data["users"].append(admin)

        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return data

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def find_user(data, email):
    for u in data["users"]:
        if u["email"].lower() == email.lower():
            return u
    return None


class DonationApp:
    PRIMARY = "#8A2BE2"
    ACCENT = "#BA55D3"
    BG = "#0D0D0D"
    CARD_BG = "#1A1A1A"
    TEXT = "white"

    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Sistema de Doações - Login"
        self.page.bgcolor = self.BG
        self.page.scroll = "auto"

        self.data = load_data()
        self.current_user = None

        self.container = ft.Column(expand=True)
        self.page.add(self.container)

        self.show_login()

    def clear(self):
        self.container.controls.clear()

    def show_login(self, e=None):
        self.clear()

        email = ft.TextField(
            label="E-mail",
            width=350,
            border_color=self.PRIMARY,
            focused_border_color=self.ACCENT,
            color=self.TEXT,
        )

        password = ft.TextField(
            label="Senha",
            password=True,
            can_reveal_password=True,
            width=350,
            border_color=self.PRIMARY,
            focused_border_color=self.ACCENT,
            color=self.TEXT,
        )

        def do_login(ev):
            user = find_user(self.data, email.value.strip())

            if not user or user["password"] != password.value:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("E-mail ou senha incorretos"),
                    bgcolor=self.PRIMARY,
                    open=True
                )
                self.page.update()
                return

            self.current_user = user

            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Bem-vindo(a), {user['name']}"),
                bgcolor=self.PRIMARY,
                open=True
            )
            self.page.update()

        
            self.show_placeholder()

        btn_login = ft.ElevatedButton(
            "Entrar",
            width=160,
            on_click=do_login,
            style=ft.ButtonStyle(
                bgcolor=self.PRIMARY,
                color=self.TEXT,
                shape=ft.RoundedRectangleBorder(radius=12)
            ),
        )

        login_card = ft.Card(
            ft.Container(
                ft.Column(
                    [
                        ft.Text(
                            "💜 Sistema de Doações Paraná",
                            style="headlineMedium",
                            color=self.TEXT
                        ),
                        ft.Text(
                            "Ajuda humanitária aos desabrigados",
                            color=self.ACCENT
                        ),
                        ft.Divider(color=self.PRIMARY),
                        email,
                        password,
                        ft.Row(
                            [btn_login],
                            alignment=ft.MainAxisAlignment.CENTER
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15,
                ),
                padding=30,
                bgcolor=self.CARD_BG,
                border_radius=15,
                alignment=ft.alignment.center,
            ),
            elevation=8,
        )

        self.container.controls.append(
            ft.Container(
                alignment=ft.alignment.center,
                content=login_card,
                expand=True
            )
        )

        self.page.update()


    def show_placeholder(self):
        self.clear()
        self.container.controls.append(
            ft.Text("Login realizado com sucesso! \nAgora coloque aqui a próxima tela.",
                    color=self.TEXT,
                    size=22)
        )
        self.page.update()


def main(page: ft.Page):
    DonationApp(page)


if __name__ == "__main__":
    ft.app(target=main)
