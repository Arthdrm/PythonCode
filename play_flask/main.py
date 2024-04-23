from flask import Flask, render_template
import requests
import json

# Instantiating the flask app session
# Told flask that everything it need is in the current directory.
app = Flask(__name__)

def get_meme():
    url = "https://meme-api.com/gimme"
    # Create a get request -> get a response object -> convert into text (JSON)
    # JSON into python dictionary.
    response = json.loads(requests.request("GET", url).text)
    meme_large = response["preview"][-2]
    subreddit = response["subreddit"]
    return meme_large, subreddit, response


# Specifying the index route
@app.route('/')
def index():
    meme_pic, subreddit, response = get_meme()
    return render_template("index.html", meme_pic=meme_pic, subreddit=subreddit, response=response)

# Running the app in development mode (autoreload is active)
app.run("0.0.0.0", "80", debug=True)