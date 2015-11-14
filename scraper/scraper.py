import json
import tweepy
import re
import pytz
from datetime import datetime
from django.db import transaction
from scraper.models import Tweet, HashTag, MainUserSnapshot, FirstWord, OtherUser, Corpus
from scraper.credentials import CONSUMER_KEY, CONSUMER_SECRET, TARGET_HANDLE
from tweepy.error import TweepError
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned


inline_user_pattern = re.compile(r'@(\w+)')
url_pattern = re.compile(r'(https?:\/\/)([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*(\/)?')
first_word_pattern = re.compile(r'^(\w+)')
final_word_pattern = re.compile(r'(@|#)(\w+)(\!|\.|\?|\.+)?$')

tz = pytz.timezone('utc')

auth=tweepy.AppAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
api=tweepy.API(auth, parser=tweepy.parsers.JSONParser(), wait_on_rate_limit=True, wait_on_rate_limit_notify=True)


def tweet_cleaner(tweet):
	tweet_text = tweet['text']
	#First we get rid of urls and any whitespace created by re.sub()
	tweet_text = re.sub(url_pattern, '', tweet_text).rstrip()
	#Then we retrieve and check the first character of the final word of the string
	final_word_match = re.search(final_word_pattern, tweet_text)
	#If we keep on finding a @ or a # at the end of the string, we keep on substituting them and rstripping
	while final_word_match:
		tweet_text = re.sub(final_word_pattern, '', tweet_text).rstrip()
		final_word_match = re.search(final_word_pattern, tweet_text)
	#Then we replace @ and # everywhere else with an empty string
	tweet_text = tweet_text.replace("@", "").replace("#", "").rstrip().lstrip()
	#And finally we fetch the first word
	try:
		first_word = tweet_text.split()[0].replace("\"", "")
	except IndexError:
		first_word = None
	else:
		#To check we're not getting hashtags after removed urls
		if first_word[0] == ".":
			first_word = None
	return first_word, tweet_text


def get_target_snapshot():
	timeline = api.user_timeline(id=TARGET_HANDLE, since_id=None, count=1)
	user = timeline[0]['user']
	new_snapshot = MainUserSnapshot(description=user['description'], favourites_count=user['favourites_count'],
		followers_count=user['followers_count'], friends_count=user['friends_count'], twitter_id=user['id_str'],
		listed_count=user['listed_count'], date_added=datetime.now(pytz.utc))
	try:
		latest_snapshot = MainUserSnapshot.objects.latest('date_added')
	except ObjectDoesNotExist:
		latest_snapshot = None
	if latest_snapshot != new_snapshot:
		new_snapshot.save()


@transaction.atomic
def scrape_target(long_run=False):
	try:
		latest_tweet = Tweet.objects.latest('twitter_published_date')
		latest_tweet_id = latest_tweet.tweet_id
	except ObjectDoesNotExist:
		latest_tweet_id = None
	if not long_run:
		timeline = api.user_timeline(id=TARGET_HANDLE, since_id=latest_tweet_id, count=200)
	else:
		timeline = api.user_timeline(id=TARGET_HANDLE, max_id=latest_tweet_id, count=200)
	count = 0
	check = 0
	while timeline:
		for tweet in timeline:
			count += 1
			tweet_id = tweet['id_str']
			try:
				match = Tweet.objects.get(tweet_id=tweet_id)
			except ObjectDoesNotExist:
				pass
			else:
				# This is a really ugly hack
				if long_run:
					check += 1
					if check > 1:
						timeline = []
						break
					else:
						check = 0
						continue
				else:
					timeline = []
					break
			hashtags = tweet['entities']['hashtags']
			user_mentions = tweet['entities']['user_mentions']
			pubdate = datetime.strptime(tweet['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
			pubdate = pubdate.replace(tzinfo=tz)
			date_added = datetime.now(pytz.utc)
			tweet_url = 'https://twitter.com/' + TARGET_HANDLE + '/status/' + str(tweet_id)
			tweet_text = tweet['text']
			text_first_word, tweet_text_clean = tweet_cleaner(tweet)
			if text_first_word == 'RT':
				continue
			retweet_count = tweet['retweet_count']
			favourite_count = tweet['favorite_count']
			in_reply_to_screen_name = tweet['in_reply_to_screen_name']
			in_reply_to_status_id = tweet['in_reply_to_status_id_str']
			in_reply_to_user_id = tweet['in_reply_to_user_id_str']
			is_quote_status = tweet['is_quote_status']
			source = tweet['source']
			json_dump = json.dumps(tweet)
			if in_reply_to_screen_name:
				try:
					existing_user = OtherUser.objects.get(handle=in_reply_to_screen_name)
				except ObjectDoesNotExist:
					new_user = OtherUser(handle=in_reply_to_screen_name, twitter_id=in_reply_to_user_id)
					new_user.save()
					reply_user = new_user
				else:
					reply_user = existing_user
				is_reply = True
			else:
				reply_user = None
				is_reply = False
			if not is_quote_status and text_first_word is not None:
				try:
					existing_firstword = FirstWord.objects.get(word=text_first_word)
					tweet_first_word = existing_firstword
				except ObjectDoesNotExist:
					new_firstword = FirstWord(word=text_first_word)
					new_firstword.save()
					tweet_first_word = new_firstword
			new_tweet = Tweet(text=tweet_text, clean_text=tweet_text_clean, tweet_id=tweet_id,
				date_added=date_added, twitter_published_date=pubdate, tweet_url=tweet_url,
				retweet_count=retweet_count, favourite_count=favourite_count, is_reply=is_reply,
				reply_user=reply_user, in_reply_to_status_id=in_reply_to_status_id,
				is_quote_status=is_quote_status, quoted_status_id=quoted_status_id, first_word=tweet_first_word,
				source=source, json_dump=json_dump)
			new_tweet.save()
			if not long_run:
				corpus = Corpus.objects.all()[0]
				corpus.content = corpus.content + new_tweet.clean_text + ' '
				corpus.save()
			if hashtags:
				for hashtag in hashtags:
					try:
						hashtag_obj = HashTag.objects.get(text=hashtag['text'])
					except ObjectDoesNotExist:
						hashtag_obj = HashTag(text=hashtag['text'])
						hashtag_obj.save()
					hashtag_obj.related_tweet.add(new_tweet)
			if user_mentions:
				for user_mention in user_mentions:
					try:
						user_mention_obj = OtherUser.objects.get(handle=user_mention['screen_name'])
					except ObjectDoesNotExist:
						user_mention_obj = OtherUser(handle=user_mention['screen_name'], twitter_id=user_mention['id_str'])
						user_mention_obj.save()
					user_mention_obj.related_tweet.add(new_tweet)
		else:
			timeline = api.user_timeline(id=TARGET_HANDLE, max_id=tweet_id, count=200)


