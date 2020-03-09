from bs4 import BeautifulSoup
import requests
import re
from imdb import IMDb
import json
from textblob import TextBlob

ia = IMDb() # create an imdb instance

url = "https://www.filmsite.org/boxoffice.html" # url from which the names of the top grossing movies are scraped from

url_request = requests.get(url) 

soup = BeautifulSoup(url_request.content, 'html.parser') # gets content

scrape = soup.find_all("li") # saving all li tags

data = []
for names in scrape: # saving just the text from the tags
    data.append(names.text)
# maybe combine lines 20 till 38 maybe in a function see if you can do a sapply like thing 
titles = []

for x in data: # from the text, saving only the movie titles 
    if re.match(r">?.*\d{4}", x, re.DOTALL):
        titles.append(x)

clean = []
for title in titles: # cleaning the movie title names
    title = re.sub(r"Filmsite.org", "", title)
    title = re.sub(r"\r|\n", "", title) 
    title = re.sub(r" +", " ", title)
    title =re.sub(r"^[ \t]+|[ \t]+$", "", title)
    clean.append(title)

for y in clean: # removing extra data that weren't titles from set
    if re.search(r"\(\d{4}\)", y): 
        continue
    else:
        clean.remove(y)

clean = list(set(clean)) # removing duplicates from list 

# the api returns a few results that match the input
# this will allow us to only get the result that matches our input exactly
movie_and_ids = []
for item in clean: 
    if re.search(r"The Domestic, Adjusted?",item): # data that wasn't deleted above
        continue
    else:
        search_return = str(ia.search_movie(item)) # search for the movie and store the result as a string
        search_return = re.split(",", search_return) 
        item = re.sub(r"\(|\)", "", item) # from our title remove any paranthesis
        movie_title = '_{}\({}\)_'.format(item[:-4], item[-4:]) # creating our pattern to search and match for
        for searches in search_return:
            if re.search(movie_title, searches): # from the api's searched movie list, find the one that matches our title exactly
                movie_and_ids.append(searches)

movie_ids = []
movie_names = []

for info in movie_and_ids: # from our matched result, we only need the title and id number
    movie_names.append(re.sub("_", "", (re.search(r"_.*_", info)).group()))
    movie_ids.append(re.search("\d{7}",info).group())

# getting imdb's own movies lists
top_250 = ia.get_top250_movies()
bottom_100 = ia.get_bottom100_movies()

# adding the titles and ids from imdb's list to our scraped list above
for x in top_250: 
    if x.movieID not in movie_ids:
        movie_ids.append(x.movieID)
        movie_names.append(x['title'])

for x in bottom_100:
    if x.movieID not in movie_ids:
        movie_ids.append(x.movieID)
        movie_names.append(x['title'])
 
#creating a dictionary of our database
data_base = dict(zip(movie_names, movie_ids))

#storing the database
path_to_store = "/Users/asnafatimaali/Desktop/STEVENS/FE595/Midterm/database.txt"
file = open(path_to_store, 'w+')
file.write(json.dumps(data_base))
file.close()


