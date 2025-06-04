from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.errors import InvalidId
import os

app = Flask(__name__)
app.secret_key = 'secreto'


# Conexão MongoDB
mongo_uri = os.getenv('MONGO_URI') or "mongodb+srv://figueiredoian7:24u1t00cN2Mesf6r@cluster1.bdw7trb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1"
client = MongoClient(mongo_uri)
db = client.meubanco
users_col = db.users

# Função para garantir que o admin exista no banco com senha hash
def garantir_admin():
    admin = users_col.find_one({"matricula": "123456"})
    if not admin:
        senha_hash = generate_password_hash("admin")
        users_col.insert_one({
            "matricula": "123456",
            "nome": "Administrador",
            "senha": senha_hash,
            "is_admin": True
        })
        print("Admin criado com senha hash")
    else:
        print("Admin já existe")

garantir_admin()


# Rota inicial
@app.route("/")
def index():
    return redirect("/login")

# Registro
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        matricula = request.form["matricula"]
        nome = request.form["nome"]
        senha = request.form["senha"]
        is_admin = request.form.get("is_admin") == "on"

        # Verifica se já existe usuário com essa matrícula
        if users_col.find_one({"matricula": matricula}):
            return "Usuário já existe."

        senha_hash = generate_password_hash(senha)
        users_col.insert_one({
            "matricula": matricula,
            "nome": nome,
            "senha": senha_hash,
            "is_admin": is_admin
        })
        return redirect("/login")

    return render_template("register.html")

# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None
    if request.method == "POST":
        matricula = request.form["matricula"]
        senha = request.form["senha"]

        usuario = users_col.find_one({"matricula": matricula})

        if usuario and check_password_hash(usuario["senha"], senha):
            session["usuario_id"] = str(usuario["_id"])
            session["is_admin"] = usuario.get("is_admin", False)
            if session["is_admin"]:
                return redirect("/admin")
            else:
                return redirect("/dashboard")
        else:
            erro = "Usuário ou senha inválidos."

    return render_template("login.html", erro=erro)

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "usuario_id" not in session or session.get("is_admin"):
        return redirect("/login")

    try:
        usuario = users_col.find_one({"_id": ObjectId(session["usuario_id"])})
    except InvalidId:
        session.clear()
        return redirect("/login")

    if not usuario:
        session.clear()
        return redirect("/login")

    # Dados fictícios para evitar erro no template
    meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio"]
    gastos = []
    total = 0.0
    mes_selecionado = None

    if request.method == "POST":
        mes_selecionado = request.form["mes"]

        # Aqui você buscaria os dados reais do banco baseado no mês e no usuário
        # Exemplo fictício:
        gastos = [
            ("01/05/2025", "Produto A", 29.99, 2),
            ("10/05/2025", "Produto B", 15.50, 1),
        ]
        total = sum(g[2] for g in gastos)

    return render_template(
        "client_dashboard.html",
        usuario=usuario,
        gastos=gastos,
        total=total,
        meses=meses,
        mes_selecionado=mes_selecionado
    )


# Admin
@app.route("/admin", endpoint="admin")
def admin_panel():
    if "usuario_id" not in session or not session.get("is_admin"):
        return redirect("/login")

    usuario = users_col.find_one({"_id": ObjectId(session["usuario_id"])})
    if not usuario:
        session.clear()
        return redirect("/login")

    # Exemplo de estruturas (ajuste conforme seu banco):
    produtos = db.produtos.find()  # Supondo que você tenha uma coleção 'produtos'
    compras_hoje = db.compras.find({"data": "03/06/2025"})  # ou use datetime.date.today().strftime("%d/%m/%Y")
    users = {u["matricula"]: u for u in users_col.find()}

    return render_template(
        "admin.html",
        usuario=usuario,
        produtos=produtos,
        compras_hoje=compras_hoje,
        users=users,
        meses=["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    )

# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# Esqueci senha
@app.route("/esqueci_senha", methods=["GET", "POST"])
def esqueci_senha():
    if request.method == "POST":
        matricula = request.form["matricula"]
        usuario = users_col.find_one({"matricula": matricula})
        if usuario:
            return redirect(f"/troca_senha?matricula={matricula}")
        else:
            return "Usuário não encontrado."
    return render_template("esqueci_senha.html")

# Troca senha
@app.route("/troca_senha", methods=["GET", "POST"])
def troca_senha():
    matricula = request.args.get("matricula")

    if request.method == "POST":
        nova_senha = request.form["nova_senha"]
        senha_hash = generate_password_hash(nova_senha)
        resultado = users_col.update_one({"matricula": matricula}, {"$set": {"senha": senha_hash}})
        if resultado.matched_count:
            return redirect("/login")
        else:
            return "Usuário não encontrado."

    return render_template("troca_senha.html", matricula=matricula)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
