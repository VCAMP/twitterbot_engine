# twitterbot_engine
A Django-powered Twitterbot engine based on super-simple Markov chains

* Markov chain code comes from this nifty blog article: http://agiliq.com/blog/2009/06/generating-pseudo-random-text-with-markov-chains-u/

### How to use

* Download to your local repo folder/upload to your server/whatever
* Modify the credentials.py and the local_settings.py files
* python manage.py makemigrations + python manage.py migrate
* Either run spider.py and updater.py manually (awkward...) or set up a scheduler/cron job to run them at regular intervals
* That should be it!

### To do

* Clean up code structure
* Write some tests
* Improve scraper models in order to get rid of some general awkwardness (i.e. FirstWord model)
* Add views for data visualisation
* Add tests!