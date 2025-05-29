from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

app = Flask(__name__)
app.secret_key = 'secreto'

# Conexão MongoDB (pegue a string da variável de ambiente no Render)
mongo_uri = os.getenv('MONGO_URI') or "mongodb+srv://figueiredoian7:2233@cluster1.bdw7trb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1"
client = MongoClient(mongo_uri)
db = client.meubanco

users_col = db.users  # coleção users

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

# Dashboard cliente
@app.route("/dashboard")
def dashboard():
    if "usuario_id" not in session or session.get("is_admin"):
        return redirect("/login")
    usuario = users_col.find_one({"_id": ObjectId(session["usuario_id"])})
    if not usuario:
        session.clear()
        return redirect("/login")

    return render_template("client_dashboard.html", usuario=usuario)

# Admin
@app.route("/admin")
def admin():
    if "usuario_id" not in session or not session.get("is_admin"):
        return redirect("/login")
    usuario = users_col.find_one({"_id": ObjectId(session["usuario_id"])})
    if not usuario:
        session.clear()
        return redirect("/login")

    return render_template("admin.html", usuario=usuario)

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
