# Trabajo colaborativo La Fortuna | DIA_2_IMPLEMENTACION | YERSON
# Archivo de referencia: services/exportacion_service.py
# Propósito: Exportación de pedidos y reportes.
# Copia de referencia del proyecto final; no sobrescribir sin revisar y probar.

"""Exporta el resultado de consultas SQLite a CSV, JSON, TXT, BIN y PDF."""
import csv, json, pickle
from datetime import datetime
from pathlib import Path
from config import DATA_DIR, APP_NAME

class ExportacionService:
    def __init__(self, pedido_model): self.pedido_model=pedido_model
    @staticmethod
    def _pdf(ruta, lineas):
        def esc(t): return str(t).encode('latin-1','replace').decode('latin-1').replace('\\','\\\\').replace('(','\\(').replace(')','\\)')
        paginas=[]
        bloques=[lineas[i:i+48] for i in range(0,len(lineas),48)] or [[]]
        objetos=[b'<< /Type /Catalog /Pages 2 0 R >>']
        kids=[]
        for idx, bloque in enumerate(bloques):
            page_id=3+idx*2; content_id=page_id+1; kids.append(f'{page_id} 0 R')
            stream='BT\n/F1 9 Tf\n40 800 Td\n'+'\n'.join((('0 -15 Td\n' if j else '')+f'({esc(x)}) Tj') for j,x in enumerate(bloque))+'\nET'
            data=stream.encode('latin-1')
            paginas.append((page_id, f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 {3+len(bloques)*2} 0 R >> >> /Contents {content_id} 0 R >>'.encode(), content_id, b'<< /Length '+str(len(data)).encode()+b' >>\nstream\n'+data+b'\nendstream'))
        objetos.append(f'<< /Type /Pages /Kids [{" ".join(kids)}] /Count {len(kids)} >>'.encode())
        for page, pobj, content, cobj in paginas: objetos.extend([pobj,cobj])
        font_id=3+len(bloques)*2; objetos.append(b'<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>')
        out=bytearray(b'%PDF-1.4\n'); offsets=[0]
        for i,obj in enumerate(objetos,1): offsets.append(len(out)); out.extend(f'{i} 0 obj\n'.encode()+obj+b'\nendobj\n')
        xref=len(out); out.extend(f'xref\n0 {len(objetos)+1}\n0000000000 65535 f \n'.encode())
        for off in offsets[1:]: out.extend(f'{off:010d} 00000 n \n'.encode())
        out.extend(f'trailer\n<< /Size {len(objetos)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF'.encode()); ruta.write_bytes(out)
    def exportar(self, formato):
        filas=self.pedido_model.listar("id")
        if not filas: raise ValueError("No existen pedidos en SQLite para exportar.")
        formato=formato.lower().lstrip('.')
        if formato not in {"csv","json","txt","bin","pdf"}: raise ValueError("Formato no admitido.")
        DATA_DIR.mkdir(parents=True,exist_ok=True)
        ruta=DATA_DIR/f"pedidos_exportacion_{datetime.now():%Y%m%d_%H%M%S_%f}.{formato}"
        if formato=="csv":
            with ruta.open('w',newline='',encoding='utf-8-sig') as f:
                w=csv.DictWriter(f,fieldnames=list(filas[0].keys())); w.writeheader(); w.writerows(filas)
        elif formato=="json": ruta.write_text(json.dumps({"pedidos":filas},ensure_ascii=False,indent=4),encoding='utf-8')
        elif formato=="txt": ruta.write_text('\n'.join(' | '.join(f'{k}: {v}' for k,v in r.items()) for r in filas),encoding='utf-8')
        elif formato=="bin":
            with ruta.open('wb') as f: pickle.dump(filas,f,protocol=pickle.HIGHEST_PROTOCOL)
        else:
            lineas=[APP_NAME,"REPORTE DE PEDIDOS",f"Generado: {datetime.now():%d/%m/%Y %H:%M:%S}",f"Total: {len(filas)}","-"*75]
            for r in filas: lineas.extend([f"{r['codigo']} | {r['cliente']} | DNI {r['dni']}",f"{r['producto']} x {r['cantidad']} | S/ {r['subtotal']:.2f} | {r['estado']}"])
            self._pdf(ruta,lineas)
        return ruta
