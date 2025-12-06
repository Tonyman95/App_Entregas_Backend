from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
    decode_token,
)
from werkzeug.security import check_password_hash
from sqlalchemy.future import select
from database import SessionLocal
from models import Usuario, RefreshToken
import logging

# Role -> perms mapping (basic)
ROLE_PERMISSIONS = {
    'operador': {
        'entregas.create', 'entregas.read', 'entregas.update'
    },
    'rrhh': {
        'trabajadores.create', 'trabajadores.read', 'trabajadores.update',
        'beneficios.read', 'periodos.read', 'entregas.read', 'reportes.read',
        'sucursales.read', 'sucursales.update', 'sucursales.create' 'beneficios.create',
        'beneficios.update', 'periodos.create', 'periodos.update'
    },
    'admin': {'*'}
}

def create_auth_blueprint(jwt):
    auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload.get('jti')
        db = SessionLocal()
        try:
            rt = db.execute(select(RefreshToken).where(RefreshToken.jti == jti)).scalar_one_or_none()
            if rt is None:
                return False
            return bool(rt.revoked)
        except Exception as e:
            logging.warning('Error checking token revocation (assuming not revoked): %s', e)
            return False
        finally:
            db.close()

    @auth_bp.post('/login')
    def login():
        data = request.get_json(force=True)
        username = (data.get('usuario') or '').strip()
        password = data.get('contrasena')
        if not username or not password:
            return jsonify({"error": "usuario y contrasena son requeridos"}), 400
        
        db = SessionLocal()
        try:
            user = db.execute(select(Usuario).where(Usuario.usuario == username)).scalar_one_or_none()
            if not user or not check_password_hash(user.contrasenaHash, password):
                return jsonify({"error": "credenciales inválidas"}), 401
            
            additional_claims = {"role": (user.rol or '').lower()}
            access = create_access_token(identity=str(user.ID), additional_claims=additional_claims)
            refresh = create_refresh_token(identity=str(user.ID))
            
            decoded = decode_token(refresh)
            jti = decoded.get('jti')
            rt = RefreshToken(jti=jti, user_id=int(user.ID))
            db.add(rt)
            db.commit()
            
            return jsonify({"access_token": access, "refresh_token": refresh}), 200
        except Exception as e:
            db.rollback()
            logging.exception('No se pudo almacenar RefreshToken (continuando): %s', e)
            return jsonify({"error": "Error interno del servidor"}), 500
        finally:
            db.close()

    @auth_bp.post('/refresh')
    @jwt_required(refresh=True)
    def auth_refresh():
        identity = get_jwt_identity()
        claims = get_jwt()
        old_jti = claims.get('jti')
        
        new_access = create_access_token(identity=str(identity), additional_claims={"role": claims.get('role')})
        new_refresh = create_refresh_token(identity=str(identity))
        new_decoded = decode_token(new_refresh)
        new_jti = new_decoded.get('jti')
        
        db = SessionLocal()
        try:
            rt_old = db.execute(select(RefreshToken).where(RefreshToken.jti == old_jti)).scalar_one_or_none()
            if rt_old:
                rt_old.revoked = True
            
            rt_new = RefreshToken(jti=new_jti, user_id=int(identity) if identity is not None else None)
            db.add(rt_new)
            db.commit()
            
            return jsonify({"access_token": new_access, "refresh_token": new_refresh}), 200
        except Exception as e:
            db.rollback()
            logging.warning('No se pudo rotar/almacenar RefreshToken (continuando): %s', e)
            return jsonify({"error": "Error interno del servidor"}), 500
        finally:
            db.close()

    @auth_bp.post('/logout')
    @jwt_required(refresh=True)
    def auth_logout():
        claims = get_jwt()
        jti = claims.get('jti')
        
        db = SessionLocal()
        try:
            rt = db.execute(select(RefreshToken).where(RefreshToken.jti == jti)).scalar_one_or_none()
            if rt:
                rt.revoked = True
                db.commit()
            return jsonify({"ok": True}), 200
        except Exception as e:
            db.rollback()
            logging.warning('No se pudo marcar RefreshToken como revocado (continuando): %s', e)
            return jsonify({"error": "Error interno del servidor"}), 500
        finally:
            db.close()

    return auth_bp

def require_perm(perm):
    from functools import wraps
    from flask_jwt_extended import jwt_required, get_jwt
    
    def deco(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            role = (claims.get('role') or '').lower()
            
            if role == 'admin' or '*' in ROLE_PERMISSIONS.get(role, set()):
                return fn(*args, **kwargs)
            
            perms = ROLE_PERMISSIONS.get(role, set())
            if perm in perms:
                return fn(*args, **kwargs)
            
            return jsonify({"error": "permiso denegado"}), 403
        return wrapper
    return deco
