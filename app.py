import json
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "clave_secreta"  # Cambiar en producción

DB_FILE = "datos.json"
#esta es una actualización para probar el proyecto
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f:
        usuarios = json.load(f)
else:
    usuarios = {}

def guardar_datos():
    with open(DB_FILE, "w") as f:
        json.dump(usuarios, f, indent=4)

@app.route('/')
def home():
    if "usuario" in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form["correo"]
        password = request.form["password"]
        user = usuarios.get(correo)

        if user and check_password_hash(user["password"], password):
            session["usuario"] = correo
            return redirect(url_for('dashboard'))
        else:
            flash("Correo o contraseña incorrectos")
    return render_template("login.html")

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nombre = request.form["nombre"]
        correo = request.form["correo"]
        password = generate_password_hash(request.form["password"])

        if correo in usuarios:
            flash("El usuario ya está registrado. Inicia sesión.")
            return redirect(url_for('login'))

        usuarios[correo] = {
            "nombre": nombre,
            "password": password,
            "datos": {
                "sueldo": None,
                "gastos_categorias": {
                    "Alimentación": [],
                    "Transporte": [],
                    "Ocio": [],
                    "Otros": []
                }
            }
        }
        guardar_datos()
        flash("Registro exitoso, ahora inicia sesión.")
        return redirect(url_for('login'))
    return render_template("registro.html")

@app.route('/dashboard', methods=["GET", "POST"])
def dashboard():
    if "usuario" not in session:
        return redirect(url_for('login'))

    correo = session["usuario"]

    if correo not in usuarios:
        session.pop("usuario", None)
        flash("Tu cuenta no se encuentra registrada. Vuelve a iniciar sesión.")
        return redirect(url_for('login'))

    user = usuarios[correo]
    sueldo = user["datos"].get("sueldo")

    if request.method == "POST":
        # Guardar sueldo si se envía
        if "sueldo" in request.form and request.form["sueldo"]:
            sueldo = float(request.form["sueldo"])
            user["datos"]["sueldo"] = sueldo

        # Guardar gasto si se envía
        if "gasto" in request.form and request.form["gasto"]:
            gasto = float(request.form["gasto"])
            categoria = request.form["categoria"]
            user["datos"]["gastos_categorias"][categoria].append(gasto)

        guardar_datos()
        flash("Datos actualizados correctamente.")
        return redirect(url_for('dashboard'))

    categorias = list(user["datos"]["gastos_categorias"].keys())
    gastos_por_categoria = [sum(vals) for vals in user["datos"]["gastos_categorias"].values()]
    gastos_totales = sum(gastos_por_categoria)
    ahorro = sueldo - gastos_totales if sueldo else 0

    gastos_categoria = user["datos"]["gastos_categorias"]

    return render_template(
        "dashboard.html",
        nombre=user["nombre"],
        sueldo=sueldo,
        ahorro=ahorro,
        categorias=categorias,
        gastos_por_categoria=gastos_por_categoria,
        gastos_totales=gastos_totales,
        gastos_categoria=gastos_categoria
    )

@app.route('/reset_datos', methods=['POST'])
def reset_datos():
    if "usuario" not in session:
        return redirect(url_for('login'))

    correo = session["usuario"]
    if correo in usuarios:
        usuarios[correo]["datos"] = {
            "sueldo": None,
            "gastos_categorias": {
                "Alimentación": [],
                "Transporte": [],
                "Ocio": [],
                "Otros": []
            }
        }
        guardar_datos()
        flash("Todos los datos financieros han sido reiniciados.")

    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop("usuario", None)
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)
