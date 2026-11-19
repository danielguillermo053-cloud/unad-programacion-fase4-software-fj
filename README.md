# Software FJ – Sistema de gestión de clientes, servicios y reservas

Proyecto de Programación (213023) – UNAD. Python 3.9+ · sin librerías externas · sin base de datos.

## Cómo usarlo
    python main.py             # abre la aplicación (interfaz gráfica)
    python main.py --consola   # ejecuta la simulación de 22 operaciones por consola
    python -m unittest -v      # ejecuta las pruebas automáticas

## Estructura
    software_fj/
    ├── main.py                     Punto de entrada (solo el arranque)
    ├── modelos/                    Entidades del negocio
    │   ├── entidad.py              EntidadBase (clase abstracta general)
    │   ├── cliente.py              Cliente (encapsulación y validaciones)
    │   ├── servicios.py            Servicio (abstracta) + ReservaSala, AlquilerEquipo, AsesoriaEspecializada
    │   └── reserva.py              Reserva (horario, confirmar, cancelar, procesar)
    ├── logica/                     Reglas de negocio
    │   ├── gestor.py               Listas internas, duplicados, choques de horario
    │   └── simulacion.py           22 operaciones válidas e inválidas
    ├── interfaz/                   Interfaz gráfica (Tkinter): una pestaña por archivo
    │   ├── ventana.py              Ventana, menú y manejo central de errores
    │   ├── comunes.py              Funciones compartidas
    │   └── pestana_*.py            Resumen, Clientes, Servicios, Reservas y Registro
    ├── utilidades/
    │   ├── excepciones.py          Excepciones personalizadas
    │   └── registro_logs.py        Archivo de logs
    └── logs/software_fj.log        Eventos y errores (único uso de archivos)

## Qué permite hacer la aplicación
- **Clientes:** registrar, editar, eliminar y buscar (documento único, correo y teléfono validados).
- **Servicios:** salas, equipos con inventario y asesorías; cambiar tarifa, activar/desactivar y eliminar.
- **Reservas:** fecha y hora, control de choques de horario, costo estimado en vivo, descuento,
  confirmar → procesar/cobrar, cancelar y detalle tipo factura (doble clic).
- **Resumen** de clientes, ingresos y próximas reservas, y **visor de logs** con filtro de errores.

> Por requisito del enunciado, los datos viven en memoria durante la sesión; solo los eventos y errores se escriben en el log.

## Conceptos aplicados
- Abstracción, herencia, polimorfismo (`calcular_costo_base`, `validar_parametros`, `hay_cupo`, `describir`) y encapsulación.
- Sobrecarga simulada: `desglosar(h)`, `desglosar(h, descuento)`, `desglosar(h, descuento, impuesto)`.
- `try/except`, `try/except/else`, `try/except/finally` y encadenamiento (`raise ... from`).
