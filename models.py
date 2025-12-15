from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import (
    Column,
    String,
    Date,
    DateTime,
    BigInteger,
    Text,
    ForeignKey,
    CheckConstraint,
    Integer,
    Boolean,
    func,
    text,
)


Base = declarative_base()


class Sucursal(Base):
    __tablename__ = "Sucursal"
    codigo = Column(String(20), primary_key=True)
    nombre_sucursal = Column(String(200), nullable=False)
    direccion = Column(String(300), nullable=True)
    telefono = Column(String(30), nullable=True)
    creado_en = Column(DateTime(timezone=False), server_default=text("SYSUTCDATETIME()"), nullable=False)
    modificado_en = Column(DateTime(timezone=False), nullable=True)


class Periodo(Base):
    __tablename__ = "Periodos"
    # Aclaramos los nombres de columna para que coincidan exactamente
    Codigo = Column('codigo', String(20), primary_key=True)
    nombre_periodo = Column('nombre_periodo', String(150), nullable=False)
    FechaInicio = Column('fecha_inicio', Date, nullable=False)
    FechaFinal = Column('fecha_final', Date, nullable=False)
    creado_en = Column('creado_en', DateTime(timezone=False), server_default=text("SYSUTCDATETIME()"), nullable=False)
    __table_args__ = (
        CheckConstraint("fecha_final >= fecha_inicio", name='CHK_Periodos_Fecha'),
    )


class Beneficio(Base):
    __tablename__ = "Beneficios"
    codigo = Column(String(50), primary_key=True)
    nombre_beneficio = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    activo = Column(Boolean, nullable=False, server_default=text('1'))
    creado_en = Column(DateTime(timezone=False), server_default=text("SYSUTCDATETIME()"), nullable=False)


class Trabajador(Base):
    __tablename__ = "Trabajadores"
    rut = Column(String(15), primary_key=True)
    primer_nombre = Column(String(100), nullable=False)
    segundo_nombre = Column(String(100), nullable=True)
    primer_apellido = Column(String(100), nullable=False)
    segundo_apellido = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    cargo = Column(String(150), nullable=True)
    activo = Column(Boolean, nullable=False, server_default=text('1'))
    creado_en = Column(DateTime(timezone=False), server_default=text("SYSUTCDATETIME()"), nullable=False)
    modificado_en = Column(DateTime(timezone=False), nullable=True)
    entregas = relationship('Entrega', back_populates='trabajador')


class Usuario(Base):
    __tablename__ = "Usuarios"
    ID = Column(Integer, primary_key=True, autoincrement=True)
    rol = Column(String(50), nullable=False)
    usuario = Column(String(150), nullable=False, unique=True)
    contrasenaHash = Column(String(512), nullable=False)
    email = Column(String(255), nullable=True)
    activo = Column(Boolean, nullable=False, server_default=text('1'))
    creado_en = Column(DateTime(timezone=False), server_default=text("SYSUTCDATETIME()"), nullable=False)
    ultimo_acceso = Column(DateTime(timezone=False), nullable=True)
    auditorias = relationship('Auditoria', back_populates='usuario')


class Auditoria(Base):
    __tablename__ = "Auditoria"
    audit_id = Column(BigInteger, primary_key=True, autoincrement=True)
    tabla_nombre = Column(String(128), nullable=False)
    llave_registro = Column(String(256), nullable=True)
    accion = Column(String(50), nullable=False)
    usuario_id = Column(Integer, ForeignKey('Usuarios.ID'), nullable=True)
    usuario_nombre = Column(String(150), nullable=True)
    fecha_accion = Column(DateTime(timezone=False), server_default=text("SYSUTCDATETIME()"), nullable=False)
    detalle = Column(Text, nullable=True)
    usuario = relationship('Usuario', back_populates='auditorias')


class Entrega(Base):
    __tablename__ = "Entregas"
    ID = Column(BigInteger, primary_key=True, autoincrement=True)
    # Mapamos los nombres de columna de la DB a atributos con nombres familiares para la app
    Rut = Column('rut_trabajador', String(15), ForeignKey('Trabajadores.rut'), nullable=False)
    FechaEntrega = Column('fecha_entrega', DateTime(timezone=False), nullable=False)
    Beneficio_cod = Column('cod_beneficio', String(50), ForeignKey('Beneficios.codigo'), nullable=False)
    Estado = Column('estado', String(30), nullable=False, server_default=text("'PENDIENTE'"))
    Periodo_cod = Column('cod_periodo', String(20), ForeignKey('Periodos.codigo'), nullable=True)
    CodSucursal = Column('cod_sucursal', String(20), ForeignKey('Sucursal.codigo'), nullable=True)
    TipoContrato = Column('tipo_contrato', String(30), nullable=True)
    Usuario_creador = Column('usuario_creador', Integer, ForeignKey('Usuarios.ID'), nullable=True)
    qr_payload = Column('qr_payload', Text, nullable=True)
    creado_en = Column(DateTime(timezone=False), server_default=text("SYSUTCDATETIME()"), nullable=False)
    modificado_en = Column(DateTime(timezone=False), nullable=True)

    trabajador = relationship('Trabajador', back_populates='entregas')

    __table_args__ = (
        CheckConstraint("estado IN ('PENDIENTE','ENTREGADO','CANCELADO','ANULADO')", name='CHK_Entregas_Estado'),
        CheckConstraint("tipo_contrato IS NULL OR tipo_contrato IN ('INDEFINIDO','PLAZO FIJO','CONTRATO','EVENTUAL')", name='CHK_Entregas_TipoContrato'),
    )

    # Propiedades convenientes para compatibilidad con el código existente
    @property
    def Nombre(self):
        if self.trabajador:
            return self.trabajador.primer_nombre
        return None

    @property
    def Apellido(self):
        if self.trabajador:
            return self.trabajador.primer_apellido
        return None

    @property
    def Correo(self):
        if self.trabajador:
            return self.trabajador.email
        return None


class RefreshToken(Base):
    __tablename__ = 'RefreshTokens'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    jti = Column(String(128), nullable=False, unique=True, index=True)
    user_id = Column(Integer, ForeignKey('Usuarios.ID'), nullable=False)
    created_at = Column(DateTime(timezone=False), server_default=text("SYSUTCDATETIME()"), nullable=False)
    revoked = Column(Boolean, nullable=False, server_default=text('0'))
    usuario = relationship('Usuario')
