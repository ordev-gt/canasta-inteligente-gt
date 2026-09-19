"""Demo Tkinter del experimento de dieta, sin ejecutar ni leer el notebook."""

import argparse
from math import isfinite
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

import pandas as pd

from canasta_inteligente.application.cba_pipeline import DEFAULT_PICKLE, load_catalog_pickle
from canasta_inteligente.application.optimizacion_dieta import (
    maximizar_cobertura,
    minimizar_costo,
    preparar_consulta,
    tabla_nutrientes,
    validar_catalogo,
)
from canasta_inteligente.domain.persona import Persona


def numero(texto, nombre, minimo=0, estricto=False, maximo=None, entero=False):
    try:
        valor = float(str(texto).strip().replace(',', '.'))
    except ValueError:
        raise ValueError(f'{nombre}: ingresa un número válido.') from None
    if (not isfinite(valor) or valor < minimo or (estricto and valor == minimo)
            or (maximo is not None and valor > maximo) or (entero and not valor.is_integer())):
        limite = 'mayor que' if estricto else 'mayor o igual a'
        raise ValueError(f'{nombre}: debe ser {limite} {minimo}'
                         + (f' y menor o igual a {maximo}' if maximo is not None else '')
                         + (' y entero.' if entero else '.'))
    return int(valor) if entero else valor


def leer_pesos(texto):
    pesos = {}
    for linea in texto.splitlines():
        if not linea.strip():
            continue
        nombre, separador, valor = linea.partition('=')
        nombre = nombre.strip()
        if not separador or not nombre:
            raise ValueError('Escribe cada peso como nutriente = valor, uno por línea.')
        if nombre in pesos:
            raise ValueError(f'El peso de {nombre} aparece más de una vez.')
        pesos[nombre] = numero(valor, f'Peso de {nombre}')
    return pesos


def crear_persona(datos):
    mujer = datos['sexo'] == 'mujer'
    embarazo = mujer and datos['embarazo']
    lactancia = mujer and datos['lactancia']
    return Persona(
        nombre=datos['nombre'].strip() or 'Persona demo',
        edad=numero(datos['edad'], 'Edad'),
        sexo=datos['sexo'],
        peso=numero(datos['peso'], 'Peso', estricto=True),
        altura=numero(datos['altura'], 'Talla', estricto=True),
        naf={'Baja': 'low', 'Moderada': 'moderate', 'Alta': 'high'}[datos['actividad']],
        exposicion_solar_suficiente=datos['solar'],
        padece_sudoracion_profusa=datos['sudoracion'],
        esta_embarazada=embarazo,
        esta_en_lactancia=lactancia,
        peso_preembarazo=numero(datos['peso_previo'], 'Peso previo', estricto=True)
        if embarazo or lactancia else None,
        mes_de_embarazo=numero(datos['mes_embarazo'], 'Mes de embarazo', minimo=1,
                              maximo=9, entero=True) if embarazo else None,
        mes_de_lactancia=numero(datos['mes_lactancia'], 'Mes de lactancia', minimo=1,
                               entero=True) if lactancia else None,
        reservas_de_energia_maternales=embarazo and datos['reservas'],
    )


def ejecutar_demo(persona, catalog_path, modo, presupuesto=15, pesos=None,
                  penalizaciones_min=None, penalizaciones_max=None):
    """Entrada sin interfaz, también útil para pruebas y otras aplicaciones."""
    consulta = preparar_consulta(persona)
    consulta.update(resultados=[], propuestas={})
    if modo == 'Solo requerimientos':
        return consulta
    if modo not in ('Comparar ambos', 'Costo mínimo', 'Con presupuesto'):
        raise ValueError(f'Modo desconocido: {modo}')
    ruta = Path(catalog_path).expanduser()
    if not ruta.is_file():
        raise ValueError(
            f'No se encontró el catálogo: {ruta}\n'
            'Genera data/processed/cba_catalog.pkl ejecutando '
            'python -m canasta_inteligente.application.cba_pipeline.'
        )
    catalog = load_catalog_pickle(ruta)
    validar_catalogo(catalog, consulta['escenarios_minimizacion'])
    consulta['cantidad_alimentos'] = len(catalog)
    consulta['catalogo'] = str(ruta.resolve())
    if modo in ('Comparar ambos', 'Costo mínimo'):
        resultados = minimizar_costo(catalog, consulta['escenarios_minimizacion'], penalizaciones_min)
        for resultado in resultados:
            resultado['tipo'] = 'Costo mínimo'
        optimos = [r for r in resultados if r['estado'] == 'Optimal']
        consulta['propuestas']['Costo mínimo'] = min(
            optimos, key=lambda r: (r['valor_objetivo'], r['costo_total_q']), default=None,
        )
        consulta['resultados'].extend(resultados)
    if modo in ('Comparar ambos', 'Con presupuesto'):
        resultados = maximizar_cobertura(
            catalog, consulta['escenarios_maximizacion'], presupuesto, pesos, penalizaciones_max,
        )
        for resultado in resultados:
            resultado['tipo'] = 'Con presupuesto'
        optimos = [r for r in resultados if r['estado'] == 'Optimal']
        consulta['propuestas']['Con presupuesto'] = max(
            optimos, key=lambda r: (r['valor_objetivo'], -r['costo_total_q']), default=None,
        )
        consulta['resultados'].extend(resultados)
        consulta['presupuesto_q'] = presupuesto
    return consulta


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


class DemoDieta(tk.Tk):
    def __init__(self, catalog_path=DEFAULT_PICKLE):
        super().__init__()
        self.title('Canasta Inteligente GT · Demo de optimización de dieta')
        self.geometry('1280x820')
        self.minsize(1000, 680)
        self.cola = Queue()
        self.ocupada = False
        self.consulta = None
        self.seleccionado = None
        self.variables = {}
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
        ttk.Label(cabecera, text='Una persona · Un día · Costos en quetzales (Q)').pack(anchor='w')
        cuerpo = ttk.Panedwindow(self, orient='horizontal')
        cuerpo.grid(row=1, column=0, sticky='nsew', padx=12)
        izquierda = ttk.Frame(cuerpo, width=340)
        derecha = ttk.Frame(cuerpo)
        cuerpo.add(izquierda, weight=0)
        cuerpo.add(derecha, weight=1)
        controles = ttk.Notebook(izquierda)
        controles.pack(fill='both', expand=True)
        perfil = ttk.Frame(controles, padding=10)
        modelo = ttk.Frame(controles, padding=10)
        controles.add(perfil, text='Perfil')
        controles.add(modelo, text='Modelo y pesos')
        self.crear_perfil(perfil)
        self.crear_modelo(modelo, catalog_path)
        self.boton_req = ttk.Button(izquierda, text='Ver requerimientos', command=lambda: self.iniciar(True))
        self.boton_req.pack(fill='x', pady=(10, 4))
        self.boton_ejecutar = ttk.Button(izquierda, text='Ejecutar optimización', command=self.iniciar)
        self.boton_ejecutar.pack(fill='x', pady=4)
        self.progreso = ttk.Progressbar(izquierda, mode='indeterminate')
        self.progreso.pack(fill='x', pady=(4, 10))

        derecha.columnconfigure(0, weight=1)
        derecha.rowconfigure(2, weight=1)
        self.resumen = tk.StringVar(value='Completa el perfil y ejecuta la optimización para comparar los escenarios.')
        ttk.Label(derecha, textvariable=self.resumen, wraplength=760, padding=10).grid(row=0, column=0, sticky='ew')
        self.escenarios = Tabla(derecha, height=8)
        self.escenarios.grid(row=1, column=0, sticky='nsew', padx=8)
        self.escenarios.tree.bind('<<TreeviewSelect>>', self.seleccionar)
        self.detalles = ttk.Notebook(derecha)
        self.detalles.grid(row=2, column=0, sticky='nsew', padx=8, pady=8)
        self.tablas = {}
        for nombre in ('Alimentos', 'Nutrientes', 'Requerimientos', 'Diagnóstico'):
            tabla = Tabla(self.detalles)
            self.tablas[nombre] = tabla
            self.detalles.add(tabla, text=nombre)
        self.aportes_alimentos = AportesPorAlimento(self.detalles)
        self.detalles.insert(2, self.aportes_alimentos, text='Aporte por alimento')
        self.notas = ScrolledText(self.detalles, wrap='word', padx=12, pady=12, state='disabled')
        self.detalles.add(self.notas, text='Detalle y supuestos')
        self.boton_exportar = ttk.Button(derecha, text='Exportar alimentos del escenario a CSV',
                                        command=self.exportar, state='disabled')
        self.boton_exportar.grid(row=3, column=0, sticky='e', padx=8, pady=(0, 8))
        self.estado = tk.StringVar(value='Listo. El perfil inicial corresponde al código del notebook: 25 años y 70 kg.')
        ttk.Label(self, textvariable=self.estado, padding=(16, 8)).grid(row=2, column=0, sticky='ew')

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

    def crear_modelo(self, parent, catalog_path):
        self.campo(parent, 0, 'Modelo', 'modo', 'Comparar ambos',
                   ('Comparar ambos', 'Costo mínimo', 'Con presupuesto'))
        self.campo(parent, 1, 'Presupuesto diario Q', 'presupuesto', '15')
        ttk.Label(parent, text='Penalización por kcal / mg de desviación', wraplength=300).grid(
            row=2, column=0, columnspan=2, sticky='w', pady=(12, 4))
        self.campo(parent, 3, 'Costo: energía', 'min_energia', '1')
        self.campo(parent, 4, 'Costo: colesterol', 'min_colesterol', '0.1')
        self.campo(parent, 5, 'Cobertura: energía', 'max_energia', '1')
        self.campo(parent, 6, 'Cobertura: colesterol', 'max_colesterol', '0.1')
        ttk.Label(parent, text='Pesos para cobertura (omitidos = 1).\n0 = sin puntuación; 2 = doble importancia.',
                  wraplength=300).grid(row=7, column=0, columnspan=2, sticky='w', pady=(12, 4))
        self.pesos = ScrolledText(parent, height=5, width=30, wrap='none')
        self.pesos.insert('1.0', 'vitamina_d_mcg = 1\nfibra_dietetica_g = 1\n')
        self.pesos.grid(row=8, column=0, columnspan=2, sticky='nsew')
        ttk.Label(parent, text='Usa los nombres de la tabla Nutrientes; un peso por línea.',
                  wraplength=300).grid(row=9, column=0, columnspan=2, sticky='w', pady=4)
        self.variables['catalogo'] = tk.StringVar(value=str(catalog_path))
        ttk.Label(parent, text='Catálogo procesado del proyecto (.pkl)').grid(
            row=10, column=0, columnspan=2, sticky='w', pady=(12, 4))
        ttk.Entry(parent, textvariable=self.variables['catalogo']).grid(row=11, column=0, columnspan=2, sticky='ew')
        ttk.Button(parent, text='Elegir catálogo…', command=self.elegir_catalogo).grid(
            row=12, column=0, columnspan=2, sticky='ew', pady=4)
        parent.rowconfigure(8, weight=1)

    def elegir_catalogo(self):
        ruta = filedialog.askopenfilename(parent=self, title='Catálogo generado por este proyecto',
                                          filetypes=[('Catálogo procesado', '*.pkl')])
        if ruta:
            self.variables['catalogo'].set(ruta)

    def iniciar(self, solo_requerimientos=False):
        if self.ocupada:
            return
        try:
            datos = {clave: variable.get() for clave, variable in self.variables.items()}
            persona = crear_persona(datos)
            modo = 'Solo requerimientos' if solo_requerimientos else datos['modo']
            opciones = {}
            if modo in ('Comparar ambos', 'Costo mínimo'):
                opciones['penalizaciones_min'] = {
                    n: numero(datos[f'min_{n}'], f'Penalización costo: {n}')
                    for n in ('energia', 'colesterol')
                }
            if modo in ('Comparar ambos', 'Con presupuesto'):
                opciones['presupuesto'] = numero(datos['presupuesto'], 'Presupuesto')
                opciones['pesos'] = leer_pesos(self.pesos.get('1.0', 'end'))
                opciones['penalizaciones_max'] = {
                    n: numero(datos[f'max_{n}'], f'Penalización cobertura: {n}')
                    for n in ('energia', 'colesterol')
                }
        except (ValueError, KeyError) as error:
            messagebox.showerror('Revisa los datos', str(error), parent=self)
            return
        self.ocupada = True
        self.consulta = None
        self.seleccionado = None
        self.escenarios.mostrar(pd.DataFrame())
        self.aportes_alimentos.mostrar()
        for tabla in self.tablas.values():
            tabla.mostrar(pd.DataFrame())
        self.escribir_notas('Calculando una nueva consulta…')
        self.resumen.set(f'Calculando: {persona.nombre}, {persona.edad:g} años · {modo}')
        for boton in (self.boton_req, self.boton_ejecutar, self.boton_exportar):
            boton.configure(state='disabled')
        self.progreso.start(12)
        self.estado.set('Calculando requerimientos y resolviendo escenarios…')

        # El hilo recibe una instantánea; únicamente el hilo principal accede a Tk.
        def trabajo():
            try:
                resultado = ejecutar_demo(persona, datos['catalogo'], modo, **opciones)
                self.cola.put(('ok', resultado))
            except Exception as error:
                self.cola.put(('error', f'{type(error).__name__}: {error}'))

        Thread(target=trabajo, daemon=True).start()
        self.after(100, self.recibir)

    def recibir(self):
        try:
            estado, resultado = self.cola.get_nowait()
        except Empty:
            self.after(100, self.recibir)
            return
        self.ocupada = False
        self.progreso.stop()
        self.boton_req.configure(state='normal')
        self.boton_ejecutar.configure(state='normal')
        if estado == 'error':
            self.resumen.set('No se pudo completar la consulta. Revisa los datos y el catálogo.')
            self.estado.set('Consulta no completada.')
            messagebox.showerror('No se pudo calcular', resultado, parent=self)
            return
        self.mostrar_consulta(resultado)

    def mostrar_consulta(self, consulta):
        self.consulta = consulta
        persona = consulta['persona']
        evaluacion = consulta['evaluacion_peso']
        energia = consulta['requerimientos']['energia']['ree']
        self.resumen.set(f'{persona.nombre} · {persona.sexo} · {persona.edad:g} años · '
                         f'{persona.peso:g} kg · {persona.altura:g} m · Actividad: {persona.naf}\n'
                         f"Estado del peso: {evaluacion['estado_de_indicador']} · "
                         f"Peso usado: {persona.peso_para_calculos:.2f} kg · "
                         f'Energía requerida: {energia:.2f} kcal/día\n'
                         'Selecciona un escenario. ★ indica la propuesta según la función objetivo de cada modelo.')
        filas = []

        def aplanar(valor, ruta=''):
            if isinstance(valor, dict):
                for clave, contenido in valor.items():
                    aplanar(contenido, f'{ruta} / {clave}' if ruta else clave)
            else:
                filas.append({'referencia': ruta, 'valor': valor})

        aplanar(consulta['evaluacion_peso'], 'evaluacion_peso')
        aplanar(consulta['requerimientos'])
        self.tablas['Requerimientos'].mostrar(pd.DataFrame(filas))
        resumen = []
        for resultado in consulta['resultados']:
            propuesta = consulta['propuestas'].get(resultado['tipo']) is resultado
            resumen.append({
                'propuesta': '★' if propuesta else '', 'modelo': resultado['tipo'],
                'escenario': resultado['escenario'], 'estado': resultado['estado'],
                'costo_Q': resultado['costo_total_q'],
                'cobertura_ponderada_%': resultado.get('cobertura_ponderada_pct'),
                'objetivo': resultado['valor_objetivo'],
                'penalizacion': resultado['penalizacion_total'],
            })
        self.escenarios.mostrar(pd.DataFrame(resumen))
        if resumen:
            indice = next((i for i, fila in enumerate(resumen) if fila['propuesta']), 0)
            self.escenarios.tree.selection_set(str(indice))
            self.escenarios.tree.focus(str(indice))
            self.seleccionar()
        else:
            self.detalles.select(self.tablas['Requerimientos'])
            self.escribir_notas('Requerimientos calculados. Ejecuta la optimización para ver las canastas.')
        optimos = sum(r['estado'] == 'Optimal' for r in consulta['resultados'])
        self.estado.set(f'Consulta terminada: {optimos} de {len(resumen)} escenarios óptimos.'
                        if resumen else 'Requerimientos calculados.')

    def seleccionar(self, event=None):
        indices = self.escenarios.tree.selection()
        if not indices or self.consulta is None:
            return
        resultado = self.consulta['resultados'][int(indices[0])]
        self.seleccionado = resultado
        optimo = resultado['estado'] == 'Optimal'
        alimentos = resultado['alimentos']
        self.tablas['Alimentos'].mostrar(alimentos.loc[alimentos['porciones_100g'] > 1e-6])
        self.tablas['Nutrientes'].mostrar(tabla_nutrientes(resultado))
        self.aportes_alimentos.mostrar(resultado)
        self.tablas['Diagnóstico'].mostrar(resultado['diagnostico_restricciones'])
        self.boton_exportar.configure(state='normal' if optimo and not self.ocupada else 'disabled')
        notas = [f"{resultado['tipo']} · {resultado['escenario']}", f"Estado: {resultado['estado']}"]
        if optimo:
            notas.extend([
                f"Costo diario de alimentos: Q {resultado['costo_total_q']:.2f}",
                f"Valor de la función objetivo: {resultado['valor_objetivo']:.4f}",
                f"Penalización total: {resultado['penalizacion_total']:.4f}",
                f"Coeficientes de penalización: {resultado['penalizaciones']}",
                f"Energía requerida con el peso evaluado: {resultado['restricciones']['energia_kcal']['ct']:.2f} kcal/día",
                f"Energía aportada por la canasta: {resultado['aportes']['energia_kcal']:.2f} kcal/día",
                *[f'{nombre}: {valor:.4f}' for nombre, valor in resultado['desviaciones'].items()],
            ])
            if 'coberturas' in resultado:
                notas.extend([
                    f"Presupuesto diario: Q {resultado['presupuesto_q']:.2f}",
                    f"Cobertura media: {resultado['cobertura_media_pct']:.2f} %",
                    f"Cobertura ponderada: {resultado['cobertura_ponderada_pct']:.2f} %",
                    f"Pesos utilizados: {resultado['pesos_nutrientes']}",
                ])
            minimo = self.consulta['propuestas'].get('Costo mínimo')
            if minimo is not None and 'presupuesto_q' in self.consulta:
                diferencia = minimo['costo_total_q'] - self.consulta['presupuesto_q']
                notas.append(f'La propuesta de costo mínimo supera el presupuesto por Q {diferencia:.2f}.'
                             if diferencia > 1e-6 else 'La propuesta de costo mínimo cabe en el presupuesto.')
        else:
            notas.append('No hay solución óptima para este escenario. No se muestran cantidades ni costos válidos.')
        notas.extend([
            '', 'Lectura del experimento:',
            '• Costo mínimo: costo de alimentos + penalizaciones; conserva mínimos y máximos obligatorios.',
            '• Con presupuesto: suma de coberturas ponderadas − penalizaciones. El objetivo puede ser negativo.',
            '• Energía: penaliza déficit y exceso. Colesterol: penaliza solo el exceso.',
            '• La energía requerida procede del peso evaluado. La energía aportada por los alimentos puede diferir de esa referencia flexible.',
            '• Las coberturas se limitan a 100 % por nutriente. La media puede ocultar déficits individuales.',
            '• En cobertura, los mínimos nutricionales se vuelven metas; los máximos y las condiciones de hierro siguen siendo obligatorios.',
            '• Alimentos: gramos y porciones de 100 g comprados. Los aportes descuentan la fracción no comestible.',
            '• En Nutrientes, carne_g y sus límites se muestran en gramos comestibles (30 / 90 g).',
            '• Se usa el último precio general disponible de cada alimento; en su ausencia, urbano y luego rural.',
            '• Las propuestas se eligen por su función objetivo, incluidas las penalizaciones; cada modelo se compara por separado.',
            '• No se distribuyen comidas ni se exige variedad o cantidades enteras.',
            '', f"Catálogo: {self.consulta['catalogo']} ({self.consulta['cantidad_alimentos']} alimentos)",
        ])
        self.escribir_notas('\n'.join(notas))
        if not optimo:
            self.detalles.select(self.notas)
        elif self.detalles.select() != str(self.aportes_alimentos):
            self.detalles.select(self.tablas['Alimentos'])

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
                alimentos = self.seleccionado['alimentos']
                alimentos.loc[alimentos['porciones_100g'] > 1e-6].to_csv(ruta, index=False, encoding='utf-8-sig')
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
