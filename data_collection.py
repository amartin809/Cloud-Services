from bs4 import BeautifulSoup
from imdb import IMDb
import json
import os
import pandas as pd
import requests
import re
from urllib.parse import urljoin

# this file is to make our data_base from our midterm larger

ia = IMDb()

url = "https://www.filmsite.org/greatestfilms-byyear.html" # url from which the names of the top grossing movies are scraped from
url_request = requests.get(url) 
soup = BeautifulSoup(url_request.content, 'html.parser') # gets content
pattern = re.compile(r"\d{4}\.html")
scrape = soup.find_all("a", {'href': pattern})

years = []
for refs in scrape:
    for match in re.findall(pattern,str(refs)):
        years.append(match)

part_url = "https://www.filmsite.org"

# getting the years from the first page and will use those to 
# create an absolutle url to go the page and scrape the movies 
additional_movies = []
for year in years:
    url_request = requests.get(urljoin(part_url, year))
    soup = BeautifulSoup(url_request.content, 'html.parser')
    titles = soup.find_all("b")
    for title in titles: 
        if re.match(r".*\(?\d{4}.*?\)", title.text, re.DOTALL):
            additional_movies.append(title.text)

movie_title = []
for movie in additional_movies:
    movie = re.sub("\\r|\\n", "", movie)
    movie = re.split(r" \(", movie)
    name = movie[0]
    name = re.sub(r" +", " ", name)
    movie_year = re.findall(r'\d{4}', str(movie))
    movie_title.append(name + " " + str(movie_year[0]))

movie_and_ids = []
for item in movie_title: 
    search_return = str(ia.search_movie(item)) # search for the movie and store the result as a string
    search_return = re.split(",", search_return) 
    item = re.sub(r"\(|\)", "", item) # from our title remove any paranthesis
    movie_ties = '_{}\({}\)_'.format(item[:-4], item[-4:]) # creating our pattern to search and match for
    for searches in search_return:
        if re.search(movie_ties, searches): # from the api's searched movie list, find the one that matches our title exactly
             movie_and_ids.append(searches)

movie_ids = []
movie_names = []

for info in movie_and_ids: # from our matched result, we only need the title and id number
    movie_names.append(re.sub("_", "", (re.search(r"_.*_", info)).group()))
    movie_ids.append(re.search(r"\d{7}",info).group())    

data_base_addition = dict(zip(movie_names, movie_ids))

# To get the original database and add moe movies to it 
cwd = os.getcwd()
path_to_database = (os.path.join(cwd, "database.txt"))

with open(path_to_database, 'r') as file:
    data_base = json.loads(file.read())

data_base = dict((y,x) for x,y in data_base.items()) # invert mapping

# seeing which movie ids are already in the old database and removing those s
# this way we will not have duplicates
already_there = []
for x in range(0,len(movie_ids)-1):
    if movie_ids[x] in data_base:
        del data_base[movie_ids[x]]
        
data_base = dict((y,x) for x,y in data_base.items()) # invert it again

data_base.update(data_base_addition)

# To store the new database
path_to_store = "/Users/asnafatimaali/Desktop/STEVENS/FE595/Final/database_new.txt" 
file = open(path_to_store, 'w+')
file.write(json.dumps(data_base))
file.close()
