# Nueva Constitución para Chile

Proyecto que busca difundir los artículos que compondrán la nueva constitución en caso de aprobarse en el [plebiscito constitucional](https://es.wikipedia.org/wiki/Plebiscito_constitucional_de_Chile_de_2022) a realizarse el 4 de septiembre de 2022.

Los artículos son publicados periódicamente en:
<p align="center">
    <a href="https://twitter.com/nuevaconstCL"><img src="https://imgur.com/hIXMqsE.png"> <b>@nuevaconstCL</b></a>
</p>

## Funcionamiento

El código en [`main.py`](https://github.com/fguinez/nueva-constitucion/blob/main/main.py) contiene la clase `Bot`, la cual recibe como parámetros:

- `filename`; Nombre del archivo que contiene los artículos divididos por doble saltos de línea.
- `end_date`: Una fecha en formato `datetime.date` que indica la fecha en la cual se deben terminar de postear los artículos.
- `init_active_time`: Una hora en formato `int` que indica la hora mínima en la cual se pueden realizar posts.
- `end_active_time`: Una hora en formato `int` que indica la hora máxima en la cual se pueden realizar posts.

En base a este información, el método `run` del objeto `Bot`:
1. Obtiene artículos desde `filename`.
2. Calcula la fecha de posteo de cada artículo. Se definen intervalos de tiempo equidistantes entre cada posteo, dividiendo las horas disponibles entre el instante actual y `end_date` por el número de artículos.
3. Postea cada artículo en su fecha correspondiente.

## Requerimientos

Puedes utilizar [pipenv](https://pypi.org/project/pipenv/) para instalar las dependencias de este proyecto. El comando `pipenv sync`instalará:
- [`tweepy`](https://pypi.org/project/tweepy/)
- [`python-dotenv`](https://pypi.org/project/python-dotenv/)
- [`pause`](https://pypi.org/project/pause/)
- [`businesstimedelta`](https://pypi.org/project/businesstimedelta/)

Adicionalmente, deberás configurar una cuenta de Twitter con la que puedas publicar los artículos y crear un archivo `.env` con la siguiente información:
```
API_KEY=[YOUR-API-KEY]
API_KEY_SECRET=[YOUR-API-KEY-SECRET]
BEARER_TOKEN=[YOUR-BEARER-TOKEN]
ACCESS_TOKEN=[YOUR-ACCESS-TOKEN]
ACCESS_TOKEN_SECRET=[YOUR-ACCESS-TOKEN-SECRET]
```

## Ejecución

Una vez que cumplas con los requisitos de más arriba, basta con ejecutar:
```
python main.py
```

## Licencia

Este proyecto es de código abierto y está licenciado bajo [GNU General Public License v3.0](https://github.com/fguinez/nueva-constitucion/blob/main/LICENSE).