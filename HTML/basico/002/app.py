"""Backend de demonstração para a página de login.

Execute "python app.py create-user" uma vez para criar um usuário e depois
"python app.py run" para iniciar o servidor local.
"""
import argparse
import getpass
import os
import secrets
import sqlite3
import time
from collections import defaultdict, deque
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, session, send_from_directory, url_for
from markupsafe import escape
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "usuarios.db"
MAX_ATTEMPTS = 5
WINDOW_SECONDS = 15 * 60
MAX_USERNAME_LENGTH = 50
MAX_PASSWORD_LENGTH = 256

# O arquivo login.html fica na mesma pasta deste app.
app = Flask(__name__, template_folder=str(BASE_DIR))
app.config.update(
    SECRET_KEY=os.environ.get("APP_SECRET_KEY") or secrets.token_urlsafe(32),
    MAX_CONTENT_LENGTH=16 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    # Em produção use HTTPS e defina APP_HTTPS=1.
    SESSION_COOKIE_SECURE=os.environ.get("APP_HTTPS") == "1",
)

# Armazenamento temporário do limite de tentativas. Para vários servidores,
# substitua por Redis ou outro armazenamento compartilhado.
tentativas = defaultdict(deque)
DUMMY_HASH = generate_password_hash("senha-inexistente")


def conexao():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


def iniciar_banco():
    with conexao() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY,
                usuario TEXT NOT NULL UNIQUE COLLATE NOCASE,
                senha_hash TEXT NOT NULL
            )
        """)


def chave_cliente():
    # Não aceite X-Forwarded-For sem configurar um proxy confiável.
    return request.remote_addr or "desconhecido"


def bloqueado(chave):
    agora = time.time()
    fila = tentativas[chave]
    while fila and agora - fila[0] > WINDOW_SECONDS:
        fila.popleft()
    return len(fila) >= MAX_ATTEMPTS


def registrar_falha(chave):
    tentativas[chave].append(time.time())


def token_csrf():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def csrf_valido():
    enviado = request.form.get("csrf_token", "")
    esperado = session.get("csrf_token", "")
    return bool(esperado) and secrets.compare_digest(enviado, esperado)


@app.after_request
def cabecalhos_seguros(resposta):
    resposta.headers["X-Content-Type-Options"] = "nosniff"
    resposta.headers["X-Frame-Options"] = "DENY"
    resposta.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    resposta.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self'"
    return resposta


@app.get("/")
def pagina_login():
    return render_template("login.html", csrf_token=token_csrf(), erro=None)


@app.get("/login.css")
def folha_estilos():
    return send_from_directory(BASE_DIR, "login.css")


@app.post("/login")
def login():
    if not csrf_valido():
        abort(400, "Requisição inválida.")

    usuario = request.form.get("usuario", "").strip()
    senha = request.form.get("senha", "")
    cliente = chave_cliente()

    if (not usuario or len(usuario) > MAX_USERNAME_LENGTH or
            not senha or len(senha) > MAX_PASSWORD_LENGTH or bloqueado(cliente)):
        registrar_falha(cliente)
        return render_template("login.html", csrf_token=token_csrf(),
                               erro="Usuário ou senha inválidos."), 401

    with conexao() as db:
        registro = db.execute(
            "SELECT id, usuario, senha_hash FROM usuarios WHERE usuario = ?", (usuario,)
        ).fetchone()

    # O hash fictício evita revelar, pelo tempo de resposta, se o usuário existe.
    hash_senha = registro["senha_hash"] if registro else DUMMY_HASH
    senha_correta = check_password_hash(hash_senha, senha)
    if registro is None or not senha_correta:
        registrar_falha(cliente)
        return render_template("login.html", csrf_token=token_csrf(),
                               erro="Usuário ou senha inválidos."), 401

    tentativas.pop(cliente, None)
    session.clear()                 # impede fixação de sessão
    session["usuario_id"] = registro["id"]
    session["usuario"] = registro["usuario"]
    return redirect(url_for("area_restrita"), code=303)


@app.get("/area-restrita")
def area_restrita():
    if "usuario_id" not in session:
        return redirect(url_for("pagina_login"), code=303)
    return f"<h1>Bem-vindo, {escape(session['usuario'])}!</h1><p>Login realizado.</p>"


def criar_usuario():
    iniciar_banco()
    usuario = input("Usuário: ").strip()
    senha = getpass.getpass("Senha: ")
    if not usuario or len(usuario) > MAX_USERNAME_LENGTH or not senha or len(senha) > MAX_PASSWORD_LENGTH:
        raise SystemExit("Usuário ou senha inválidos.")
    try:
        with conexao() as db:
            db.execute("INSERT INTO usuarios (usuario, senha_hash) VALUES (?, ?)",
                       (usuario, generate_password_hash(senha)))
    except sqlite3.IntegrityError:
        raise SystemExit("Este usuário já existe.")
    print("Usuário criado com sucesso.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("comando", choices=["run", "create-user"])
    args = parser.parse_args()
    if args.comando == "create-user":
        criar_usuario()
    else:
        iniciar_banco()
        app.run(host="127.0.0.1", port=5000, debug=False)
