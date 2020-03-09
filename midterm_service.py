from collections import defaultdict
import contextlib
from flask import Flask, escape, request, Response, render_template, redirect, url_for, send_file
from fuzzywuzzy import fuzz
import glob
from imdb import IMDb
import json
import matplotlib
import matplotlib.pyplot as plt
import operator
import os
import pandas as pd
import random
import re
from textblob import TextBlob, Word, Blobber 
from sklearn.feature_extraction.text import TfidfVectorizer
import wikipedia
from wordcloud import WordCloud

app = Flask(__name__)

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0 # Max age for the defailt cache to be zero seconds
app.config["CACHE_DEFAULT_TIMEOUT"] = 0 # chase timeout within zero seconds. 
matplotlib.use('Agg') # to get output for matplot lib

ia = IMDb() # to create an imdb instance from which we will be collecting data throughout 

cwd = os.getcwd()

# to open movie database
path_to_database = (os.path.join(cwd, "database_new.txt"))
#path_to_database = "/Users/asnafatimaali/Desktop/STEVENS/FE595/Midterm_extra/database.txt"   # PATH TO DATABASE 
with open(path_to_database, 'r') as file:
    data_base = json.loads(file.read())

# to open dictionary of actors and their corresponding ids from imdb
path_to_actorids = (os.path.join(cwd, "actor_ids.txt"))
with open(path_to_actorids, 'r') as file:
    actor_ids = json.loads(file.read())

# to open dictionary where the actor id is key and the list of movies they 
# were in base on our database are values
path_to_actorinmovies = (os.path.join(cwd, "actor_in_movies.txt"))
with open(path_to_actorinmovies, 'r') as file:
    actors_in_movies = json.loads(file.read())

# to open csv in which we only keep the movie reviews calculated and the 
#group number from the kmeans analysis 
movie_data = pd.read_csv(os.path.join(cwd, "movie_data.csv"))# this needs to go up
movie_data = movie_data[["movie_id", "reviews", "group"]] # this needs to go up
movie_data.set_index('movie_id', inplace=True)

# this is partial path to the word cloud images 
path_to_cloud = os.path.join(cwd, "static","images")

# this is a function to clean the synopsis once we get it from imdb
def info_cleaner(movie_synopsis):
    movie_synopsis = re.sub(r'[^\w\s\'\/]', " ", movie_synopsis) # remove everything that is not an alphanumeric and space
    movie_synopsis = re.sub(r" \'", "", movie_synopsis) # this will remove quotes that are not used as apostrophes
    movie_synopsis = re.sub(r" +", " ", movie_synopsis) # remove multiple spaces 
    movie_synopsis = re.sub(r" \'", "", movie_synopsis)
    movie_synopsis = re.sub(r"^[ \t]+|[ \t]+$", "", movie_synopsis) # remove trailing and leading spaces 
    return movie_synopsis

# this function is used to get the movie id from our data base from the title 
# inputted by the user
def getting_movie_id(nam):
    value_holder = 0
    closest_movie = ""
    for names in data_base:
        score = fuzz.ratio(nam, names)
        if score > value_holder:
            value_holder = score
            closest_movie = names
    if value_holder > 20:
        return data_base[closest_movie]
    else: 
        return "ERROR"
    

# to get the synopis from the the id
def movie_selection(user_input):
    user_input = re.sub(r'[^\w\s]', " ",user_input)
    user_input = re.sub(r" +" , " ", user_input)
    user_input = TextBlob(user_input)
    closest_match = getting_movie_id(user_input)
    if closest_match == "ERROR":
        movie_info = "ERROR"
    else:
        try:
            movie_info = ia.get_movie(closest_match)
            movie_info = movie_info['synopsis']
            movie_info = str(movie_info)
            movie_info = info_cleaner(movie_info)
        except KeyError:
            movie_info = "ERROR"
    return movie_info

# dictionary used in our services to get the keys in which we use to convert synopsis to another language
# this is from textblobs website
language = dict([('ab', 'Abkhaz'),
    ('aa', 'Afar'),('af', 'Afrikaans'),('ak', 'Akan'),('sq', 'Albanian'),('am', 'Amharic'),('ar', 'Arabic'),
    ('an', 'Aragonese'),('hy', 'Armenian'),('as', 'Assamese'),('av', 'Avaric'),('ae', 'Avestan'),('ay', 'Aymara'),
    ('az', 'Azerbaijani'),('bm', 'Bambara'),('ba', 'Bashkir'),('eu', 'Basque'),('be', 'Belarusian'),
    ('bn', 'Bengali'),('bh', 'Bihari'),('bi', 'Bislama'),('bs', 'Bosnian'),('br', 'Breton'),('bg', 'Bulgarian'),
    ('my', 'Burmese'),('ca', 'Catalan; Valencian'),('ch', 'Chamorro'),('ce', 'Chechen'),('ny', 'Chichewa; Chewa; Nyanja'),
    ('zh', 'Chinese'),('cv', 'Chuvash'),('kw', 'Cornish'),('co', 'Corsican'),('cr', 'Cree'),('hr', 'Croatian'),
    ('cs', 'Czech'),('da', 'Danish'),('dv', 'Divehi; Maldivian;'),('nl', 'Dutch'),('dz', 'Dzongkha'),
    ('en', 'English'),('eo', 'Esperanto'),('et', 'Estonian'),('ee', 'Ewe'),('fo', 'Faroese'),('fj', 'Fijian'),
    ('fi', 'Finnish'),('fr', 'French'),('ff', 'Fula'),('gl', 'Galician'),('ka', 'Georgian'),('de', 'German'),
    ('el', 'Greek, Modern'),('gn', 'Guaraní'),('gu', 'Gujarati'),('ht', 'Haitian'),('ha', 'Hausa'),('he', 'Hebrew (modern)'),
    ('hz', 'Herero'),('hi', 'Hindi'),('ho', 'Hiri Motu'),('hu', 'Hungarian'),('ia', 'Interlingua'),('id', 'Indonesian'),
    ('ie', 'Interlingue'),('ga', 'Irish'),('ig', 'Igbo'),('ik', 'Inupiaq'),('io', 'Ido'),('is', 'Icelandic'),
    ('it', 'Italian'),('iu', 'Inuktitut'),('ja', 'Japanese'),('jv', 'Javanese'),('kl', 'Kalaallisut'),('kn', 'Kannada'),
    ('kr', 'Kanuri'),('ks', 'Kashmiri'),('kk', 'Kazakh'),('km', 'Khmer'),('ki', 'Kikuyu, Gikuyu'),('rw', 'Kinyarwanda'),
    ('ky', 'Kirghiz, Kyrgyz'),('kv', 'Komi'),('kg', 'Kongo'),('ko', 'Korean'),('ku', 'Kurdish'),('kj', 'Kwanyama, Kuanyama'),
    ('la', 'Latin'),('lb', 'Luxembourgish'),('lg', 'Luganda'),('li', 'Limburgish'),('ln', 'Lingala'),('lo', 'Lao'),
    ('lt', 'Lithuanian'),('lu', 'Luba-Katanga'),('lv', 'Latvian'),('gv', 'Manx'),('mk', 'Macedonian'),('mg', 'Malagasy'),
    ('ms', 'Malay'),('ml', 'Malayalam'),('mt', 'Maltese'),('mi', 'Māori'),('mr', 'Marathi (Marāṭhī)'),('mh', 'Marshallese'),
    ('mn', 'Mongolian'),('na', 'Nauru'),('nv', 'Navajo, Navaho'),('nb', 'Norwegian Bokmål'),('nd', 'North Ndebele'),
    ('ne', 'Nepali'),('ng', 'Ndonga'),('nn', 'Norwegian Nynorsk'),('no', 'Norwegian'),('ii', 'Nuosu'),('nr', 'South Ndebele'),
    ('oc', 'Occitan'),('oj', 'Ojibwe, Ojibwa'),('cu', 'Old Church Slavonic'),('om', 'Oromo'),('or', 'Oriya'),
    ('os', 'Ossetian, Ossetic'),('pa', 'Panjabi, Punjabi'),('pi', 'Pāli'),('fa', 'Persian'),('pl', 'Polish'),
    ('ps', 'Pashto, Pushto'),('pt', 'Portuguese'),('qu', 'Quechua'),('rm', 'Romansh'),('rn', 'Kirundi'),
    ('ro', 'Romanian, Moldavan'),('ru', 'Russian'),('sa', 'Sanskrit (Saṁskṛta)'),('sc', 'Sardinian'),('sd', 'Sindhi'),
    ('se', 'Northern Sami'),('sm', 'Samoan'),('sg', 'Sango'),('sr', 'Serbian'),('gd', 'Scottish Gaelic'),('sn', 'Shona'),
    ('si', 'Sinhala, Sinhalese'),('sk', 'Slovak'),('sl', 'Slovene'),('so', 'Somali'),('st', 'Southern Sotho'),('es', 'Spanish'),
    ('su', 'Sundanese'),('sw', 'Swahili'),('ss', 'Swati'),('sv', 'Swedish'),('ta', 'Tamil'),('te', 'Telugu'),('tg', 'Tajik'),
    ('th', 'Thai'),('ti', 'Tigrinya'),('bo', 'Tibetan'),('tk', 'Turkmen'),('tl', 'Tagalog'),('tn', 'Tswana'),('to', 'Tonga'),
    ('tr', 'Turkish'),('ts', 'Tsonga'),('tt', 'Tatar'),('tw', 'Twi'),('ty', 'Tahitian'),('ug', 'Uighur, Uyghur'),
    ('uk', 'Ukrainian'),('ur', 'Urdu'),('uz', 'Uzbek'),('ve', 'Venda'),('vi', 'Vietnamese'),('vo', 'Volapük'),
    ('wa', 'Walloon'),('cy', 'Welsh'),('wo', 'Wolof'),('fy', 'Western Frisian'),('xh', 'Xhosa'),('yi', 'Yiddish'),
    ('yo', 'Yoruba'),('za', 'Zhuang, Chuang'),('zu', 'Zulu')])

# These exact stop words are from the NLTK stopwords
stopwords_list = ['a','about','above','after','again','against','ain','all','am','an','and',
'any','are','aren',"aren't",'as','at','be','because','been','before','being','below',
'between','both','but','by','can','couldn',"couldn't",'d','did','didn',"didn't",
'do','does','doesn', "doesn't",'doing','don',"don't",'down','during','each',
'few','for','from','further','had','hadn',"hadn't",'has','hasn',"hasn't",'have',
'haven',"haven't",'having','he','her','here','hers','herself','him','himself',
'his','how','i','if','in','into','is','isn',"isn't",'it',"it's",'its','itself',
'just','ll','m','ma','me','mightn',"mightn't",'more','most','mustn',"mustn't",
'my','myself','needn',"needn't",'no','nor','not','now','o','of','off','on',
'once','only','or','other','our','ours','ourselves','out','over','own','re',
's','same','shan',"shan't",'she',"she's",'should',"should've",'shouldn',"shouldn't",
'so','some','such','t','than','that',"that'll",'the','their','theirs','them','themselves',
'then','there','these','they','this','those','through','to','too','under','until',
'up','ve','very','was','wasn',"wasn't",'we','were','weren',"weren't",'what','when',
'where','which','while','who','whom','why','will','with','won',"won't",'wouldn',
"wouldn't",'y','you',"you'd","you'll","you're","you've",'your','yours','yourself',
'yourselves']

# a list of happy words and it's synonyms which will be used in cosine similarity 
happy_list = ["overjoy","cheerful", "happy","content", "delighted", "delight","ecstatic", "elated","glad", "joyful","joyous","joy", 
"jubilant", "lively", "merry","overjoyed","peaceful","pleasant", "pleased","thrilled", "upbeat","blessed","blest","blissful", "blithe",
"captivated", "chipper", "chirpy","convivial", "exultant", "gay","gleeful", "gratified","intoxicated", "light", "peppy","perky", "sparkling", 
"sunny","tickled", "up", "satisfy"]
happy_list = " ".join(happy_list)

# a list of sad words and it's synonyms which will be used in cosine similarity 
sad_list = ["bitter", "dismal", "melancholy", "mournful", "somber","wistful", "low", 
"morose", "bereaved", "wistful", "sorry", "doleful", "heartsick", "hurting","gloomy", "blue","weeping"
"dejected","sad", "irritate","lousy","upset","incapable","disappointment","doubtful","alone",
"hostile","discourage","uncertain","insult","ashame","indecisive","fatigue","sore","powerless",
"perplex","useless","annoy","diminish","embarrass","inferior","upset","guilty","hesitant","vulnerable",
"hateful","dissatisfy","shy","empty","unpleasant","miserable","stupefied","forced","offensive","detestable",
"disillusion","hesitant","bitter","repugnant","unbelieving","despair","aggressive","despicable","skeptical",
"frustrated","resentful","distress","inflame","abominable","misgiving","woeful","terrible","lost","pathetic","incensed","indespair","unsure","tragic","infuriate","sulky","uneasy",
"cross","dominate","tense","boil","insensitive","fearful","tearful","dull","terrified","torment",
"sorrowful","nonchalant","deprive","neutral","anxious","pain","grief","reserve",
"anguish","weary","deject","desolate","bore","nervous","reject","desperate","preoccupied","injure",
"pessimistic","worry","offend","unhappy","disinterest","afflict","lonely","lifeless","timid","ache",
"grieve","shaky","victim","mourn","restless","heartbroken","dismay","doubt","agony","threaten","coward","humiliate","alienate","wary"]
sad_list = " ".join(sad_list)

# a list of scary words and it's synonyms which will be used in cosine similarity 
scary_list = ["alarm", "torture", "morbid", "tragic", "distrustful", "enraged", "provoke", "bad", "alarming", "chilling", "creepy", 
"eerie", "horrifying", "horrify", "intimidating", "shocking", "spooky", "shock", "bloddcurdling", "panic"
"horrendous", "gore", "unnerving" "frightening",  "daunting", "blood", "carnage", "slaughter", "evil", "paralyze", "dark"]
scary_list = " ".join(scary_list)

# a list of romance words and it's synonyms which will be used in cosine similarity 
romantic_list = ["amorous", "charming", "corny", "dreamy", "erotic", "exciting", "exotic", "fanciful", "glamorous", "passionate", "tender", 
"chivalrous", "fond", "pituresque", "loving", "idyllic", 'heart','lovely', 'family','caring','forever','trust','passion','romance','sweet',
'kiss','love','hugs','warm','fun','kisses','joy','friendship','marriage','husband','wife','forever']
romantic_list = " ".join(romantic_list)

# a list of mystery words and it's synonyms which will be used in cosine similarity 
mystery_list =["suspicious", "baffling", "cryptic", "curious", "enigmatic", "inexplicable", "mystical", "obscure", "perplexing", "puzzling", "mysterious", "mystery"
"secretive", "weird", "abstruse", "arcane", "covert", "hidden", "impenetrable", "strange", "unknown", "insoluble", "incomprehensible", "furtive", "difficult", 
"necromantic", "occult", "oracular", "recondite", 'spiritual', "subjective", "symbolic", 'uncanny', "transcendental", "unfathomable", "unknowable", "unnatural", "veiled"]
mystery_list = " ".join(mystery_list)

# a list of funny words and it's synonyms which will be used in cosine similarity 
comedy_list = ["absurd", "amusing", "droll", "entertaining", "hilarious", "ludicrous", "playful", "ridiculous", "silly", "whimsical", "antic", "slapstick", "farcical",
"jolly", "laughable", "mirthful", "priceless", "riotous", "waggish", "witty", "joke", "comedy", "comedic", "comedians"]
comedy_list = " ".join(comedy_list)

vectorization = TfidfVectorizer()

# calculating cosine similarity with a sparse matrix
def cosine_similarity(input1, input2):
    tfidf = vectorization.fit_transform([input1, input2])
    return ((tfidf * tfidf.T).A)[0,1]


@app.route('/', methods =['GET', 'POST'])
def homepage():
    return render_template('services.html')

@app.route('/service1', methods = ["GET", "POST"])
def service1():
    render_template('one.html')
    if request.method == "POST":
        return redirect(url_for('/service1_result'))
    else:
        return render_template('one.html')

# this service gets the sentiment score of the movies. 
@app.route('/service1_result', methods = ['GET', 'POST'])
def service1_result():

    user_input1 = request.form['text']

    def get_sentiment(user_movie_input):
        text = movie_selection(user_movie_input)
        if text == "ERROR":
            text_sentiment = "Cannot Compute Sentiment for this Movie. Please Enter Another Title."
        else:
            blob = TextBlob(text)
            for sentence in blob.sentences:
                text_sentiment = sentence.sentiment.polarity
            # Depending on the polarity the color of the text will change
            if float(text_sentiment) < -0.5: 
                text_sentiment = "The score is {}. Which means the polarity is:".format(text_sentiment)
                pols = "NEGATIVE"
                col1 = 122
                col2 = 0
            elif 0 > float(text_sentiment) >= -0.5:
                text_sentiment = "The score is {}. Which means the polarity is:".format(text_sentiment)
                pols = "SLIGHTLY NEGATIVE"
                col1 = 204
                col2 = 0
            elif float(text_sentiment) == 0:
                text_sentiment = "The score is {}. Which means the polarity is:".format(text_sentiment)
                pols = "NEUTRAL"
                col1 = 206
                col2 = 206
            elif 0.5 > float(text_sentiment) > 0:
                text_sentiment = "The score is {}. Which means the polarity is:".format(text_sentiment)
                pols = "SLIGHTLY POSITIVE"
                col1 = 82
                col2 = 164
            elif 0.5 > float(text_sentiment) > 0:
                text_sentiment = "The score is {}. Which means the polarity is:".format(text_sentiment)
                pols = "POSITIVE"
                col1 = 120
                col2 = 241
        
        return text_sentiment, pols, col1, col2

    movie_sentiment, pol, coll1, coll2 = get_sentiment(user_input1)

    return render_template('present1.html', output = movie_sentiment, pols = pol, col1 = coll1, col2 = coll2)

@app.route('/service2',methods = ['GET', "POST"])
def service2():
    render_template('two.html')
    if request.method == "POST":
        return redirect(url_for('/service2_result'))
    else:
        return render_template('two.html')

# this service is used to translate the synopsis in the langauage the user inputted
# of a movie of their own choosing
@app.route('/service2_result', methods = ['GET', "POST"])
def service2_result():
    user_input1 = request.form['text']
    user_input2 = request.form['text2']

    def get_key(val):
        for key, value in language.items(): 
            if val.lower() == value.lower():
                lang = key
                break
            else:
                lang = "Cannot Translate Synopsis"
        return lang
    
    def final_text(user_movie_input, chosen_language):
        chosen_language = get_key(chosen_language)
        if chosen_language == "Cannot Translate Synopsis":
            translation = chosen_language
        else:
            blob = TextBlob(movie_selection(user_movie_input))
            if blob == "ERROR":
                translation = "Cannot Translate for this Movie. Please Enter Another Title."
            else:
                translation = blob.translate(to = chosen_language)
        return(translation)

    return render_template('present.html', output = final_text(user_input1, user_input2))

@app.route('/service3', methods = ['GET', 'POST'])
def service3():
    render_template('three.html')
    if request.method == "POST":
        return redirect(url_for('/service3_result'))
    else:
        return render_template('three.html')

# this service is used to get the similarity score between two movies
@app.route('/service3_result', methods = ['GET', 'POST'])
def service3_result():
    user_input1 = request.form['text']
    user_input2 = request.form['text2']
    
    def lemmatize_sentence(input_string):
        lemma_sentence = ""
        lemmas = []
        input_string = TextBlob(input_string)
        for x in input_string.words:
            x = Word(x)
            lemmas.append(x.lemmatize())
        for lemma in lemmas:
            if lemma not in stopwords_list:
                lemma_sentence = lemma_sentence + " " + lemma
        lemma_sentence = re.sub(r" \'", "\'", lemma_sentence)
        lemma_sentence = re.sub(r"^[ \t]+|[ \t]+$", "", lemma_sentence)

        return lemma_sentence

    movie1 = lemmatize_sentence(movie_selection(user_input1))
    movie2 = lemmatize_sentence(movie_selection(user_input2))

    def scoring_movies (movie1, movie2):
        if movie1 == "ERROR" or movie2 == "ERROR":
            output = "Cannot Calculate the Similarity between these movies. Please Enter Another Title."
            wording = ""
            ending_sent= ""
        else:
            score = cosine_similarity(movie1, movie2)
            if 0 <= float(score) < 0.4:
                output = "The movies are" 
                wording = "OPPOSITES"
                ending_sent = "because the score is {}".format(score)
            elif 0.4 <= float(score) <0.7: 
                output = "The movies are"
                wording = "NOT REALLY RELATED"
                ending_sent = "because the score is {}".format(score)
            elif 0.7 <= float(score) <= 1:
                output = "The movies are"
                wording = "VERY SIMILAR"
                ending_sent = "because the score is {}".format(score)
        return output, wording, ending_sent

    output, wording, ending_sent = scoring_movies(movie1, movie2)        
        #score = str(score)

    return render_template('present6.html', output = output, exp = wording, ending_sent = ending_sent)


@app.route('/service4', methods = ['GET', 'POST'])
def service4():
    render_template('four.html')
    if request.method == "POST":
        return redirect(url_for('/service4_result'))
    else:
        return render_template('four.html')

# this service is used to get the similarity between a movie and the emotion inputted
@app.route('/service4_result', methods = ['GET', 'POST'])
def service4_result():
    user_input1 = request.form['text']
    user_input2 = request.form['text2']

        # to calculate the expression needed to be displayed for service 4
    def expression(mood_num):
        if mood_num == "ERROR":
            wording = ""
            ending_sent = ""
        else:
            if 0 <= float(mood_num) < 0.4:
                wording = "OPPOSITE"
                ending_sent = "of the mood/emotion entered."
            elif 0.4 <= float(mood_num) <0.7: 
                wording = "SOMEWHAT"
                ending_sent = "of the mood/emotion entered."
            elif 0.7 <= float(mood_num) <= 1:
                wording = "EPITOME"
                ending_sent = "of the mood/emotion entered."
        return wording, ending_sent

    def mood_similarity(user_movie_input, mood_input):
        if movie_selection(user_movie_input) == "ERROR":
            service_output = "Cannot Calculate the Mood of this Movie, please enter another title"
            mood_num = "ERROR"
        else:
            user_movie_input = movie_selection(user_movie_input)
            mood_input = str(mood_input)
            if mood_input in happy_list:
                mood_num = cosine_similarity(user_movie_input, happy_list)
                service_output = "The cosine score of this being a happy movie is {}. Which is".format(mood_num)
            elif mood_input in sad_list:
                mood_num = cosine_similarity(user_movie_input, sad_list)
                service_output = "The cosine score of this being a sad movie is {}. Which is".format(mood_num)
            elif mood_input in scary_list:
                mood_num = cosine_similarity(user_movie_input, scary_list)
                service_output = "The cosine score of this being a scary movie is {}. Which is".format(mood_num)
            elif mood_input in mystery_list:
                mood_num = cosine_similarity(user_movie_input, mystery_list)
                service_output = "The cosine score of this being a mysterious movie is {}. Which is".format(mood_num)
            elif mood_input in romantic_list:
                mood_num = cosine_similarity(user_movie_input, romantic_list)
                service_output = "The cosine score of this being a romantic movie is {}. Which is".format(mood_num)
            elif mood_input in comedy_list:
                mood_num = cosine_similarity(user_movie_input, comedy_list)
                service_output = "The cosine score of this being a comedic movie is {}. Which is".format(mood_num)
            else:
                service_output = "Please enter another mood, or a synonym variation."
                mood_num = "ERROR"

        return service_output, mood_num
    mood_score, exp_mood = mood_similarity(user_input1, user_input2)
    mood_score = str(mood_score)
    exp_mood, ending_sent = expression(exp_mood)

    return render_template('present6.html', output = mood_score, exp = exp_mood, ending_sent = ending_sent)

@app.route('/service5', methods = ['GET', 'POST'])
def service5():
    render_template('five.html')
    if request.method == "POST":
        return redirect(url_for('/service5_result'))
    else:
        return render_template('five.html')  

# to get top noun phrases 
@app.route('/service5_result', methods = ['GET', 'POST'])
def service5_result():
    user_input1 = request.form['text']

    def top_noun_phrases(user_movie_input): 
        movie_info = movie_selection(user_movie_input)
        if movie_info == "ERROR":
            count_noun = "Cannot Calculate the Top Noun Phrases of this Movie, please enter another title"
            count_noun = pd.DataFrame([x.split(';') for x in count_noun.split('\n')])
        else:
            blob = TextBlob(movie_info)
            nouns = list(blob.noun_phrases)
            frequency = defaultdict(int)

            for noun in nouns:
                if noun in frequency:
                    frequency[noun] += 1
                else:
                    frequency[noun] = 1

            top_common_nouns = sorted(frequency.items(), key=operator.itemgetter(1), reverse=True)
            top_common_nouns = top_common_nouns[:10]
            count_top_ten = pd.DataFrame(top_common_nouns)
            count_noun = count_top_ten.rename(columns={0: "Nouns", 1: "Frequency"})
            count_noun = count_noun.reset_index(drop=True)

        return count_noun

    top_noun = top_noun_phrases(user_input1)

    return render_template('present2.html', tables=[top_noun.to_html(classes='data', header="true")])


@app.route('/service6', methods = ['GET', "POST"])
def service6():
    render_template('six.html')
    if request.method == "POST":
        return redirect(url_for('/service6_result'))
    else:
        return render_template('six.html')  

# to get adjectives 
@app.route('/service6_result', methods = ['GET', "POST"])
def service6_result():

    user_input1 = request.form['text']

    count = list()
    adjectives = []
    def top_adj(user_movie_input):
        movie_info = movie_selection(user_movie_input)
        if movie_info == "ERROR":
            top_adjectives = "Cannot Calculate the Top Adjectives of this Movie, please enter another title"
            top_adjectives = pd.DataFrame([x.split(';') for x in top_adjectives.split('\n')])
        else:
            blob = TextBlob(movie_info)

            for word, pos in blob.tags:
                if pos == 'JJ':
                    adjectives.append(word)

            for i in range(0, len(adjectives)):
                count.append(adjectives.count(adjectives[i]))

            top_adjectives = pd.DataFrame()
            top_adjectives['Adjectives'] = adjectives
            top_adjectives['Count'] = count

            sort_count = top_adjectives.sort_values('Count',ascending = False)
            top_adjectives = sort_count.drop_duplicates().head(10)
            top_adjectives = top_adjectives.reset_index(drop=True)
        return top_adjectives

    top_adjies = top_adj(user_input1) 

    return render_template('present2.html', tables=[top_adjies.to_html(classes='data', header="true")])


@app.route('/service7', methods = ['GET', "POST"])
def service7():
    render_template('seven.html')
    if request.method == "POST":
        return redirect(url_for('/service7_result'))
    else:
        return render_template('seven.html') 

# to get the 20 0f the movies from the kmeans cluster group. 
# from the test only six groups were created, with hundreds of movies in each
# as a result we decided to output only 20, which will be selected randomly after
# each user input from the group in which their inputted movie belongs
@app.route('/service7_result', methods = ['GET', "POST"])
def service7_result():
    user_input1 = request.form['text']

    def get_suggestion(user_input1):
        user_movie_id = getting_movie_id(user_input1)
        group = movie_data.group[int(user_movie_id)] 
        num_match = movie_data.loc[movie_data.group == group]
        rand20 = num_match.sample(n=20)
        suggested_titles = []
        for x in rand20.index.values:
            suggested_titles.extend([key for key, value in data_base.items() if int(value) == x])
        return suggested_titles

    suggested_output = get_suggestion(user_input1)
    return render_template('present5.html', the_list = suggested_output, output = "")

@app.route('/service8', methods = ['GET', 'POST'])
def service8():
    render_template('eight.html')
    if request.method == "POST":
        return redirect(url_for('/service8_result'))
    else:
        return render_template('eight.html')  

# this service creates word clouds of the user review and the top frequent adjectives used in the user
# reviews, we believed it gave a stronger indication of what the users were talking about
@app.route('/service8_result', methods = ['GET', "POST"])
def service8_result():

    user_input1 = request.form['text']
    user_movie_id = getting_movie_id(user_input1)

    #calculate sentiment polarity
    def detect_polarity(reviews):
        return TextBlob(reviews).sentiment.polarity

    #Calculate sentiiment polarity of the movie based on reviews
    def get_movie_sentiment(movie_idx):
        reviews = str(movie_data.reviews[int(movie_idx)]) 
        mov_sentiment = detect_polarity(reviews)
        return mov_sentiment

    #Find top adjectives in the review
    def top_adjectives(movie_idx):
        count = list()
        adjectives = []
        mov_adjectives = pd.DataFrame()
        reviews = str(movie_data.reviews[int(movie_idx)])
        blob = TextBlob(reviews)
        
        for word, pos in blob.tags:
            if pos =='JJ':
                adjectives.append(word)

        for i in range(0, len(adjectives)):
            count.append(adjectives.count(adjectives[i]))

        mov_adjectives['Adjectives'] = adjectives
        mov_adjectives['Frequency'] = count
        sorted_adj = mov_adjectives.sort_values('Frequency', ascending = False)
        return sorted_adj

    #generate word cloud
    def word_cloud(text, num):        
        wc = WordCloud(max_font_size=50, max_words=100, background_color="white").generate(text)
        plt.figure()
        plt.imshow(wc, interpolation="bilinear")
        plt.axis("off")
        if num == 1:
            path_to_pic = "wordcloud.png"

        elif num == 2:
            path_to_pic = "wordcloud1.png"

        plt.savefig(os.path.join(path_to_cloud, path_to_pic))
        return path_to_pic

  
    mov_sentiment_val = get_movie_sentiment(user_movie_id)
 
    mov_adjective = top_adjectives(user_movie_id)

    #update adjective items based on the overall polarity of the movie
    mov_adjective['polarity'] = mov_adjective.Adjectives.apply(detect_polarity) #add polarity column to include polarity of all the adjectives

    #based on the overall movie sentiment polarity, select only the adjectives that have the same polarity as the movie
    
    if(mov_sentiment_val > 0):
        updated_adj = mov_adjective[mov_adjective.polarity > 0]

    elif(mov_sentiment_val < 0):
        updated_adj = mov_adjective[mov_adjective.polarity < 0]

    else: 
        updated_adj = mov_adjective[mov_adjective.polarity == 0]
        
    #Output of adjective word cloud
    output_cloud = word_cloud(str(updated_adj.Adjectives), 1)
    output_cloud2 = word_cloud(str(movie_data.reviews[int(user_movie_id)]),2 )

    return render_template('present4.html', output = output_cloud , output2 = output_cloud2)


@app.route('/service9', methods = ['GET', 'POST'])
def service9():
    render_template('nine.html')
    if request.method == "POST":
        return redirect(url_for('/service9_result'))
    else:
        return render_template('nine.html')  

# this service gets a list of the movies, restricted to our database, that the user inputted 
# actor was in. The Wikipedia api is also used to get the image of the actor if they have their 
# own page, the pictures represented are based on the first link from the list that end in
# jpg. As a result, some pictures contain additional people
@app.route('/service9_result', methods = ['GET', "POST"])
def service9_result():
    user_input1 = request.form['text']

    def actor_pic(nam):
        try:
            wiki_page = wikipedia.page(nam)
            display_image = ""
            if fuzz.ratio(nam.lower(), wiki_page.title.lower()) >= 80:
                images = wiki_page.images
                for image in images:
                    if image[-3:] == "jpg":
                        display_image = image
                        break
            else:
                display_image = "/static/unavailable.png"
        except wikipedia.exceptions.DisambiguationError: # for cases where the name has mnay ouputs 
            display_image = "/static/unavailable.png"
        except wikipedia.exceptions.PageError: # if the image can't be found
            display_image = "/static/unavailable.png"

        return display_image


    def actin_movies(nam):
        value_holder = 0
        actor_name = ""

        for acts in actor_ids:
            score = fuzz.ratio(nam, acts)
            if score > value_holder:
                value_holder = score
                actor_name = acts
                # threshold for fuzz score it is higher because there is a greater
                # chance someone will type in actor name far more correctly as opposed to the 
                # movie name 
                if value_holder > 75: 
                    act_id = actor_ids[actor_name]
                    movies_in = actors_in_movies[act_id]

                    movies_in_title = []
                    for inmovie in movies_in:
                        movies_in_title.extend([key for key, value in data_base.items() if value == inmovie])
                    extra = ""
                else: 
                    extra = "Cannot Find Actor in Our Database of Movies"
                    movies_in_title = []
        return movies_in_title, extra

    pic = actor_pic(user_input1)
    movie_output, extra = actin_movies(user_input1)

    return render_template('present3.html', the_list = movie_output, output = pic, extra = extra)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
