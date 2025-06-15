import sqlite3
import os
import datetime

# Crear la carpeta de base de datos si no existe
if not os.path.exists('instance'):
    os.makedirs('instance')

# Conectar a la base de datos (la crea si no existe)
conn = sqlite3.connect('instance/ferreteria.db')
cursor = conn.cursor()

# Crear tablas
cursor.execute('''
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    rol TEXT NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    descripcion TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    precio_compra REAL NOT NULL,
    precio_venta REAL NOT NULL,
    stock INTEGER NOT NULL,
    stock_minimo INTEGER NOT NULL,
    categoria_id INTEGER,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (categoria_id) REFERENCES categorias (id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    email TEXT UNIQUE,
    telefono TEXT,
    direccion TEXT,
    nit TEXT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER,
    usuario_id INTEGER NOT NULL,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total REAL NOT NULL,
    estado TEXT DEFAULT 'completada',
    numero_factura TEXT UNIQUE,
    FOREIGN KEY (cliente_id) REFERENCES clientes (id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS detalle_ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venta_id INTEGER NOT NULL,
    producto_id INTEGER NOT NULL,
    cantidad INTEGER NOT NULL,
    precio_unitario REAL NOT NULL,
    subtotal REAL NOT NULL,
    FOREIGN KEY (venta_id) REFERENCES ventas (id),
    FOREIGN KEY (producto_id) REFERENCES productos (id)
)
''')

# Insertar datos de ejemplo
# Usuario administrador (contraseña: admin123)
cursor.execute('''
INSERT OR IGNORE INTO usuarios (nombre, email, password, rol)
VALUES (?, ?, ?, ?)
''', ('Administrador', 'admin@ferreteria.com', 'pbkdf2:sha256:150000$lLVTXvoj$ec82f10940b8e36a7b34fac790f9b3696e9ad7188be96e26262896f0d2f82928', 'admin'))

# Categorías
categorias = [
    ('Herramientas manuales', 'Herramientas que funcionan manualmente'),
    ('Herramientas eléctricas', 'Herramientas que funcionan con electricidad'),
    ('Materiales de construcción', 'Materiales para construcción'),
    ('Plomería', 'Artículos para plomería'),
    ('Electricidad', 'Artículos para instalaciones eléctricas')
]

for categoria in categorias:
    cursor.execute('''
    INSERT OR IGNORE INTO categorias (nombre, descripcion)
    VALUES (?, ?)
    ''', categoria)

# Productos
productos = [
    ('HM001', 'Martillo', 'Martillo de carpintero', 45.00, 65.00, 20, 5, 1),
    ('HM002', 'Destornillador Phillips', 'Destornillador de estrella', 15.00, 25.00, 30, 10, 1),
    ('HM003', 'Llave ajustable', 'Llave inglesa de 10"', 35.00, 55.00, 15, 3, 1),
    ('HE001', 'Taladro eléctrico', 'Taladro eléctrico 750W', 250.00, 350.00, 8, 2, 2),
    ('HE002', 'Sierra circular', 'Sierra circular 1200W', 320.00, 450.00, 5, 2, 2),
    ('MC001', 'Cemento', 'Bolsa de cemento 50kg', 75.00, 95.00, 50, 10, 3),
    ('MC002', 'Arena', 'Arena fina por m³', 180.00, 220.00, 15, 3, 3),
    ('PL001', 'Tubo PVC 1/2"', 'Tubo PVC 1/2" x 6m', 18.00, 28.00, 40, 10, 4),
    ('PL002', 'Codo PVC 1/2"', 'Codo PVC 1/2"', 2.50, 5.00, 100, 20, 4),
    ('EL001', 'Cable #12', 'Cable #12 por metro', 3.50, 6.00, 200, 50, 5),
    ('EL002', 'Interruptor simple', 'Interruptor de luz simple', 8.00, 15.00, 30, 10, 5)
]

for producto in productos:
    cursor.execute('''
    INSERT OR IGNORE INTO productos (codigo, nombre, descripcion, precio_compra, precio_venta, stock, stock_minimo, categoria_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', producto)

# Clientes
clientes = [
    ('Juan', 'Pérez', 'juan.perez@email.com', '555-1234', 'Calle Principal 123', '123456-7'),
    ('María', 'González', 'maria.gonzalez@email.com', '555-5678', 'Avenida Central 456', '234567-8'),
    ('Carlos', 'Rodríguez', 'carlos.rodriguez@email.com', '555-9012', 'Boulevard Norte 789', '345678-9')
]

for cliente in clientes:
    cursor.execute('''
    INSERT OR IGNORE INTO clientes (nombre, apellido, email, telefono, direccion, nit)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', cliente)

# Ventas y detalles de ventas
# Obtener IDs
cursor.execute('SELECT id FROM clientes LIMIT 3')
cliente_ids = [row[0] for row in cursor.fetchall()]

cursor.execute('SELECT id FROM usuarios LIMIT 1')
usuario_id = cursor.fetchone()[0]

cursor.execute('SELECT id FROM productos LIMIT 5')
producto_ids = [row[0] for row in cursor.fetchall()]

# Crear algunas ventas de ejemplo
for i in range(3):
    fecha = datetime.datetime.now() - datetime.timedelta(days=i)
    total = 0
    
    # Crear venta
    cursor.execute('''
    INSERT INTO ventas (cliente_id, usuario_id, fecha, total, numero_factura)
    VALUES (?, ?, ?, ?, ?)
    ''', (cliente_ids[i % len(cliente_ids)], usuario_id, fecha, 0, f'F-{2023}0{i+1}'))
    
    venta_id = cursor.lastrowid
    
    # Agregar detalles de venta (2-3 productos por venta)
    for j in range(2, 4):
        producto_id = producto_ids[(i+j) % len(producto_ids)]
        
        # Obtener precio del producto
        cursor.execute('SELECT precio_venta FROM productos WHERE id = ?', (producto_id,))
        precio = cursor.fetchone()[0]
        
        cantidad = j
        subtotal = precio * cantidad
        total += subtotal
        
        cursor.execute('''
        INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario, subtotal)
        VALUES (?, ?, ?, ?, ?)
        ''', (venta_id, producto_id, cantidad, precio, subtotal))
        
        # Actualizar stock
        cursor.execute('''
        UPDATE productos SET stock = stock - ? WHERE id = ?
        ''', (cantidad, producto_id))
    
    # Actualizar total de la venta
    cursor.execute('''
    UPDATE ventas SET total = ? WHERE id = ?
    ''', (total, venta_id))

# Guardar cambios y cerrar conexión
conn.commit()
print("Base de datos inicializada correctamente con datos de ejemplo.")
conn.close()
