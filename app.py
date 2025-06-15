from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import datetime
from functools import wraps
import io
import csv
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from reportlab.platypus.flowables import KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import pandas as pd

from reportlab.lib.styles import getSampleStyleSheet



app = Flask(__name__)
app.secret_key = 'clave_secreta_ferreteria'
app.config['DATABASE'] = 'instance/ferreteria.db'

# Agregar context processor para 'now'
@app.context_processor
def inject_now():
    # Usar la hora de Caracas, Venezuela (UTC-4)
    tz = datetime.timezone(datetime.timedelta(hours=-4))
    now_caracas = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("Hora Caracas:", now_caracas)
    return {'now': now_caracas}

# Función para obtener conexión a la base de datos
def get_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

# Decorador para verificar si el usuario está logueado
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Por favor inicie sesión para acceder a esta página', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Rutas de autenticación
@app.route('/')
def index():
    if 'usuario_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        db = get_db()
        usuario = db.execute('SELECT * FROM usuarios WHERE email = ? AND password = ?', 
                            (email, password)).fetchone()
        
        if usuario:
            session['usuario_id'] = usuario['id']
            session['usuario_nombre'] = usuario['nombre']
            session['usuario_rol'] = usuario['rol']
            flash(f'Bienvenido, {usuario["nombre"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciales incorrectas. Intente nuevamente.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Ha cerrado sesión correctamente', 'info')
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    hoy = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("Hora Caracas dashboard:", hoy)
    ventas_hoy = db.execute(
        'SELECT COUNT(*) as count, SUM(total) as total FROM ventas WHERE date(fecha) = ?', 
        (hoy,)
    ).fetchone()
    
    # Productos con stock bajo
    productos_stock_bajo = db.execute(
        'SELECT * FROM productos WHERE stock <= stock_minimo ORDER BY stock ASC LIMIT 5'
    ).fetchall()
    
    # Últimas ventas
    ultimas_ventas = db.execute(
        '''
        SELECT v.id, v.fecha, v.total, c.nombre || ' ' || c.apellido as cliente, v.numero_factura
        FROM ventas v
        LEFT JOIN clientes c ON v.cliente_id = c.id
        ORDER BY v.fecha DESC LIMIT 5
        '''
    ).fetchall()

    # Agregar conteo de productos y clientes
    total_productos = db.execute('SELECT COUNT(*) FROM productos').fetchone()[0]
    total_clientes = db.execute('SELECT COUNT(*) FROM clientes').fetchone()[0]
    
    return render_template(
        'dashboard.html',
        total_productos=total_productos,
        total_clientes=total_clientes,
        ventas_hoy=ventas_hoy,
        productos_stock_bajo=productos_stock_bajo,
        ultimas_ventas=ultimas_ventas
    )

# Rutas de productos
@app.route('/productos')
@login_required
def productos():
    db = get_db()
    productos = db.execute(
        '''
        SELECT p.*, c.nombre as categoria_nombre
        FROM productos p
        LEFT JOIN categorias c ON p.categoria_id = c.id
        ORDER BY p.nombre
        '''
    ).fetchall()
    
    categorias = db.execute('SELECT * FROM categorias ORDER BY nombre').fetchall()
    
    return render_template('productos/index.html', productos=productos, categorias=categorias)

@app.route('/productos/crear', methods=['POST'])
@login_required
def crear_producto():
    if request.method == 'POST':
        codigo = request.form['codigo']
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        precio_compra = float(request.form['precio_compra'])
        precio_venta = float(request.form['precio_venta'])
        stock = int(request.form['stock'])
        stock_minimo = int(request.form['stock_minimo'])
        categoria_id = int(request.form['categoria_id'])
        
        db = get_db()
        try:
            db.execute(
                '''
                INSERT INTO productos (codigo, nombre, descripcion, precio_compra, precio_venta, stock, stock_minimo, categoria_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (codigo, nombre, descripcion, precio_compra, precio_venta, stock, stock_minimo, categoria_id)
            )
            db.commit()
            flash('Producto creado correctamente', 'success')
        except sqlite3.IntegrityError:
            flash('Error: El código del producto ya existe', 'danger')
        
    return redirect(url_for('productos'))

@app.route('/productos/editar/<int:id>', methods=['POST'])
@login_required
def editar_producto(id):
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        precio_compra = float(request.form['precio_compra'])
        precio_venta = float(request.form['precio_venta'])
        stock = int(request.form['stock'])
        stock_minimo = int(request.form['stock_minimo'])
        categoria_id = int(request.form['categoria_id'])
        
        db = get_db()
        db.execute(
            '''
            UPDATE productos
            SET nombre = ?, descripcion = ?, precio_compra = ?, precio_venta = ?, 
                stock = ?, stock_minimo = ?, categoria_id = ?
            WHERE id = ?
            ''',
            (nombre, descripcion, precio_compra, precio_venta, stock, stock_minimo, categoria_id, id)
        )
        db.commit()
        flash('Producto actualizado correctamente', 'success')
        
    return redirect(url_for('productos'))

@app.route('/productos/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_producto(id):
    db = get_db()
    
    # Verificar si el producto está en alguna venta
    ventas = db.execute(
        'SELECT COUNT(*) as count FROM detalle_ventas WHERE producto_id = ?', 
        (id,)
    ).fetchone()['count']
    
    if ventas > 0:
        flash('No se puede eliminar el producto porque está asociado a ventas', 'danger')
    else:
        db.execute('DELETE FROM productos WHERE id = ?', (id,))
        db.commit()
        flash('Producto eliminado correctamente', 'success')
    
    return redirect(url_for('productos'))

# Rutas de clientes
@app.route('/clientes')
@login_required
def clientes():
    db = get_db()
    clientes = db.execute('SELECT * FROM clientes ORDER BY nombre').fetchall()
    return render_template('clientes/index.html', clientes=clientes)

@app.route('/clientes/crear', methods=['POST'])
@login_required
def crear_cliente():
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        email = request.form['email']
        telefono = request.form['telefono']
        direccion = request.form['direccion']
        nit = request.form['nit']
        # Obtener hora de Caracas
        fecha_registro = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-4))).strftime('%Y-%m-%d %H:%M:%S')
        
        db = get_db()
        try:
            db.execute(
                '''
                INSERT INTO clientes (nombre, apellido, email, telefono, direccion, nit, fecha_registro)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''',
                (nombre, apellido, email, telefono, direccion, nit, fecha_registro)
            )
            db.commit()
            flash('Cliente creado correctamente', 'success')
        except sqlite3.IntegrityError:
            flash('Error: El email ya está registrado', 'danger')
        
    return redirect(url_for('clientes'))

@app.route('/clientes/editar/<int:id>', methods=['POST'])
@login_required
def editar_cliente(id):
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        email = request.form['email']
        telefono = request.form['telefono']
        direccion = request.form['direccion']
        nit = request.form['nit']
        
        db = get_db()
        try:
            db.execute(
                '''
                UPDATE clientes
                SET nombre = ?, apellido = ?, email = ?, telefono = ?, direccion = ?, nit = ?
                WHERE id = ?
                ''',
                (nombre, apellido, email, telefono, direccion, nit, id)
            )
            db.commit()
            flash('Cliente actualizado correctamente', 'success')
        except sqlite3.IntegrityError:
            flash('Error: El email ya está registrado', 'danger')
        
    return redirect(url_for('clientes'))

@app.route('/clientes/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_cliente(id):
    db = get_db()
    
    # Verificar si el cliente tiene ventas
    ventas = db.execute(
        'SELECT COUNT(*) as count FROM ventas WHERE cliente_id = ?', 
        (id,)
    ).fetchone()['count']
    
    if ventas > 0:
        flash('No se puede eliminar el cliente porque tiene ventas asociadas', 'danger')
    else:
        db.execute('DELETE FROM clientes WHERE id = ?', (id,))
        db.commit()
        flash('Cliente eliminado correctamente', 'success')
    
    return redirect(url_for('clientes'))

@app.route('/clientes/<int:id>/historial')
@login_required
def historial_cliente(id):
    db = get_db()
    
    cliente = db.execute('SELECT * FROM clientes WHERE id = ?', (id,)).fetchone()
    
    if not cliente:
        flash('Cliente no encontrado', 'danger')
        return redirect(url_for('clientes'))
    
    ventas = db.execute(
        '''
        SELECT v.*, COUNT(dv.id) as num_items
        FROM ventas v
        LEFT JOIN detalle_ventas dv ON v.id = dv.venta_id
        WHERE v.cliente_id = ?
        GROUP BY v.id
        ORDER BY v.fecha DESC
        ''',
        (id,)
    ).fetchall()
    
    return render_template('clientes/historial.html', cliente=cliente, ventas=ventas)

# Rutas de ventas
@app.route('/ventas')
@login_required
def ventas():
    db = get_db()
    ventas = db.execute(
        '''
        SELECT v.*, c.nombre || ' ' || c.apellido as cliente_nombre
        FROM ventas v
        LEFT JOIN clientes c ON v.cliente_id = c.id
        ORDER BY v.fecha DESC
        '''
    ).fetchall()
    
    return render_template('ventas/index.html', ventas=ventas)

@app.route('/ventas/nueva')
@login_required
def nueva_venta():
    db = get_db()
    clientes = db.execute('SELECT * FROM clientes ORDER BY nombre').fetchall()
    productos = db.execute(
        '''
        SELECT p.*, c.nombre as categoria_nombre
        FROM productos p
        LEFT JOIN categorias c ON p.categoria_id = c.id
        WHERE p.stock > 0
        ORDER BY p.nombre
        '''
    ).fetchall()
    # Usar hora de Caracas para número de factura
    tz = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ultimo_numero = db.execute(
        'SELECT numero_factura FROM ventas ORDER BY id DESC LIMIT 1'
    ).fetchone()
    if ultimo_numero and ultimo_numero['numero_factura']:
        partes = ultimo_numero['numero_factura'].split('-')
        if len(partes) == 2:
            try:
                nuevo_numero = int(partes[1]) + 1
                numero_factura = f"{partes[0]}-{nuevo_numero:06d}"
            except ValueError:
                numero_factura = f"F-{datetime.datetime.now().strftime('%Y%m')}001"
        else:
            numero_factura = f"F-{datetime.datetime.now().strftime('%Y%m')}001"
    else:
        numero_factura = f"F-{datetime.datetime.now().strftime('%Y%m')}001"
    return render_template(
        'ventas/nueva.html', 
        clientes=clientes, 
        productos=productos,
        numero_factura=numero_factura
    )

@app.route('/ventas/crear', methods=['POST'])
@login_required
def crear_venta():
    if request.method == 'POST':
        data = request.json
        cliente_id = data.get('cliente_id')
        items = data.get('items', [])
        total = data.get('total', 0)
        numero_factura = data.get('numero_factura')
        
        if not items:
            return jsonify({'success': False, 'message': 'No hay productos en la venta'})
        
        db = get_db()
        
        try:
            # Crear la venta
            cursor = db.cursor()
            cursor.execute(
                '''
                INSERT INTO ventas (cliente_id, usuario_id, total, numero_factura)
                VALUES (?, ?, ?, ?)
                ''',
                (cliente_id, session['usuario_id'], total, numero_factura)
            )
            
            venta_id = cursor.lastrowid
            
            # Agregar los detalles de la venta
            for item in items:
                producto_id = item['id']
                cantidad = item['cantidad']
                precio = item['precio']
                subtotal = item['subtotal']
                
                cursor.execute(
                    '''
                    INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario, subtotal)
                    VALUES (?, ?, ?, ?, ?)
                    ''',
                    (venta_id, producto_id, cantidad, precio, subtotal)
                )
                
                # Actualizar el stock
                cursor.execute(
                    'UPDATE productos SET stock = stock - ? WHERE id = ?',
                    (cantidad, producto_id)
                )
            
            db.commit()
            return jsonify({'success': True, 'venta_id': venta_id})
        
        except Exception as e:
            db.rollback()
            return jsonify({'success': False, 'message': str(e)})
    
    return jsonify({'success': False, 'message': 'Método no permitido'})

@app.route('/ventas/<int:id>')
@login_required
def detalle_venta(id):
    db = get_db()
    
    venta = db.execute(
        '''
        SELECT v.*, c.nombre || ' ' || c.apellido as cliente_nombre, c.nit, c.direccion
        FROM ventas v
        LEFT JOIN clientes c ON v.cliente_id = c.id
        WHERE v.id = ?
        ''',
        (id,)
    ).fetchone()
    
    if not venta:
        flash('Venta no encontrada', 'danger')
        return redirect(url_for('ventas'))
    
    detalles = db.execute(
        '''
        SELECT dv.*, p.nombre as producto_nombre, p.codigo as producto_codigo
        FROM detalle_ventas dv
        JOIN productos p ON dv.producto_id = p.id
        WHERE dv.venta_id = ?
        ''',
        (id,)
    ).fetchall()
    
    return render_template('ventas/detalle.html', venta=venta, detalles=detalles)

@app.route('/ventas/<int:id>/factura')
@login_required
def generar_factura(id):
    db = get_db()
    
    # Obtener datos de la venta
    venta = db.execute(
        '''
        SELECT v.*, c.nombre || ' ' || c.apellido as cliente_nombre, c.nit, c.direccion, c.telefono, c.email
        FROM ventas v
        LEFT JOIN clientes c ON v.cliente_id = c.id
        WHERE v.id = ?
        ''',
        (id,)
    ).fetchone()
    
    if not venta:
        flash('Venta no encontrada', 'danger')
        return redirect(url_for('ventas'))
    
    # Obtener detalles de la venta
    detalles = db.execute(
        '''
        SELECT dv.*, p.nombre as producto_nombre, p.codigo as producto_codigo, p.descripcion
        FROM detalle_ventas dv
        JOIN productos p ON dv.producto_id = p.id
        WHERE dv.venta_id = ?
        ''',
        (id,)
    ).fetchall()
    
    # Configuración del documento
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, 
                          rightMargin=40, leftMargin=40,
                          topMargin=60, bottomMargin=60)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    styles.add(ParagraphStyle(
        name='Header1',
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#2c3e50')
    ))
    
    styles.add(ParagraphStyle(
        name='Header2',
        fontSize=12,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#7f8c8d')
    ))
    
    styles.add(ParagraphStyle(
        name='Label',
        fontSize=10,
        textColor=colors.HexColor('#7f8c8d')
    ))
    
    styles.add(ParagraphStyle(
        name='Value',
        fontSize=10,
        textColor=colors.HexColor('#2c3e50')
    ))
    
    styles.add(ParagraphStyle(
        name='TotalLabel',
        fontSize=12,
        textColor=colors.HexColor('#2c3e50'),
        alignment=TA_RIGHT
    ))
    
    styles.add(ParagraphStyle(
        name='TotalValue',
        fontSize=12,
        textColor=colors.HexColor('#2c3e50'),
        alignment=TA_RIGHT,
        fontName='Helvetica-Bold'
    ))
    
    # Logo (opcional)
    try:
        logo_path = 'static/img/logo.png'
        logo = Image(logo_path, width=120, height=60)
        elements.append(logo)
    except:
        pass
    
    # Encabezado
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("FACTURA", styles['Header1']))
    elements.append(Paragraph(f"No. {venta['numero_factura']}", styles['Header2']))
    elements.append(Spacer(1, 30))
    
    # Información de la empresa y cliente
    empresa_data = [
        ["<b>EMPRESA XYZ</b>", ""],
        ["Dirección: Av. Principal 1234", ""],
        ["Teléfono: +123 456 7890", ""],
        ["Email: info@empresa.com", ""],
        ["NIT: 123456789", ""]
    ]
    
    cliente_data = [
        ["<b>DATOS DEL CLIENTE</b>", ""],
        [f"<b>Nombre:</b> {venta['cliente_nombre']}", ""],
        [f"<b>NIT:</b> {venta['nit'] or 'N/A'}", ""],
        [f"<b>Dirección:</b> {venta['direccion'] or 'N/A'}", ""],
        [f"<b>Teléfono:</b> {venta['telefono'] or 'N/A'}", ""],
        [f"<b>Email:</b> {venta['email'] or 'N/A'}", ""]
    ]
    
    # Crear tablas
    empresa_table = Table(empresa_data, colWidths=[doc.width/2]*2)
    cliente_table = Table(cliente_data, colWidths=[doc.width/2]*2)
    
    info_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ])
    
    empresa_table.setStyle(info_style)
    cliente_table.setStyle(info_style)
    
    elements.append(KeepTogether([empresa_table, cliente_table]))
    elements.append(Spacer(1, 30))
    
    # Detalles de factura
    elements.append(Paragraph(f"<b>Fecha de emisión:</b> {venta['fecha']}", styles['Value']))
    elements.append(Spacer(1, 20))
    
    # Tabla de productos
    data = [
        ['CÓDIGO', 'DESCRIPCIÓN', 'CANT.', 'PRECIO', 'SUBTOTAL']
    ]
    
    for detalle in detalles:
        data.append([
            detalle['producto_codigo'],
            Paragraph(f"<b>{detalle['producto_nombre']}</b><br/>{detalle['descripcion']}", styles['Value']),
            str(detalle['cantidad']),
            f"${detalle['precio_unitario']:.2f}",
            f"${detalle['subtotal']:.2f}"
        ])
    
    table = Table(data, colWidths=[60, 200, 50, 80, 80], repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 20))
    
    # Totales
    total_data = [
        ['Subtotal:', f"${venta['total']:.2f}"],
        ['IVA (12%):', f"${venta['total'] * 0.12:.2f}"],
        ['<b>TOTAL:</b>', f"<b>${venta['total'] * 1.12:.2f}</b>"]
    ]
    
    total_table = Table(total_data, colWidths=[400, 100])
    total_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('TEXTCOLOR', (0, -1), (1, -1), colors.HexColor('#e74c3c')),
        ('FONTNAME', (0, -1), (1, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, -1), (1, -1), 12),
    ]))
    
    elements.append(total_table)
    elements.append(Spacer(1, 30))
    
    # Notas
    elements.append(Paragraph("<b>Condiciones de pago:</b>", styles['Label']))
    elements.append(Paragraph("Pago al contado. No se aceptan devoluciones después de 7 días.", styles['Value']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("<b>Gracias por su compra!</b>", styles['Value']))
    
    # Pie de página
    footer = Paragraph(
        "Empresa XYZ • Av. Principal 1234 • Tel: +123 456 7890 • info@empresa.com",
        ParagraphStyle(
            name='Footer',
            fontSize=8,
            textColor=colors.HexColor('#7f8c8d'),
            alignment=TA_CENTER
        )
    )
    elements.append(Spacer(1, 20))
    elements.append(footer)
    
    # Generar PDF
    doc.build(elements)
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"factura_{venta['numero_factura']}.pdf",
        mimetype='application/pdf'
    )



# Rutas de reportes
@app.route('/reportes')
@login_required
def reportes():
    return render_template('reportes/index.html')

@app.route('/reportes/ventas-diarias', methods=['GET', 'POST'])
@login_required
def reporte_ventas_diarias():
    tz = datetime.timezone(datetime.timedelta(hours=-4))
    fecha = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    db = get_db()
    ventas = db.execute(
        '''
        SELECT v.*, c.nombre || ' ' || c.apellido as cliente_nombre
        FROM ventas v
        LEFT JOIN clientes c ON v.cliente_id = c.id
        WHERE date(v.fecha) = ?
        ORDER BY v.fecha
        ''',
        (fecha,)
    ).fetchall()
    total_ventas = sum(venta['total'] for venta in ventas)
    if request.form.get('formato') == 'pdf':
        # Crear PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        styles = getSampleStyleSheet()
        
        # Título
        elements.append(Paragraph(f"REPORTE DE VENTAS DIARIAS - {fecha}", styles['Title']))
        elements.append(Paragraph(f"Generado el: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        elements.append(Paragraph(" ", styles['Normal']))  # Espacio
        
        # Tabla de ventas
        data = [['#', 'Factura', 'Cliente', 'Hora', 'Total']]
        
        for i, venta in enumerate(ventas, 1):
            # Manejar microsegundos en la fecha
            try:
                dt = datetime.datetime.strptime(venta['fecha'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                dt = datetime.datetime.strptime(venta['fecha'], '%Y-%m-%d %H:%M:%S')
            hora = dt.strftime('%H:%M:%S')
            data.append([
                i,
                venta['numero_factura'],
                venta['cliente_nombre'] or 'Cliente General',
                hora,
                f"${venta['total']:.2f}"
            ])
        
        # Agregar total
        data.append(['', '', '', 'TOTAL:', f"${total_ventas:.2f}"])
        
        # Crear tabla
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('BACKGROUND', (0, -1), (-1, -1), colors.grey),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(table)
        
        # Construir PDF
        doc.build(elements)
        
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"ventas_diarias_{fecha}.pdf",
            mimetype='application/pdf'
        )
    
    elif request.form.get('formato') == 'csv':
        # Crear CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Encabezados
        writer.writerow(['ID', 'Factura', 'Cliente', 'Fecha', 'Total'])
        
        # Datos
        for venta in ventas:
            writer.writerow([
                venta['id'],
                venta['numero_factura'],
                venta['cliente_nombre'] or 'Cliente General',
                venta['fecha'],
                venta['total']
            ])
        
        # Fila de total
        writer.writerow(['', '', '', 'TOTAL', total_ventas])
        
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            as_attachment=True,
            download_name=f"ventas_diarias_{fecha}.csv",
            mimetype='text/csv'
        )
    
    return render_template(
        'reportes/ventas_diarias.html',
        ventas=ventas,
        fecha=fecha,
        total_ventas=total_ventas
    )

@app.route('/reportes/productos-stock-bajo')
@login_required
def reporte_productos_stock_bajo():
    tz = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    db = get_db()
    productos = db.execute(
        '''
        SELECT p.*, c.nombre as categoria_nombre
        FROM productos p
        LEFT JOIN categorias c ON p.categoria_id = c.id
        WHERE p.stock <= p.stock_minimo
        ORDER BY (p.stock * 1.0 / p.stock_minimo) ASC
        '''
    ).fetchall()
    
    if request.args.get('formato') == 'pdf':
        # Crear PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        styles = getSampleStyleSheet()
        
        # Título
        elements.append(Paragraph("REPORTE DE PRODUCTOS CON STOCK BAJO", styles['Title']))
        elements.append(Paragraph(f"Generado el: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        elements.append(Paragraph(" ", styles['Normal']))  # Espacio
        
        # Tabla de productos
        data = [['Código', 'Producto', 'Categoría', 'Stock Actual', 'Stock Mínimo', 'Estado']]
        
        for producto in productos:
            # Calcular estado
            if producto['stock'] == 0:
                estado = "AGOTADO"
            elif producto['stock'] <= producto['stock_minimo'] * 0.5:
                estado = "CRÍTICO"
            else:
                estado = "BAJO"
                
            data.append([
                producto['codigo'],
                producto['nombre'],
                producto['categoria_nombre'],
                producto['stock'],
                producto['stock_minimo'],
                estado
            ])
        
        # Crear tabla
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(table)
        
        # Construir PDF
        doc.build(elements)
        
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"productos_stock_bajo_{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.pdf",
            mimetype='application/pdf'
        )
    elif request.args.get('formato') == 'csv':
        # Crear CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Encabezados
        writer.writerow(['Código', 'Producto', 'Categoría', 'Stock Actual', 'Stock Mínimo', 'Estado'])
        
        # Datos
        for producto in productos:
            # Calcular estado
            if producto['stock'] == 0:
                estado = "AGOTADO"
            elif producto['stock'] <= producto['stock_minimo'] * 0.5:
                estado = "CRÍTICO"
            else:
                estado = "BAJO"
                
            writer.writerow([
                producto['codigo'],
                producto['nombre'],
                producto['categoria_nombre'],
                producto['stock'],
                producto['stock_minimo'],
                estado
            ])
        
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            as_attachment=True,
            download_name=f"productos_stock_bajo_{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.csv",
            mimetype='text/csv'
        )
    
    return render_template('reportes/productos_stock_bajo.html', productos=productos)

@app.route('/reportes/ventas-periodo', methods=['GET', 'POST'])
@login_required
def reporte_ventas_periodo():
    if request.method == 'POST':
        fecha_inicio = request.form['fecha_inicio']
        fecha_fin = request.form['fecha_fin']
        formato = request.form.get('formato')
        
        db = get_db()
        ventas = db.execute(
            '''
            SELECT v.*, c.nombre || ' ' || c.apellido as cliente_nombre
            FROM ventas v
            LEFT JOIN clientes c ON v.cliente_id = c.id
            WHERE date(v.fecha) BETWEEN ? AND ?
            ORDER BY v.fecha
            ''',
            (fecha_inicio, fecha_fin)
        ).fetchall()
        
        total_ventas = sum(venta['total'] for venta in ventas)
        # Calcular días del período
        dias_periodo = (datetime.datetime.strptime(fecha_fin, '%Y-%m-%d') - datetime.datetime.strptime(fecha_inicio, '%Y-%m-%d')).days + 1
        
        if formato == 'pdf':
            # Crear PDF
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []
            
            styles = getSampleStyleSheet()
            
            # Título
            elements.append(Paragraph(f"REPORTE DE VENTAS - {fecha_inicio} al {fecha_fin}", styles['Title']))
            elements.append(Paragraph(f"Generado el: {datetime.datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
            elements.append(Paragraph(" ", styles['Normal']))
            
            # Tabla de ventas
            data = [['Factura', 'Cliente', 'Fecha', 'Total']]
            
            for venta in ventas:
                data.append([
                    venta['numero_factura'],
                    venta['cliente_nombre'] or 'Cliente General',
                    venta['fecha'],
                    f"${venta['total']:.2f}"
                ])
            
            data.append(['', '', 'TOTAL:', f"${total_ventas:.2f}"])
            
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
                ('BACKGROUND', (0, -1), (-1, -1), colors.grey),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            elements.append(table)
            doc.build(elements)
            buffer.seek(0)
            
            return send_file(
                buffer,
                as_attachment=True,
                download_name=f"ventas_periodo_{fecha_inicio}_{fecha_fin}.pdf",
                mimetype='application/pdf'
            )
        
        elif formato == 'csv':
            # Crear CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            writer.writerow(['Factura', 'Cliente', 'Fecha', 'Total'])
            
            for venta in ventas:
                writer.writerow([
                    venta['numero_factura'],
                    venta['cliente_nombre'] or 'Cliente General',
                    venta['fecha'],
                    venta['total']
                ])
            
            writer.writerow(['', '', 'TOTAL', total_ventas])
            
            output.seek(0)
            
            return send_file(
                io.BytesIO(output.getvalue().encode('utf-8')),
                as_attachment=True,
                download_name=f"ventas_periodo_{fecha_inicio}_{fecha_fin}.csv",
                mimetype='text/csv'
            )
        
        return render_template(
            'reportes/ventas_periodo.html',
            ventas=ventas,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            total_ventas=total_ventas,
            dias_periodo=dias_periodo
        )
    
    return redirect(url_for('reportes'))

@app.route('/reportes/productos-mas-vendidos', methods=['GET', 'POST'])
@login_required
def reporte_productos_mas_vendidos():
    if request.method == 'POST':
        limite = int(request.form.get('limite', 10))
        formato = request.form.get('formato')
        
        db = get_db()
        productos = db.execute(
            '''
            SELECT p.codigo, p.nombre, c.nombre as categoria_nombre,
                   SUM(dv.cantidad) as total_vendido,
                   SUM(dv.subtotal) as ingresos_totales,
                   COUNT(DISTINCT dv.venta_id) as num_ventas
            FROM productos p
            JOIN detalle_ventas dv ON p.id = dv.producto_id
            LEFT JOIN categorias c ON p.categoria_id = c.id
            GROUP BY p.id
            ORDER BY total_vendido DESC
            LIMIT ?
            ''',
            (limite,)
        ).fetchall()
        
        if formato == 'pdf':
            # Crear PDF
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []
            
            styles = getSampleStyleSheet()
            
            elements.append(Paragraph(f"TOP {limite} PRODUCTOS MÁS VENDIDOS", styles['Title']))
            elements.append(Paragraph(f"Generado el: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            elements.append(Paragraph(" ", styles['Normal']))
            
            data = [['#', 'Código', 'Producto', 'Categoría', 'Cantidad Vendida', 'Ingresos', 'Ventas']]
            
            for i, producto in enumerate(productos, 1):
                data.append([
                    i,
                    producto['codigo'],
                    producto['nombre'],
                    producto['categoria_nombre'],
                    producto['total_vendido'],
                    f"${producto['ingresos_totales']:.2f}",
                    producto['num_ventas']
                ])
            
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            elements.append(table)
            doc.build(elements)
            buffer.seek(0)
            
            return send_file(
                buffer,
                as_attachment=True,
                download_name=f"productos_mas_vendidos_top_{limite}.pdf",
                mimetype='application/pdf'
            )
        
        elif formato == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            
            writer.writerow(['Posición', 'Código', 'Producto', 'Categoría', 'Cantidad Vendida', 'Ingresos Totales', 'Número de Ventas'])
            
            for i, producto in enumerate(productos, 1):
                writer.writerow([
                    i,
                    producto['codigo'],
                    producto['nombre'],
                    producto['categoria_nombre'],
                    producto['total_vendido'],
                    producto['ingresos_totales'],
                    producto['num_ventas']
                ])
            
            output.seek(0)
            
            return send_file(
                io.BytesIO(output.getvalue().encode('utf-8')),
                as_attachment=True,
                download_name=f"productos_mas_vendidos_top_{limite}.csv",
                mimetype='text/csv'
            )
        
        return render_template(
            'reportes/productos_mas_vendidos.html',
            productos=productos,
            limite=limite
        )
    
    return redirect(url_for('reportes'))

# API para verificar stock bajo
@app.route('/api/stock-bajo')
@login_required
def api_stock_bajo():
    db = get_db()
    productos = db.execute(
        '''
        SELECT codigo, nombre, stock, stock_minimo
        FROM productos
        WHERE stock <= stock_minimo
        ORDER BY (stock * 1.0 / stock_minimo) ASC
        LIMIT 5
        '''
    ).fetchall()
    
    return jsonify({
        'productos': [dict(producto) for producto in productos]
    })

# Ruta para gestionar categorías
@app.route('/categorias')
@login_required
def categorias():
    db = get_db()
    categorias = db.execute('''
        SELECT c.*, 
               (SELECT COUNT(*) FROM productos p WHERE p.categoria_id = c.id) AS productos_count
        FROM categorias c
        ORDER BY c.nombre
    ''').fetchall()
    return render_template('categorias/index.html', categorias=categorias)

@app.route('/categorias/crear', methods=['POST'])
@login_required
def crear_categoria():
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        
        db = get_db()
        db.execute(
            'INSERT INTO categorias (nombre, descripcion) VALUES (?, ?)',
            (nombre, descripcion)
        )
        db.commit()
        flash('Categoría creada correctamente', 'success')
        
    return redirect(url_for('categorias'))

@app.route('/categorias/editar/<int:id>', methods=['POST'])
@login_required
def editar_categoria(id):
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        
        db = get_db()
        db.execute(
            'UPDATE categorias SET nombre = ?, descripcion = ? WHERE id = ?',
            (nombre, descripcion, id)
        )
        db.commit()
        flash('Categoría actualizada correctamente', 'success')
        
    return redirect(url_for('categorias'))

@app.route('/categorias/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_categoria(id):
    db = get_db()
    
    # Verificar si la categoría tiene productos
    productos = db.execute(
        'SELECT COUNT(*) as count FROM productos WHERE categoria_id = ?', 
        (id,)
    ).fetchone()['count']
    
    if productos > 0:
        flash('No se puede eliminar la categoría porque tiene productos asociados', 'danger')
    else:
        db.execute('DELETE FROM categorias WHERE id = ?', (id,))
        db.commit()
        flash('Categoría eliminada correctamente', 'success')
    
    return redirect(url_for('categorias'))

# API para obtener datos de productos
@app.route('/api/productos/<int:id>')
@login_required
def api_producto(id):
    db = get_db()
    producto = db.execute('SELECT * FROM productos WHERE id = ?', (id,)).fetchone()
    
    if not producto:
        return jsonify({'error': 'Producto no encontrado'}), 404
    
    return jsonify({
        'id': producto['id'],
        'codigo': producto['codigo'],
        'nombre': producto['nombre'],
        'precio_venta': producto['precio_venta'],
        'stock': producto['stock']
    })

# Inicializar la base de datos si no existe
def init_db():
    if not os.path.exists('instance/ferreteria.db'):
        os.system('python scripts/init_db.py')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

@app.template_filter('todate')
def todate(value, format='%Y-%m-%d %H:%M:%S'):
    import datetime
    try:
        return datetime.datetime.strptime(value, format)
    except Exception:
        return value
