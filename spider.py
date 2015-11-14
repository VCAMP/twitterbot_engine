from scraper.models import HashTag, Corpus, OtherUser, MainUserSnapshot, Tweet, FirstWord
from scraper.scraper import scrape_target, get_target_snapshot

get_target_snapshot()
scrape_target()
print("DONE!")

