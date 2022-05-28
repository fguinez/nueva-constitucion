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
arguments = parser.parse_args()


def print(*args, add_time=True, **kwargs):
    if not arguments.verbose:
        return
    if len(args) and add_time:
        now = dt.datetime.now().strftime("%m-%d-%Y %H:%M:%S")
        return builtins.print(f'[{now}]', *args, **kwargs)
    else:
        return builtins.print(*args, **kwargs)




class Bot:
    def __init__(self, end_date, init_active_time, end_active_time, max_len=280):
        # Twitter
        self.twitter = tweepy.Client(
            bearer_token        = env['BEARER_TOKEN'],
            consumer_key        = env['API_KEY'],
            consumer_secret     = env['API_KEY_SECRET'],
            access_token        = env['ACCESS_TOKEN'],
            access_token_secret = env['ACCESS_TOKEN_SECRET'],
        )
        self.end_date = end_date
        self.init_active_time = init_active_time
        self.end_active_time = end_active_time
        self.max_len = max_len
        self.read_ultimo_publicado()

    @property
    def post_datetimes(self):
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
        post_delta = active_hours / len(self.arts)
        actual_time = init_time + (post_delta / 2)
        for _ in self.arts:
            if actual_time.hour >= self.end_active_time:
                actual_time += dt.timedelta(days=1)
                new_hour = self.init_active_time + actual_time.hour - self.end_active_time
                actual_time = actual_time.replace(hour=new_hour)
            elif actual_time.hour < self.init_active_time:
                actual_time = actual_time.replace(hour=self.init_active_time)
            yield actual_time
            actual_time += post_delta

    def read_ultimo_publicado(self):
        try:
            with open('tmp/ultimo_publicado,txt', 'r') as f:
                self.ultimo_publicado = int(f.readline().strip())
        except FileNotFoundError:
            self.ultimo_publicado = 0
        if not self.ultimo_publicado:
            self.ultimo_publicado = 0
        return self.ultimo_publicado

    def write_ultimo_publicado(self):
        os.makedirs("tmp", exist_ok=True)
        with open('tmp/ultimo_publicado,txt', 'w') as f:
            f.write(str(self.ultimo_publicado))

    def tweet(self, text, parent_tweet):
        '''
        Twittea un texto. Retorna el id del tweet generado.
        '''
        response = self.twitter.create_tweet(text=text, in_reply_to_tweet_id=parent_tweet)
        return response.data['id']

    def post_article(self, article):
        '''
        Publica un artículo.
        '''
        print(f"Publicando artículo {self.ultimo_publicado+1}...", end=' ')
        tweets = get_tweets(article, self.max_len)
        actual_tweet = None
        for tweet_text in tweets:
            actual_tweet = self.tweet(tweet_text, parent_tweet=actual_tweet)
        print(f"Publicado!", add_time=False)
        self.ultimo_publicado += 1
        self.write_ultimo_publicado()

    def run(self, verbose=False):
        '''
        Ejecuta el programa.
        '''
        arts = get_arts("borrador_nueva_constitución.txt")
        self.arts = arts[self.ultimo_publicado+1:]
        for art, post_datetime in zip(self.arts, self.post_datetimes):
            pause.until(post_datetime)
            self.post_article(art)
            



def get_arts(filename):
    with open(filename, 'r') as file:
        text = file.read()
        arts = re.split("\n\n", text)
    return arts

def get_tweets(art, max_len=280):
    '''
    Dado un artículo (srt), retorna una lista de tweets con el artículo.
    '''
    # Se eliminan los espacios en blanco en los extremos
    art = art.strip()
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
    return tweets

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
    # Fecha en la que se publica el último tweet
    end_date = dt.datetime(2022, 6, 29)
    # Los tweets solo se publican entre init_active_time y end_active_time
    init_active_time = 8
    end_active_time =  24
    bot = Bot(end_date, init_active_time, end_active_time, max_len = 280)
    bot.run()
    exit()
    arts = get_arts('borrador_nueva_constitución.txt')
    print(len(arts))
    for art in arts[400:401]:
        print(art)
        print()
        tweets = get_tweets(art)
        print(len(tweets))
        print()
        print(tweets)
        print()
        for tweet in tweets:
            print(tweet, add_time=False)
            print('|', add_time=False)
        print()
        print()
        print()
        print()