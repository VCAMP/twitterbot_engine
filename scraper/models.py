from django.db import models

# Create your models here.

class Tweet(models.Model):
    text = models.CharField(max_length=200, blank=True)
    clean_text = models.CharField(max_length=200, blank=True)
    tweet_id = models.CharField(max_length=200, blank=True)
    date_added = models.DateTimeField('added_to_db_on', blank=True)
    twitter_published_date = models.DateTimeField('published_on_twitter', blank=True)
    tweet_url = models.URLField(max_length=200, default=None)
    retweet_count = models.IntegerField(blank=True)
    favourite_count = models.IntegerField(blank=True)
    is_reply = models.BooleanField(blank=True)
    reply_user = models.ForeignKey('OtherUser', blank=True, null=True)
    in_reply_to_status_id = models.CharField(max_length=200, blank=True, null=True)
    is_quote_status = models.BooleanField(blank=True)
    source = models.CharField(max_length=400, blank=True)
    first_word = models.ForeignKey('FirstWord', blank=True, null=True)
    json_dump = models.TextField(blank=True)

    def __str__(self):
        return self.text


class HashTag(models.Model):
	text = models.CharField(max_length=200)
	related_tweet = models.ManyToManyField(Tweet)

	def __str__(self):
		return self.text


class OtherUser(models.Model):
    handle = models.CharField(max_length=200)
    twitter_id = models.CharField(max_length=200, blank=True)
    related_tweet = models.ManyToManyField(Tweet)


class MainUserSnapshot(models.Model):
    description = models.TextField(blank=True)
    favourites_count = models.IntegerField(blank=True)
    followers_count = models.IntegerField(blank=True)
    friends_count = models.IntegerField(blank=True)
    twitter_id = models.CharField(max_length=200, blank=True)
    listed_count = models.IntegerField(blank=True)
    date_added = models.DateTimeField('added_to_db_on', blank=True)


class FirstWord(models.Model):
    word = models.CharField(max_length=200)

    def __str__(self):
        return self.text


class Corpus(models.Model):
    content = models.TextField(blank=True)