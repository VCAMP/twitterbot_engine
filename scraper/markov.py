import random
import tweepy
from scraper.models import Corpus, FirstWord, HashTag
from scraper.credentials import CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET
from tweepy.error import TweepError


auth=tweepy.auth.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api=tweepy.API(auth)

class Markov(object):
	
	def __init__(self, corpus_object=Corpus.objects.all()[0]):
		self.cache = {}
		self.all_words = corpus_object.content.split()
		self.first_words = [row.word for row in FirstWord.objects.all()]
		self.all_words_size = len(self.all_words)
		self.first_words_size = len(self.first_words)
		self.database()
		
	
	def triples(self):		
		if len(self.all_words) < 3:
			return
		
		for i in range(len(self.all_words) - 2):
			yield (self.all_words[i], self.all_words[i+1], self.all_words[i+2])
			

	def database(self):
		for w1, w2, w3 in self.triples():
			key = (w1, w2)
			if key in self.cache:
				self.cache[key].append(w3)
			else:
				self.cache[key] = [w3]
				
	def generate_markov_text(self, length=140):
		seed = random.randint(0, self.all_words_size-3)
		seed_word, next_word = self.all_words[seed], self.all_words[seed+1]
		w1, w2 = seed_word, next_word
		gen_words = []
		for i in range(20):
			gen_words.append(w1)
			w1, w2 = w2, random.choice(self.cache[(w1, w2)])
		gen_words.append(w2)
		finalstring = ' '.join(gen_words)
		if len(finalstring) > 140:
			return self.generate_markov_text()
		else:
			if finalstring[-1] not in ".!?:":
				try:
					bang = finalstring.rindex("!")
				except ValueError:
					bang = 0
				try:
					comma = finalstring.rindex(",")
				except ValueError:
					comma = 0
				try:
					question = finalstring.rindex("?")
				except ValueError:
					question = 0
				try:
					fullstop = finalstring.rindex(".")
				except ValueError:
					fullstop = 0
				try:
					colon = finalstring.rindex(":")
				except ValueError:
					colon = 0
				winner = max(bang, comma, question, fullstop, colon)
				if 100 < winner < 140:
					finalstring = finalstring[:winner]
				else:
					return self.generate_markov_text()
			return finalstring


def produce_status():
	generator = Markov()
	markov_string = generator.generate_markov_text()
	hashtags = HashTag.objects.all()
	if len(markov_string) < 130:
		index = random.randint(0, len(hashtags))
		additional_hashtag = hashtags[index].text
		if len((markov_string + ' ' + additional_hashtag)) < 140:
			markov_string = markov_string + ' ' + '#' + additional_hashtag
	return markov_string


def post_status():
	status = produce_status()
	api.update_status(status=status)