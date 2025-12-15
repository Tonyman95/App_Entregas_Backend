from flask import Blueprint, jsonify, request
from database import SessionLocal
from sqlalchemy import select
from models import Periodo
from flask import abort
from datetime import date

def create_periodos_blueprint(require_perm):
    bp = Blueprint('periodos', __name__, url_prefix='/periodos')

    @bp.get('/')
    @require_perm('periodos.read')
    def list_periodos():
        db = SessionLocal()
        try:
            
            rows = db.execute(select(Periodo)).scalars().all()
            items = []
            for r in rows:
                items.append({
                    'codigo': getattr(r, 'Codigo', None),
                    'nombre_periodo': getattr(r, 'nombre_periodo', None),
                    'fecha_inicio': getattr(r, 'FechaInicio', None).isoformat() if getattr(r, 'FechaInicio', None) else None,
                    'fecha_final': getattr(r, 'FechaFinal', None).isoformat() if getattr(r, 'FechaFinal', None) else None,
                })
            return jsonify(items)
        finally:
            db.close()

    

    @bp.get('/<string:codigo>')
    @require_perm('periodos.read')
    def get_periodo(codigo):
        db = SessionLocal()
        try:
            p = db.execute(select(Periodo).where(Periodo.Codigo == codigo)).scalar_one_or_none()
            if not p:
                return abort(404)
            return jsonify({
                'codigo': getattr(p, 'Codigo', None),
                'nombre_periodo': getattr(p, 'nombre_periodo', None),
                'fecha_inicio': getattr(p, 'FechaInicio', None).isoformat() if getattr(p, 'FechaInicio', None) else None,
                'fecha_final': getattr(p, 'FechaFinal', None).isoformat() if getattr(p, 'FechaFinal', None) else None,
            })
        finally:
            db.close()

    @bp.post('/')
    @require_perm('periodos.create')
    def create_periodo():
        data = request.get_json(force=True)
        codigo = data.get('codigo')
        nombre = data.get('nombre_periodo')
        fecha_inicio = data.get('fecha_inicio')
        fecha_final = data.get('fecha_final')
        if not codigo or not nombre or not fecha_inicio or not fecha_final:
            return jsonify({'error': 'codigo, nombre_periodo, fecha_inicio y fecha_final son requeridos'}), 400
        try:
            fi = date.fromisoformat(fecha_inicio)
            ff = date.fromisoformat(fecha_final)
        except Exception:
            return jsonify({'error': 'fechas deben estar en formato YYYY-MM-DD'}), 400
        db = SessionLocal()
        try:
            periodo = Periodo(Codigo=codigo, nombre_periodo=nombre, FechaInicio=fi, FechaFinal=ff)
            db.add(periodo)
            db.commit()
            return jsonify({'ok': True, 'codigo': periodo.Codigo}), 201
        except Exception as e:
            db.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            db.close()

    @bp.put('/<string:codigo>')
    @require_perm('periodos.update')
    def update_periodo(codigo):
        data = request.get_json(force=True)
        db = SessionLocal()
        try:
            p = db.execute(select(Periodo).where(Periodo.Codigo == codigo)).scalar_one_or_none()
            if not p:
                return abort(404)
            if 'nombre_periodo' in data:
                p.nombre_periodo = data.get('nombre_periodo')
            if 'fecha_inicio' in data:
                try:
                    p.FechaInicio = date.fromisoformat(data.get('fecha_inicio'))
                except Exception:
                    return jsonify({'error': 'fecha_inicio formato inválido'}), 400
            if 'fecha_final' in data:
                try:
                    p.FechaFinal = date.fromisoformat(data.get('fecha_final'))
                except Exception:
                    return jsonify({'error': 'fecha_final formato inválido'}), 400
            db.commit()
            return jsonify({'ok': True, 'codigo': p.Codigo}), 200
        except Exception as e:
            db.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            db.close()

    return bp
