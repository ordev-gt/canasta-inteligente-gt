from ..entities.Persona import Persona
from .evaluacion import evaluacion_de_requerimientos_diarios, Peso

if __name__ == "__main__":

    personas_prueba = {
        # 0 A 5 AÑOS
        "Niño <5 rango referencia": Persona(
            nombre="5 rango referencia",
            edad=0.1,
            sexo="hombre",
            peso=3.3,
            naf="low",
            altura=0.50
        ),
        "Niño <5 sobrepeso": Persona(
            nombre="<5 sobrepeso",
            edad=0.1,
            sexo="hombre",
            peso=4.2,
            naf="low",
            altura=0.50
        ),
        "Niña <5 rango referencia": Persona(
            nombre="5 rango referencia",
            edad=0.1,
            sexo="mujer",
            peso=3.35,
            naf="low",
            altura=0.50
        ),
        "Niña <5 sobrepeso": Persona(
            nombre="<5 sobrepeso",
            edad=0.1,
            sexo="mujer",
            peso=4.2,
            naf="low",
            altura=0.50
        ),

        # 5 A 19 AÑOS
        "Niño 10 años rango referencia": Persona(
            nombre="años rango referencia",
            edad=10,
            sexo="hombre",
            peso=32,
            naf="low",
            altura=1.40
        ),
        "Niño 10 años sobrepeso": Persona(
            nombre="10 años sobrepeso",
            edad=10,
            sexo="hombre",
            peso=45,
            naf="low",
            altura=1.40
        ),
        "Niña 12 años rango referencia": Persona(
            nombre="años rango referencia",
            edad=12.1,
            sexo="mujer",
            peso=41,
            naf="low",
            altura=1.50
        ),
        "Niña 12 años sobrepeso": Persona(
            nombre="12 años sobrepeso",
            edad=12,
            sexo="mujer",
            peso=55,
            naf="low",
            altura=1.50
        ),

        # ADULTOS
        "Hombre adulto normal": Persona(
            nombre="Hombre adulto normal",
            edad=25,
            sexo="hombre",
            peso=65,
            naf="low",
            altura=1.70
        ),
        "Hombre adulto sobrepeso": Persona(
            nombre="Hombre adulto sobrepeso",
            edad=25,
            sexo="hombre",
            peso=85,
            naf="low",
            altura=1.70
        ),
        "Mujer adulta normal": Persona(
            nombre="Mujer adulta normal",
            edad=25,
            sexo="mujer",
            peso=60,
            naf="low",
            altura=1.65
        ),
        "Mujer adulta sobrepeso": Persona(
            nombre="Mujer adulta sobrepeso",
            edad=25,
            sexo="mujer",
            peso=75,
            naf="low",
            altura=1.65
        ),

        # EMBARAZO
        "Embarazada peso pregestacional normal": Persona(
            nombre="peso pregestacional normal",
            edad=28,
            sexo="mujer",
            peso=70,
            naf="low",
            altura=1.65,
            esta_embarazada=True,
            mes_de_embarazo=5,
            peso_preembarazo=62
        ),
        "Embarazada con sobrepeso pregestacional": Persona(
            nombre="con sobrepeso pregestacional",
            edad=30,
            sexo="mujer",
            peso=85,
            naf="low",
            altura=1.65,
            esta_embarazada=True,
            mes_de_embarazo=8,
            peso_preembarazo=78
        ),

        # LACTANCIA
        "Mujer lactante con reservas": Persona(
            nombre="lactante con reservas",
            edad=28,
            sexo="mujer",
            peso=64,
            naf="low",
            altura=1.65,
            esta_en_lactancia=True,
            reservas_de_energia_maternales=True,
            mes_de_lactancia=2
        ),
        "Mujer lactante sin reservas": Persona(
            nombre="lactante sin reservas",
            edad=28,
            sexo="mujer",
            peso=58,
            naf="low",
            altura=1.65,
            esta_en_lactancia=True,
            reservas_de_energia_maternales=False,
            mes_de_lactancia=5
        ),
    }

    for nombre, persona in personas_prueba.items():

        print("\n" + "=" * 80)
        print(nombre)
        print("=" * 80)

        try:
            # evaluacion_de_requerimientos_diarios ya establece
            # persona.peso_para_calculos internamente.
            requerimientos = evaluacion_de_requerimientos_diarios(persona)

            # Se vuelve a obtener solamente para mostrar los detalles antropométricos.
            evaluacion_peso_resultado = Peso.evaluacion_peso(persona)

            print(f"Edad: {persona.edad} años ({persona.edad_meses} meses)")
            print(f"Sexo: {persona.sexo}")
            print(f"Peso real: {persona.peso:.2f} kg")
            print(f"Altura: {persona.altura:.2f} m")
            print(f"NAF: {persona.naf}")
            print()

            # --------------------------------------------------
            # PESO
            # --------------------------------------------------

            print("EVALUACIÓN DEL PESO")
            print(
                f"Indicador: "
                f"{evaluacion_peso_resultado['indicador']}"
            )
            print(
                f"Estado: "
                f"{evaluacion_peso_resultado['estado_de_indicador']}"
            )
            print(
                f"Peso para cálculos: "
                f"{evaluacion_peso_resultado['peso_para_calculos']:.2f} kg"
            )
            print(
                f"Fuente de peso: "
                f"{evaluacion_peso_resultado['fuente_de_peso']}"
            )
            print(
                f"Requiere intervención profesional: "
                f"{evaluacion_peso_resultado['requiere_intervencion_profesional']}"
            )

            if evaluacion_peso_resultado["valor_de_indicador"] is not None:
                print(
                    f"Valor del indicador: "
                    f"{evaluacion_peso_resultado['valor_de_indicador']:.2f}"
                )

            print()

            # --------------------------------------------------
            # ENERGÍA
            # --------------------------------------------------

            energia = requerimientos["energia"]

            print("ENERGÍA")
            print(
                f"REE: {energia['ree']:.2f} "
                f"{energia['unidad']}/día"
            )
            print()

            # --------------------------------------------------
            # PROTEÍNA
            # --------------------------------------------------

            proteina = requerimientos["proteina"]

            print("PROTEÍNA")
            print(
                f"RPE: {proteina['rpe']:.2f} "
                f"{proteina['unidad']}/día"
            )
            print(
                f"RDD proteína de referencia: "
                f"{proteina['rdd_referencia']:.2f} "
                f"{proteina['unidad']}/día"
            )

            if proteina["rdd_dieta_mixta"] is not None:
                print(
                    f"RDD dieta mixta: "
                    f"{proteina['rdd_dieta_mixta']:.2f} "
                    f"{proteina['unidad']}/día"
                )
            else:
                print("RDD dieta mixta: No disponible")

        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")