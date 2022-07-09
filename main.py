from collections import namedtuple
from dotenv import dotenv_values
from textwrap import wrap
import businesstimedelta as btd
import datetime as dt
import builtins
import argparse
import tweepy
import pause
import re
import os


env = dotenv_values(".env")


parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", default=False, action='store_true',
                    help='Imprime el avance del programa (default: False)')
parser.add_argument("-t", "--twitter", default=False, action='store_true',
                    help='Publica en Twitter (default: False)')
arguments = parser.parse_args()


def print(*args, add_time=True, **kwargs):
    if not arguments.verbose:
        return
    if len(args) and add_time:
        now = dt.datetime.now().strftime("%m-%d-%Y %H:%M:%S")
        return builtins.print(f'[{now}]', *args, **kwargs)
    else:
        return builtins.print(*args, **kwargs)


Chapther = namedtuple("Chapther", ["emoji", "name"])




class Bot:
    def __init__(self, filename, end_date, init_active_time, end_active_time, max_len=280, chapters_filename=None):
        # Twitter
        if arguments.twitter:
            self.twitter = tweepy.Client(
                bearer_token        = env['BEARER_TOKEN'],
                consumer_key        = env['API_KEY'],
                consumer_secret     = env['API_KEY_SECRET'],
                access_token        = env['ACCESS_TOKEN'],
                access_token_secret = env['ACCESS_TOKEN_SECRET'],
            )
        self.filename = filename
        self.end_date = end_date
        self.init_active_time = init_active_time
        self.end_active_time = end_active_time
        self.max_len = max_len
        self.chapters_filename = chapters_filename
        self.chapters = self.read_chapters()
        self.read_next_article()
        self.post_datetimes = None
        self.interval = None

    def read_next_article(self):
        try:
            with open('tmp/next_article.txt', 'r') as f:
                self.next_article = int(f.readline().strip())
        except FileNotFoundError:
            self.next_article = 0
        if not self.next_article:
            self.next_article = 0
        return self.next_article

    def write_next_article(self):
        os.makedirs("tmp", exist_ok=True)
        with open('tmp/next_article.txt', 'w') as f:
            f.write(str(self.next_article))

    def read_chapters(self):
        '''
        Lee los capítulos de un archivo CSV.

        Parámetros
        ----------

        chapters_filename: str
            Nombre del archivo CSV con los capítulos. Si es none, retorna un diccionario vacío.
            El archivo debe seguir el siguiente formato:
                1,<emoji_capítulo>,<nombre_capítulo>\n
                ...\n
                <número_capítulo>,<emoji_capítulo>,<nombre_capítulo>

        Retorna
        -------
        dict
            Un diccionario que tiene como llaves el número de los capítulos y como valores objetos namedtuple.Chapther con el emoji y el nombre del capítulo.
        '''
        chapters = dict()
        if self.chapters_filename:
            with open(self.chapters_filename, 'r') as f:
                chapters = f.readlines()
            chapters = (line.strip().split(',') for line in chapters)
            chapters = {chapter[0]: Chapther(*chapter[1:]) for chapter in chapters}
        return chapters

    def get_post_datetimes(self):
        '''
        Devuelve una lista con las fechas de publicación de los artículos.
        '''
        workday = btd.WorkDayRule(
            start_time=dt.time(self.init_active_time),
            end_time=dt.time(self.end_active_time % 24),
            working_days=[0, 1, 2, 3, 4, 5, 6]
        )
        hours_rules = btd.Rules([workday])
        init_time = dt.datetime.now()
        active_hours = hours_rules.difference(init_time, self.end_date).timedelta
        self.interval = active_hours / len(self.arts)
        times = []
        actual_time = init_time + (self.interval / 2)
        for _ in self.arts:
            if actual_time.hour >= self.end_active_time:
                actual_time += dt.timedelta(days=1)
                new_hour = self.init_active_time + actual_time.hour - self.end_active_time
                actual_time = actual_time.replace(hour=new_hour)
            elif actual_time.hour < self.init_active_time:
                actual_time = actual_time.replace(hour=self.init_active_time)
            times.append(actual_time)
            actual_time += self.interval
        return times

    def write_post_datetimes(self):
        '''
        Escribe las fechas de publicación en un archivo temporal.
        '''
        os.makedirs("tmp", exist_ok=True)
        with open('tmp/post_datetimes.txt', 'w') as f:
            for i, post_datetime in enumerate(self.post_datetimes, start=1):
                f.write(f"art {i:03} | {post_datetime.strftime('%m-%d-%Y %H:%M:%S')}\n")

    def get_tweets(self, art, max_len=280):
        '''
        Dado un artículo (srt), retorna una lista de tweets con el artículo.

        Parámetros
        ----------

        art: str
            Un string que contiene en su primera línea el cápitulo y apartado al que corresponde el artículo.
            El resto del string es el texto del artículo.

            Debe tener la siguiente forma:
                <numero_capitulo>, <nombre_apartado>\n
                <texto_artículo>\n
                ...\n
                <texto_artículo>
        
        max_len: int, opcional
            La longitud máxima que puede tener cada tweet. Por defecto es 280.

        Retorna
        -------
        list
            Una lista de strings, donde cada elemento corresponde a un tweet.
        '''
        # Se eliminan los espacios en blanco en los extremos
        art = art.strip()
        # Se separa el artículo en su información y texto
        info, art = art.split('\n', 1)
        n_chapter, header = info.split(',')
        # Se obtiene la información del capítulo correspondiente
        chapter = self.chapters[n_chapter]
        # Se añade el emoji del capítulo al inicio del artículo
        art = f"{chapter.emoji} {art}"
        # Si el artículo es muy corto, se devuelve un solo tweet
        if len(art) <= max_len:
            return [art]
        # En caso contrario, se calculan los tweets necesarios
        tweets = []
        # Se resta de max_len es espacio necesario para codificar el índice de cada tweet
        max_len -= len("\n\n[XX/XX]")
        # Se separa el artículo en incisos
        clauses = art.split('\n')
        # Se recorren los incisos
        i = 0
        i_new = 0
        while i < len(clauses):
            actual_tweet = clauses[i]
            # Si el inciso es corto, se intenta añadir otro inciso en el mismo tweet
            if len(actual_tweet) <= max_len:
                actual_tweet_new = actual_tweet
                i_new = i
                while len(actual_tweet_new) < max_len and i_new < len(clauses):
                    actual_tweet = actual_tweet_new
                    i = i_new
                    i_new += 1
                    if i_new < len(clauses):
                        actual_tweet_new += '\n' + clauses[i_new]
                tweets.append(actual_tweet)
            # Si el inciso es muy largo, se divide en varios tweets
            else:
                incise_tweets = get_incise_tweets(actual_tweet, max_len - 2*len("..."))
                tweets.extend(incise_tweets)
            i += 1
        # Añadimos el índice de cada tweet
        tweets = list(tweet + f"\n\n[{i}/{len(tweets)}]" for i, tweet in enumerate(tweets, start=1))
        # Añadimos un último tweet con la información referida al capítulo y título del artículo
        context_tweet  = f"Este artículo es parte de:\n"
        context_tweet += f"\n{chapter.emoji} {chapter.name}"
        if header:
            context_tweet += f"\n          Apartado: {header}"
        context_tweet += f"\n\nPuedes leer la constitución completa en: chileconvencion.cl"
        if len(context_tweet) <= max_len:
            context_tweet = [context_tweet]
        else:
            context_tweet = get_incise_tweets(context_tweet, max_len - 2*len("..."))
        tweets.extend(context_tweet)
        return tweets

    def tweet(self, text, parent_tweet):
        '''
        Twittea un texto. Retorna el id del tweet generado.
        '''
        response = self.twitter.create_tweet(text=text, in_reply_to_tweet_id=parent_tweet)
        return response.data['id']

    def post_twitter(self, article):
        '''
        Publica un artículo en Twitter.
        '''
        print(f"Publicando artículo {self.next_article+1} en Twitter...", end=' ')
        tweets = self.get_tweets(article, self.max_len)
        actual_tweet = None
        for tweet_text in tweets:
            actual_tweet = self.tweet(tweet_text, parent_tweet=actual_tweet)
        print(f"Publicado!", add_time=False)

    def post_article(self, article):
        '''
        Publica un artículo en todas las redes sociales pedidas.
        '''
        if arguments.twitter:
            self.post_twitter(article)
        self.next_article += 1
        self.write_next_article()     

    def run(self, verbose=False):
        '''
        Ejecuta el programa.
        '''
        arts = get_arts(self.filename)
        self.arts = arts[self.next_article:]
        self.post_datetimes = self.get_post_datetimes()
        self.write_post_datetimes()
        print("Intervalo de publicación:", self.interval)
        for art, post_datetime in zip(self.arts, self.post_datetimes):
            pause.until(post_datetime)
            self.post_article(art)
            



def get_arts(filename):
    with open(filename, 'r') as file:
        text = file.read()
        arts = re.split("\n\n", text)
    return arts

def get_incise_tweets(incise, max_len):
    '''
    Dado un inciso, retorna una lista de tweets con el inciso.
    '''
    # Se eliminan los espacios en blanco en los extremos
    incise = incise.strip()
    # Se divide el inciso en bloques del largo de un tweet
    tweets = wrap(incise, max_len)
    # Se recorren los tweets generados
    for i in range(len(tweets)):
        # Si el tweet no es inicial y el tweet anterior no termina con un punto, se añaden puntos suspensivos al inicio
        if i > 0:
            if not re.search("[^.][.]", tweets[i-1][-2:]):
                tweets[i] = "..." + tweets[i]
        # Si el tweet no es final y no termina con un punto, se añaden puntos suspensivos al final
        if i < len(tweets) - 1:
            if not re.search("[^.][.]", tweets[i][-2:]):
                tweets[i] = tweets[i] + "..."
    return tweets


if __name__ == "__main__":
    # Archivos a leer
    filename = "nueva_constitución_texto_definitivo.txt"
    chapters_filename = "capitulos.csv"
    # Fecha en la que se publica el último tweet
    end_date = dt.datetime(2022, 8, 28, 23, 30, 0)
    # Cada día, los tweets solo se publican entre init_active_time y end_active_time
    init_active_time = 8
    end_active_time =  24
    bot = Bot(filename, end_date, init_active_time, end_active_time, max_len=280, chapters_filename=chapters_filename)

    bot.run()