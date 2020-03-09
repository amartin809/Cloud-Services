# FE595_Midterm- NLP Web API Services

This project is for creating a web API that will provide users with NLP data on movies submitted data. We have created & deployed this application through Flask.

# Getting Started

These instructions will get you a copy of the project up and running on your own AWS machine for development and testing purposes.

# Prerequisites

An AWS ec2 instance needs to be created. For more details on this please refer to the AWS user guide here- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/concepts.html


# Installing
A step by step series of commands to get your environment running

Preparing the AWS instance. First you need to have super user permissions to create folders:

```sudo su```

Install git and Python 3 if they are not already presenton the instance
```
yum install git
yum install python3
```

You may not need to install pip separately, but if you run into an error while installing the required libraries, use the following command:
```
sudo easy_install pip
```

Install the following required libraries:
```
pip3 install flask

pip3 install fuzzywuzzy

pip3 install imdbpy

pip3 install matplotlib

pip3 install pandas

pip3 install textblob

python3 -m textblob.download_corpora

pip3 install sklearn

pip3 install wikipedia

pip3 install wordcloud
```
We have made the code available in a git repo. Clone to repository and get the code
```
cd ../..
git clone https://github.com/AsnaFatimaAli/FE595_Midterm.git
ls 
cd FE595_MidTerm/
ls -ltr
```
Now lets try to run the flask application-
```
python3 midterm_service.py
[root@ip-172-31-43-40 MidTerm]# python3 midterm_service.py
 * Serving Flask app "midterm_serice" (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: off
 * Running on http://0.0.0.0:8080/ (Press CTRL+C to quit)
```
Now the applcation is up and running.

# Running the tests
You can look at the application file using the base link - http://your specfic IP address :8080/

# Built With

Flask - The web framework used
Git - Code management

# Description of Serivces

Movie Polarity: provides polarity of the movie based on the movie's synopsis.

Language Switch: translates the synopsis to different languages.

Movie Similarity: compares two movies using cosine similarity.

Mood Mood: Uses cosine similarity to compare a movie's synopsis to an inputted movie/emotion. 

Top Noun Phrases: calculates the top noun phrases of a movie.

Top Adjectives: displays the top adjectives of a movie.

Movie Recommender: provides you with 20 movies similar to the movie inputted determined with kmeans.

Word Clouds of User Reviews: Gives you a word of the user reviews. 

Actor in Movie: Gives you a list of movies the actor has been in along with their picture.



