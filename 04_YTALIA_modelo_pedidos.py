# Trabajo colaborativo La Fortuna | DIA_1_BASE_Y_ANALISIS | THALIA
# Archivo de referencia: models/pedido_model.py
# Propósito: Operaciones del modelo de pedidos.

"""Modelo de pedidos: todas las operaciones CRUD se realizan en SQLite."""
from datetime import datetime
from models.database import conectar
from config import MAX_REGISTROS

class PedidoModel:
    CAMPOS = ("codigo","cliente","dni","producto","cantidad","precio","subtotal","observacion","estado","forma_pago","fecha_registro")

    def listar(self, criterio="id"):
        permitidos = {"id", "codigo", "cliente", "subtotal", "estado", "fecha_registro"}
        orden = criterio if criterio in permitidos else "id"
        with conectar() as db:
            return [dict(r) for r in db.execute(f"SELECT * FROM pedidos ORDER BY {orden}").fetchall()]

    def obtener(self, codigo):
        with conectar() as db:
            fila = db.execute("SELECT * FROM pedidos WHERE codigo=?", (codigo.upper().strip(),)).fetchone()
            return dict(fila) if fila else None

    def contar(self):
        with conectar() as db:
            return db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]

    def contar_por_dni(self, dni):
        with conectar() as db:
            return db.execute("SELECT COUNT(*) FROM pedidos WHERE dni=?", (dni,)).fetchone()[0]

    def crear(self, datos):
        if self.contar() >= MAX_REGISTROS:
            raise ValueError(f"Se alcanzó el límite de seguridad de {MAX_REGISTROS} registros.")
        campos = ",".join(self.CAMPOS)
        marcas = ",".join("?" for _ in self.CAMPOS)
        with conectar() as db:
            db.execute(f"INSERT INTO pedidos ({campos}) VALUES ({marcas})", tuple(datos[c] for c in self.CAMPOS))
        return datos["codigo"]

    def actualizar_estado(self, codigo, estado):
        with conectar() as db:
            cur = db.execute("UPDATE pedidos SET estado=? WHERE codigo=?", (estado, codigo.upper().strip()))
            return cur.rowcount == 1

    def eliminar(self, codigo):
        with conectar() as db:
            cur = db.execute("DELETE FROM pedidos WHERE codigo=?", (codigo.upper().strip(),))
            return cur.rowcount == 1

    def resumen(self):
        with conectar() as db:
            total, importe = db.execute("SELECT COUNT(*), COALESCE(SUM(subtotal),0) FROM pedidos").fetchone()
            estados = {r[0]: r[1] for r in db.execute("SELECT estado,COUNT(*) FROM pedidos GROUP BY estado")}
        return {"total": total, "importe": float(importe), "estados": estados}

    def siguiente_codigo(self):
        with conectar() as db:
            codigos = db.execute("SELECT codigo FROM pedidos").fetchall()
        mayor = max((int(r[0][1:]) for r in codigos if r[0].startswith("F") and r[0][1:].isdigit()), default=0)
        return f"F{mayor+1:04d}"

    def actualizar_datos(self, codigo, cliente, dni, producto, cantidad, precio, observacion, forma_pago):
        with conectar() as db:
            cur = db.execute("UPDATE pedidos SET cliente=?,dni=?,producto=?,cantidad=?,precio=?,subtotal=?,observacion=?,forma_pago=? WHERE codigo=?",
                (cliente,dni,producto,cantidad,precio,round(precio*cantidad,2),observacion,forma_pago,codigo.upper().strip()))
            return cur.rowcount == 1
