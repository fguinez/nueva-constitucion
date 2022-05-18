from dotenv import dotenv_values
from textwrap import wrap
import datetime as dt
import builtins
import argparse
import tweepy
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
    def __init__(self, max_len=280):
        # Twitter
        auth_twitter = tweepy.OAuthHandler(env['API_KEY'], env['API_KEY_SECRET'])
        auth_twitter.set_access_token(env['ACCESS_TOKEN'], env['ACCESS_TOKEN_SECRET'])
        self.twitter = tweepy.API(auth_twitter)
        self.max_len = max_len
        self.read_ultimo_publicado()

    def read_ultimo_publicado(self):
        try:
            with open('tmp/ultimo_publicado,txt', 'r') as f:
                self.ultimo_publicado = int(f.readline().strip())
        except FileNotFoundError:
            self.ultimo_publicado = -1
        return self.ultimo_publicado

    def write_ultimo_publicado(self):
        os.makedirs("tmp", exist_ok=True)
        with open('tmp/ultimo_publicado,txt', 'w') as f:
            f.write(str(self.ultimo_publicado))
    
    def tweet(self, text, in_reply_to_status):
        '''
        Twittea un texto.
        '''
        # Si el tweet debe ser una respuesta a otro tweet:
        if in_reply_to_status:
            status = self.twitter.update_status(status=text, in_reply_to_status_id=in_reply_to_status.id, auto_populate_reply_metadata=True)
        # En caso contrario:
        else:
            status = self.twitter.update_status(status=text)
        return status

    def post_art(self, article):
        '''
        Publica un artículo.
        '''
        print(f"Publicando artículo {self.ultimo_publicado+1}...", end=' ')
        tweets = get_tweets(article, self.max_len)
        actual_status = None
        for tweet_text in tweets:
            actual_status = self.tweet(tweet_text, actual_status)
        print(f"Publicado!", add_time=False)
        self.ultimo_publicado += 1
        self.write_ultimo_publicado()

    def run(self, verbose=False):
        '''
        Ejecuta el programa.
        '''
        arts = get_arts("borrador_nueva_constitución.txt")
        arts = arts[self.ultimo_publicado+1:]
        for art in arts[:3]:
            self.post_art(art)



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
    max_len -= len(" (XX/XX)")
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
    tweets = list(tweet + f" ({i}/{len(tweets)})" for i, tweet in enumerate(tweets, start=1))
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
    #bot = Bot(max_len = 280)
    #bot.run()
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