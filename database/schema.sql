-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tabla: usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    rol VARCHAR(50) NOT NULL, -- 'admin', 'tecnico', 'usuario'
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: categorias_equipos
CREATE TABLE IF NOT EXISTS categorias_equipos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(100) UNIQUE NOT NULL,
    descripcion TEXT,
    vida_util_anios INTEGER NOT NULL,
    depreciacion_anual DECIMAL(5, 2) -- Porcentaje
);

-- Tabla: proveedores
CREATE TABLE IF NOT EXISTS proveedores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(100) NOT NULL,
    ruc VARCHAR(20) UNIQUE NOT NULL,
    contacto_nombre VARCHAR(100),
    contacto_email VARCHAR(100),
    contacto_telefono VARCHAR(20),
    direccion TEXT,
    activo BOOLEAN DEFAULT TRUE,
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: ubicaciones
CREATE TABLE IF NOT EXISTS ubicaciones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(100) NOT NULL, -- Ej: "Laboratorio 1"
    edificio VARCHAR(100) NOT NULL,
    piso VARCHAR(20),
    tipo VARCHAR(50), -- 'aula', 'oficina', 'laboratorio', 'almacen'
    activo BOOLEAN DEFAULT TRUE
);

-- Tabla: equipos
CREATE TABLE IF NOT EXISTS equipos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codigo_inventario VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    marca VARCHAR(50),
    modelo VARCHAR(50),
    numero_serie VARCHAR(100),
    categoria_id UUID REFERENCES categorias_equipos(id),
    proveedor_id UUID REFERENCES proveedores(id),
    ubicacion_actual_id UUID REFERENCES ubicaciones(id),
    estado VARCHAR(50) DEFAULT 'disponible', -- 'disponible', 'en_uso', 'mantenimiento', 'baja', 'reparacion'
    fecha_compra DATE,
    fecha_garantia_fin DATE,
    costo_compra DECIMAL(12, 2),
    especificaciones JSONB, -- Detalles técnicos flexibles
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: movimientos_equipos
CREATE TABLE IF NOT EXISTS movimientos_equipos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    equipo_id UUID REFERENCES equipos(id),
    ubicacion_origen_id UUID REFERENCES ubicaciones(id),
    ubicacion_destino_id UUID REFERENCES ubicaciones(id),
    usuario_id UUID REFERENCES usuarios(id), -- Quién realizó el movimiento
    fecha_movimiento TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    motivo TEXT
);

-- Tabla: contratos
CREATE TABLE IF NOT EXISTS contratos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    proveedor_id UUID REFERENCES proveedores(id),
    numero_contrato VARCHAR(50),
    tipo VARCHAR(50), -- 'compra', 'mantenimiento', 'arrendamiento'
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    monto_total DECIMAL(12, 2),
    archivo_url TEXT,
    estado VARCHAR(20) DEFAULT 'vigente' -- 'vigente', 'vencido', 'cancelado'
);

-- Tabla: mantenimientos
CREATE TABLE IF NOT EXISTS mantenimientos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    equipo_id UUID REFERENCES equipos(id),
    tipo VARCHAR(50) NOT NULL, -- 'preventivo', 'correctivo'
    prioridad VARCHAR(20) DEFAULT 'media', -- 'baja', 'media', 'alta', 'critica'
    estado VARCHAR(50) DEFAULT 'programado', -- 'programado', 'en_proceso', 'completado', 'cancelado'
    fecha_programada DATE NOT NULL,
    fecha_realizacion DATE,
    costo DECIMAL(10, 2),
    descripcion TEXT,
    tecnico_responsable VARCHAR(100),
    notas_tecnicas TEXT,
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: notificaciones
CREATE TABLE IF NOT EXISTS notificaciones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tipo VARCHAR(50) NOT NULL, -- 'mantenimiento', 'garantia', 'obsolescencia', 'sistema'
    mensaje TEXT NOT NULL,
    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    leida BOOLEAN DEFAULT FALSE,
    prioridad VARCHAR(20) DEFAULT 'media',
    datos_extra JSONB
);

-- Índices
CREATE INDEX idx_equipos_codigo ON equipos(codigo_inventario);
CREATE INDEX idx_equipos_categoria ON equipos(categoria_id);
CREATE INDEX idx_equipos_ubicacion ON equipos(ubicacion_actual_id);
CREATE INDEX idx_equipos_estado ON equipos(estado);
CREATE INDEX idx_mantenimientos_equipo ON mantenimientos(equipo_id);
CREATE INDEX idx_mantenimientos_fecha ON mantenimientos(fecha_programada);
CREATE INDEX idx_movimientos_equipo ON movimientos_equipos(equipo_id);
CREATE INDEX idx_notificaciones_leida ON notificaciones(leida);

-- DATOS DE PRUEBA --

-- Usuarios
INSERT INTO usuarios (nombre, email, rol) VALUES
('Admin Sistema', 'admin@uni.edu.pe', 'admin'),
('Técnico Juan', 'juan@uni.edu.pe', 'tecnico'),
('Usuario María', 'maria@uni.edu.pe', 'usuario');

-- Categorías
INSERT INTO categorias_equipos (nombre, descripcion, vida_util_anios, depreciacion_anual) VALUES
('Laptops', 'Computadoras portátiles para personal y laboratorios', 4, 25.00),
('Desktops', 'Computadoras de escritorio', 5, 20.00),
('Servidores', 'Equipos de centro de datos', 5, 20.00),
('Proyectores', 'Proyectores multimedia para aulas', 3, 33.33),
('Impresoras', 'Impresoras láser y multifuncionales', 4, 25.00),
('Switches', 'Equipos de red', 7, 14.28);

-- Ubicaciones
INSERT INTO ubicaciones (nombre, edificio, piso, tipo) VALUES
('Laboratorio 101', 'Facultad Ingeniería', '1', 'laboratorio'),
('Laboratorio 102', 'Facultad Ingeniería', '1', 'laboratorio'),
('Aula 201', 'Facultad Ingeniería', '2', 'aula'),
('Aula 202', 'Facultad Ingeniería', '2', 'aula'),
('Oficina Decanato', 'Facultad Ingeniería', '3', 'oficina'),
('Data Center', 'Edificio Central', 'Sótano', 'laboratorio'),
('Almacén Central', 'Edificio Central', '1', 'almacen'),
('Biblioteca Sala A', 'Biblioteca', '1', 'aula'),
('Biblioteca Sala B', 'Biblioteca', '1', 'aula'),
('Oficina TI', 'Edificio Central', '2', 'oficina');

-- Proveedores
INSERT INTO proveedores (nombre, ruc, contacto_nombre, contacto_email, contacto_telefono) VALUES
('Tecnología Global SAC', '20123456789', 'Carlos Ruiz', 'ventas@tecglobal.com', '999888777'),
('Compumundo EIRL', '20987654321', 'Ana López', 'ana@compumundo.com', '987654321'),
('Redes y Datos SA', '20555666777', 'Pedro Diaz', 'pdiaz@redesydatos.com', '955444333'),
('Servicios TI Pro', '20111222333', 'Luis Torres', 'ltorres@tipro.com', '911222333'),
('Importaciones Tech', '20444555666', 'Sofia M.', 'sofia@impostech.com', '944555666');

-- Equipos (Se insertarán dinámicamente en el script de init si es necesario, pero aquí ponemos algunos ejemplos estáticos)
-- Nota: Para insertar equipos necesitamos los IDs de las otras tablas. 
-- En un script SQL puro es difícil referenciar los IDs generados aleatoriamente arriba sin usar variables o DO blocks complejos.
-- Para simplificar, el script de python init_db.py podría manejar la inserción de datos relacionales o usar un enfoque de DO block aquí.
-- Usaremos un DO block para insertar equipos de prueba vinculados correctamente.

DO $$
DECLARE
    cat_laptop UUID;
    cat_desktop UUID;
    prov_tec UUID;
    prov_compu UUID;
    ubic_lab101 UUID;
    ubic_almacen UUID;
BEGIN
    SELECT id INTO cat_laptop FROM categorias_equipos WHERE nombre = 'Laptops' LIMIT 1;
    SELECT id INTO cat_desktop FROM categorias_equipos WHERE nombre = 'Desktops' LIMIT 1;
    SELECT id INTO prov_tec FROM proveedores WHERE nombre = 'Tecnología Global SAC' LIMIT 1;
    SELECT id INTO prov_compu FROM proveedores WHERE nombre = 'Compumundo EIRL' LIMIT 1;
    SELECT id INTO ubic_lab101 FROM ubicaciones WHERE nombre = 'Laboratorio 101' LIMIT 1;
    SELECT id INTO ubic_almacen FROM ubicaciones WHERE nombre = 'Almacén Central' LIMIT 1;

    -- Equipos
    INSERT INTO equipos (codigo_inventario, nombre, marca, modelo, numero_serie, categoria_id, proveedor_id, ubicacion_actual_id, estado, fecha_compra, fecha_garantia_fin, costo_compra) VALUES
    ('LAP-001', 'Laptop Dell Latitude', 'Dell', 'Latitude 5420', 'SN10001', cat_laptop, prov_tec, ubic_lab101, 'disponible', '2023-01-15', '2026-01-15', 1200.00),
    ('LAP-002', 'Laptop Dell Latitude', 'Dell', 'Latitude 5420', 'SN10002', cat_laptop, prov_tec, ubic_lab101, 'disponible', '2023-01-15', '2026-01-15', 1200.00),
    ('LAP-003', 'Laptop HP ProBook', 'HP', 'ProBook 450', 'SN20001', cat_laptop, prov_compu, ubic_almacen, 'mantenimiento', '2022-06-10', '2025-06-10', 1100.00),
    ('DESK-001', 'PC Lenovo ThinkCentre', 'Lenovo', 'M70q', 'SN30001', cat_desktop, prov_tec, ubic_lab101, 'disponible', '2023-03-20', '2026-03-20', 800.00),
    ('DESK-002', 'PC Lenovo ThinkCentre', 'Lenovo', 'M70q', 'SN30002', cat_desktop, prov_tec, ubic_lab101, 'disponible', '2023-03-20', '2026-03-20', 800.00);

END $$;
