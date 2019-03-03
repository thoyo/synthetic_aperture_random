from twython import Twython
from dotenv import load_dotenv
import pprint
import os

load_dotenv()
APP_KEY = os.getenv("APP_KEY")
APP_SECRET = os.getenv("APP_SECRET")

twitter = Twython(APP_KEY, APP_SECRET)
auth = twitter.get_authentication_tokens()
OAUTH_TOKEN = auth['oauth_token']
OAUTH_TOKEN_SECRET = auth['oauth_token_secret']

print(auth['auth_url'])

# I manually open this url in the browers and
# set oaut_verifier to the value like seen below.

oauth_verifier = input('Enter your pin:')
twitter = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
final_step = twitter.get_authorized_tokens(oauth_verifier)
FINAL_OAUTH_TOKEN = final_step['oauth_token']
FINAL_OAUTH_TOKEN_SECRET = final_step['oauth_token_secret']
twitter = Twython(APP_KEY, APP_SECRET,
                  FINAL_OAUTH_TOKEN, FINAL_OAUTH_TOKEN_SECRET)
pp = pprint.PrettyPrinter()
pp.pprint(twitter.verify_credentials())
pp.pprint(FINAL_OAUTH_TOKEN)
pp.pprint(FINAL_OAUTH_TOKEN_SECRET)
