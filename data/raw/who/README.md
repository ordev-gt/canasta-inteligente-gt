## Child Growth Standards 2006

Contiene información estadística sobre el peso esperado de acuerdo con la longitud o talla de niños y niñas de 0 a 5 años, utilizando los estándares de crecimiento infantil de la Organización Mundial de la Salud (OMS).

Los archivos están separados por sexo y grupo de edad:

* `wfl_boys_0-to-2-years_zscores.xlsx`: peso para longitud en niños de 0 a 2 años.
* `wfl_girls_0-to-2-years_zscores.xlsx`: peso para longitud en niñas de 0 a 2 años.
* `wfh_boys_2-to-5-years_zscores.xlsx`: peso para talla en niños de 2 a 5 años.
* `wfh_girls_2-to-5-years_zscores.xlsx`: peso para talla en niñas de 2 a 5 años.

La diferencia entre *length* y *height* responde al método de medición utilizado por la OMS. En menores de 2 años se utiliza longitud corporal medida en posición recostada, mientras que a partir de los 2 años se utiliza talla medida de pie.

### Fuente

Originalmente se obtuvieron los datos de:

https://www.who.int/tools/child-growth-standards/standards/weight-for-length-height

Los archivos corresponden a las tablas de puntajes Z (*z-scores*) publicadas por la OMS dentro de los *WHO Child Growth Standards*.

### Estructura de los archivos

Los cuatro archivos mantienen prácticamente la misma estructura. La principal diferencia es la primera columna:

* `Length`: longitud corporal en centímetros para niños y niñas de 0 a 2 años.
* `Height`: talla en centímetros para niños y niñas de 2 a 5 años.

El resto de columnas corresponde a parámetros estadísticos utilizados por la OMS para representar la distribución esperada del peso para cada longitud o talla.

#### `Length` / `Height`

Longitud o talla del niño o niña, expresada en centímetros.

Cada fila representa la distribución de peso esperada para una longitud o talla determinada.

Por ejemplo, una fila correspondiente a `50.0 cm` contiene los valores de peso de referencia para un niño o niña que mide 50 cm.

#### `L`

Parámetro de transformación Box-Cox utilizado por el método LMS de la OMS.

Las distribuciones antropométricas no son necesariamente simétricas. El parámetro `L` permite corregir esta asimetría para calcular puntajes Z de manera más precisa.

#### `M`

Mediana del peso esperado para la longitud o talla correspondiente, expresada en kilogramos.

Representa el valor central de la distribución de referencia de la OMS.

Para efectos del sistema, este valor puede utilizarse como peso poblacional de referencia cuando sea necesario sustituir un peso observado que se encuentre fuera del intervalo considerado adecuado.

`M` contiene mayor precisión decimal que la columna `SD0`.

#### `S`

Parámetro relacionado con la dispersión o variabilidad de la distribución.

Junto con `L` y `M`, permite calcular un puntaje Z continuo mediante el método LMS utilizado por la OMS.

Para valores donde `L != 0`, el puntaje Z puede calcularse aproximadamente mediante:

[
Z =
\frac{(X/M)^L - 1}
{L \cdot S}
]

donde:

* `X` es el peso observado del niño o niña.
* `L`, `M` y `S` son los parámetros correspondientes a su longitud o talla.

### Columnas SD

`SD` significa *Standard Deviation*, o desviación estándar.

Estas columnas muestran directamente el peso correspondiente a diferentes puntajes Z respecto de la mediana de referencia.

#### `SD3neg`

Peso correspondiente a un puntaje Z de `-3`.

Representa tres desviaciones estándar por debajo de la mediana.

#### `SD2neg`

Peso correspondiente a un puntaje Z de `-2`.

Este punto es utilizado por la OMS como límite para identificar emaciación mediante el indicador peso para longitud/talla.

#### `SD1neg`

Peso correspondiente a un puntaje Z de `-1`.

#### `SD0`

Peso correspondiente a un puntaje Z de `0`.

Representa la mediana de referencia, aunque normalmente se encuentra redondeada a una décima de kilogramo.

Para cálculos que requieran mayor precisión se recomienda utilizar la columna `M`.

#### `SD1`

Peso correspondiente a un puntaje Z de `+1`.

#### `SD2`

Peso correspondiente a un puntaje Z de `+2`.

Valores superiores a este punto se clasifican como sobrepeso de acuerdo con el indicador peso para longitud/talla de la OMS.

#### `SD3`

Peso correspondiente a un puntaje Z de `+3`.

Valores superiores a este punto representan un grado más pronunciado de exceso de peso y se utilizan en la clasificación de obesidad infantil dentro de los estándares de crecimiento de la OMS.

### Interpretación general

Para este proyecto, el indicador se interpreta de la siguiente manera:

| Puntaje Z   | Interpretación                                                              |
| ----------- | --------------------------------------------------------------------------- |
| `< -3`      | Emaciación grave                                                            |
| `-3 a < -2` | Emaciación                                                                  |
| `-2 a +2`   | Sin clasificación de emaciación ni sobrepeso según peso para longitud/talla |
| `> +2 a +3` | Sobrepeso                                                                   |
| `> +3`      | Obesidad                                                                    |

El intervalo comprendido entre `-2` y `+2` desviaciones estándar no debe interpretarse como una evaluación completa de la salud del niño. Únicamente indica que, según el indicador peso para longitud/talla, el peso no se encuentra dentro de los puntos de corte utilizados por la OMS para emaciación o sobrepeso.

Otros aspectos del crecimiento infantil, como talla para la edad o peso para la edad, no son evaluados mediante estos archivos.

### Uso dentro del proyecto

Estos datos se utilizan como referencia antropométrica antes de calcular requerimientos nutricionales.

La lógica general prevista es:

1. Identificar el archivo correspondiente según sexo y grupo de edad.
2. Buscar la fila correspondiente a la longitud o talla de la persona.
3. Comparar el peso observado con los valores de referencia de la OMS.
4. Determinar si el peso real puede utilizarse como referencia para los cálculos posteriores.
5. Cuando sea necesario obtener un peso poblacional de referencia, utilizar la mediana `M` correspondiente a la longitud o talla.

Los archivos no pretenden sustituir una evaluación nutricional profesional. Su función dentro del sistema es proporcionar una referencia antropométrica estandarizada y reproducible para población infantil sana.

## WHO BMI-for-age 5–19 years

Contiene información estadística de referencia de la Organización Mundial de la Salud para evaluar el **índice de masa corporal para la edad (IMC/edad)** en niños, niñas y adolescentes de aproximadamente 5 a 19 años.

Los archivos incluidos son:

* `bmi-boys-z-who-2007-exp.xlsx`: referencia de IMC para la edad en niños y adolescentes varones.
* `bmi-girls-z-who-2007-exp.xlsx`: referencia de IMC para la edad en niñas y adolescentes mujeres.

Estas tablas forman parte de la **WHO Growth Reference 2007** para población de 5 a 19 años.

### Fuente

Los datos provienen de la referencia oficial de crecimiento de la OMS para escolares y adolescentes:

https://www.who.int/tools/growth-reference-data-for-5to19-years

La documentación específica del indicador IMC para la edad se encuentra en:

https://www.who.int/tools/growth-reference-data-for-5to19-years/indicators/bmi-for-age

La referencia fue desarrollada originalmente en 2007 y continúa siendo utilizada y mantenida actualmente por la OMS para la evaluación antropométrica de niños y adolescentes de 5 a 19 años.

### Rango de edad

Los archivos contienen registros desde:

* `61 meses`
* hasta `228 meses`

Esto corresponde aproximadamente a edades entre 5 años y 1 mes y 19 años.

La edad se expresa en meses porque el IMC esperado cambia progresivamente durante el crecimiento y no puede evaluarse mediante puntos de corte fijos como en adultos.

### Indicador utilizado

El indicador evaluado es:

**IMC para la edad**

El IMC se calcula mediante:

[
IMC = \frac{peso\ (kg)}{altura^2\ (m)}
]

Sin embargo, en niños y adolescentes el valor del IMC por sí solo no es suficiente para determinar si el peso se encuentra dentro de un rango esperado.

El IMC observado debe compararse con la distribución de referencia correspondiente a:

* sexo;
* edad exacta;
* población de referencia OMS.

Por este motivo, un mismo IMC puede tener interpretaciones diferentes según la edad y el sexo de la persona.

### Estructura de los archivos

Ambos archivos contienen las siguientes columnas:

* `Month`
* `L`
* `M`
* `S`
* `SD4neg`
* `SD3neg`
* `SD2neg`
* `SD1neg`
* `SD0`
* `SD1`
* `SD2`
* `SD3`
* `SD4`

### Significado de las columnas

#### `Month`

Edad de la persona expresada en meses.

Cada fila representa la distribución de IMC esperada para una edad específica.

Por ejemplo, una fila con:

```text
Month = 120
```

corresponde aproximadamente a una persona de 10 años.

#### `L`

Parámetro de transformación Box-Cox utilizado por el método LMS.

Permite corregir la asimetría de la distribución antropométrica para calcular puntajes Z con mayor precisión.

#### `M`

Mediana del IMC esperado para una persona del sexo y edad correspondiente.

Representa el valor central de la distribución de referencia de la OMS.

Para este proyecto también puede utilizarse para calcular un peso corporal de referencia:

[
Peso_{ref} = M \times altura^2
]

donde:

* `M` es el IMC mediano de la OMS;
* `altura` se expresa en metros.

#### `S`

Parámetro relacionado con la dispersión de la distribución.

En conjunto con `L` y `M`, permite calcular un puntaje Z continuo mediante el método LMS.

Para valores donde `L != 0`, el puntaje Z puede calcularse mediante:

[
Z =
\frac{(X/M)^L - 1}
{L \cdot S}
]

donde:

* `X` es el IMC observado;
* `L`, `M` y `S` son los parámetros de referencia para la edad y sexo correspondientes.

### Columnas SD

`SD` significa *Standard Deviation*, o desviación estándar.

Estas columnas muestran directamente el IMC correspondiente a distintos puntajes Z.

#### `SD4neg`

IMC correspondiente a un puntaje Z de `-4`.

#### `SD3neg`

IMC correspondiente a un puntaje Z de `-3`.

Se utiliza como referencia para identificar delgadez severa.

#### `SD2neg`

IMC correspondiente a un puntaje Z de `-2`.

Valores inferiores a este punto se clasifican como delgadez de acuerdo con los criterios de la OMS.

#### `SD1neg`

IMC correspondiente a un puntaje Z de `-1`.

#### `SD0`

IMC correspondiente a un puntaje Z de `0`.

Representa la mediana de referencia, aunque puede encontrarse redondeada.

Para cálculos con mayor precisión se recomienda utilizar la columna `M`.

#### `SD1`

IMC correspondiente a un puntaje Z de `+1`.

Valores superiores a este punto se clasifican como sobrepeso en la referencia OMS de 5 a 19 años.

#### `SD2`

IMC correspondiente a un puntaje Z de `+2`.

Valores superiores a este punto se clasifican como obesidad.

#### `SD3`

IMC correspondiente a un puntaje Z de `+3`.

Representa un grado mayor de desviación respecto de la mediana.

#### `SD4`

IMC correspondiente a un puntaje Z de `+4`.

Representa valores extremos superiores dentro de la tabla de referencia.

### Interpretación según la OMS

Para el indicador IMC para la edad en población de 5 a 19 años, la OMS utiliza los siguientes puntos de corte:

| Puntaje Z      | Interpretación                             |
| -------------- | ------------------------------------------ |
| `< -3 SD`      | Delgadez severa                            |
| `-3 a < -2 SD` | Delgadez                                   |
| `-2 a +1 SD`   | Sin clasificación de delgadez ni sobrepeso |
| `> +1 a +2 SD` | Sobrepeso                                  |
| `> +2 SD`      | Obesidad                                   |

Es importante notar que los puntos de corte son diferentes de los utilizados para peso para longitud/talla en menores de 5 años.

En particular:

* en menores de 5 años, el sobrepeso se identifica a partir de `+2 SD`;
* entre 5 y 19 años, el sobrepeso se identifica a partir de `+1 SD`.

La OMS diseñó esta referencia de forma que, hacia los 19 años:

* `+1 SD` se aproxima a un IMC adulto de `25 kg/m²`;
* `+2 SD` se aproxima a un IMC adulto de `30 kg/m²`.

Esto permite una transición progresiva hacia los puntos de corte utilizados en adultos.

### Uso dentro del proyecto

Estas tablas se utilizan para determinar si el peso corporal de una persona entre 5 y 18 años puede considerarse una referencia adecuada para el cálculo posterior de requerimientos nutricionales.

La lógica general prevista es:

1. Calcular el IMC real:

[
IMC = \frac{peso}{altura^2}
]

2. Obtener la edad de la persona en meses.

3. Seleccionar el archivo correspondiente según el sexo.

4. Consultar la fila correspondiente a la edad en meses.

5. Comparar el IMC observado con los puntos de corte de la OMS.

6. Determinar el estado antropométrico según IMC para la edad.

7. Si el peso observado se encuentra dentro del rango aceptado para el indicador, utilizar el peso real para los cálculos posteriores.

8. Si existe exceso de peso y se requiere un peso poblacional de referencia, utilizar el IMC mediano `M` para calcular:

[
Peso_{ref} = M \times altura^2
]

### Alcance

El indicador IMC para la edad se utiliza únicamente como una herramienta antropométrica de referencia dentro del sistema.

No constituye por sí solo una evaluación completa del estado nutricional ni reemplaza la valoración realizada por un profesional de la salud.

Otros indicadores, como talla para la edad, desarrollo puberal, composición corporal o antecedentes clínicos, no son evaluados mediante estos archivos.

El propósito de estas tablas dentro del proyecto es determinar de forma reproducible si el peso observado constituye una referencia razonable para calcular requerimientos nutricionales en población sana.
