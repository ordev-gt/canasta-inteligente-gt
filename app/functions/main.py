from ..entities.Persona import Persona
from ..data.extractors import cargar_referencia_peso_longitud_0_5, cargar_referencia_imc_edad_5_19
from .evaluacion import evaluacion_de_requerimientos_diarios, Peso

if __name__ == "__main__":

    personas_prueba = {
        # 0 A 5 AÑOS
        "Niño <5 rango referencia": Persona(edad=0.1, sexo="hombre", peso=3.3, naf="low", altura=0.50),
        "Niño <5 sobrepeso": Persona(edad=0.1, sexo="hombre", peso=4.2, naf="low", altura=0.50),
        "Niña <5 rango referencia": Persona(edad=0.1, sexo="mujer", peso=3.35, naf="low", altura=0.50),
        "Niña <5 sobrepeso": Persona(edad=0.1, sexo="mujer", peso=4.2, naf="low", altura=0.50),

        # 5 A 19 AÑOS
        "Niño 10 años rango referencia": Persona(edad=10, sexo="hombre", peso=32, naf="low", altura=1.40),
        "Niño 10 años sobrepeso": Persona(edad=10, sexo="hombre", peso=45, naf="low", altura=1.40),
        "Niña 12 años rango referencia": Persona(edad=12.1, sexo="mujer", peso=41, naf="low", altura=1.50),
        "Niña 12 años sobrepeso": Persona(edad=12, sexo="mujer", peso=55, naf="low", altura=1.50),

        # ADULTOS
        "Hombre adulto normal": Persona(edad=25, sexo="hombre", peso=65, naf="low", altura=1.70),
        "Hombre adulto sobrepeso": Persona(edad=25, sexo="hombre", peso=85, naf="low", altura=1.70),
        "Mujer adulta normal": Persona(edad=25, sexo="mujer", peso=60, naf="low", altura=1.65),
        "Mujer adulta sobrepeso": Persona(edad=25, sexo="mujer", peso=75, naf="low", altura=1.65),

        # EMBARAZO
        "Embarazada peso pregestacional normal": Persona(edad=28, sexo="mujer", peso=70, naf="low", altura=1.65, esta_embarazada=True, mes_de_embarazo=5, peso_preembarazo=62),
        "Embarazada con sobrepeso pregestacional": Persona(edad=30, sexo="mujer", peso=85, naf="low", altura=1.65, esta_embarazada=True, mes_de_embarazo=8, peso_preembarazo=78),

        # LACTANCIA
        "Mujer lactante con reservas": Persona(edad=28, sexo="mujer", peso=64, naf="low", altura=1.65, esta_en_lactancia=True, reservas_de_energia_maternales=True, mes_de_lactancia=2),
        "Mujer lactante sin reservas": Persona(edad=28, sexo="mujer", peso=58, naf="low", altura=1.65, esta_en_lactancia=True, reservas_de_energia_maternales=False, mes_de_lactancia=5),
    }

    for nombre, persona in personas_prueba.items():

        print("\n" + "=" * 80)
        print(nombre)
        print("=" * 80)

        #try:
        evaluacion_peso_resultado = Peso.evaluacion_peso(persona)
        requerimientos = evaluacion_de_requerimientos_diarios(persona)

        print(f"Edad: {persona.edad} años ({persona.edad_meses} meses)")
        print(f"Sexo: {persona.sexo}")
        print(f"Peso real: {persona.peso:.2f} kg")
        print(f"Altura: {persona.altura:.2f} m")
        print(f"NAF: {persona.naf}")
        print()

        print("EVALUACIÓN DEL PESO")
        print(f"Estado: {evaluacion_peso_resultado['estado_de_indicador']}")
        print(f"Peso para cálculos: {evaluacion_peso_resultado['peso_para_calculos']:.2f} kg")
        print(f"Fuente de peso: {evaluacion_peso_resultado['fuente_de_peso']}")
        print(f"Requiere intervención profesional: {evaluacion_peso_resultado['requiere_intervencion_profesional']}")
        print()

        print("REQUERIMIENTOS DIARIOS")
        print(f"Energía: {requerimientos['energia']['ree']:.2f} kcal/día")
        print(f"Proteína RPE: {requerimientos['proteina']['rpe']:.2f} g/día")
        print(f"Proteína dieta de referencia: {requerimientos['proteina']['rdd']['dieta_de_referencia']:.2f} g/día")

        proteina_mixta = requerimientos["proteina"]["rdd"]["dieta_mixta"]

        if proteina_mixta is not None:
            print(f"Proteína dieta mixta: {proteina_mixta:.2f} g/día")
        else:
            print("Proteína dieta mixta: No disponible")

        #except Exception as e:
            #print(f"ERROR: {e}")