from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import select, and_, or_, func
from sqlalchemy.exc import IntegrityError
from database import SessionLocal
from models import Base, Periodo, Beneficio, Entrega, Usuario, Trabajador, Auditoria
from validators import is_valid_rut
from datetime import datetime, date


app = Flask(__name__)
CORS(app)


@app.teardown_appcontext
def shutdown_session(exception=None):
    SessionLocal.remove()


@app.get('/')
def index():
    try:
        db = SessionLocal()
        db.execute(select(func.getdate()))
        return jsonify({"ok": "API de Gestión de Entregas"}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.get('/health')
def health():
# Prueba rápida de conexión
    try:
        db = SessionLocal()
        db.execute(select(func.getdate()))
        return jsonify({"ok": "Todo Bien, API funcionando"}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    


# ------------------ Beneficios ------------------
@app.get('/beneficios')
def list_beneficios():
    db = SessionLocal()
    q = db.execute(select(Beneficio).order_by(Beneficio.nombre_beneficio))
    items = [
        {"codigo": b.codigo, "nombre_beneficio": b.nombre_beneficio}
        for (b,) in q.all()
    ]
    return jsonify(items)


@app.post('/beneficios')
def create_beneficio():
    data = request.get_json(force=True)
    codigo = (data.get('codigo') or '').strip()
    nombre = (data.get('nombre_beneficio') or '').strip()
    if not codigo or not nombre:
        return jsonify({"error": "codigo y nombre_beneficio son obligatorios"}), 400
    db = SessionLocal()
    b = Beneficio(codigo=codigo, nombre_beneficio=nombre)
    db.add(b)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return jsonify({"error": "Ya existe un beneficio con ese codigo"}), 409
    return jsonify({"codigo": b.Codigo, "nombre_beneficio": b.NombreBeneficio}), 201


# Beneficios - single / update / delete
@app.get('/beneficios/<string:codigo>')
def get_beneficio(codigo: str):
    db = SessionLocal()
    b = db.get(Beneficio, codigo)
    if not b:
        return jsonify({"error": "Beneficio no encontrado"}), 404
    return jsonify({
        "codigo": b.codigo,
        "nombre_beneficio": b.nombre_beneficio,
        "descripcion": b.descripcion,
        "activo": bool(b.activo),
        "creado_en": b.creado_en.isoformat() if getattr(b, 'creado_en', None) else None
    })


@app.put('/beneficios/<string:codigo>')
def update_beneficio(codigo: str):
    db = SessionLocal()
    b = db.get(Beneficio, codigo)
    if not b:
        return jsonify({"error": "Beneficio no encontrado"}), 404
    data = request.get_json(force=True)
    nombre = data.get('nombre_beneficio')
    descripcion = data.get('descripcion')
    activo = data.get('activo')
    if nombre is not None:
        b.nombre_beneficio = nombre.strip()
    if descripcion is not None:
        b.descripcion = descripcion
    if activo is not None:
        # accept boolean or truthy/falsy values
        if isinstance(activo, bool):
            b.activo = activo
        else:
            b.activo = str(activo).lower() in ('1','true','yes')
    db.commit()
    return jsonify({"ok": True})


@app.delete('/beneficios/<string:codigo>')
def delete_beneficio(codigo: str):
    db = SessionLocal()
    b = db.get(Beneficio, codigo)
    if not b:
        return jsonify({"error": "Beneficio no encontrado"}), 404
    db.delete(b)
    db.commit()
    return jsonify({"ok": True}), 200


# ------------------ Periodos ------------------
@app.get('/periodos')
def list_periodos():
    db = SessionLocal()
    q = db.execute(select(Periodo).order_by(Periodo.FechaInicio.desc()))
    items = [
        {
            "codigo": p.Codigo,
            "nombre_periodo": getattr(p, 'nombre_periodo', None),
            "fecha_inicio": p.FechaInicio.isoformat(),
            "fecha_final": p.FechaFinal.isoformat()
        }
        for (p,) in q.all()
    ]
    return jsonify(items)


# Periodos - create / single / update / delete (CRUD para administrador)
@app.post('/periodos')
def create_periodo():
    db = SessionLocal()
    data = request.get_json(force=True)
    codigo = (data.get('codigo') or '').strip()
    nombre = (data.get('nombre_periodo') or '').strip()
    fecha_inicio = data.get('fecha_inicio')
    fecha_final = data.get('fecha_final')
    if not all([codigo, nombre, fecha_inicio, fecha_final]):
        return jsonify({"error": "codigo, nombre_periodo, fecha_inicio y fecha_final son obligatorios"}), 400
    try:
        fi = date.fromisoformat(fecha_inicio)
        ff = date.fromisoformat(fecha_final)
    except Exception:
        return jsonify({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}), 400
    if ff < fi:
        return jsonify({"error": "fecha_final no puede ser anterior a fecha_inicio"}), 400
    # crear
    p = Periodo(Codigo=codigo, nombre_periodo=nombre, FechaInicio=fi, FechaFinal=ff)
    db.add(p)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return jsonify({"error": "Ya existe un periodo con ese codigo"}), 409
    return jsonify({"codigo": p.Codigo, "nombre_periodo": p.nombre_periodo}), 201


@app.get('/periodos/<string:codigo>')
def get_periodo(codigo: str):
    db = SessionLocal()
    p = db.get(Periodo, codigo)
    if not p:
        return jsonify({"error": "Periodo no encontrado"}), 404
    return jsonify({
        "codigo": p.Codigo,
        "nombre_periodo": p.nombre_periodo,
        "fecha_inicio": p.FechaInicio.isoformat() if p.FechaInicio else None,
        "fecha_final": p.FechaFinal.isoformat() if p.FechaFinal else None,
    })


@app.put('/periodos/<string:codigo>')
def update_periodo(codigo: str):
    db = SessionLocal()
    p = db.get(Periodo, codigo)
    if not p:
        return jsonify({"error": "Periodo no encontrado"}), 404
    data = request.get_json(force=True)
    nombre = data.get('nombre_periodo')
    fecha_inicio = data.get('fecha_inicio')
    fecha_final = data.get('fecha_final')
    if nombre is not None:
        p.nombre_periodo = nombre.strip()
    if fecha_inicio is not None:
        try:
            p.FechaInicio = date.fromisoformat(fecha_inicio)
        except Exception:
            return jsonify({"error": "Formato fecha_inicio inválido"}), 400
    if fecha_final is not None:
        try:
            p.FechaFinal = date.fromisoformat(fecha_final)
        except Exception:
            return jsonify({"error": "Formato fecha_final inválido"}), 400
    if p.FechaFinal < p.FechaInicio:
        return jsonify({"error": "fecha_final no puede ser anterior a fecha_inicio"}), 400
    db.commit()
    return jsonify({"ok": True})


@app.delete('/periodos/<string:codigo>')
def delete_periodo(codigo: str):
    db = SessionLocal()
    p = db.get(Periodo, codigo)
    if not p:
        return jsonify({"error": "Periodo no encontrado"}), 404
    db.delete(p)
    db.commit()
    return jsonify({"ok": True}), 200


# ------------------ Entregas ------------------
@app.get('/entregas')
def list_entregas():
    db = SessionLocal()
    # Filtros
    rut = request.args.get('rut')
    periodo = request.args.get('periodo')
    beneficio = request.args.get('beneficio')
    estado = request.args.get('estado')
    fecha_desde = request.args.get('desde') # yyyy-mm-dd
    fecha_hasta = request.args.get('hasta') # yyyy-mm-dd


    conditions = []
    if rut:
        conditions.append(Entrega.Rut == rut)
    if periodo:
        conditions.append(Entrega.Periodo_cod == periodo)
    if beneficio:
        conditions.append(Entrega.Beneficio_cod == beneficio)
    if estado:
        conditions.append(Entrega.Estado == (estado or '').strip().upper())
    if fecha_desde:
        conditions.append(func.convert(func.date, Entrega.FechaEntrega) >= fecha_desde)
    if fecha_hasta:
        conditions.append(func.convert(func.date, Entrega.FechaEntrega) <= fecha_hasta)


    page = max(int(request.args.get('page', 1)), 1)
    size = min(max(int(request.args.get('size', 20)), 1), 200)
    offset = (page - 1) * size


    base_q = select(Entrega).where(and_(*conditions)) if conditions else select(Entrega)
    total = db.execute(base_q.with_only_columns(func.count())).scalar()


    q = db.execute(base_q.order_by(Entrega.FechaEntrega.desc()).offset(offset).limit(size))


    items = []
    for (e,) in q.all():
        items.append({
            "id": e.ID,
            "rut": e.Rut,
            "nombre": e.Nombre,
            "apellido": e.Apellido,
            "fecha_entrega": e.FechaEntrega.isoformat() if e.FechaEntrega else None,
            "beneficio_cod": e.Beneficio_cod,
            "periodo_cod": e.Periodo_cod,
            "estado": e.Estado,
            "tiene_firma": False
        })
    return jsonify({"page": page, "size": size, "total": total, "items": items})


@app.get('/entregas/<int:eid>')
def get_entrega(eid: int):
    db = SessionLocal()
    e = db.get(Entrega, eid)
    if not e:
        return jsonify({"error": "Entrega no encontrada"}), 404
    return jsonify({
        "id": e.ID,
        "rut": e.Rut,
        "nombre": e.Nombre,
        "apellido": e.Apellido,
        "fecha_entrega": e.FechaEntrega.isoformat() if e.FechaEntrega else None,
        "beneficio_cod": e.Beneficio_cod,
        "periodo_cod": e.Periodo_cod,
        "estado": e.Estado,
        "firma_base64": None,
    })


@app.post('/entregas')
def create_entrega():
    db = SessionLocal()
    data = request.get_json(force=True)
    rut = (data.get('rut') or '').strip()
    nombre = (data.get('nombre') or '').strip()
    apellido = (data.get('apellido') or '').strip()
    beneficio = (data.get('beneficio_cod') or '').strip()
    periodo = (data.get('periodo_cod') or '').strip()
    firma = data.get('firma_base64') # opcional
    fecha_entrega = data.get('fecha_entrega')


    # Validaciones
    if not all([rut, nombre, apellido, beneficio, periodo]):
        return jsonify({"error": "rut, nombre, apellido, beneficio_cod y periodo_cod son obligatorios"}), 400
    if not is_valid_rut(rut):
        return jsonify({"error": "RUT con formato inválido"}), 400


    # Validación de duplicado: (Rut, Beneficio_cod, Periodo_cod) único
    exists_q = select(func.count()).select_from(Entrega).where(
        and_(Entrega.Rut == rut, Entrega.Beneficio_cod == beneficio, Entrega.Periodo_cod == periodo)
    )
    if db.execute(exists_q).scalar() > 0:
        return jsonify({"error": "La persona ya tiene registrada una entrega de ese beneficio en el periodo indicado"}), 409


    # Validación de FKs simples
    if db.get(Beneficio, beneficio) is None:
        return jsonify({"error": "beneficio_cod no existe"}), 400
    if db.get(Periodo, periodo) is None:
        return jsonify({"error": "periodo_cod no existe"}), 400

    # Aseguramos que exista el trabajador; si no existe, lo creamos
    trabajador = db.get(Trabajador, rut)
    if trabajador is None:
        trabajador = Trabajador(
            rut=rut,
            primer_nombre=nombre,
            primer_apellido=apellido,
            email=data.get('email')
        )
        db.add(trabajador)
        db.commit()
        db.refresh(trabajador)


    # FechaEntrega es NOT NULL en la nueva definición; si no viene, la ponemos ahora
    if fecha_entrega:
        try:
            fecha = datetime.fromisoformat(fecha_entrega)
        except Exception:
            fecha = datetime.utcnow()
    else:
        fecha = datetime.utcnow()

    e = Entrega(
        Rut=rut,
        FechaEntrega=fecha,
        Beneficio_cod=beneficio,
        Periodo_cod=periodo,
        Estado='PENDIENTE'
    )
    db.add(e)
    db.commit()
    db.refresh(e)

    # Si se entregó firma, registramos un evento de auditoría con el detalle (no guardamos la firma en la tabla Entregas)
    if firma:
        a = Auditoria(
            tabla_nombre='Entregas',
            llave_registro=str(e.ID),
            accion='FIRMA',
            usuario_nombre=None,
            detalle=(firma[:2000] if isinstance(firma, str) else None)
        )
        db.add(a)
        db.commit()
        db.refresh(a)
    return jsonify({"id": e.ID}), 201


@app.patch('/entregas/<int:eid>')
def update_entrega(eid: int):
    db = SessionLocal()
    e = db.get(Entrega, eid)
    if not e:
        return jsonify({"error": "Entrega no encontrada"}), 404


    data = request.get_json(force=True)
    estado = data.get('estado')
    firma = data.get('firma_base64')


    if estado is not None:
        estado = estado.strip().upper()
        if estado not in ('PENDIENTE', 'ENTREGADO', 'CANCELADO', 'ANULADO'):
            return jsonify({"error": "estado inválido"}), 400
        e.Estado = estado
    if firma is not None:
        # Guardamos la firma como un evento de auditoría
        a = Auditoria(
            tabla_nombre='Entregas',
            llave_registro=str(e.ID),
            accion='FIRMA',
            usuario_nombre=None,
            detalle=(firma[:2000] if isinstance(firma, str) else None)
        )
        db.add(a)


    db.commit()
    return jsonify({"ok": True})


# ------------------ Reportes ------------------
@app.get('/reportes/entregas-por-beneficio')
def reporte_entregas_por_beneficio():
    db = SessionLocal()
    periodo = request.args.get('periodo')
    if not periodo:
        return jsonify({"error": "Debe indicar ?periodo=CODIGO"}), 400


    q = db.execute(
        select(
            Entrega.Periodo_cod.label('periodo'),
            Entrega.Beneficio_cod.label('beneficio'),
            func.count().label('total'),
            func.sum(func.iif(Entrega.Estado == 'ENTREGADO', 1, 0)).label('entregados'),
            func.sum(func.iif(Entrega.Estado == 'PENDIENTE', 1, 0)).label('pendientes'),
            func.sum(func.iif(Entrega.Estado == 'CANCELADO', 1, 0)).label('rechazados')
        ).where(Entrega.Periodo_cod == periodo)
        .group_by(Entrega.Periodo_cod, Entrega.Beneficio_cod)
        .order_by(Entrega.Beneficio_cod)
    )


    items = []
    for row in q.all():
        items.append({
            "periodo": row.periodo,
            "beneficio_cod": row.beneficio,
            "total": int(row.total or 0),
            "entregados": int(row.entregados or 0),
            "pendientes": int(row.pendientes or 0),
            "rechazados": int(row.rechazados or 0)
        })
    return jsonify(items)


if __name__ == '__main__':
    import os
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
    