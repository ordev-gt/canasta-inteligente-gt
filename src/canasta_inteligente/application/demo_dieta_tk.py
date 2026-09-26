"""Canasta personal y familiar en Tkinter, con aportes nutricionales por alimento."""

import argparse
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

import pandas as pd

from canasta_inteligente.application.cba_pipeline import DEFAULT_PICKLE
from canasta_inteligente.application.cba_pipeline import load_catalog_pickle
from canasta_inteligente.application.demo_canasta import (
    ejecutar_canasta, seleccionar_catalogo_region, tabla_alimentos,
)
from canasta_inteligente.application.demo_dieta import (
    crear_persona, ejecutar_demo, leer_pesos, numero,
)
from canasta_inteligente.application.optimizacion_dieta import tabla_nutrientes


def formato(valor):
    if valor is None or pd.isna(valor):
        return '—'
    if isinstance(valor, float):
        return f'{valor:,.4f}'.rstrip('0').rstrip('.')
    return str(valor)


class Tabla(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent)
        self.tree = ttk.Treeview(self, show='headings', selectmode='browse', **kwargs)
        vertical = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        horizontal = ttk.Scrollbar(self, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.tree.grid(row=0, column=0, sticky='nsew')
        vertical.grid(row=0, column=1, sticky='ns')
        horizontal.grid(row=1, column=0, sticky='ew')
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

    def mostrar(self, dataframe):
        self.tree.delete(*self.tree.get_children())
        columnas = list(dataframe.columns)
        self.tree.configure(columns=columnas)
        for columna in columnas:
            titulo = 'Nombre INCAP' if columna == 'nombre_incap' else columna.replace('_', ' ').capitalize()
            self.tree.heading(columna, text=titulo)
            ancho = 280 if columna in ('alimento', 'nutriente', 'referencia', 'escenario', 'restriccion') else 130
            if columna == 'nombre_incap':
                ancho = 380
            self.tree.column(columna, width=ancho, minwidth=85, stretch=False)
        for i, fila in enumerate(dataframe.itertuples(index=False, name=None)):
            self.tree.insert('', 'end', iid=str(i), values=[formato(v) for v in fila])


class AportesPorAlimento(ttk.Frame):
    """Desglose de la cantidad diaria seleccionada, nutriente por nutriente."""

    def __init__(self, parent):
        super().__init__(parent, padding=8)
        self.resultado = None
        self.nutriente = tk.StringVar()
        barra = ttk.Frame(self)
        barra.pack(fill='x', pady=(0, 8))
        ttk.Label(barra, text='Nutriente:').pack(side='left')
        self.selector = ttk.Combobox(barra, textvariable=self.nutriente, state='disabled', width=30)
        self.selector.pack(side='left', padx=8)
        self.selector.bind('<<ComboboxSelected>>', self.actualizar)
        self.resumen = tk.StringVar(value='Selecciona un escenario con solución óptima.')
        ttk.Label(self, textvariable=self.resumen).pack(anchor='w', pady=(0, 4))
        ttk.Label(self, text='Aportes diarios ajustados por fracción comestible. '
                  'El porcentaje corresponde al total de la canasta.').pack(anchor='w', pady=(0, 8))
        self.tabla = Tabla(self)
        self.tabla.pack(fill='both', expand=True)

    def mostrar(self, resultado=None):
        self.resultado = resultado
        if resultado is None or resultado['estado'] != 'Optimal':
            self.selector.configure(values=(), state='disabled')
            self.nutriente.set('')
            self.resumen.set('Selecciona un escenario con solución óptima.')
            self.tabla.mostrar(pd.DataFrame())
            return
        nutrientes = list(resultado['restricciones'])
        self.selector.configure(values=nutrientes, state='readonly')
        if self.nutriente.get() not in nutrientes:
            self.nutriente.set(nutrientes[0] if nutrientes else '')
        self.actualizar()

    def actualizar(self, event=None):
        if self.resultado is None or self.resultado['estado'] != 'Optimal':
            return
        nutriente = self.nutriente.get()
        if nutriente not in self.resultado['restricciones']:
            return
        datos = self.resultado['aportes_por_alimento']
        filas = datos.loc[datos['nutriente'] == nutriente].sort_values('aporte', ascending=False)
        self.tabla.mostrar(filas[[
            'alimento', 'nombre_incap', 'aporte', 'unidad', 'porcentaje_del_total',
            'gramos_comprados', 'gramos_comestibles',
        ]])
        total = self.resultado['aportes'][nutriente]
        unidad = nutriente.rsplit('_', 1)[-1]
        self.resumen.set(f'Total de la canasta: {formato(total)} {unidad} · '
                         f'{len(filas)} alimentos · Ordenados de mayor a menor aporte'
                         + (' · Porcentaje no definido porque el total es cero.' if total == 0 else ''))


class FormularioDesplazable(ttk.Frame):
    """Mantiene accesibles los campos del perfil en pantallas pequeñas."""

    def __init__(self, parent):
        super().__init__(parent, width=390)
        canvas = tk.Canvas(self, width=370, highlightthickness=0)
        barra = ttk.Scrollbar(self, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=barra.set)
        barra.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)
        self.contenido = ttk.Frame(canvas, padding=8)
        ventana = canvas.create_window((0, 0), window=self.contenido, anchor='nw')
        self.contenido.bind('<Configure>', lambda event: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>', lambda event: canvas.itemconfigure(ventana, width=event.width))


class DemoDieta(tk.Tk):
    def __init__(self, catalog_path=DEFAULT_PICKLE):
        super().__init__()
        self.title('Canasta Inteligente GT · Dieta personal y familiar')
        self.geometry('1280x820')
        self.minsize(1000, 680)
        self.cola = Queue()
        self.ocupada = False
        self.consulta = None
        self.seleccionado = None
        self.variables = {}
        self.miembros = []
        self.limites = {}
        self.exclusiones = set()
        self.alimentos_catalogo = {}
        self.revision = 0
        self.resultados = []
        self.protocol('WM_DELETE_WINDOW', self.cerrar)
        estilo = ttk.Style(self)
        if 'clam' in estilo.theme_names():
            estilo.theme_use('clam')
        estilo.configure('Treeview', rowheight=26)
        estilo.configure('Title.TLabel', font=('Segoe UI', 17, 'bold'))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        cabecera = ttk.Frame(self, padding=(16, 12))
        cabecera.grid(row=0, column=0, sticky='ew')
        ttk.Label(cabecera, text='Canasta Inteligente GT', style='Title.TLabel').pack(anchor='w')
        ttk.Label(cabecera, text='Agrega una persona para su dieta personal o varios integrantes para la canasta familiar.').pack(anchor='w')
        self.pasos = ttk.Notebook(self)
        self.pasos.grid(row=1, column=0, sticky='nsew', padx=12)
        self.paginas = [ttk.Frame(self.pasos, padding=10) for _ in range(4)]
        for pagina, titulo in zip(self.paginas, (
            '1. Integrantes', '2. Configuración', '3. Calcular canasta', '4. Resultados',
        )):
            self.pasos.add(pagina, text=titulo)

        integrantes = self.paginas[0]
        formulario = FormularioDesplazable(integrantes)
        formulario.pack(side='left', fill='y', padx=(0, 16))
        perfil = formulario.contenido
        self.crear_perfil(perfil)
        ttk.Button(perfil, text='Agregar integrante', command=self.agregar_miembro).grid(
            row=15, column=0, columnspan=2, sticky='ew', pady=8)
        lista = ttk.Frame(integrantes)
        lista.pack(side='left', fill='both', expand=True)
        self.resumen_miembros = tk.StringVar(value='Todavía no has agregado integrantes.')
        ttk.Label(lista, textvariable=self.resumen_miembros).pack(anchor='w', pady=8)
        self.tabla_miembros = Tabla(lista, height=8)
        self.tabla_miembros.pack(fill='both', expand=True)
        acciones = ttk.Frame(lista)
        acciones.pack(fill='x', pady=8)
        for texto, comando in (
            ('Cargar seleccionado en el formulario', self.editar_miembro),
            ('Guardar cambios', self.guardar_miembro), ('Eliminar', self.eliminar_miembro),
        ):
            ttk.Button(acciones, text=texto, command=comando).pack(side='left', padx=(0, 8))
        self.crear_configuracion(self.paginas[1], catalog_path)

        calcular = self.paginas[2]
        ttk.Label(calcular, text='Revisa la canasta que vas a calcular', style='Title.TLabel').pack(anchor='w', pady=12)
        self.revision_texto = tk.StringVar()
        ttk.Label(calcular, textvariable=self.revision_texto, justify='left', wraplength=950).pack(anchor='w', pady=12)
        self.boton_req = ttk.Button(calcular, text='Ver requerimientos de los integrantes', command=lambda: self.iniciar(True))
        self.boton_req.pack(anchor='w', pady=8)
        self.boton_ejecutar = ttk.Button(calcular, text='Calcular canasta', command=self.iniciar, state='disabled')
        self.boton_ejecutar.pack(anchor='w', pady=8)
        self.progreso = ttk.Progressbar(calcular, mode='indeterminate')
        self.progreso.pack(fill='x', pady=12)

        derecha = self.paginas[3]
        derecha.columnconfigure(0, weight=1)
        derecha.rowconfigure(3, weight=1)
        self.resumen = tk.StringVar(value='Agrega integrantes y calcula una canasta.')
        ttk.Label(derecha, textvariable=self.resumen, wraplength=760, padding=10).grid(row=0, column=0, sticky='ew')
        barra = ttk.Frame(derecha)
        barra.grid(row=1, column=0, sticky='ew', padx=8, pady=4)
        ttk.Label(barra, text='Dieta:').pack(side='left')
        self.vista = tk.StringVar()
        self.selector_vista = ttk.Combobox(barra, textvariable=self.vista, state='disabled', width=40)
        self.selector_vista.pack(side='left', padx=8)
        self.selector_vista.bind('<<ComboboxSelected>>', self.cambiar_vista)
        ttk.Label(barra, text='★ Propuesta elegida · Selecciona un modelo o escenario').pack(side='left')
        self.escenarios = Tabla(derecha, height=4)
        self.escenarios.grid(row=2, column=0, sticky='ew', padx=8)
        self.escenarios.tree.bind('<<TreeviewSelect>>', self.seleccionar)
        self.detalles = ttk.Notebook(derecha)
        self.detalles.grid(row=3, column=0, sticky='nsew', padx=8, pady=8)
        self.tablas = {}
        for nombre, titulo in (
            ('Alimentos', 'Alimentos / día'), ('Compra del período', 'Compra del período'),
            ('Nutrientes', 'Nutrientes / día'), ('Requerimientos', 'Requerimientos'),
            ('Comparación de repartos', 'Repartos'), ('Reparto del período', 'Distribución'),
            ('Diagnóstico', 'Diagnóstico'),
        ):
            tabla = Tabla(self.detalles)
            self.tablas[nombre] = tabla
            self.detalles.add(tabla, text=titulo)
        self.aportes_alimentos = AportesPorAlimento(self.detalles)
        self.detalles.insert(3, self.aportes_alimentos, text='Aporte por alimento')
        self.notas = ScrolledText(self.detalles, wrap='word', padx=12, pady=12, state='disabled')
        self.detalles.add(self.notas, text='Notas')
        self.boton_exportar = ttk.Button(derecha, text='Exportar compra y nutrientes del período a CSV',
                                        command=self.exportar, state='disabled')
        self.boton_exportar.grid(row=4, column=0, sticky='e', padx=8, pady=(0, 8))
        pie = ttk.Frame(self, padding=(16, 6))
        pie.grid(row=2, column=0, sticky='ew')
        ttk.Button(pie, text='Anterior', command=lambda: self.avanzar(-1)).pack(side='left')
        ttk.Button(pie, text='Siguiente', command=lambda: self.avanzar(1)).pack(side='right')
        self.estado = tk.StringVar(value='Agrega el primer integrante para comenzar.')
        ttk.Label(self, textvariable=self.estado, padding=(16, 8)).grid(row=3, column=0, sticky='ew')
        for clave in ('dias', 'presupuesto', 'modo', 'min_energia', 'min_colesterol', 'max_energia', 'max_colesterol'):
            self.variables[clave].trace_add('write', lambda *args: self.invalidar())
        self.variables['catalogo'].trace_add('write', self.cambio_catalogo)
        self.variables['region'].trace_add('write', self.cambio_region)
        self.pesos.bind('<<Modified>>', self.cambio_pesos)
        self.actualizar_revision()
        self.after_idle(self.cargar_catalogo)

    def campo(self, parent, fila, texto, clave, valor, opciones=None):
        ttk.Label(parent, text=texto).grid(row=fila, column=0, sticky='w', pady=4)
        variable = tk.StringVar(value=valor)
        self.variables[clave] = variable
        if opciones:
            widget = ttk.Combobox(parent, textvariable=variable, values=opciones, state='readonly', width=16)
        else:
            widget = ttk.Entry(parent, textvariable=variable, width=18)
        widget.grid(row=fila, column=1, sticky='ew', padx=(8, 0), pady=4)
        parent.columnconfigure(1, weight=1)
        return widget

    def casilla(self, parent, fila, texto, clave, valor=False):
        variable = tk.BooleanVar(value=valor)
        self.variables[clave] = variable
        widget = ttk.Checkbutton(parent, text=texto, variable=variable, command=self.actualizar_maternidad)
        widget.grid(row=fila, column=0, columnspan=2, sticky='w', pady=3)
        return widget

    def crear_perfil(self, parent):
        self.campo(parent, 0, 'Nombre', 'nombre', 'Persona demo')
        self.campo(parent, 1, 'Edad (años)', 'edad', '25')
        sexo = self.campo(parent, 2, 'Sexo', 'sexo', 'hombre', ('hombre', 'mujer'))
        sexo.bind('<<ComboboxSelected>>', lambda event: self.actualizar_maternidad())
        self.campo(parent, 3, 'Peso actual (kg)', 'peso', '70')
        self.campo(parent, 4, 'Talla (metros)', 'altura', '1.70')
        self.campo(parent, 5, 'Actividad física', 'actividad', 'Baja', ('Baja', 'Moderada', 'Alta'))
        self.casilla(parent, 6, 'Exposición solar suficiente', 'solar', True)
        self.casilla(parent, 7, 'Sudoración profusa', 'sudoracion')
        ttk.Separator(parent).grid(row=8, column=0, columnspan=2, sticky='ew', pady=8)
        self.embarazo = self.casilla(parent, 9, 'Embarazo actual', 'embarazo')
        self.mes_embarazo = self.campo(parent, 10, 'Mes de embarazo', 'mes_embarazo', '6')
        self.reservas = self.casilla(parent, 11, 'Reservas de energía maternales', 'reservas')
        self.lactancia = self.casilla(parent, 12, 'Lactancia actual', 'lactancia')
        self.mes_lactancia = self.campo(parent, 13, 'Mes de lactancia', 'mes_lactancia', '3')
        self.peso_previo = self.campo(parent, 14, 'Peso previo (kg)', 'peso_previo', '60')
        self.actualizar_maternidad()

    def actualizar_maternidad(self):
        if not hasattr(self, 'peso_previo'):
            return
        mujer = self.variables['sexo'].get() == 'mujer'
        if not mujer:
            self.variables['embarazo'].set(False)
            self.variables['lactancia'].set(False)
        embarazo = mujer and self.variables['embarazo'].get()
        lactancia = mujer and self.variables['lactancia'].get()
        for widget, habilitar in ((self.embarazo, mujer), (self.lactancia, mujer),
                                  (self.mes_embarazo, embarazo), (self.reservas, embarazo),
                                  (self.mes_lactancia, lactancia), (self.peso_previo, embarazo or lactancia)):
            widget.configure(state='normal' if habilitar else 'disabled')

    def avanzar(self, paso):
        indice = self.pasos.index(self.pasos.select())
        self.pasos.select(max(0, min(3, indice + paso)))

    def datos_perfil(self):
        claves = ('nombre', 'edad', 'sexo', 'peso', 'altura', 'actividad', 'solar',
                  'sudoracion', 'embarazo', 'lactancia', 'peso_previo', 'mes_embarazo',
                  'mes_lactancia', 'reservas')
        datos = {clave: self.variables[clave].get() for clave in claves}
        if not datos['nombre'].strip():
            raise ValueError('Ingresa el nombre del integrante.')
        crear_persona(datos)
        return datos

    def agregar_miembro(self):
        try:
            self.miembros.append(self.datos_perfil())
        except ValueError as error:
            messagebox.showerror('Revisa el perfil', str(error), parent=self)
            return
        self.actualizar_miembros()

    def editar_miembro(self):
        seleccion = self.tabla_miembros.tree.selection()
        if seleccion:
            for clave, valor in self.miembros[int(seleccion[0])].items():
                self.variables[clave].set(valor)
            self.actualizar_maternidad()

    def guardar_miembro(self):
        seleccion = self.tabla_miembros.tree.selection()
        if not seleccion:
            return
        try:
            self.miembros[int(seleccion[0])] = self.datos_perfil()
        except ValueError as error:
            messagebox.showerror('Revisa el perfil', str(error), parent=self)
            return
        self.actualizar_miembros()

    def eliminar_miembro(self):
        seleccion = self.tabla_miembros.tree.selection()
        if seleccion:
            self.miembros.pop(int(seleccion[0]))
            self.actualizar_miembros()

    def actualizar_miembros(self):
        self.tabla_miembros.mostrar(pd.DataFrame([
            {clave: datos[clave] for clave in ('nombre', 'edad', 'sexo', 'peso', 'altura', 'actividad')}
            for datos in self.miembros
        ]))
        cantidad = len(self.miembros)
        self.resumen_miembros.set(f'{cantidad} integrante(s) · '
                                  + ('Dieta personal' if cantidad == 1 else 'Canasta familiar'))
        self.invalidar()

    def crear_configuracion(self, parent, catalog_path):
        controles = ttk.Notebook(parent)
        controles.pack(side='left', fill='both', expand=True, padx=(0, 12))
        general = ttk.Frame(controles, padding=12)
        avanzado = ttk.Frame(controles, padding=12)
        controles.add(general, text='Parámetros de la canasta')
        controles.add(avanzado, text='Modelo y pesos')
        self.campo(general, 0, 'Número de días', 'dias', '30')
        self.campo(general, 1, 'Presupuesto total Q', 'presupuesto', '2500')
        self.campo(general, 2, 'Cálculo', 'modo', 'Con presupuesto',
                   ('Con presupuesto', 'Costo mínimo'))
        ttk.Label(general, text='El presupuesto cubre todo el período y todos los integrantes. '
                  'Costo mínimo calcula sin un tope de presupuesto.', wraplength=420).grid(
            row=3, column=0, columnspan=2, sticky='w', pady=12)
        self.variables['catalogo'] = tk.StringVar(value=str(catalog_path))
        ttk.Label(general, text='Catálogo procesado (.pkl)').grid(row=4, column=0, columnspan=2, sticky='w')
        ttk.Entry(general, textvariable=self.variables['catalogo']).grid(row=5, column=0, columnspan=2, sticky='ew', pady=8)
        ttk.Button(general, text='Elegir catálogo…', command=self.elegir_catalogo).grid(row=6, column=0, sticky='ew')
        ttk.Button(general, text='Cargar alimentos', command=self.cargar_catalogo).grid(row=6, column=1, sticky='ew')
        self.catalogo_estado = tk.StringVar(value='Catálogo pendiente de cargar.')
        ttk.Label(general, textvariable=self.catalogo_estado, wraplength=420).grid(row=7, column=0, columnspan=2, sticky='w', pady=12)
        self.campo(general, 8, 'Región del catálogo', 'region', 'general',
                   ('general', 'urbana', 'rural'))
        ttk.Label(general, text='General conserva todos los alimentos y prioriza el precio general '
                  '(si falta, urbano y luego rural). Urbana y rural usan solo precios de esa región.',
                  wraplength=420).grid(row=9, column=0, columnspan=2, sticky='w', pady=12)
        for fila, (texto, clave, valor) in enumerate((
            ('Costo: energía', 'min_energia', '1'), ('Costo: colesterol', 'min_colesterol', '0.1'),
            ('Cobertura: energía', 'max_energia', '1'), ('Cobertura: colesterol', 'max_colesterol', '0.1'),
        )):
            self.campo(avanzado, fila, texto, clave, valor)
        ttk.Label(avanzado, text='Penalizaciones por kcal / mg de desviación.\n'
                  'Pesos de cobertura: nutriente = valor (omitidos = 1).', wraplength=420).grid(
            row=4, column=0, columnspan=2, sticky='w', pady=12)
        self.pesos = ScrolledText(avanzado, height=6, width=35)
        self.pesos.grid(row=5, column=0, columnspan=2, sticky='nsew')
        self.pesos.insert('1.0', 'vitamina_d_mcg = 1\nfibra_dietetica_g = 1\n')
        self.pesos.edit_modified(False)
        avanzado.rowconfigure(5, weight=1)

        restricciones = ttk.LabelFrame(parent, text='Restricciones adicionales', padding=12)
        restricciones.pack(side='left', fill='both', expand=True)
        ttk.Label(restricciones, text='Selecciona un alimento para excluirlo o limitarlo.').pack(anchor='w')
        self.alimento = tk.StringVar()
        self.selector_alimento = ttk.Combobox(restricciones, textvariable=self.alimento, state='disabled', width=48)
        self.selector_alimento.pack(fill='x', pady=8)
        ttk.Button(restricciones, text='Excluir alimento', command=self.excluir_alimento).pack(anchor='w')
        barra = ttk.Frame(restricciones)
        barra.pack(fill='x', pady=12)
        ttk.Label(barra, text='Máximo diario (g por persona):').pack(side='left')
        self.limite_gramos = tk.StringVar(value='100')
        ttk.Entry(barra, textvariable=self.limite_gramos, width=10).pack(side='left', padx=8)
        ttk.Button(restricciones, text='Agregar / actualizar límite', command=self.agregar_limite).pack(anchor='w')
        ttk.Label(restricciones, text='Los límites se aplican a cada integrante en ambos modelos.\n'
                  'Una exclusión elimina también el límite de ese alimento.', wraplength=450).pack(anchor='w', pady=8)
        self.tabla_restricciones = Tabla(restricciones, height=8)
        self.tabla_restricciones.pack(fill='both', expand=True)
        ttk.Button(restricciones, text='Eliminar restricción seleccionada', command=self.eliminar_restriccion).pack(anchor='w', pady=8)

    def elegir_catalogo(self):
        ruta = filedialog.askopenfilename(parent=self, title='Catálogo generado por este proyecto',
                                          filetypes=[('Catálogo procesado', '*.pkl')])
        if ruta:
            self.variables['catalogo'].set(ruta)
            self.cargar_catalogo()

    def cambio_catalogo(self, *args):
        self.alimentos_catalogo = {}
        self.exclusiones.clear()
        self.limites.clear()
        self.selector_alimento.configure(values=(), state='disabled')
        self.alimento.set('')
        self.catalogo_estado.set('Carga los alimentos del nuevo catálogo.')
        self.actualizar_restricciones()

    def cargar_catalogo(self):
        self.alimentos_catalogo = {}
        self.selector_alimento.configure(values=(), state='disabled')
        self.alimento.set('')
        try:
            original = load_catalog_pickle(self.variables['catalogo'].get())
            region = self.variables['region'].get()
            catalog = seleccionar_catalogo_region(original, region)
            self.alimentos_catalogo = {f'{food.name} ({food.id})': food.id
                                       for food in sorted(catalog, key=lambda f: str(f.name).lower())}
        except Exception as error:
            self.catalogo_estado.set(f'No se pudo cargar el catálogo: {error}')
            self.invalidar()
            return
        disponibles = set(self.alimentos_catalogo.values())
        retiradas = len((self.exclusiones | set(self.limites)) - disponibles)
        self.exclusiones.intersection_update(disponibles)
        self.limites = {food_id: gramos for food_id, gramos in self.limites.items() if food_id in disponibles}
        self.actualizar_restricciones()
        self.selector_alimento.configure(values=list(self.alimentos_catalogo), state='readonly')
        if self.alimentos_catalogo:
            self.selector_alimento.current(0)
        self.catalogo_estado.set(
            f'Región {region}: {len(catalog)} de {len(original)} alimentos disponibles.'
            + (f' Se omitieron {len(original) - len(catalog)} sin precio válido en esta región.'
               if len(catalog) < len(original) else '')
            + (f' Se retiraron {retiradas} restricciones de alimentos no disponibles.' if retiradas else '')
        )

    def cambio_region(self, *args):
        self.invalidar()
        self.cargar_catalogo()

    def excluir_alimento(self):
        food_id = self.alimentos_catalogo.get(self.alimento.get())
        if food_id is not None:
            self.exclusiones.add(food_id)
            self.limites.pop(food_id, None)
            self.actualizar_restricciones()

    def agregar_limite(self):
        food_id = self.alimentos_catalogo.get(self.alimento.get())
        if food_id is None:
            return
        try:
            gramos = numero(self.limite_gramos.get(), 'Límite diario', estricto=True)
        except ValueError as error:
            messagebox.showerror('Revisa el límite', str(error), parent=self)
            return
        self.exclusiones.discard(food_id)
        self.limites[food_id] = gramos
        self.actualizar_restricciones()

    def actualizar_restricciones(self):
        nombres = {food_id: nombre for nombre, food_id in self.alimentos_catalogo.items()}
        self.filas_restricciones = [
            {'alimento_id': food_id, 'alimento': nombres.get(food_id, food_id),
             'restriccion': 'Excluido', 'maximo_g_persona_dia': None}
            for food_id in sorted(self.exclusiones)
        ] + [
            {'alimento_id': food_id, 'alimento': nombres.get(food_id, food_id),
             'restriccion': 'Límite diario', 'maximo_g_persona_dia': gramos}
            for food_id, gramos in self.limites.items()
        ]
        self.tabla_restricciones.mostrar(pd.DataFrame(self.filas_restricciones))
        self.invalidar()

    def eliminar_restriccion(self):
        seleccion = self.tabla_restricciones.tree.selection()
        if seleccion:
            food_id = self.filas_restricciones[int(seleccion[0])]['alimento_id']
            self.exclusiones.discard(food_id)
            self.limites.pop(food_id, None)
            self.actualizar_restricciones()

    def cambio_pesos(self, event=None):
        if self.pesos.edit_modified():
            self.pesos.edit_modified(False)
            self.invalidar()

    def actualizar_revision(self):
        cantidad = len(self.miembros)
        presupuesto = ('Sin tope de presupuesto' if self.variables['modo'].get() == 'Costo mínimo'
                       else f"Presupuesto total: Q {self.variables['presupuesto'].get()}")
        self.revision_texto.set(
            f"{cantidad} integrante(s): {', '.join(p['nombre'] for p in self.miembros)}\n\n"
            f"Período: {self.variables['dias'].get()} días · {presupuesto}\n\n"
            f"Región del catálogo: {self.variables['region'].get()}\n\n"
            f'{len(self.exclusiones)} alimento(s) excluido(s) · {len(self.limites)} límite(s) diarios por persona.\n\n'
            'Podrás consultar la compra del período, los escenarios de cada persona y el aporte '
            'nutricional diario de cada alimento.'
        )
        estado = 'normal' if cantidad and not self.ocupada else 'disabled'
        self.boton_ejecutar.configure(state=estado)
        self.boton_req.configure(state=estado)

    def limpiar_resultados(self):
        self.consulta = None
        self.seleccionado = None
        self.resultados = []
        self.escenarios.mostrar(pd.DataFrame())
        self.aportes_alimentos.mostrar()
        for tabla in self.tablas.values():
            tabla.mostrar(pd.DataFrame())
        self.selector_vista.configure(values=(), state='disabled')
        self.vista.set('')
        self.boton_exportar.configure(state='disabled')
        self.escribir_notas('')

    def invalidar(self):
        self.revision += 1
        self.limpiar_resultados()
        self.resumen.set('La configuración cambió. Calcula nuevamente para ver los resultados.')
        self.actualizar_revision()

    def iniciar(self, solo_requerimientos=False):
        if self.ocupada:
            return
        try:
            if not self.miembros:
                raise ValueError('Agrega al menos un integrante antes de calcular.')
            personas = [crear_persona(dict(datos)) for datos in self.miembros]
            opciones = {'solo_requerimientos': solo_requerimientos}
            if not solo_requerimientos:
                opciones.update(
                    dias=numero(self.variables['dias'].get(), 'Días', minimo=1, maximo=365, entero=True),
                    presupuesto=numero(self.variables['presupuesto'].get(), 'Presupuesto total')
                    if self.variables['modo'].get() == 'Con presupuesto' else None,
                    exclusiones=tuple(self.exclusiones), limites=dict(self.limites),
                    region=self.variables['region'].get(),
                    penalizaciones_min={n: numero(self.variables[f'min_{n}'].get(), f'Penalización costo: {n}')
                                        for n in ('energia', 'colesterol')},
                )
                if opciones['presupuesto'] is not None:
                    opciones['pesos'] = leer_pesos(self.pesos.get('1.0', 'end'))
                    opciones['penalizaciones_max'] = {
                        n: numero(self.variables[f'max_{n}'].get(), f'Penalización cobertura: {n}')
                        for n in ('energia', 'colesterol')
                    }
            ruta = self.variables['catalogo'].get()
        except (ValueError, KeyError) as error:
            messagebox.showerror('Revisa los datos', str(error), parent=self)
            return
        self.ocupada = True
        revision = self.revision
        self.limpiar_resultados()
        self.actualizar_revision()
        self.resumen.set('Calculando la canasta…')
        self.estado.set('Calculando requerimientos y escenarios del hogar…')
        self.pasos.select(self.paginas[2])
        self.progreso.start(12)

        # El hilo recibe una instantánea; únicamente el hilo principal accede a Tk.
        def trabajo():
            try:
                resultado = ejecutar_canasta(personas, ruta, **opciones)
                self.cola.put(('ok', revision, resultado))
            except Exception as error:
                self.cola.put(('error', revision, f'{type(error).__name__}: {error}'))

        Thread(target=trabajo, daemon=True).start()
        self.after(100, self.recibir)

    def recibir(self):
        try:
            estado, revision, resultado = self.cola.get_nowait()
        except Empty:
            self.after(100, self.recibir)
            return
        self.ocupada = False
        self.progreso.stop()
        self.actualizar_revision()
        if revision != self.revision:
            self.estado.set('La configuración cambió durante el cálculo. Vuelve a calcular.')
            return
        if estado == 'error':
            self.resumen.set('No se pudo completar la consulta. Revisa los datos y el catálogo.')
            self.estado.set('Consulta no completada.')
            messagebox.showerror('No se pudo calcular', resultado, parent=self)
            return
        self.mostrar_consulta(resultado)

    def mostrar_requerimientos(self, perfiles):
        filas = []
        def aplanar(valor, persona, ruta=''):
            if isinstance(valor, dict):
                for clave, contenido in valor.items():
                    aplanar(contenido, persona, f'{ruta} / {clave}' if ruta else clave)
            else:
                filas.append({'persona': persona, 'referencia': ruta, 'valor': valor})
        for perfil in perfiles:
            aplanar(perfil['evaluacion_peso'], perfil['persona'].nombre, 'evaluacion_peso')
            aplanar(perfil['requerimientos'], perfil['persona'].nombre)
        self.tablas['Requerimientos'].mostrar(pd.DataFrame(filas))

    def mostrar_consulta(self, consulta):
        self.consulta = consulta
        self.pasos.select(self.paginas[3])
        hogar = consulta['hogar']
        if hogar is None:
            self.mostrar_requerimientos(consulta['perfiles'])
            self.resumen.set('Requerimientos diarios de los integrantes calculados.')
            self.detalles.select(self.tablas['Requerimientos'])
            self.estado.set('Requerimientos calculados.')
            return
        nombres = [vista['nombre'] for vista in consulta['vistas']]
        self.selector_vista.configure(values=nombres, state='readonly')
        self.selector_vista.current(1 if len(consulta['perfiles']) == 1 else 0)
        for nombre, clave in (('Comparación de repartos', 'comparacion_repartos'),
                             ('Reparto del período', 'reparto_periodo')):
            datos = hogar.get(clave)
            self.tablas[nombre].mostrar(datos if datos is not None else pd.DataFrame())
        self.cambiar_vista()
        self.estado.set(f"Consulta terminada: {hogar['estado']} · {hogar['motivo_parada']}")

    def cambiar_vista(self, event=None):
        if self.consulta is None:
            return
        indice = self.selector_vista.current()
        if indice < 0:
            return
        vista = self.consulta['vistas'][indice]
        self.resultados = vista['resultados']
        self.mostrar_requerimientos([vista['perfil']] if vista['perfil'] else self.consulta['perfiles'])
        self.escenarios.mostrar(pd.DataFrame([
            {'propuesta': '★' if r['propuesta'] else '', 'modelo': r['tipo'],
             'escenario': r['escenario'], 'estado': r['estado'], 'costo_diario_Q': r['costo_total_q'],
             'cobertura_ponderada_pct': r.get('cobertura_ponderada_pct')}
            for r in self.resultados
        ]))
        # Preferir el modelo con presupuesto cuando existe, conservando los otros escenarios.
        elegido = next((i for i in reversed(range(len(self.resultados)))
                        if self.resultados[i]['propuesta']), 0)
        if vista['perfil'] is None:
            elegido = len(self.resultados) - 1
        if self.resultados:
            self.escenarios.tree.selection_set(str(elegido))
            self.escenarios.tree.focus(str(elegido))
            self.seleccionar()

    def seleccionar(self, event=None):
        indices = self.escenarios.tree.selection()
        if not indices or self.consulta is None or not self.resultados:
            return
        indice = int(indices[0])
        if indice >= len(self.resultados):
            return
        resultado = self.resultados[indice]
        self.seleccionado = resultado
        dias = self.consulta['dias']
        optimo = resultado['estado'] == 'Optimal'
        self.tablas['Alimentos'].mostrar(tabla_alimentos(resultado))
        self.tablas['Compra del período'].mostrar(tabla_alimentos(resultado, dias))
        self.tablas['Nutrientes'].mostrar(tabla_nutrientes(resultado))
        self.aportes_alimentos.mostrar(resultado)
        self.tablas['Diagnóstico'].mostrar(resultado['diagnostico_restricciones'])
        self.boton_exportar.configure(state='normal' if optimo and not self.ocupada else 'disabled')
        hogar = self.consulta['hogar']
        costo = resultado['costo_total_q']
        costos = (f'Costo diario: Q {costo:.2f} · Costo de {dias} días: Q {costo * dias:.2f}'
                  if costo is not None else 'Sin compra válida para este escenario.')
        self.resumen.set(f"{self.vista.get()} · {resultado['tipo']} · {resultado['estado']} · "
                         f"Región: {self.consulta['region_catalogo']}\n"
                         f"{costos}\nEstado del hogar: {hogar['estado']} · {hogar['motivo_parada']}")
        vista = self.consulta['vistas'][self.selector_vista.current()]
        if vista['perfil']:
            perfil = vista['perfil']
            self.resumen.set(self.resumen.get() +
                             f"\nPeso usado: {perfil['persona'].peso_para_calculos:.2f} kg · "
                             f"Energía requerida: {perfil['requerimientos']['energia']['ree']:.2f} kcal/día")
        self.escribir_notas(
            f"{self.vista.get()} · {resultado['escenario']}\n{costos}\n\n"
            'Alimentos y Aporte por alimento muestran cantidades y valores nutricionales DIARIOS.\n'
            f'Compra del período y la exportación multiplican cantidades, costos y aportes por {dias} días.\n'
            'Los aportes nutricionales descuentan la fracción no comestible.\n'
            'Nutrientes compara aportes diarios con referencias y límites del modelo.\n'
            'El hogar suma las propuestas elegidas; revisa cada persona para evaluar su cobertura.\n'
            '★ identifica la propuesta de cada modelo según su función objetivo, incluidas penalizaciones.\n'
            'Costo mínimo conserva mínimos nutricionales; con presupuesto los convierte en metas.\n'
            'Los límites de alimentos son gramos comprados por persona y día, en ambos modelos.\n'
            'Una propuesta de costo mínimo puede superar el presupuesto total configurado.\n'
            'El reparto y su comparación corresponden al cálculo final con presupuesto, cuando existe.\n'
            'No se distribuyen comidas ni se exige variedad o cantidades enteras.'
        )
        if not optimo:
            self.detalles.select(self.notas)

    def escribir_notas(self, texto):
        self.notas.configure(state='normal')
        self.notas.delete('1.0', 'end')
        self.notas.insert('1.0', texto)
        self.notas.configure(state='disabled')

    def exportar(self):
        if self.seleccionado is None or self.seleccionado['estado'] != 'Optimal':
            return
        ruta = filedialog.asksaveasfilename(parent=self, defaultextension='.csv',
                                            initialfile='canasta_demo.csv', filetypes=[('CSV', '*.csv')])
        if ruta:
            try:
                tabla_alimentos(self.seleccionado, self.consulta['dias']).to_csv(
                    ruta, index=False, encoding='utf-8-sig')
            except OSError as error:
                messagebox.showerror('No se pudo exportar', str(error), parent=self)
            else:
                self.estado.set(f'Canasta exportada: {ruta}')

    def cerrar(self):
        self.destroy()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, default=DEFAULT_PICKLE, help='Catálogo procesado (.pkl).')
    args = parser.parse_args()
    DemoDieta(args.catalog).mainloop()


if __name__ == '__main__':
    main()
