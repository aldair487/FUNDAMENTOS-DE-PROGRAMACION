# Trabajo colaborativo La Fortuna | DIA_1_BASE_Y_ANALISIS | DENIS
# Archivo de referencia: services/validaciones.py
# Propósito: Validaciones de nombre, DNI, cantidad y observaciones.
# Copia de referencia del proyecto final; no sobrescribir sin revisar y probar.

"""Validaciones centralizadas para La Fortuna."""
import re
import unicodedata
from services.recursividad import solo_digitos_recursivo

def normalizar(texto):
    texto = unicodedata.normalize("NFD", str(texto).strip().lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")

def limpiar_espacios(texto):
    return " ".join(str(texto).strip().split())

def validar_dni(dni):
    """Valida formato y patrones sospechosos; no consulta RENIEC."""
    if not isinstance(dni, str) or len(dni) != 8 or not solo_digitos_recursivo(dni):
        return False
    if len(set(dni)) == 1:
        return False
    # Evita tres o más dígitos iguales consecutivos en cualquier posición.
    if re.search(r"(\d)\1{2,}", dni):
        return False
    # Secuencias consecutivas de seis o más dígitos en cualquier posición.
    for i in range(len(dni) - 5):
        tramo = dni[i:i+6]
        dif = [int(tramo[j+1])-int(tramo[j]) for j in range(5)]
        if all(x == 1 for x in dif) or all(x == -1 for x in dif):
            return False
    # Patrones periódicos de uno o dos dígitos (ej. 12121212).
    if len(set(dni)) <= 2 and any(dni == (dni[:p] * (8 // p + 1))[:8] for p in (1, 2)):
        return False
    return True

def validar_nombre(nombre):
    if not isinstance(nombre, str):
        return False
    nombre = limpiar_espacios(nombre)
    if not 3 <= len(nombre) <= 80 or len(nombre.split()) < 2:
        return False
    particulas = {"de", "del", "la", "las", "los", "y", "san", "santa"}
    for palabra in nombre.split():
        partes = re.split(r"[-']", palabra)
        if any(not parte or not parte.isalpha() for parte in partes):
            return False
    relevantes = [p for p in nombre.split() if p.lower() not in particulas]
    return bool(relevantes) and not all(len(set(normalizar(p))) == 1 for p in relevantes)

def validar_cantidad(cantidad):
    return isinstance(cantidad, int) and not isinstance(cantidad, bool) and 1 <= cantidad <= 50

def validar_observacion(observacion):
    return isinstance(observacion, str) and len(limpiar_espacios(observacion)) <= 200
