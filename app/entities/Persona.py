
class Persona: 
    nombre: str
    edad: int # years
    edad_meses: int
    sexo: str
    peso: float
    altura: float = None
    naf: str # liviana, moderada, intensa
    naf_indice: float = None
    esta_embarazada: bool
    mes_de_embarazo:int 
    reservas_de_energia_maternales: bool
    esta_en_lactancia: bool
    peso_preembarazo: float | None
    mes_de_lactancia: int

    peso_para_calculos:float

    def __init__(self, nombre, edad, sexo, peso, naf=None, altura=None, 
                 esta_embarazada=False, mes_de_embarazo=None, reservas_de_energia_maternales=False,
                  esta_en_lactancia=False, peso_preembarazo: float = None, mes_de_lactancia: int = None,
                  exposicion_solar_suficiente = True):

        if not sexo in ['hombre', 'mujer']: 
            raise ValueError('Gender must be either hombre or mujer ')

        if edad < 0:
            raise ValueError("Edad must be greater than 0")

        if sexo=='hombre': 
            if esta_embarazada or esta_en_lactancia: 
                raise ValueError('Cannot instanciate hombre pregnant or in lactancy.')

        else:
            if esta_embarazada:
                if not mes_de_embarazo is None:
                    if not (mes_de_embarazo < 10 and  mes_de_embarazo >= 0 ):
                        raise ValueError(f'Pregnancy month not a valid value, must be a number between 0-9 ()')
                else: 
                    raise ValueError('Must define pregnancy in case mujer is pregnant') 


        self.nombre = nombre
        self.edad = edad
        self.edad_meses = round(edad * 12) # Aproximacion, preguntar si es conveniente indicar que se ingrese la edad exacta con meses. Ingresar fecha de nacimiento?
        self.sexo = sexo
        self.peso = peso
        self.naf = naf
        self.altura = altura
        self.esta_embarazada = esta_embarazada
        self.mes_de_embarazo = mes_de_embarazo
        self.esta_en_lactancia = esta_en_lactancia
        self.mes_de_lactancia = mes_de_lactancia
        self.reservas_de_energia_maternales = reservas_de_energia_maternales
        self.peso_preembarazo = peso_preembarazo
        self.exposicion_solar_suficiente = exposicion_solar_suficiente
        self.peso_para_calculos = None
        self.calculate_naf_index()

    
    def calculate_naf_index(self): 
        if self.naf is None: 
            self.naf_indice = None
            return 

        if self.naf == 'low': 
            self.naf_indice = 1.55
            return 
        
        if self.sexo == 'mujer': 
            self.naf_indice = 1.75 if self.naf == 'moderate' else 2.1 
            return
        # Hombre
        self.naf_indice = 1.85 if self.naf == 'moderate' else 2.2 
        return
