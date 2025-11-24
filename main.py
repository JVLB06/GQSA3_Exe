import flet as ft
import json
import os
import uuid
import tempfile
import requests
from requests.exceptions import RequestException

API_URL = "http://localhost:8000"  # padrão 
DATA_FILE = os.path.join(tempfile.gettempdir(), "donation_temp.json")  # fallback temporário local
REQ_TIMEOUT = 0.1  # segundos para timeout de requisições (evita travar muito a UI)

#UTILITÁRIOS API / FALLBACK 

def api_get(path):
    try:
        r = requests.get(f"{API_URL}{path}", timeout=REQ_TIMEOUT)
        if r.status_code == 200:
            return r.json()
        return None
    except RequestException:
        return None

def api_post(path, payload):
    try:
        r = requests.post(f"{API_URL}{path}", json=payload, timeout=REQ_TIMEOUT)
        if 200 <= r.status_code < 300:
            try:
                return r.json()
            except Exception:
                return {"status": "ok"}
        return None
    except RequestException:
        return None

def api_put(path, payload):
    try:
        r = requests.put(f"{API_URL}{path}", json=payload, timeout=REQ_TIMEOUT)
        if 200 <= r.status_code < 300:
            try:
                return r.json()
            except Exception:
                return {"status": "ok"}
        return None
    except RequestException:
        return None

def api_delete(path):
    try:
        r = requests.delete(f"{API_URL}{path}", timeout=REQ_TIMEOUT)
        if 200 <= r.status_code < 300:
            try:
                return r.json()
            except Exception:
                return {"status": "ok"}
        return None
    except RequestException:
        return None

#LOCAL (FALLBACK)

def load_local_data():
    if not os.path.exists(DATA_FILE):
        data = {"users": [], "causes": []}
        admin = {
            "id": str(uuid.uuid4()),
            "role": "admin",
            "name": "Administrador",
            "email": "admin@local",
            "cpf_cnpj": "",
            "cep": "",
            "password": "admin",
            "description": "Conta administradora",
            "pix_key": "",
            "favorites": []
        }
        data["users"].append(admin)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return data

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_local_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

#CAMADA DE DADOS tenta API se não obtiver resposta tenta O LOCAL

def load_data():
    api_res = api_get("/data")
    if api_res is not None:
        return api_res
    # fallback local
    return load_local_data()

def save_data(data):
    api_res = api_put("/data", data)
    if api_res is not None:
        return True
    # fallback local
    save_local_data(data)
    return True

def find_user_local(data, email):
    for u in data["users"]:
        if u["email"].lower() == email.lower():
            return u
    return None

def get_user_by_id_local(data, uid):
    for u in data["users"]:
        if u["id"] == uid:
            return u
    return None

def find_cause_local(data, cid):
    for c in data["causes"]:
        if c["id"] == cid:
            return c
    return None

#API (usada antes do fallback) 

def api_register_user(user_dict):
    return api_post("/users", user_dict)

def api_login(email, password):
    return api_post("/auth/login", {"email": email, "password": password})

def api_get_all_causes():
    return api_get("/causes")

def api_create_cause(cause_dict):
    return api_post("/causes", cause_dict)

def api_delete_cause(cid):
    return api_delete(f"/causes/{cid}")

def api_update_user(uid, user_dict):
    return api_put(f"/users/{uid}", user_dict)

def api_delete_user(uid):
    return api_delete(f"/users/{uid}")

def api_get_user_by_email(email):
    res = api_get(f"/users?email={email}")
    if res is None:
        # tenta GET /users/{email} (algumas APIs usam isso)
        res = api_get(f"/users/{email}")
    return res

#Aplicação Flet (UI)

class DonationApp:
    PRIMARY = "#8A2BE2"      # Roxo forte (botão Sair usa esta cor, conforme pediu)
    ACCENT = "#BA55D3"       # Roxo claro
    BG = "#FFFFFF"           # fundo da página
    CARD_BG = "#26023F"      # Fundo dos cartões
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
            "Poppins": "assets/fonts/Poppins-Regular.ttf",
            "PoppinsBold": "assets/fonts/Poppins-Bold.ttf"
        }

        page.theme = ft.Theme(
            font_family="Poppins"
        )

        self.data = load_data()
        self.current_user = None

        self.container = ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True
        )

        self.header = self.build_header()

        self.main_column = ft.Column(
            [
                self.header,
                ft.Container(
                    expand=True,
                    alignment=ft.alignment.center,
                    content=self.container
                )
            ],
            spacing=0,
            expand=True
        )

        bg_image_path = "assets/01.png"

        self.page.add(
            ft.Stack(
                [
                    ft.Container(
                        expand=True,
                        content=ft.Image(
                            src=bg_image_path,
                            fit=ft.ImageFit.FILL,
                            expand=True
                        )
                    ),
                    self.main_column
                ],
                expand=True
            )
        )

        self.show_login()

    def build_header(self):
        if self.current_user:
            return ft.Container(
                content=ft.Row(
                    [
                        ft.Text(
                            "Sistema de Doações",
                            size=24,
                            color="white",
                            font_family="PoppinsBold",
                        ),
                        ft.Container(expand=True),
                        ft.Text(
                            f"Logado como: {self.current_user.get('name','')} ({self.current_user.get('role','')})",
                            color="white",
                            size=14
                        ),
                        ft.Container(width=10),
                        ft.ElevatedButton(
                            "Sair",
                            on_click=self.logout,
                            style=ft.ButtonStyle(bgcolor=self.PRIMARY, color="white")
                        )
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                bgcolor=self.CARD_BG,
                padding=ft.padding.symmetric(horizontal=20),
                height=70,
                expand=True,
                alignment=ft.alignment.center_left,
                margin=ft.margin.all(0),
            )
        else:
            return ft.Container(
                content=ft.Row(
                    [
                        ft.Text(
                            "Sistema de Doações",
                            size=28,
                            color="white",
                            font_family="PoppinsBold",
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                bgcolor=self.CARD_BG,
                padding=ft.padding.symmetric(horizontal=20),
                height=70,
                expand=True,
                alignment=ft.alignment.center_left,
                margin=ft.margin.all(0),
            )

    def refresh_header(self):
        try:
            self.main_column.controls[0] = self.build_header()
            self.page.update()
        except Exception:
            # fallback: re-add main layout
            pass

    #Layout e Atualização 
    def clear(self):
        self.container.controls.clear()

    def update(self):
        save_data(self.data)
        self.page.update()

    def snackbar(self, msg):
        self.page.snack_bar = ft.SnackBar(
            ft.Text(msg),
            open=True,
            bgcolor=self.CARD_BG,
        )
        self.page.update()

    # LOGIN
    def show_login(self, e=None):
        self.clear()

        email = ft.TextField(label="E-mail", width=350, color=self.TEXT,
                             border_color=self.PRIMARY, focused_border_color=self.ACCENT)

        password = ft.TextField(label="Senha", width=350, password=True,
                                can_reveal_password=True, color=self.TEXT,
                                border_color=self.PRIMARY, focused_border_color=self.ACCENT)

        def do_login(ev):

            api_res = api_login(email.value.strip(), password.value)
            if api_res is not None:
                user = api_res.get("user") if isinstance(api_res, dict) else None
                if user:
                    self.current_user = user
                    # atualiza o header agora que temos usuário
                    self.refresh_header()
                    self.snackbar(f"Bem-vindo(a), {user.get('name','')}")
                    self.show_home()
                    return
                fetched = api_get_user_by_email_and_merge(email.value.strip())
                if fetched:
                    self.current_user = fetched
                    self.refresh_header()
                    self.snackbar(f"Bem-vindo(a), {fetched.get('name','')}")
                    self.show_home()
                    return
            u = find_user_local(self.data, email.value.strip())
            if not u or u["password"] != password.value:
                self.snackbar("E-mail ou senha inválidos")
                return
            self.current_user = u
            self.refresh_header()
            self.snackbar(f"Bem-vindo(a), {u['name']}")
            self.show_home()

        login_btn = ft.ElevatedButton(
            "Entrar", on_click=do_login,
            width=150,
            style=ft.ButtonStyle(bgcolor=self.PRIMARY, color=self.TEXT)
        )

        register_btn = ft.TextButton(
            "Criar conta",
            on_click=lambda e: self.show_register(),
            style=ft.ButtonStyle(color=self.ACCENT)
        )

        card_inner = ft.Container(
            ft.Column(
                [
                    ft.Text(
                        "Sistema de Doações Paraná",
                        style="headlineMedium",
                        color=self.TEXT,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Text(
                        "Plataforma de auxílio às vítimas do tornado em Rio Bonito do Iguaçu, "
                        "conectamos voluntários e doadores de forma rápida e transparente.",
                        color=self.ACCENT,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Divider(color=self.PRIMARY),
                    email,
                    password,
                    ft.Row([login_btn, register_btn],
                        alignment=ft.MainAxisAlignment.CENTER),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15,
            ),
            padding=30,
            bgcolor=self.CARD_BG,
            border_radius=15,
            alignment=ft.alignment.center,
            width=500,
        )

        card = ft.Card(card_inner, elevation=8, margin=ft.margin.only(top=80))

        self.container.controls.append(card)
        # header já está no estado correto aqui (não-logado)
        self.update()

    # REGISTRO
    def show_register(self, e=None):
        self.clear()

        role = ft.Dropdown(
            label="Tipo de conta",
            width=300,
            value="doador",
            options=[
                ft.dropdown.Option("doador", "Doador"),
                ft.dropdown.Option("receptor", "Receptor")
            ]
            ,
            border_color=self.PRIMARY, focused_border_color=self.ACCENT,
        )

        name = ft.TextField(label="Nome/Razão Social", width=400, color=self.TEXT,
                                border_color=self.PRIMARY, focused_border_color=self.ACCENT)
        email = ft.TextField(label="E-mail", width=400, color=self.TEXT,
                                border_color=self.PRIMARY, focused_border_color=self.ACCENT)
        cpf_cnpj = ft.TextField(label="CPF/CNPJ", width=400, color=self.TEXT,
                                border_color=self.PRIMARY, focused_border_color=self.ACCENT)
        cep = ft.TextField(label="CEP", width=300, color=self.TEXT,
                                border_color=self.PRIMARY, focused_border_color=self.ACCENT)
        password = ft.TextField(label="Senha", width=400, password=True, can_reveal_password=True, color=self.TEXT,
                                border_color=self.PRIMARY, focused_border_color=self.ACCENT)
        description = ft.TextField(label="Motivo/Descrição", width=400, multiline=True, color=self.TEXT,
                                border_color=self.PRIMARY, focused_border_color=self.ACCENT)

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

            # tenta registrar via API primeiro
            new_user = {
                "id": str(uuid.uuid4()),
                "role": role.value,
                "name": name.value.strip(),
                "email": email.value.strip(),
                "cpf_cnpj": cpf_cnpj.value.strip() if role.value == "receptor" else "",
                "cep": cep.value.strip() if role.value == "receptor" else "",
                "password": password.value,
                "description": description.value.strip() if role.value == "receptor" else "",
                "pix_key": "",
                "favorites": []
            }

            api_res = api_register_user(new_user)
            if api_res is not None:
                reloaded = load_data()
                if reloaded:
                    self.data = reloaded
                self.snackbar("Cadastro realizado com sucesso (via API).")
                self.show_login()
                return

            if find_user_local(self.data, new_user["email"]):
                self.snackbar("Este e-mail já está cadastrado.")
                return

            self.data["users"].append(new_user)
            save_local_data(self.data)
            self.snackbar("Cadastro realizado com sucesso (local).")
            self.show_login()

        btn_register = ft.ElevatedButton("Registrar", on_click=do_register,
                                         style=ft.ButtonStyle(bgcolor=self.PRIMARY, color=self.TEXT))

        btn_back = ft.TextButton("Voltar", on_click=lambda e: self.show_login(),
                                 style=ft.ButtonStyle(color=self.ACCENT))

        card_inner = ft.Container(
            ft.Column(
                [
                    ft.Text(
                        "Registrar nova conta",
                        style="headlineMedium",
                        color=self.TEXT
                    ),
                    ft.Text(
                        "Preencha os dados para criar sua conta",
                        color=self.ACCENT,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Divider(color=self.PRIMARY),
                    role,
                    name,
                    email,
                    cpf_cnpj,
                    cep,
                    password,
                    description,
                    ft.Row([btn_register, btn_back], alignment=ft.MainAxisAlignment.CENTER),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15,
            ),
            padding=30,
            bgcolor=self.CARD_BG,
            border_radius=15,
            alignment=ft.alignment.center,
            width=500,
        )

        card = ft.Card(card_inner, elevation=8, margin=ft.margin.only(top=80))

        self.container.controls.append(card)
        self.update()

    # HOME
    def show_home(self, e=None):
        self.clear()
        u = self.current_user

        if u["role"] == "receptor":
            self.show_receptor_dashboard()
        elif u["role"] == "doador":
            self.show_donor_feed()
        elif u["role"] == "admin":
            self.show_admin_panel()

        self.refresh_header()
        self.update()

    def logout(self, e=None):
        self.current_user = None
        self.refresh_header()
        self.show_login()

    # RECEPTORES
    def show_receptor_dashboard(self):
        u = self.current_user

        self.clear()

        # Card de edição da chave PIX
        pix_tf = ft.TextField(
            label="Chave PIX",
            value=u.get("pix_key", ""),
            width=400,
            color=self.TEXT,
            border_color=self.PRIMARY, focused_border_color=self.ACCENT
        )

        def save_pix(ev):
            u["pix_key"] = pix_tf.value.strip()
            api_res = api_update_user(u["id"], u)
            if api_res:
                self.data = load_data()
            else:
                save_local_data(self.data)
            self.snackbar("Chave PIX atualizada!")

        pix_card = ft.Card(
            ft.Container(
                ft.Column(
                    [
                        ft.Text("Informações de Recebimento", style="headlineSmall", color=self.TEXT),
                        ft.Divider(color=self.PRIMARY),
                        pix_tf,
                        ft.Row(
                            [
                                ft.ElevatedButton(
                                    "Salvar PIX",
                                    on_click=save_pix,
                                    style=ft.ButtonStyle(bgcolor=self.PRIMARY, color=self.TEXT)
                                )
                            ],
                            alignment=ft.MainAxisAlignment.CENTER
                        )
                    ],
                    spacing=15,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                padding=25,
                bgcolor=self.CARD_BG,
                border_radius=15,
                width=550
            ),
            elevation=4,
            margin=ft.margin.only(bottom=25, top=15)
        )
        self.container.controls.append(pix_card)

        # Card de criação de cotas
        title = ft.TextField(label="Título da Cota", width=400, color=self.TEXT,
                                border_color=self.PRIMARY, focused_border_color=self.ACCENT)
        value = ft.TextField(label="Valor (ex: 50.00)", width=400, color=self.TEXT,
                                border_color=self.PRIMARY, focused_border_color=self.ACCENT)
        desc = ft.TextField(label="Descrição", width=400, multiline=True, height=100, color=self.TEXT,
                                border_color=self.PRIMARY, focused_border_color=self.ACCENT)

        def create_cause(ev):
            t = title.value.strip()
            v = value.value.strip().replace(",", ".")
            d = desc.value.strip()

            if not t or not v:
                self.snackbar("Preencha título e valor.")
                return

            try:
                v_float = float(v)
            except:
                self.snackbar("Valor inválido. Ex: 50.00")
                return

            new_cause = {
                "id": str(uuid.uuid4()),
                "receptor_id": u["id"],
                "title": t,
                "description": d,
                "value": v_float
            }

            api_res = api_create_cause(new_cause)
            if api_res:
                self.data = load_data()
            else:
                self.data["causes"].append(new_cause)
                save_local_data(self.data)

            title.value = ""
            value.value = ""
            desc.value = ""
            self.snackbar("Cota criada com sucesso!")
            self.show_home()

        create_cause_card = ft.Card(
            ft.Container(
                ft.Column(
                    [
                        ft.Text("Criar nova Cota", style="headlineMedium", color=self.TEXT),
                        ft.Text("Preencha os dados da cota para publicá-la", color=self.ACCENT),
                        ft.Divider(color=self.PRIMARY),
                        title,
                        value,
                        desc,
                        ft.Row(
                            [ft.ElevatedButton("Criar Cota", on_click=create_cause,
                                            style=ft.ButtonStyle(bgcolor=self.PRIMARY, color=self.TEXT))],
                            alignment=ft.MainAxisAlignment.CENTER
                        )
                    ],
                    spacing=15,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                padding=25,
                bgcolor=self.CARD_BG,
                border_radius=15,
                width=550
            ),
            elevation=4,
            margin=ft.margin.only(bottom=25)
        )
        self.container.controls.append(create_cause_card)

        # Minhas cotas (lista)
        my_causes = [c for c in self.data["causes"] if c["receptor_id"] == u["id"]]
        list_column = ft.Column(spacing=10)

        for c in my_causes:
            def delete_factory(cid):
                def delete(ev):
                    api_res = api_delete_cause(cid)
                    if api_res:
                        self.data = load_data()
                    else:
                        self.data["causes"] = [x for x in self.data["causes"] if x["id"] != cid]
                        save_local_data(self.data)
                    self.snackbar("Cota removida.")
                    self.show_home()
                return delete

            item = ft.Card(
                ft.Container(
                    ft.Column(
                        [
                            ft.Text(c["title"], style="titleMedium", color=self.TEXT),
                            ft.Text(f"R$ {c['value']:.2f}", color=self.TEXT),
                            ft.Text(c["description"], color=self.TEXT),
                            ft.Row(
                                [
                                    ft.ElevatedButton(
                                        "Excluir",
                                        on_click=delete_factory(c["id"]),
                                        style=ft.ButtonStyle(bgcolor=self.ACCENT, color=self.TEXT)
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.END
                            )
                        ],
                        spacing=8
                    ),
                    padding=15,
                    bgcolor=self.CARD_BG,
                    border_radius=10
                ),
                elevation=2
            )

            list_column.controls.append(item)

        list_card = ft.Card(
            ft.Container(
                ft.Column(
                    [
                        ft.Text("Minhas Cotas Publicadas", style="headlineSmall", color=self.TEXT),
                        ft.Divider(color=self.PRIMARY),
                        list_column
                    ],
                    spacing=15
                ),
                padding=25,
                bgcolor=self.CARD_BG,
                border_radius=15,
                width=650
            ),
            elevation=4
        )

        self.container.controls.append(list_card)
        self.refresh_header()
        self.update()


    # DOADORES
    def show_donor_feed(self):
        u = self.current_user

        self.clear()

        self.container.controls.append(
            ft.Container(
                content=ft.Text(
                    "Feed de causas",
                    color=self.TEXT,
                    font_family="PoppinsBold",
                    size=22
                ),
                padding=10,
                bgcolor=self.CARD_BG,
                border_radius=10,
                margin=ft.margin.only(bottom=25, top=15)
            )
        )

        api_causes = api_get("/causes")
        if api_causes is not None and isinstance(api_causes, list):
            causes = sorted(api_causes, key=lambda x: x.get("title", ""))
        else:
            causes = sorted(self.data["causes"], key=lambda x: x["title"])

        rows = ft.Column(spacing=12)

        cols = 3
        card_width = 260

        for i in range(0, len(causes), cols):
            line = causes[i:i+cols]
            row_items = []

            for c in line:
                receptor = get_user_by_id_local(self.data, c["receptor_id"]) or {"name": "—"}
                fav = c["id"] in u.get("favorites", [])
                fav_text = "Desfavoritar" if fav else "Favoritar"
                fav_color = self.ACCENT if fav else self.CARD_BG

                def toggle_factory(cid):
                    def toggle(ev):
                        if cid in u.get("favorites", []):
                            u["favorites"].remove(cid)
                        else:
                            u.setdefault("favorites", []).append(cid)

                        api_res = api_update_user(u["id"], u)
                        if api_res:
                            self.data = load_data()
                            self.show_home()
                            return

                        save_local_data(self.data)
                        self.show_home()
                    return toggle

                toggle_fn = toggle_factory(c["id"])

                card = ft.Card(
                    ft.Container(
                        ft.Column(
                            [
                                ft.Text(c["title"], style="titleMedium", color=self.TEXT, text_align=ft.TextAlign.CENTER),
                                ft.Text(c["description"], color=self.TEXT, max_lines=2, overflow="ellipsis", text_align=ft.TextAlign.CENTER),
                                ft.Text(f"Valor: R$ {c['value']:.2f}", color=self.TEXT, text_align=ft.TextAlign.CENTER),
                                ft.Text(f"Receptor: {receptor['name']}", color=self.TEXT, text_align=ft.TextAlign.CENTER),
                                ft.ElevatedButton(
                                    fav_text,
                                    on_click=toggle_fn,
                                    width=150,
                                    style=ft.ButtonStyle(bgcolor=fav_color, color=self.TEXT)
                                )
                            ],
                            spacing=5,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER
                        ),
                        padding=12,
                        bgcolor=self.CARD_BG,
                        width=card_width,
                        height=220,
                        border_radius=15
                    ),
                    elevation=2,
                )

                row_items.append(card)

            while len(row_items) < cols:
                row_items.append(ft.Container(width=card_width))

            rows.controls.append(
                ft.Row(row_items, alignment=ft.MainAxisAlignment.CENTER)
            )

        self.container.controls.append(rows)
        self.refresh_header()
        self.update()

    # ADMIN
    def show_admin_panel(self):
        self.clear()
        self.container.controls.append(ft.Text("Painel do Administrador",style="headlineSmall", color=self.TEXT))

        users_list = ft.Column()

        for user in self.data["users"]:

            def delete(ev, uid=user["id"]):
                if uid == self.current_user["id"]:
                    self.snackbar("Você não pode excluir a si mesmo.")
                    return
                
                api_res = api_delete_user(uid)
                if api_res is not None:
                    self.data = load_data()
                    self.snackbar("Usuário removido (via API).")
                    self.show_home()
                    return

                
                self.data["users"] = [x for x in self.data["users"] if x["id"] != uid]
                self.data["causes"] = [x for x in self.data["causes"] if x.get("receptor_id") != uid]
                save_local_data(self.data)
                self.snackbar("Usuário removido (local).")
                self.show_home()

            card = ft.Card(
                ft.Container(
                    ft.Row([
                        ft.Column([
                            ft.Text(user["name"], style="titleMedium", color=self.TEXT),
                            ft.Text(f"{user['email']} — {user['role']}", color=self.TEXT)
                        ], expand=True),
                        ft.Column([
                            ft.ElevatedButton("Excluir",
                                              on_click=delete,
                                              style=ft.ButtonStyle(bgcolor=self.ACCENT, color=self.TEXT))
                        ])
                    ]),
                    padding=10,
                    bgcolor=self.CARD_BG
                ),
                elevation=1
            )

            users_list.controls.append(card)

        self.container.controls.append(users_list)
        self.refresh_header()
        self.update()


def api_get_user_by_email_and_merge(email):
    res = api_get(f"/users?email={email}")
    if res is None:
        res = api_get(f"/users/{email}")
    if isinstance(res, list) and len(res) > 0:
        return res[0]
    if isinstance(res, dict):
        return res
    return None



def main(page: ft.Page):
    DonationApp(page)

if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.FLET_APP)
