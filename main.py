import flet as ft
import json
import os
import uuid
import requests
from requests.exceptions import RequestException
from datetime import datetime

API_URL = os.environ.get("API_URL", "http://localhost:8000")
REQ_TIMEOUT = 0.5
ACCESS_TOKEN = None

def _headers():
    h = {"Content-Type": "application/json"}
    if ACCESS_TOKEN:
        h["Authorization"] = f"Bearer {ACCESS_TOKEN}"
    return h

def float_format(value)-> float:
    str(value).replace(",",".")
    return float(value)

def api_get(path):
    try:
        r = requests.get(f"{API_URL}{path}", headers=_headers(), timeout=REQ_TIMEOUT)
        if r.status_code in (200, 201):
            try:
                return r.json()
            except Exception:
                return {"status": "ok"}
        return None
    except RequestException:
        return None

def api_post(path, payload):
    try:
        r = requests.post(f"{API_URL}{path}", json=payload, headers=_headers(), timeout=REQ_TIMEOUT)
        if r.status_code == 409:
            return {"error": "conflict"}
        if 200 <= r.status_code < 300:
            try:
                return r.json()
            except:
                return {"status": "ok"}
        return {"error": r.status_code}
    except RequestException:
        return None

def api_put(path, payload):
    try:
        r = requests.put(f"{API_URL}{path}", json=payload, headers=_headers(), timeout=REQ_TIMEOUT)
        if 200 <= r.status_code < 300:
            try:
                return r.json()
            except Exception:
                return {"status": "ok"}
        return None
    except RequestException:
        return None

def api_delete(path, payload=None):
    try:
        if payload is not None:
            r = requests.delete(f"{API_URL}{path}", json=payload, headers=_headers(), timeout=REQ_TIMEOUT)
        else:
            r = requests.delete(f"{API_URL}{path}", headers=_headers(), timeout=REQ_TIMEOUT)
        if 200 <= r.status_code < 300:
            try:
                return r.json()
            except Exception:
                return {"status": "ok"}
        return None
    except RequestException:
        return None

def api_login(email, password):
    return api_post("/login", {"Username": email, "Password": password})

def api_register_user(user_dict):
    payload = {
        "Email": user_dict.get("email"),
        "Password": user_dict.get("password"),
        "IsReceiver": user_dict.get("role"),
        "Name": user_dict.get("name"),
        "Document": user_dict.get("cpf_cnpj") if user_dict.get("role") == "receptor" else None,
        "Address": user_dict.get("cep") if user_dict.get("role") == "receptor" else None,
        "Cause": user_dict.get("description") if user_dict.get("role") == "receptor" else None
    }
    return api_post("/cadastrate", payload)

def api_add_pix(pix_value):
    payload = {
        "UserId" : 0,
        "PixKey": str(pix_value),
        "KeyType": "cpf",
        "CreatedAt": datetime.now().isoformat()
    }
    return api_post("/receiver/add_pix_key", payload)

def api_delete_pix():
    payload = {}
    return api_delete("/receiver/delete_pix_key", payload)

def api_create_product(prod):
    payload = {
        "CauseId" : 0,
        "Name": prod.get("title"),
        "Description": prod.get("description"),
        "Value": float_format(prod.get("value"))
    }
    return api_post("/receiver/create_product", payload)

def api_delete_product(product_payload):
    return api_delete("/receiver/delete_product", product_payload)

def api_get_products():
    return api_get("/receiver/get_products")

def api_list_receivers(order_type="name_asc"):
    return api_get(f"/donator/list_receivers/{order_type}")

def api_favorite_cause(cause_id):
    return api_post(f"/donator/favorite/{cause_id}", {})

def api_remove_favorite(fav_id):
    return api_delete(f"/donator/favorite/{fav_id}")

def api_list_favorites():
    return api_get("/donator/favorites")

def api_add_donation(donation_payload):
    return api_post("/donator/add_donation", donation_payload)

def api_list_donations_made():
    return api_get("/donator/list_donations_made")

def api_get_cause_products(causeId):
    return api_get(f"/donator/get_cause_products/{causeId}")

class DonationApp:
    PRIMARY = "#8A2BE2"
    ACCENT = "#BA55D3"
    BG = "#FFFFFF"
    CARD_BG = "#26023F"
    TEXT = "white"

    def __init__(self, page: ft.Page):
        self.page = page
        page.title = "Paraná — Sistema de Doações"
        page.window.max_width = 1980
        page.window.min_width = 1280
        page.window.max_height = 1080
        page.window.min_height = 720
        page.bgcolor = self.BG
        page.scroll = "auto"
        page.padding = 0
        page.assets_dir = "assets"
        page.fonts = {
            "Poppins": "assets/fonts/Poppins-Regular.ttf" if os.path.exists("assets/fonts/Poppins-Regular.ttf") else None,
            "PoppinsBold": "assets/fonts/Poppins-Bold.ttf" if os.path.exists("assets/fonts/Poppins-Bold.ttf") else None
        }
        page.theme = ft.Theme(font_family="Poppins")

        self.current_user = None
        self.access_token = None

        self.container = ft.Column(alignment=ft.MainAxisAlignment.CENTER,
                                   horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                   expand=True)

        self.header = self.build_header()

        self.main_column = ft.Column(
            [
                self.header,
                ft.Container(expand=True, alignment=ft.alignment.center, content=self.container)
            ],
            spacing=0, expand=True
        )

        bg_image_path = "assets/01.png" if os.path.exists("assets/01.png") else None
        stack_children = []
        if bg_image_path:
            stack_children.append(ft.Container(expand=True, content=ft.Image(src=bg_image_path, fit=ft.ImageFit.FILL, expand=True)))
        stack_children.append(self.main_column)

        self.page.add(ft.Stack(stack_children, expand=True))
        self.show_login()

    def build_header(self):
        if self.current_user:
            return ft.Container(
                content=ft.Row([
                    ft.Text("Sistema de Doações", size=24, color="white", font_family="PoppinsBold"),
                    ft.Container(expand=True),
                    ft.Text(f"Logado: {self.current_user.get('name','') or self.current_user.get('email','') } ({self.current_user.get('role','')})", color="white", size=14),
                    ft.Container(width=10),
                    ft.ElevatedButton("Sair", on_click=self.logout, style=ft.ButtonStyle(bgcolor=self.PRIMARY, color="white"))
                ], alignment=ft.MainAxisAlignment.START),
                bgcolor=self.CARD_BG, padding=ft.padding.symmetric(horizontal=20), height=70, expand=True,
                alignment=ft.alignment.center_left
            )
        else:
            return ft.Container(
                content=ft.Row([ft.Text("Sistema de Doações", size=28, color="white", font_family="PoppinsBold")]),
                bgcolor=self.CARD_BG, padding=ft.padding.symmetric(horizontal=20), height=70, expand=True,
                alignment=ft.alignment.center_left
            )

    def refresh_header(self):
        try:
            self.main_column.controls[0] = self.build_header()
            self.page.update()
        except Exception:
            pass

    def clear(self):
        self.container.controls.clear()

    def update(self):
        self.page.update()

    def snackbar(self, msg):
        self.page.snack_bar = ft.SnackBar(ft.Text(msg), open=True, bgcolor=self.CARD_BG)
        self.page.update()

    def show_login(self, e=None):
        self.clear()

        email = ft.TextField(label="E-mail", width=350, color=self.TEXT, border_color=self.PRIMARY, focused_border_color=self.ACCENT)
        password = ft.TextField(label="Senha", width=350, password=True, can_reveal_password=True, color=self.TEXT, border_color=self.PRIMARY, focused_border_color=self.ACCENT)

    
        def do_login(ev):
            global ACCESS_TOKEN
            res = api_login(email.value.strip(), password.value)

            if res is None:
                error_msg.value = "Falha ao comunicar com o servidor."
                error_msg.visible = True
                self.update()
                return
            
            if isinstance(res, dict) and res.get("error"):
                error_msg.value = "E-mail ou senha incorretos."
                error_msg.visible = True
                self.update()
                return

            error_msg.visible = False         

            if "access_token" in res:
                ACCESS_TOKEN = res.get("access_token")

                role = self.detect_role()

                if role is None:
                     return 

                self.current_user = {
                    "email": res.get("user"),
                    "name": res.get("user"),
                    "role": role
                }

                self.refresh_header()
                self.snackbar(f"Bem-vindo(a), {self.current_user.get('name')}")
                self.show_home()
                return
            else:
                self.snackbar("Login inválido.")
                return


        login_btn = ft.ElevatedButton("Entrar", on_click=do_login, width=150, style=ft.ButtonStyle(bgcolor=self.PRIMARY, color=self.TEXT))
        register_btn = ft.TextButton("Criar conta", on_click=lambda e: self.show_register(), style=ft.ButtonStyle(color=self.ACCENT))

        error_msg = ft.Text("", color="red", size=14, visible=False, text_align=ft.TextAlign.CENTER)

        card_inner = ft.Container(
            ft.Column([
                ft.Text("Sistema de Doações Paraná", style="headlineMedium", color=self.TEXT, text_align=ft.TextAlign.CENTER),
                ft.Text("Plataforma de auxílio", color=self.ACCENT, text_align=ft.TextAlign.CENTER),
                ft.Divider(color=self.PRIMARY),
                email, password,
                error_msg,
                ft.Row([login_btn, register_btn], alignment=ft.MainAxisAlignment.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            padding=30, bgcolor=self.CARD_BG, border_radius=15, alignment=ft.alignment.center, width=500
        )


        card = ft.Card(card_inner, elevation=8, margin=ft.margin.only(top=80))
        self.container.controls.append(card)
        self.update()

    def show_register(self, e=None):
        self.clear()

        role = ft.Dropdown(label="Tipo de conta", width=300, value="doador", options=[ft.dropdown.Option("doador", "Doador"), ft.dropdown.Option("receptor", "Receptor")], border_color=self.PRIMARY, focused_border_color=self.ACCENT)
        name = ft.TextField(label="Nome/Razão Social", width=400, color=self.TEXT, border_color=self.PRIMARY)
        email = ft.TextField(label="E-mail", width=400, color=self.TEXT, border_color=self.PRIMARY)
        cpf_cnpj = ft.TextField(label="CPF/CNPJ", width=400, color=self.TEXT, border_color=self.PRIMARY)
        cep = ft.TextField(label="CEP", width=300, color=self.TEXT, border_color=self.PRIMARY)
        password = ft.TextField(label="Senha", width=400, password=True, can_reveal_password=True, color=self.TEXT, border_color=self.PRIMARY)
        description = ft.TextField(label="Motivo/Descrição", width=400, multiline=True, color=self.TEXT, border_color=self.PRIMARY)

        def on_role_change(e):
            vis = (role.value == "receptor")
            cpf_cnpj.visible = vis
            cep.visible = vis
            description.visible = vis
            self.page.update()

        role.on_change = on_role_change
        on_role_change(None)

        def do_register(ev):
            if not name.value.strip() or not email.value.strip() or not password.value.strip():
                self.snackbar("Preencha nome, e-mail e senha.")
                return
            new_user = {
                "id": str(uuid.uuid4()),
                "role": role.value if role.value else "doador",
                "name": name.value.strip(),
                "email": email.value.strip(),
                "cpf_cnpj": cpf_cnpj.value.strip() if role.value == "receptor" else "",
                "cep": cep.value.strip() if role.value == "receptor" else "",
                "password": password.value,
                "description": description.value.strip() if role.value == "receptor" else "",
            }
            res = api_register_user(new_user)
            if res is None:
                self.snackbar("Erro ao cadastrar (backend).")
                return
            self.snackbar("Cadastro realizado com sucesso.")
            self.show_login()

        btn_register = ft.ElevatedButton("Registrar", on_click=do_register, style=ft.ButtonStyle(bgcolor=self.PRIMARY, color=self.TEXT))
        btn_back = ft.TextButton("Voltar", on_click=lambda e: self.show_login(), style=ft.ButtonStyle(color=self.ACCENT))

        card_inner = ft.Container(ft.Column([
            ft.Text("Registrar nova conta", style="headlineMedium", color=self.TEXT),
            ft.Text("Preencha os dados para criar sua conta", color=self.ACCENT, text_align=ft.TextAlign.CENTER),
            ft.Divider(color=self.PRIMARY),
            role, name, email, cpf_cnpj, cep, password, description,
            ft.Row([btn_register, btn_back], alignment=ft.MainAxisAlignment.CENTER)
        ], spacing=15), padding=30, bgcolor=self.CARD_BG, border_radius=15, width=500)
        card = ft.Card(card_inner, elevation=8, margin=ft.margin.only(top=80))
        self.container.controls.append(card)
        self.update()

    def detect_role(self):
        products = api_get("/receiver/get_products")
        if products is not None:
            return "receptor"
        favs = api_get("/donator/favorites")
        if favs is not None:
            return "doador"
        return "doador"

    def show_home(self, e=None):
        self.clear()
        if not self.current_user:
            self.show_login()
            return
        role = self.current_user.get("role", "doador")
        if role == "receptor":
            self.show_receptor_dashboard()
        elif role == "doador":
            self.show_donor_feed()
        else:
            self.show_donor_feed()
        self.refresh_header()
        self.update()

    def logout(self, e=None):
        global ACCESS_TOKEN
        ACCESS_TOKEN = None
        self.current_user = None
        self.refresh_header()
        self.show_login()

    def show_receptor_dashboard(self):
        u = self.current_user
        self.clear()

        pix_tf = ft.TextField(label="Chave PIX", value="", width=400, color=self.TEXT, border_color=self.PRIMARY)

        def save_pix(ev):
            val = pix_tf.value.strip()
            if not val:
                self.snackbar("Preencha a chave PIX.")
                return
            res = api_add_pix(val)
            if res is None:
                self.snackbar("Erro ao salvar PIX.")
            else:
                self.snackbar("PIX salvo com sucesso.")

        pix_card = ft.Card(ft.Container(ft.Column([
            ft.Text("Informações de Recebimento", style="headlineSmall", color=self.TEXT),
            ft.Divider(color=self.PRIMARY),
            pix_tf,
            ft.Row([ft.ElevatedButton("Salvar PIX", on_click=save_pix, style=ft.ButtonStyle(bgcolor=self.PRIMARY, color=self.TEXT))], alignment=ft.MainAxisAlignment.CENTER)
        ], spacing=15), padding=25, bgcolor=self.CARD_BG, border_radius=15, width=550), elevation=4, margin=ft.margin.only(bottom=25, top=15))
        self.container.controls.append(pix_card)

        title = ft.TextField(label="Título do Produto/Cota", width=400, color=self.TEXT, border_color=self.PRIMARY)
        value = ft.TextField(label="Valor (ex: 50.00)", width=400, color=self.TEXT, border_color=self.PRIMARY)
        desc = ft.TextField(label="Descrição", width=400, multiline=True, height=100, color=self.TEXT, border_color=self.PRIMARY)

        def create_product(ev):
            t = title.value.strip(); v = value.value.strip().replace(",", "."); d = desc.value.strip()
            if not t or not v:
                self.snackbar("Preencha título e valor.")
                return
            try:
                v_float = float(v)
            except:
                self.snackbar("Valor inválido.")
                return
            new_prod = {"title": t, "value": v_float, "description": d}
            res = api_create_product(new_prod)
            if res is None:
                self.snackbar("Erro ao criar produto.")
            else:
                self.snackbar("Produto criado com sucesso.")
                self.show_receptor_dashboard()

        create_card = ft.Card(ft.Container(ft.Column([
            ft.Text("Criar novo produto/cota", style="headlineMedium", color=self.TEXT),
            ft.Divider(color=self.PRIMARY),
            title, value, desc,
            ft.Row([ft.ElevatedButton("Criar", on_click=create_product, style=ft.ButtonStyle(bgcolor=self.PRIMARY, color=self.TEXT))], alignment=ft.MainAxisAlignment.CENTER)
        ], spacing=15), padding=25, bgcolor=self.CARD_BG, border_radius=15, width=550), elevation=4, margin=ft.margin.only(bottom=25))
        self.container.controls.append(create_card)

        prods = api_get("/receiver/get_products")
        list_column = ft.Column(spacing=10)
        if prods and isinstance(prods, list):
            for p in prods:
                def delete_factory(prod):
                    def delete(ev):
                        payload = {"ProductId": prod.get("id")} if prod.get("id") else {"ProductId": prod.get("ProductId", None)}
                        res = api_delete_product(payload)
                        if res is None:
                            self.snackbar("Erro ao remover produto.")
                        else:
                            self.snackbar("Produto removido.")
                            self.show_receptor_dashboard()
                    return delete
                item = ft.Card(ft.Container(ft.Column([
                    ft.Text(p.get("ProductName", "—"), style="titleMedium", color=self.TEXT),
                    ft.Text(f"R$ {float(p.get('Value', p.get('value', 0))):.2f}", color=self.TEXT),
                    ft.Text(p.get("Description", ""), color=self.TEXT),
                    ft.Row([ft.ElevatedButton("Excluir", on_click=delete_factory(p), style=ft.ButtonStyle(bgcolor=self.ACCENT, color=self.TEXT))], alignment=ft.MainAxisAlignment.END)
                ], spacing=8), padding=15, bgcolor=self.CARD_BG, border_radius=10), elevation=2)
                list_column.controls.append(item)
        else:
            list_column.controls.append(ft.Text("Nenhum produto encontrado.", color=self.TEXT))

        list_card = ft.Card(ft.Container(ft.Column([ft.Text("Meus Produtos", style="headlineSmall", color=self.TEXT), ft.Divider(color=self.PRIMARY), list_column], spacing=15), padding=25, bgcolor=self.CARD_BG, border_radius=15, width=650), elevation=4)
        self.container.controls.append(list_card)
        self.refresh_header()
        self.update()

    def show_donor_feed(self):
        self.clear()

        self.container.controls.append(
            ft.Container(
                content=ft.Text(
                    "Causas disponíveis",
                    color=self.TEXT,
                    font_family="PoppinsBold",
                    size=26,
                    text_align=ft.TextAlign.CENTER
                ),
                padding=10,
                bgcolor=self.CARD_BG,
                border_radius=10,
                margin=ft.margin.only(bottom=25, top=15),
                alignment=ft.alignment.center,      # ← centraliza o conteúdo dentro do container
                width=600                           # ← opcional: define largura para centralizar visualmente
            )
        )

        receivers_res = api_list_receivers("name_asc")

        if isinstance(receivers_res, dict) and "receivers" in receivers_res:
            receivers = receivers_res["receivers"]
        elif isinstance(receivers_res, list):
            receivers = receivers_res
        else:
            receivers = []

        list_column = ft.Column(spacing=20)

        for r in receivers:
            rid = r.get("UserId") or r.get("id_usuario") or r.get("Id")
            receptor_nome = r.get("Name") or r.get("nome") or "Receptor"
            receptor_desc = r.get("Description") or r.get("descricao") or "Sem descrição"

            prods = api_get_cause_products(rid)

            prod_list = []

            if isinstance(prods, list):
                for p in prods:
                    product_name = p.get("ProductName") or p.get("name")
                    product_desc = p.get("Description") or p.get("description")
                    product_value = float(p.get("Value") or p.get("value") or 0.0)

                    # Campos do formulário de doação por produto
                    value_tf = ft.TextField(
                        label="Valor da doação",
                        width=200,
                        keyboard_type=ft.KeyboardType.NUMBER,
                        bgcolor="#4b0a6d",
                        color="white",
                        border_color=self.ACCENT,
                    )
                    msg_tf = ft.TextField(
                        label="Mensagem (opcional)",
                        width=300,
                        multiline=True,
                        bgcolor="#4b0a6d",
                        color="white",
                        border_color=self.ACCENT,
                    )

                    donation_controls = ft.Column(visible=False, spacing=8)

                    def make_handlers(receiver_id, value_field, msg_field, controls_container):
                        def open_form(e):
                            controls_container.visible = True
                            self.update()

                        def cancel(e):
                            controls_container.visible = False
                            value_field.value = ""
                            msg_field.value = ""
                            self.update()

                        def confirm(e):
                            if not value_field.value.strip():
                                self.snackbar("Informe um valor para a doação.")
                                return
                            try:
                                amount = float(value_field.value.replace(",", "."))
                            except ValueError:
                                self.snackbar("Valor inválido.")
                                return

                            message = msg_field.value.strip() or "Doação feita"

                            payload = {
                                "DonorId": 0,
                                "ReceiverId": receiver_id,
                                "Amount": amount,
                                "Date": str(datetime.now()),
                                "Message": message,
                            }

                            print("Enviando doação:", payload)  # debug no console

                            res = api_add_donation(payload)
                            if res is None:
                                self.snackbar("Erro ao registrar doação.")
                            elif isinstance(res, dict) and res.get("error"):
                                self.snackbar(f"Erro ao registrar doação: {res.get('error')}")
                            else:
                                self.snackbar("Doação realizada com sucesso!")
                                controls_container.visible = False
                                value_field.value = ""
                                msg_field.value = ""

                            self.update()

                        return open_form, confirm, cancel

                    open_form, confirm, cancel = make_handlers(
                        rid, value_tf, msg_tf, donation_controls
                    )

                    confirm_btn = ft.ElevatedButton(
                        "Confirmar doação",
                        bgcolor=self.PRIMARY,
                        color=self.TEXT,
                        on_click=confirm,
                    )
                    cancel_btn = ft.TextButton(
                        "Cancelar",
                        on_click=cancel,
                        style=ft.ButtonStyle(color=self.ACCENT),
                    )

                    donation_controls.controls.extend(
                        [
                            value_tf,
                            msg_tf,
                            ft.Row(
                                [confirm_btn, cancel_btn],
                                alignment=ft.MainAxisAlignment.START,
                            ),
                        ]
                    )

                    donate_btn = ft.ElevatedButton(
                        "Doar",
                        bgcolor=self.PRIMARY,
                        color=self.TEXT,
                        on_click=open_form,
                    )

                    prod_list.append(
                        ft.Container(
                            bgcolor="#3b0057",
                            padding=10,
                            border_radius=10,
                            content=ft.Column(
                                [
                                    ft.Text(
                                        product_name,
                                        color="white",
                                        size=18,
                                    ),
                                    ft.Text(
                                        product_desc,
                                        color="white",
                                    ),
                                    ft.Text(
                                        f"Valor sugerido: R$ {product_value:.2f}",
                                        color="white",
                                    ),
                                    ft.Container(height=5),
                                    donate_btn,
                                    donation_controls,
                                ],
                                spacing=8,
                            ),
                        )
                    )

            expansion = ft.ExpansionTile(
                title=ft.Text(receptor_nome, size=20, color=self.TEXT),
                subtitle=ft.Text(receptor_desc, color=self.ACCENT),
                controls=prod_list
            )

            list_column.controls.append(
                ft.Card(
                    ft.Container(
                        content=expansion,
                        padding=15,
                        bgcolor=self.CARD_BG,
                        border_radius=15
                    ),
                    elevation=4
                )
            )

        self.container.controls.append(list_column)
        self.refresh_header()
        self.update()
    
       
def main(page: ft.Page):
    DonationApp(page)

if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.FLET_APP)
