# Trabajo colaborativo La Fortuna | DIA_1_BASE_Y_ANALISIS | YERSON
# Archivo de referencia: web_app.py
# Propósito: Punto de entrada y rutas web.
# Copia de referencia del proyecto final; no sobrescribir sin revisar y probar.

"""Interfaz web responsive de La Fortuna. Conserva la arquitectura MVC."""
import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from config import MENU, ESTADOS, FORMAS_PAGO
from models.database import inicializar
from models.usuario_model import UsuarioModel
from models.pedido_model import PedidoModel
from models.auditoria_model import AuditoriaModel
from controllers.auth_controller import AuthController
from controllers.pedido_controller import PedidoController
from controllers.reporte_controller import ReporteController
from services.exportacion_service import ExportacionService

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("LA_FORTUNA_SECRET", "cambiar-esta-clave-en-produccion-la-fortuna")
inicializar()

def requiere_sesion(f):
    @wraps(f)
    def envoltura(*args, **kwargs):
        if "usuario" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return envoltura

def componentes():
    usuario = session.get("usuario", "sistema")
    modelo = PedidoModel()
    auditoria = AuditoriaModel()
    return modelo, auditoria, PedidoController(modelo, auditoria, usuario), ReporteController(
        modelo, ExportacionService(modelo), auditoria, usuario)

@app.route("/sw.js")
def service_worker():
    from flask import make_response
    respuesta = make_response(app.send_static_file("sw.js"))
    respuesta.headers["Service-Worker-Allowed"] = "/"
    respuesta.headers["Content-Type"] = "application/javascript"
    return respuesta

@app.route("/", methods=["GET"])
def inicio():
    return redirect(url_for("panel") if "usuario" in session else url_for("login"))

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        try:
            nombre_usuario = request.form.get("usuario", "")
            correo = request.form.get("email", "")
            AuthController(UsuarioModel()).crear_cuenta(
                nombre_usuario, correo, request.form.get("password", ""))
            AuditoriaModel().registrar(nombre_usuario, "CREAR_CUENTA", "Usuario", nombre_usuario,
                                       f"Cuenta creada para {correo}")
            flash("Cuenta creada. Ya puedes iniciar sesión.", "ok")
            return redirect(url_for("login"))
        except Exception as exc:
            flash(str(exc), "error")
    return render_template("registro.html")

@app.route("/configurar", methods=["GET", "POST"])
def configurar():
    usuarios = UsuarioModel()
    if usuarios.existe_admin():
        return redirect(url_for("login"))
    if request.method == "POST":
        try:
            AuthController(usuarios).crear_admin_inicial(
                request.form.get("usuario", ""), request.form.get("password", ""),
                request.form.get("email", ""))
            flash("Administrador creado. Inicia sesión.", "ok")
            return redirect(url_for("login"))
        except Exception as exc:
            flash(str(exc), "error")
    return render_template("configurar.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if not UsuarioModel().existe_admin():
        return redirect(url_for("configurar"))
    if request.method == "POST":
        usuario = request.form.get("usuario", "")
        password = request.form.get("password", "")
        if AuthController(UsuarioModel()).autenticar(usuario, password):
            session.clear()
            session["usuario"] = usuario.strip()
            AuditoriaModel().registrar(usuario.strip(), "INICIAR_SESION", "Usuario", usuario.strip(),
                                       "Inicio de sesión correcto")
            return redirect(url_for("panel"))
        flash("Usuario/correo o contraseña incorrectos.", "error")
    return render_template("login.html")

@app.route("/salir")
def salir():
    usuario = session.get("usuario")
    if usuario:
        AuditoriaModel().registrar(usuario, "CERRAR_SESION", "Usuario", usuario, "Cierre de sesión")
    session.clear()
    return redirect(url_for("login"))

@app.route("/panel")
@requiere_sesion
def panel():
    modelo, auditoria, pedidos, reportes = componentes()
    filas = modelo.listar("id")
    return render_template("panel.html", filas=filas, menu=MENU, estados=ESTADOS,
                           pagos=FORMAS_PAGO, resumen=reportes.resumen(),
                           auditoria=reportes.auditoria_reciente(), usuario=session["usuario"])

@app.route("/pedido/registrar", methods=["POST"])
@requiere_sesion
def registrar_pedido():
    try:
        _, _, ctrl, _ = componentes()
        cantidad_txt = request.form.get("cantidad", "")
        if not cantidad_txt.isascii() or not cantidad_txt.isdigit():
            raise ValueError("La cantidad debe ser un número entero.")
        codigo = ctrl.registrar(request.form.get("cliente", ""), request.form.get("dni", ""),
            request.form.get("producto", ""), int(cantidad_txt), request.form.get("observacion", ""),
            request.form.get("forma_pago", ""))
        flash(f"Pedido {codigo} registrado correctamente.", "ok")
    except Exception as exc:
        flash(str(exc), "error")
    return redirect(url_for("panel"))

@app.route("/pedido/<codigo>/estado", methods=["POST"])
@requiere_sesion
def cambiar_estado(codigo):
    try:
        _, _, ctrl, _ = componentes()
        ctrl.cambiar_estado(codigo, request.form.get("estado", ""))
        flash("Estado actualizado.", "ok")
    except Exception as exc:
        flash(str(exc), "error")
    return redirect(url_for("panel"))

@app.route("/pedido/<codigo>/eliminar", methods=["POST"])
@requiere_sesion
def eliminar_pedido(codigo):
    try:
        _, _, ctrl, _ = componentes()
        ctrl.eliminar(codigo)
        flash("Pedido eliminado.", "ok")
    except Exception as exc:
        flash(str(exc), "error")
    return redirect(url_for("panel"))

@app.route("/exportar/json")
@requiere_sesion
def exportar_json():
    try:
        _, _, _, reportes = componentes()
        ruta = reportes.exportar("json")
        return send_file(ruta, as_attachment=True, download_name=ruta.name)
    except Exception as exc:
        flash(str(exc), "error")
        return redirect(url_for("panel"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
