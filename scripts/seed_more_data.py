import sqlite3
import datetime
import random

# Conectar a la base de datos
conn = sqlite3.connect('instance/ferreteria.db')
cursor = conn.cursor()

# Agregar más productos
productos_adicionales = [
    ('HM004', 'Alicate universal', 'Alicate universal 8"', 28.00, 45.00, 25, 5, 1),
    ('HM005', 'Sierra de mano', 'Sierra de mano para madera', 65.00, 95.00, 12, 3, 1),
    ('HM006', 'Nivel de burbuja', 'Nivel de burbuja 60cm', 85.00, 125.00, 8, 2, 1),
    ('HE003', 'Amoladora angular', 'Amoladora angular 4.5"', 180.00, 280.00, 6, 2, 2),
    ('HE004', 'Pistola de calor', 'Pistola de calor 2000W', 220.00, 320.00, 4, 1, 2),
    ('MC003', 'Varilla de hierro', 'Varilla de hierro 3/8"', 25.00, 35.00, 100, 20, 3),
    ('MC004', 'Block de concreto', 'Block de concreto 15x20x40', 8.50, 12.00, 200, 50, 3),
    ('MC005', 'Grava', 'Grava por m³', 150.00, 190.00, 20, 5, 3),
    ('PL003', 'Válvula de paso', 'Válvula de paso 1/2"', 35.00, 55.00, 15, 5, 4),
    ('PL004', 'Pegamento PVC', 'Pegamento para PVC 250ml', 18.00, 28.00, 30, 10, 4),
    ('PL005', 'Llave de chorro', 'Llave de chorro cromada', 45.00, 75.00, 20, 5, 4),
    ('EL003', 'Tomacorriente doble', 'Tomacorriente doble con tierra', 12.00, 20.00, 50, 15, 5),
    ('EL004', 'Breaker 20A', 'Breaker de 20 amperios', 25.00, 40.00, 25, 8, 5),
    ('EL005', 'Extensión eléctrica', 'Extensión eléctrica 10m', 35.00, 55.00, 15, 5, 5),
    ('HM007', 'Cinta métrica', 'Cinta métrica 5m', 22.00, 35.00, 30, 8, 1),
    ('HM008', 'Escuadra', 'Escuadra de carpintero 30cm', 18.00, 28.00, 20, 5, 1),
    ('HE005', 'Soldadora eléctrica', 'Soldadora eléctrica 200A', 850.00, 1200.00, 2, 1, 2),
    ('MC006', 'Cal hidratada', 'Cal hidratada 25kg', 15.00, 22.00, 80, 15, 3),
    ('PL006', 'Sifón para lavamanos', 'Sifón cromado para lavamanos', 28.00, 45.00, 12, 3, 4)
]

for producto in productos_adicionales:
    cursor.execute('''
    INSERT OR IGNORE INTO productos (codigo, nombre, descripcion, precio_compra, precio_venta, stock, stock_minimo, categoria_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', producto)

# Agregar más clientes
clientes_adicionales = [
    ('Ana', 'Martínez', 'ana.martinez@email.com', '555-2468', 'Zona 10, Ciudad', '456789-0'),
    ('Luis', 'García', 'luis.garcia@email.com', '555-3579', 'Zona 1, Centro', '567890-1'),
    ('Carmen', 'López', 'carmen.lopez@email.com', '555-4680', 'Zona 15, Vista Hermosa', '678901-2'),
    ('Roberto', 'Hernández', 'roberto.hernandez@email.com', '555-5791', 'Zona 7, Kaminal Juyú', '789012-3'),
    ('Patricia', 'Morales', 'patricia.morales@email.com', '555-6802', 'Zona 11, Mariscal', '890123-4'),
    ('Fernando', 'Castillo', 'fernando.castillo@email.com', '555-7913', 'Zona 13, Aurora', '901234-5'),
    ('Sofía', 'Ramírez', 'sofia.ramirez@email.com', '555-8024', 'Zona 14, La Villa', '012345-6'),
    ('Diego', 'Torres', 'diego.torres@email.com', '555-9135', 'Zona 16, Cayalá', '123456-7'),
    ('Valeria', 'Flores', 'valeria.flores@email.com', '555-0246', 'Zona 9, Centro Histórico', '234567-8'),
    ('Andrés', 'Vargas', 'andres.vargas@email.com', '555-1357', 'Zona 12, Colonia', '345678-9')
]

for cliente in clientes_adicionales:
    cursor.execute('''
    INSERT OR IGNORE INTO clientes (nombre, apellido, email, telefono, direccion, nit)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', cliente)

# Generar ventas adicionales para los últimos 30 días
cursor.execute('SELECT id FROM clientes')
cliente_ids = [row[0] for row in cursor.fetchall()]

cursor.execute('SELECT id FROM usuarios LIMIT 1')
usuario_id = cursor.fetchone()[0]

cursor.execute('SELECT id, precio_venta, stock FROM productos WHERE stock > 0')
productos_disponibles = cursor.fetchall()

# Generar ventas para los últimos 30 días
for i in range(50):  # 50 ventas adicionales
    # Fecha aleatoria en los últimos 30 días
    dias_atras = random.randint(0, 30)
    fecha_venta = datetime.datetime.now() - datetime.timedelta(days=dias_atras)
    
    # Cliente aleatorio (puede ser None para cliente general)
    cliente_id = random.choice(cliente_ids + [None, None, None])  # Mayor probabilidad de cliente general
    
    # Número de factura
    numero_factura = f'F-{fecha_venta.strftime("%Y%m")}{random.randint(100, 999)}'
    
    # Crear venta
    cursor.execute('''
    INSERT INTO ventas (cliente_id, usuario_id, fecha, total, numero_factura)
    VALUES (?, ?, ?, ?, ?)
    ''', (cliente_id, usuario_id, fecha_venta, 0, numero_factura))
    
    venta_id = cursor.lastrowid
    
    # Agregar productos aleatorios a la venta
    num_productos = random.randint(1, 5)
    productos_venta = random.sample(productos_disponibles, min(num_productos, len(productos_disponibles)))
    
    total_venta = 0
    
    for producto_id, precio_venta, stock_actual in productos_venta:
        cantidad = random.randint(1, min(3, stock_actual))
        subtotal = precio_venta * cantidad
        total_venta += subtotal
        
        # Insertar detalle de venta
        cursor.execute('''
        INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario, subtotal)
        VALUES (?, ?, ?, ?, ?)
        ''', (venta_id, producto_id, cantidad, precio_venta, subtotal))
        
        # Actualizar stock
        cursor.execute('''
        UPDATE productos SET stock = stock - ? WHERE id = ?
        ''', (cantidad, producto_id))
    
    # Actualizar total de la venta
    cursor.execute('''
    UPDATE ventas SET total = ? WHERE id = ?
    ''', (total_venta, venta_id))

# Simular algunos productos con stock muy bajo para las alertas
productos_stock_bajo = [
    ('HE005', 0),  # Soldadora agotada
    ('MC006', 2),  # Cal con stock crítico
    ('PL006', 1),  # Sifón con stock crítico
    ('EL004', 3),  # Breaker con stock bajo
]

for codigo, nuevo_stock in productos_stock_bajo:
    cursor.execute('''
    UPDATE productos SET stock = ? WHERE codigo = ?
    ''', (nuevo_stock, codigo))

# Guardar cambios
conn.commit()
print("Datos adicionales agregados correctamente:")
print(f"- {len(productos_adicionales)} productos adicionales")
print(f"- {len(clientes_adicionales)} clientes adicionales") 
print("- 50 ventas adicionales de los últimos 30 días")
print("- Productos con stock bajo para alertas")

conn.close()
