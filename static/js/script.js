// JavaScript personalizado para el sistema de ferretería

// Configuración global
const CONFIG = {
  CURRENCY: "Q",
  DECIMAL_PLACES: 2,
  TOAST_DURATION: 3000,
  ANIMATION_DURATION: 300,
}

// Utilidades generales
const Utils = {
  // Formatear moneda
  formatCurrency: (amount) => CONFIG.CURRENCY + Number.parseFloat(amount).toFixed(CONFIG.DECIMAL_PLACES),

  // Formatear número
  formatNumber: (number) => Number.parseFloat(number).toLocaleString("es-GT"),

  // Mostrar toast/notificación
  showToast: function (message, type = "info") {
    const toastContainer = document.getElementById("toast-container") || this.createToastContainer()
    const toast = this.createToast(message, type)
    toastContainer.appendChild(toast)

    // Mostrar toast
    setTimeout(() => {
      toast.classList.add("show")
    }, 100)

    // Ocultar toast
    setTimeout(() => {
      toast.classList.remove("show")
      setTimeout(() => {
        if (toast.parentNode) {
          toast.parentNode.removeChild(toast)
        }
      }, CONFIG.ANIMATION_DURATION)
    }, CONFIG.TOAST_DURATION)
  },

  // Crear contenedor de toasts
  createToastContainer: () => {
    const container = document.createElement("div")
    container.id = "toast-container"
    container.className = "position-fixed top-0 end-0 p-3"
    container.style.zIndex = "9999"
    document.body.appendChild(container)
    return container
  },

  // Crear toast individual
  createToast: (message, type) => {
    const toast = document.createElement("div")
    toast.className = `toast align-items-center text-white bg-${type} border-0`
    toast.setAttribute("role", "alert")
    toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `
    return toast
  },

  // Confirmar acción
  confirm: (message, callback) => {
    if (confirm(message)) {
      callback()
    }
  },

  // Validar email
  validateEmail: (email) => {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return re.test(email)
  },

  // Validar teléfono
  validatePhone: (phone) => {
    const re = /^[\d\s\-+$$$$]+$/
    return re.test(phone)
  },

  // Debounce para búsquedas
  debounce: (func, wait) => {
    let timeout
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout)
        func(...args)
      }
      clearTimeout(timeout)
      timeout = setTimeout(later, wait)
    }
  },
}

// Gestión de formularios
const FormManager = {
  // Validar formulario
  validateForm: function (formId) {
    const form = document.getElementById(formId)
    if (!form) return false

    const inputs = form.querySelectorAll("input[required], select[required], textarea[required]")
    let isValid = true

    inputs.forEach((input) => {
      if (!input.value.trim()) {
        this.showFieldError(input, "Este campo es requerido")
        isValid = false
      } else {
        this.clearFieldError(input)

        // Validaciones específicas
        if (input.type === "email" && !Utils.validateEmail(input.value)) {
          this.showFieldError(input, "Email inválido")
          isValid = false
        }

        if (input.type === "tel" && !Utils.validatePhone(input.value)) {
          this.showFieldError(input, "Teléfono inválido")
          isValid = false
        }

        if (input.type === "number" && Number.parseFloat(input.value) < 0) {
          this.showFieldError(input, "El valor debe ser positivo")
          isValid = false
        }
      }
    })

    return isValid
  },

  // Mostrar error en campo
  showFieldError: function (field, message) {
    this.clearFieldError(field)
    field.classList.add("is-invalid")

    const errorDiv = document.createElement("div")
    errorDiv.className = "invalid-feedback"
    errorDiv.textContent = message
    field.parentNode.appendChild(errorDiv)
  },

  // Limpiar error en campo
  clearFieldError: (field) => {
    field.classList.remove("is-invalid")
    const errorDiv = field.parentNode.querySelector(".invalid-feedback")
    if (errorDiv) {
      errorDiv.remove()
    }
  },

  // Limpiar formulario
  clearForm: function (formId) {
    const form = document.getElementById(formId)
    if (form) {
      form.reset()
      const invalidFields = form.querySelectorAll(".is-invalid")
      invalidFields.forEach((field) => this.clearFieldError(field))
    }
  },
}

// Gestión de stock
const StockManager = {
  // Verificar stock bajo
  checkLowStock: function () {
    fetch("/api/stock-bajo")
      .then((response) => response.json())
      .then((data) => {
        if (data.productos && data.productos.length > 0) {
          this.showStockAlert(data.productos)
        }
      })
      .catch((error) => console.error("Error checking stock:", error))
  },

  // Mostrar alerta de stock
  showStockAlert: (productos) => {
    const alertContainer = document.getElementById("stock-alerts")
    if (!alertContainer) return

    const alert = document.createElement("div")
    alert.className = "alert alert-warning alert-dismissible fade show"
    alert.innerHTML = `
            <strong><i class="fas fa-exclamation-triangle me-2"></i>Alerta de Stock!</strong>
            ${productos.length} producto(s) con stock bajo.
            <a href="/reportes/productos-stock-bajo" class="alert-link">Ver detalles</a>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `

    alertContainer.appendChild(alert)
  },
}

// Gestión de búsquedas
const SearchManager = {
  // Búsqueda en tiempo real
  setupLiveSearch: function (inputId, tableId) {
    const input = document.getElementById(inputId)
    const table = document.getElementById(tableId)

    if (!input || !table) return

    const debouncedSearch = Utils.debounce((searchTerm) => {
      this.filterTable(table, searchTerm)
    }, 300)

    input.addEventListener("input", (e) => {
      debouncedSearch(e.target.value)
    })
  },

  // Filtrar tabla
  filterTable: (table, searchTerm) => {
    const tbody = table.querySelector("tbody")
    const rows = tbody.querySelectorAll("tr")

    rows.forEach((row) => {
      const text = row.textContent.toLowerCase()
      const matches = text.includes(searchTerm.toLowerCase())
      row.style.display = matches ? "" : "none"
    })
  },
}

// Gestión de ventas
const SalesManager = {
  cart: [],

  // Agregar producto al carrito
  addToCart: function (product) {
    const existingIndex = this.cart.findIndex((item) => item.id === product.id)

    if (existingIndex >= 0) {
      this.cart[existingIndex].quantity += product.quantity
      this.cart[existingIndex].subtotal = this.cart[existingIndex].quantity * this.cart[existingIndex].price
    } else {
      this.cart.push({
        ...product,
        subtotal: product.quantity * product.price,
      })
    }

    this.updateCartDisplay()
    Utils.showToast("Producto agregado al carrito", "success")
  },

  // Remover del carrito
  removeFromCart: function (productId) {
    this.cart = this.cart.filter((item) => item.id !== productId)
    this.updateCartDisplay()
    Utils.showToast("Producto removido del carrito", "info")
  },

  // Actualizar cantidad
  updateQuantity: function (productId, newQuantity) {
    const item = this.cart.find((item) => item.id === productId)
    if (item) {
      item.quantity = newQuantity
      item.subtotal = item.quantity * item.price
      this.updateCartDisplay()
    }
  },

  // Actualizar visualización del carrito
  updateCartDisplay: function () {
    const cartContainer = document.getElementById("cart-items")
    const totalElement = document.getElementById("cart-total")

    if (!cartContainer || !totalElement) return

    if (this.cart.length === 0) {
      cartContainer.innerHTML = '<p class="text-muted text-center">Carrito vacío</p>'
      totalElement.textContent = Utils.formatCurrency(0)
      return
    }

    let html = ""
    let total = 0

    this.cart.forEach((item, index) => {
      total += item.subtotal
      html += `
                <div class="cart-item mb-2 p-2 border rounded">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${item.name}</strong><br>
                            <small class="text-muted">${Utils.formatCurrency(item.price)} x ${item.quantity}</small>
                        </div>
                        <div class="text-end">
                            <div>${Utils.formatCurrency(item.subtotal)}</div>
                            <button class="btn btn-sm btn-danger" onclick="SalesManager.removeFromCart(${item.id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `
    })

    cartContainer.innerHTML = html
    totalElement.textContent = Utils.formatCurrency(total)
  },

  // Limpiar carrito
  clearCart: function () {
    this.cart = []
    this.updateCartDisplay()
    Utils.showToast("Carrito limpiado", "info")
  },

  // Procesar venta
  processSale: function (customerId, invoiceNumber) {
    if (this.cart.length === 0) {
      Utils.showToast("El carrito está vacío", "warning")
      return
    }

    const saleData = {
      customer_id: customerId,
      invoice_number: invoiceNumber,
      items: this.cart,
      total: this.cart.reduce((sum, item) => sum + item.subtotal, 0),
    }

    fetch("/ventas/crear", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(saleData),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          Utils.showToast("Venta procesada correctamente", "success")
          this.clearCart()
          window.location.href = `/ventas/${data.sale_id}`
        } else {
          Utils.showToast("Error al procesar la venta: " + data.message, "danger")
        }
      })
      .catch((error) => {
        console.error("Error:", error)
        Utils.showToast("Error al procesar la venta", "danger")
      })
  },
}

// Gestión de reportes
const ReportManager = {
  // Generar reporte
  generateReport: (type, params = {}) => {
    const url = new URL(`/reportes/${type}`, window.location.origin)
    Object.keys(params).forEach((key) => {
      if (params[key]) {
        url.searchParams.append(key, params[key])
      }
    })

    window.open(url.toString(), "_blank")
  },

  // Exportar datos
  exportData: function (data, filename, format = "csv") {
    if (format === "csv") {
      this.exportToCSV(data, filename)
    } else if (format === "json") {
      this.exportToJSON(data, filename)
    }
  },

  // Exportar a CSV
  exportToCSV: function (data, filename) {
    const csv = this.convertToCSV(data)
    const blob = new Blob([csv], { type: "text/csv" })
    this.downloadFile(blob, filename + ".csv")
  },

  // Exportar a JSON
  exportToJSON: function (data, filename) {
    const json = JSON.stringify(data, null, 2)
    const blob = new Blob([json], { type: "application/json" })
    this.downloadFile(blob, filename + ".json")
  },

  // Convertir a CSV
  convertToCSV: (data) => {
    if (!data || data.length === 0) return ""

    const headers = Object.keys(data[0])
    const csvContent = [
      headers.join(","),
      ...data.map((row) => headers.map((header) => `"${row[header] || ""}"`).join(",")),
    ].join("\n")

    return csvContent
  },

  // Descargar archivo
  downloadFile: (blob, filename) => {
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  },
}

// Inicialización cuando el DOM está listo
document.addEventListener("DOMContentLoaded", () => {
  // Inicializar tooltips de Bootstrap
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
  const bootstrap = window.bootstrap // Declare bootstrap variable
  tooltipTriggerList.map((tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl))

  // Inicializar popovers de Bootstrap
  const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
  popoverTriggerList.map((popoverTriggerEl) => new bootstrap.Popover(popoverTriggerEl))

  // Configurar DataTables si está disponible
  const $ = window.jQuery // Declare $ variable
  if (typeof $.fn.DataTable !== "undefined") {
    $(".data-table").DataTable({
      language: {
        url: "https://cdn.datatables.net/plug-ins/1.11.5/i18n/es-ES.json",
      },
      responsive: true,
      pageLength: 25,
      order: [[0, "desc"]],
    })
  }

  // Verificar stock bajo cada 5 minutos
  StockManager.checkLowStock()
  setInterval(() => {
    StockManager.checkLowStock()
  }, 300000) // 5 minutos

  // Configurar búsquedas en tiempo real
  SearchManager.setupLiveSearch("buscarProducto", "tablaProductos")
  SearchManager.setupLiveSearch("buscarCliente", "tablaClientes")

  // Auto-guardar formularios cada 30 segundos
  const forms = document.querySelectorAll("form[data-autosave]")
  forms.forEach((form) => {
    setInterval(() => {
      const formData = new FormData(form)
      localStorage.setItem(`autosave_${form.id}`, JSON.stringify(Object.fromEntries(formData)))
    }, 30000)
  })

  // Restaurar datos auto-guardados
  forms.forEach((form) => {
    const savedData = localStorage.getItem(`autosave_${form.id}`)
    if (savedData) {
      const data = JSON.parse(savedData)
      Object.keys(data).forEach((key) => {
        const field = form.querySelector(`[name="${key}"]`)
        if (field) {
          field.value = data[key]
        }
      })
    }
  })

  // Configurar atajos de teclado
  document.addEventListener("keydown", (e) => {
    // Ctrl + N = Nueva venta
    if (e.ctrlKey && e.key === "n") {
      e.preventDefault()
      window.location.href = "/ventas/nueva"
    }

    // Ctrl + P = Productos
    if (e.ctrlKey && e.key === "p") {
      e.preventDefault()
      window.location.href = "/productos"
    }

    // Ctrl + C = Clientes
    if (e.ctrlKey && e.key === "c") {
      e.preventDefault()
      window.location.href = "/clientes"
    }

    // Ctrl + R = Reportes
    if (e.ctrlKey && e.key === "r") {
      e.preventDefault()
      window.location.href = "/reportes"
    }
  })

  // Animaciones de entrada
  const elements = document.querySelectorAll(".card, .table, .btn")
  elements.forEach((element, index) => {
    element.style.opacity = "0"
    element.style.transform = "translateY(20px)"

    setTimeout(() => {
      element.style.transition = "all 0.5s ease"
      element.style.opacity = "1"
      element.style.transform = "translateY(0)"
    }, index * 100)
  })
})

// Exponer objetos globalmente para uso en templates
window.Utils = Utils
window.FormManager = FormManager
window.StockManager = StockManager
window.SearchManager = SearchManager
window.SalesManager = SalesManager
window.ReportManager = ReportManager
