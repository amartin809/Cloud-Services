from imdb import IMDb
import json
import numpy as np
import os
import pandas as pd
import re 
from sklearn.preprocessing import MultiLabelBinarizer

ia = IMDb() # get the imdb instance
cwd = os.getcwd() # get the working directory
path_to_database = (os.path.join(cwd, "database_new.txt"))
#path_to_database = "/Users/asnafatimaali/Desktop/STEVENS/FE595/Midterm_extra/database.txt"   # PATH TO DATABASE 
with open(path_to_database, 'r') as file: # load in data
    data_base = json.loads(file.read())


# to initialize variables for data storage
reviews = []
rating_votes = []
genres = []
first_genre = []
movie_rating = []
budget = []
runtime = [] #in minutes
num_actors = []

actors = []
roles = []

for ids in data_base.values(): # for the movie ids in the data base get the following
    if ids not in movie_id:  
        moveee = ia.get_movie(ids)
        ia.update(moveee, info=['vote details', 'reviews'])

        # to get reviews 
        try:
            moview_review = ""
            for x in range(0,len(moveee['reviews'][x])-1): # imdbpy api only gives you 25 reviews 
                one_review = moveee['reviews'][x]['content']
                moview_review = moview_review + " " + one_review
            reviews.append(moview_review)
        except IndexError:
            reviews.append(" ")
        except KeyError:
            reviews.append(" ")

        # to get votes by users. The votes are used by imdb to come up with their score
        try:
            rating_votes.append(moveee['votes'])
        except ValueError:
            rating_votes.append(np.NAN)
        except KeyError:
            rating_votes.append(np.NAN)

        # to get genres, we collected all genres and the first one in the list

        genres.append(moveee['genres'])
        first_genre.append(moveee['genres'][0])

        # Imdb's ratings 
        try:
            movie_rating.append(moveee['rating'])
        except ValueError:
            movie_rating.append(np.NAN)
        except KeyError:
            movie_rating.append(np.NAN)

        # the budget of the film  
        try:
            something = moveee['box office']
            numba = re.split(" ", something['Budget'])[0]
            numba = re.sub("\$","", numba)
            numba = re.sub(",", "", numba)
            numba = re.sub(r"\D","", numba)
            try:
                numba = int(numba)
            except ValueError:
                numba = float(numba)
        except KeyError:
            numba = np.NAN
        budget.append(numba)


        # the Runtime in minutes
        try:
            runtime = runtime + moveee['runtimes']
        except ValueError:
            runtime.append(np.NAN)
        except KeyError:
            runtime.append(np.NAN)


        # The number of actor Actors
        try: 
            num_actors.append(len(moveee['cast']))
        except KeyError:
            num_actors.append(np.NAN)
            movie_id.append(ids)

# to create a data frame and store the information
movie_data = pd.DataFrame()

movie_data['movie_id'] = movie_id
movie_data['reviews'] = reviews
movie_data['rating_votes'] = rating_votes
movie_data["genres"] = genres
movie_data['first_genre'] = first_genre
movie_data["movie_rating"] = movie_rating
movie_data['budget'] = budget
movie_data['runtime'] = runtime
movie_data["num_actors"] = num_actors
    
movie_data.to_csv('/Users/asnafatimaali/Desktop/STEVENS/FE595/Final/movie_data.csv')

# created a separate loop later to get information on the actors 
#initializing variables 
actor_ids = {}
movie_cast = []
movie_id = []

# for the actor searched, store the movie id, since order is not perserved in the dictionary, 
# the actors name and their id, from which a dictionary database is being created 
# and the list of actors in the movie 
for ids in data_base.values():
    movie_id.append(ids)
    moveee = ia.get_movie(ids)
    try:
        cast = moveee['cast']
        cast_string = str(moveee['cast'])
        cast_id = re.findall(r'\d{7}', cast_string)
        movie_cast.append(cast_id)
        for x in range(0,len(cast_id)-1):
            if cast_id[x] not in actor_ids.values():
                temp = dict({str(cast[x]): cast_id[x]})
                actor_ids.update(temp)
    except KeyError:
        movie_cast.append("N/A")
    except ValueError:
        movie_cast.append("N/A")

# To store actor and their ids
path_to_store = "/Users/asnafatimaali/Desktop/STEVENS/FE595/Final/actor_ids.txt" 
file = open(path_to_store, 'w+')
file.write(json.dumps(actor_ids))
file.close()


actors_data = pd.DataFrame()

actors_data['cast_ids'] = movie_cast
actors_data['movie_id'] = movie_id

actors_data.to_csv('/Users/asnafatimaali/Desktop/STEVENS/FE595/Final/actors_data.csv')

# we will be hot encoding the data frame actors_data in which we can get a breakdown of actors by movies 
movie_cast1 = pd.Series(movie_cast)

mlb = MultiLabelBinarizer()

cast_encoded = pd.DataFrame(mlb.fit_transform(movie_cast1), columns=mlb.classes_, index=movie_cast1.index)

#hot encoding created extra columns which we are removing
extra_cols = []
for x in cast_encoded.columns:
    if x not in actor_ids.values():
        extra_cols.append(x)

data = cast_encoded
data = data.drop(extra_cols, axis=1)

cast_encoded.index = movie_id

# from the hot encoded database we will create a dictionary by actor id key and list of movies values
actors_in_movies = {}
for x in data.columns:
    num_match = data.loc[data[x] == 1]
    index_match = list(num_match.index)
    temp = dict({str(x): index_match}) # dictionary where actor ids are key and movie ids are values
    actors_in_movies.update(temp)


# To store actor and their ids
path_to_store = "/Users/asnafatimaali/Desktop/STEVENS/FE595/Final/actor_in_movies.txt" 
file = open(path_to_store, 'w+')
file.write(json.dumps(actors_in_movies))
file.close()

