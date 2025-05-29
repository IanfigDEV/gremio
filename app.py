from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import os

# Configurações básicas do Flask
app = Flask(__name__)
app.secret_key = 'secreto'

# Configurações do banco de dados
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'banco.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa o SQLAlchemy
db = SQLAlchemy(app)

# Modelo de usuário
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    matricula = db.Column(db.String(50), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    senha = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

# Rota inicial
@app.route("/")
def index():
    return redirect("/login")

# Registro de novo usuário
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        matricula = request.form["matricula"]
        nome = request.form["nome"]
        senha = request.form["senha"]
        is_admin = request.form.get("is_admin") == "on"

        if Usuario.query.filter_by(matricula=matricula).first():
            return "Usuário já existe."

        senha_hash = generate_password_hash(senha)
        novo_usuario = Usuario(matricula=matricula, nome=nome, senha=senha_hash, is_admin=is_admin)
        db.session.add(novo_usuario)
        db.session.commit()
        return redirect("/login")

    return render_template("register.html")

# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None
    if request.method == "POST":
        matricula = request.form["matricula"]
        senha = request.form["senha"]

        usuario = Usuario.query.filter_by(matricula=matricula).first()
        if usuario and check_password_hash(usuario.senha, senha):
            session["usuario_id"] = usuario.id
            if usuario.is_admin:
                return redirect("/admin")
            else:
                return redirect("/dashboard")
        else:
            erro = "Usuário ou senha inválidos."

    return render_template("login.html", erro=erro)

# Dashboard para cliente
@app.route("/dashboard")
def dashboard():
    if "usuario_id" not in session:
        return redirect("/login")

    usuario = Usuario.query.get(session["usuario_id"])
    if not usuario or usuario.is_admin:
        session.pop("usuario_id", None)
        return redirect("/login")

    return render_template("client_dashboard.html", usuario=usuario)

# Painel do admin
@app.route("/admin")
def admin():
    if "usuario_id" not in session:
        return redirect("/login")

    usuario = Usuario.query.get(session["usuario_id"])
    if not usuario or not usuario.is_admin:
        session.pop("usuario_id", None)
        return redirect("/login")

    return render_template("admin.html", usuario=usuario)

# Logout
@app.route("/logout")
def logout():
    session.pop("usuario_id", None)
    return redirect("/login")

# Esqueci minha senha
@app.route("/esqueci_senha", methods=["GET", "POST"])
def esqueci_senha():
    if request.method == "POST":
        matricula = request.form["matricula"]
        usuario = Usuario.query.filter_by(matricula=matricula).first()
        if usuario:
            return redirect(f"/troca_senha?matricula={matricula}")
        else:
            return "Usuário não encontrado."
    return render_template("esqueci_senha.html")

# Troca de senha
@app.route("/troca_senha", methods=["GET", "POST"])
def troca_senha():
    matricula = request.args.get("matricula")

    if request.method == "POST":
        nova_senha = request.form["nova_senha"]
        usuario = Usuario.query.filter_by(matricula=matricula).first()

        if usuario:
            usuario.senha = generate_password_hash(nova_senha)
            db.session.commit()
            return redirect("/login")
        else:
            return "Usuário não encontrado."

    return render_template("troca_senha.html", matricula=matricula)

# Execução do app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=3000, debug=True)