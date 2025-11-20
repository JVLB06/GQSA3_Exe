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
    PRIMARY = "#8A2BE2"      # Roxo forte
    ACCENT = "#BA55D3"       # Roxo claro
    BG = "#0D0D0D"           # Fundo escuro geral
    CARD_BG = "#1A1A1A"      # Fundo dos cartões
    TEXT = "white"

    def __init__(self, page: ft.Page):
        self.page = page
        page.title = "Paraná — Sistema de Doações"
        page.window_width = 1000
        page.window_height = 700
        page.bgcolor = self.BG
        page.scroll = "auto"

        self.data = load_data()
        self.current_user = None

        self.header = ft.Row(
            [
                ft.Text("Sistema de Doações", style="headlineSmall", color=self.TEXT),
                ft.Container(expand=True)
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self.container = ft.Column()
        self.page.add(self.header, ft.Divider(color=self.PRIMARY), self.container)

        self.show_login()

    #Layout e Atualização conforme nxessario 
    def clear(self):
        self.container.controls.clear()

    def update(self):
        save_data(self.data)
        self.page.update()

    def snackbar(self, msg):
        self.page.snack_bar = ft.SnackBar(
            ft.Text(msg),
            open=True,
            bgcolor=self.PRIMARY,
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
                    self.snackbar(f"Bem-vindo(a), {user.get('name','')}")
                    self.show_home()
                    return
                fetched = api_get_user_by_email_and_merge(email.value.strip())
                if fetched:
                    self.current_user = fetched
                    self.snackbar(f"Bem-vindo(a), {fetched.get('name','')}")
                    self.show_home()
                    return
            u = find_user_local(self.data, email.value.strip())
            if not u or u["password"] != password.value:
                self.snackbar("E-mail ou senha inválidos")
                return
            self.current_user = u
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

        card = ft.Card(
            ft.Container(
                ft.Column(
                    [
                        ft.Text("💜 Sistema de Doações Paraná", style="headlineMedium", color=self.TEXT),
                        ft.Text("Ajuda humanitária aos desabrigados da cidade de Rio Bonito do Iguaçu", color=self.ACCENT),
                        ft.Divider(color=self.PRIMARY),
                        email,
                        password,
                        ft.Row([login_btn, register_btn], alignment=ft.MainAxisAlignment.CENTER),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15,
                ),
                padding=30,
                bgcolor=self.CARD_BG,
                border_radius=15,
                alignment=ft.alignment.center,
            ),
            elevation=8
        )

        self.container.controls.append(
            ft.Container(expand=True, alignment=ft.alignment.center, content=card)
        )
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
            ],
        )

        name = ft.TextField(label="Nome/Razão Social", width=400, color=self.TEXT)
        email = ft.TextField(label="E-mail", width=400, color=self.TEXT)
        cpf_cnpj = ft.TextField(label="CPF/CNPJ", width=400, color=self.TEXT)
        cep = ft.TextField(label="CEP", width=300, color=self.TEXT)
        password = ft.TextField(label="Senha", width=400, password=True, can_reveal_password=True, color=self.TEXT)
        description = ft.TextField(label="Motivo/Descrição", width=400, multiline=True, color=self.TEXT)

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

        card = ft.Card(
            ft.Container(
                ft.Column([
                    ft.Text("Registrar nova conta", style="titleLarge", color=self.TEXT),
                    role, name, email, cpf_cnpj, cep, password, description,
                    ft.Row([btn_register, btn_back])
                ]),
                padding=20,
                bgcolor=self.CARD_BG,
                border_radius=12
            ),
            elevation=2
        )

        self.container.controls.append(card)
        self.update()

    # HOME
    def show_home(self, e=None):
        self.clear()
        u = self.current_user

        top = ft.Row(
            [
                ft.Text(f"Logado como: {u['name']} ({u['role']})", color=self.TEXT),
                ft.Container(expand=True),
                ft.ElevatedButton("Sair", on_click=self.logout,
                                  style=ft.ButtonStyle(bgcolor=self.PRIMARY, color=self.TEXT))
            ]
        )

        self.container.controls.append(top)

        if u["role"] == "receptor":
            self.show_receptor_dashboard()
        elif u["role"] == "doador":
            self.show_donor_feed()
        elif u["role"] == "admin":
            self.show_admin_panel()

        self.update()

    def logout(self, e=None):
        self.current_user = None
        self.show_login()

    # RECEPTORES
    def show_receptor_dashboard(self):
        u = self.current_user

        pix_tf = ft.TextField(
            label="Chave PIX (para receber)",
            value=u.get("pix_key", ""),
            width=400,
            color=self.TEXT
        )

        def save_pix(ev):
            u["pix_key"] = pix_tf.value.strip()
            api_res = api_update_user(u["id"], u)
            if api_res is not None:
                self.data = load_data()
                self.snackbar("Chave PIX salva (via API).")
                return

            save_local_data(self.data)
            self.snackbar("Chave PIX salva (local).")

        btn_pix = ft.ElevatedButton(
            "Salvar PIX",
            on_click=save_pix,
            style=ft.ButtonStyle(bgcolor=self.PRIMARY, color=self.TEXT)
        )

        # COTAS
        title = ft.TextField(
            label="Título da cota",
            width=400,
            color=self.TEXT
        )

        value = ft.TextField(
            label="Valor (ex: 50.00)",
            width=200,
            color=self.TEXT
        )

        desc = ft.TextField(
            label="Descrição da cota",
            width=400,
            height=80,
            multiline=True,
            color=self.TEXT
        )

        # CRIAÇÃO DAS COTAS 
        def create_cause(ev):
            t = title.value.strip()
            v = value.value.strip().replace(",", ".")
            d = desc.value.strip()

            if not t or not v:
                self.snackbar("Título e valor são obrigatórios.")
                return

            try:
                v_float = float(v)
            except:
                self.snackbar("Valor inválido. Use apenas números, ex: 50.00")
                return

            new = {
                "id": str(uuid.uuid4()),
                "receptor_id": u["id"],
                "title": t,
                "description": d,
                "value": v_float
            }

            # tenta criar via API
            api_res = api_create_cause(new)
            if api_res is not None:
                self.data = load_data()
                title.value = ""
                value.value = ""
                desc.value = ""
                self.snackbar("Cota criada com sucesso (via API)!")
                self.show_home()
                return

            # fallback local
            self.data["causes"].append(new)
            save_local_data(self.data)

            title.value = ""
            value.value = ""
            desc.value = ""
            self.snackbar("Cota criada com sucesso (local)!")
            self.show_home()

        btn_create = ft.ElevatedButton(
            "Criar cota",
            on_click=create_cause,
            style=ft.ButtonStyle(bgcolor=self.PRIMARY, color=self.TEXT)
        )

        my_causes = [c for c in self.data["causes"] if c["receptor_id"] == u["id"]]
        causes_list = ft.Column()

        for c in my_causes:

            def delete_closure(cid):
                def delete(ev):
                    # tenta deletar via API
                    api_res = api_delete_cause(cid)
                    if api_res is not None:
                        self.data = load_data()
                        self.snackbar("Cota removida (via API).")
                        self.show_home()
                        return
                    # fallback local
                    self.data["causes"] = [x for x in self.data["causes"] if x["id"] != cid]
                    save_local_data(self.data)
                    self.snackbar("Cota removida (local).")
                    self.show_home()
                return delete

            card = ft.Card(
                ft.Container(
                    ft.Row([
                        ft.Column([
                            ft.Text(c["title"], style="titleMedium", color=self.TEXT),
                            ft.Text(f"Valor: R$ {c['value']:.2f}", color=self.TEXT),
                            ft.Text(c["description"], color=self.TEXT),
                        ], expand=True),
                        ft.ElevatedButton(
                            "Excluir",
                            on_click=delete_closure(c["id"]),
                            style=ft.ButtonStyle(bgcolor=self.ACCENT, color=self.TEXT)
                        )
                    ]),
                    padding=12,
                    bgcolor=self.CARD_BG
                ),
                elevation=1
            )

            causes_list.controls.append(card)

        self.container.controls.extend([
            ft.Text("Painel do Receptor", style="headlineSmall", color=self.TEXT),
            ft.Row([pix_tf, btn_pix]),
            ft.Divider(color=self.PRIMARY),

            ft.Text("Criar nova cota", style="titleMedium", color=self.TEXT),
            title, value, desc, btn_create,

            ft.Divider(color=self.PRIMARY),

            ft.Text("Minhas cotas", style="titleMedium", color=self.TEXT),
            causes_list
        ])

    # DOADORES
    def show_donor_feed(self):
        u = self.current_user

        self.container.controls.append(
            ft.Text("Feed de causas", style="headlineSmall", color=self.TEXT)
        )

        # tenta carregar causas da API 
        api_causes = api_get("/causes")
        if api_causes is not None and isinstance(api_causes, list):
            all_causes = sorted(api_causes, key=lambda x: x.get("title",""))
        else:
            all_causes = sorted(self.data["causes"], key=lambda x: x["title"])

        feed = ft.Column()

        for c in all_causes:
            receptor = get_user_by_id_local(self.data, c["receptor_id"]) or {"name": "—"}
            fav = c["id"] in u.get("favorites", [])

            fav_color = self.ACCENT if fav else self.CARD_BG

            def toggle(ev, cid=c["id"]):
                if cid in u.get("favorites", []):
                    u["favorites"].remove(cid)
                else:
                    u.setdefault("favorites", []).append(cid)
           
                api_res = api_update_user(u["id"], u)
                if api_res is not None:
                    self.data = load_data()
                    self.show_home()
                    return
                
                save_local_data(self.data)
                self.show_home()

            card = ft.Card(
                ft.Container(
                    ft.Row([
                        ft.Column([
                            ft.Text(c["title"], style="titleMedium", color=self.TEXT),
                            ft.Text(c["description"], color=self.TEXT),
                            ft.Text(f"Valor: R$ {c['value']:.2f}", color=self.TEXT),
                            ft.Text(f"Receptor: {receptor.get('name','')}", color=self.TEXT),
                        ], expand=True),
                        ft.Column([
                            ft.ElevatedButton(
                                "Desfavoritar" if fav else "Favoritar",
                                on_click=toggle,
                                style=ft.ButtonStyle(
                                    bgcolor=fav_color,
                                    color=self.TEXT,
                                    elevation=3,
                                    shape=ft.RoundedRectangleBorder(radius=12)
                                )
                            ),
                        ])
                    ]),
                    padding=12,
                    bgcolor=self.CARD_BG
                ),
                elevation=1
            )

            feed.controls.append(card)

        self.container.controls.append(feed)

    # ADMIN
    def show_admin_panel(self):
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
