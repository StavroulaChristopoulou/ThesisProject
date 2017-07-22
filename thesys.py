from __future__ import division, unicode_literals
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import json
from itertools import islice
from pydash import py_
import re
import operator
import unicodedata
import sys
import pprint
import os.path
import nltk
import ast
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import numpy as np
import random
import math
from textblob import TextBlob as tb
from collections import Counter


# For word count
from string import punctuation
from nltk.tokenize import word_tokenize, wordpunct_tokenize, sent_tokenize
from nltk.corpus import stopwords

# Set the character encoding
# latin-1 seems to be the only working properly since posts are going back all the way in 2001
#
reload(sys)
sys.setdefaultencoding('latin-1')


# Import files
entities = '/var/scratch/schristo/data/201607_vox-pol_jonathan/stormfront_replies_entities.jsons'
# entities = 'stormfront_replies_entitie.jsons'
results = '/var/scratch/schristo/results/'
userPosts = 'results/AllUsers.txt'
userContents = 'results/userContentData.json'
timelineData = 'results/timelineData.json'
timelineContents = 'results/timelineContents.json'
categoryContents = results+ 'categoryContents.json'
categoryTfIdf = 'results/categoryTfIdf.json'
sentiRange = 'results/SentimentsFromRange.json'
sentiUsers = 'results/SentimentsFromAllUsers.json'
# Import word counts
wcLadies = 'results/For_Stormfront_Ladies_Only-WordCount.json'
allCategoriesSentiments = 'results/SentimentsFor-39-MostActiveCategories.json'

wcCat = ['500-MostCommonWords.json', 'Announcements-WordCount.json', 'Classified_Ads-WordCount.json', 'Dating_Advice-WordCount.json', 'eActivism_and_Stormfront_Webmasters-WordCount.json', 'Fourth_Annual_Stormfront_Smoky_Mountain__Summit-WordCount.json', 'General_Questions_and_Comments-WordCount.json', 'Guidelines_for_Posting-WordCount.json', 'Ideology_and_Philosophy-WordCount.json', 'Introduction_and_FAQ-WordCount.json', 'Legal_Issues-WordCount.json', 'Multimedia-WordCount.json', 'New_Members_Introduce_Yourselves-WordCount.json', 'Newslinks_&_Articles-WordCount.json', 'The_Eternal_Flame-WordCount.json', 'The_Truth_About_Martin_Luther_King-WordCount.json']
wcLadiesCat = ['For_Stormfront_Ladies_Only-WordCount.json']

dating_advice_wordcount = 'results/dating_advice_wordcount.json'
for_stormfront_ladies_only_wordcount = 'results/for_stormfront_ladies_only_wordcount.json'

tfidfDatingAdvice = 'results/tfidfDatingAdvice.json'



# Constants
punchMarks = [".", ",", "''", "``", "...", ":", "(", ")", "{", "}", "[", "]", "?", "'s", "'m", "'ve", "n't"]
stopWords = set(stopwords.words('english'))
stop_words = stopwords.words('english') + list(punctuation)


stop = set(STOPWORDS)
stop.add("int")
stop.add("ext")

# population = ['Politics & Continuing Crises', 'Lounge', 'Strategy and Tactics' ]
# politicalRegimes = ['Stormfront Canada','Stormfront Britain', 'Stormfront South Africa','Stormfront Italia', 'Stormfront Russia' ]

# categoriesToTranslate = ['Stormfront en Francais', 'Stormfront en Espanol y Portugues', 'Stormfront Russia', 'Stormfront Baltic / Scandinavia', 'Stormfront Europe', 'Stormfront Italia', 'Stormfront Srbija', 'Stormfront Canada', 'Stormfront Croatia', 'Stormfront Hungary', 'Stormfront South Africa', 'Stormfront Nederland & Vlaanderen', ]
#[('Opposing Views Forum', 813550), ('Politics & Continuing Crises', 166120), ('Lounge', 128560), ('Stormfront en Francais', 115393), ('Talk', 82808), ('Stormfront en Espanol y Portugues', 69502), ('Stormfront Russia', 62106), ('Questions about this Board', 59803), ('Stormfront Ireland', 51372), ('For Stormfront Ladies Only', 50098), ('Events', 45920), ('Local and Regional', 45715), ('Strategy and Tactics', 43944), ('Stormfront Baltic / Scandinavia', 41367), ('Ideology and Philosophy', 37159), ('Suggestions for this Board', 28289), ('Stormfront Europe', 28191), ('Stormfront Britain', 21551), ('Classified Ads', 19392), ('Newslinks & Articles', 18752), ('New Members Introduce Yourselves', 14722), ('eActivism and Stormfront Webmasters', 14661), ('Multimedia', 14598), ('Legal Issues', 12838), ('Stormfront Italia', 11991), ('Stormfront Srbija', 8208), ('Stormfront Canada', 4658), ('General Questions and Comments', 3940), ('The Truth About Martin Luther King', 3930), ('Stormfront Croatia', 3625), ('Stormfront Hungary', 3416), ('Stormfront South Africa', 3106), ('The Eternal Flame', 2604), ('Dating Advice', 1097), ('Announcements', 245), ('Introduction and FAQ', 236), ('Stormfront Nederland & Vlaanderen', 126), ('Fourth Annual Stormfront Smoky Mountain  Summit', 64), ('Stormfront Downunder', 48)]
# cwc = [('General Questions and Comments', 37159), ('Legal Issues', 37159), ('Multimedia', 37159), ('eActivism and Stormfront Webmasters', 37159), ('Classified Ads', 37159) ] 

# wcc = [('For Stormfront Ladies Only', 353), ('Guidelines for Posting', 123), ('General Questions and Comments', 123), ('Fourth Annual Stormfront Smoky Mountain  Summit', 123), ('eActivism and Stormfront Webmasters', 123)]


# Functions START -----
# 
# 

def tokenize(text):
    print 'Tokenizing...'
    words = word_tokenize(text)
    words = [w.lower() for w in words]
    return [w for w in words if w not in stop_words and not w.isdigit() and not w in punchMarks]



# TF-IDF
# 
def tf(word, blob):
    print 'tf...'
    return blob.words.count(word) / len(blob.words)

def n_containing(word, bloblist):
    print 'n_containing...'
    return sum(1 for blob in bloblist if word in blob.words)

def idf(word, bloblist):
    print 'idf...'
    return math.log(len(bloblist) / (1 + n_containing(word, bloblist))) 

def tfidf(word, blob, bloblist):
    print 'tfidf...'
    return tf(word, blob) * idf(word, bloblist)

def doTFIDF():
    print 'Starting doTFIDF'
    dict = {}
    txt = ''
    with open(timelineContents) as f:
        for line in f:
            data = json.loads(line)
            for year, values in data.iteritems():
                for month, contents in data[year].iteritems():
                    txt = ''
                    title = "Top words in " + year + "-" + month
                    writeToFile( 'TfIdf.txt', title)
                    print("Top words in " + year+ "-" + month)
                    for content in contents:
                        txt += content + ' '
                    txt = tokenize(txt)
                    txt = ' '.join(txt)
                    print txt
                    blob = tb(txt)
                    bloblist = [blob]
                    scores = {word: tfidf(word, blob, bloblist) for word in blob.words}
                    sorted_words = sorted(scores.items(), key=lambda x: x[1], reverse=True)
                    for word, score in sorted_words[:50]:
                        word = "\tWord: {}, TF-IDF: {}".format(word, round(score, 5))
                        writeToFile( 'TfIdf.txt', word)
                        print("\tWord: {}, TF-IDF: {}".format(word, round(score, 5)))

    print 'Finished...'

def doTFIDFbyCategory():
    print 'Starting doTFIDFbyCategory'
    cats = ['For Stormfront Ladies Only', 'Dating Advice']
    dict = {}
    allCats = {}
    bloblist = []
    with open(categoryContents) as f:
        for line in f:
            data = json.loads(line)
            for category, contents in data.iteritems():
                if not category in allCats:
                    print 'Adding "' +category+'" in the dictionary joining its content'
                    catContent = ' '.join(contents)
                    allCats[category] = catContent
                    print 'Start bloblist addition'
                    bloblist.append( tb(catContent) )
                    print 'Finished "' + category + '" : Categories finished so far: ' + repr(len(bloblist))

    for cat, conts in allCats.iteritems():
        print 'Getting allCats...'
        if cat in cats:
            blob = tb(conts)
            print 'Finished blob from "' + cat + '"'
            print 'Starting tfidf scoring'
            scores = {word: tfidf(word, blob, bloblist) for word in blob.words}
            print 'Finished tfidf scoring'
            sorted_words = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            if not cat in dict:
                dict[cat] = {}
            for word, score in sorted_words[:500]:
                dict[category][word] = score

    print 'Finished All Tfidf'
    print 'Start writing file...'

    with open(results +'categoryTfIdf.json', 'w') as outfile:
        json.dump(dict, outfile)


    print 'Finished...'



def countAllWords():
    print 'Starting countAllWords'
    cats = ['For Stormfront Ladies Only', 'Dating Advice']
    emptySpace = re.compile('\ ')
    with open(categoryContents) as f:
        for line in f:
            data = json.loads(line)
            for category, contents in data.iteritems():
                dict = {}
                if category in cats:
                    for cont in contents:
                        tokensPerPost = tokenize(cont)
                        for tpp in tokensPerPost:
                            if not tpp in dict:
                                dict[tpp] = 1
                            else:
                                dict[tpp] +=1

                    # allWords = sorted(dict.items(), key=operator.itemgetter(1), reverse=True)

                    keyCat = emptySpace.sub('_', category ) + '_wordcount'
                    keyCat = keyCat.lower()

                    with open('results/'+keyCat+'.json', 'w') as outfile:
                        json.dump(dict, outfile)





# Word Count from a given dictionary without the stop-words
# 
def wordCount( posts, mostCommon = False, filename = False ):
    print 'Starting: wordCount'

    postsDict = {}  
    words = []

    for key, posts in posts.iteritems():
        for post in posts:
            tokens = word_tokenize(post)
            for token in tokens:
                words.append(token.lower())

    uniqueWords = set(words);

    for word in uniqueWords:
        if not word in stopWords:
            if not word in punchMarks:
                postsDict[word] = words.count(word)

    allWords = sorted(postsDict.items(), key=operator.itemgetter(1), reverse=True)

    if mostCommon:
            print allWords[:mostCommon]
            if filename:
                writeToFile( filename, repr(allWords[:mostCommon]))
            else:
                writeToFile( repr(mostCommon) + '-MostCommonWords.txt', repr(allWords[:mostCommon]))

    else:
        print allWords
        if filename:
            writeToFile( filename, allWords)
        else:
            writeToFile( 'AllWords.txt', allWords)


    print 'Finished...'
    return postsDict

# Clean up how it looks premium stage
# 
def basicCleanUp( cont ):
    # Clean Up regex
    nrt = re.compile(r'[\n\r\t\_\-\-\~\*\!\@\$\%\^\<\>]')
    quoteA = re.compile('\[QUOTE=.*]')
    quoteB = re.compile('\Quote:           Originally Posted by .*   ')
    emptySpaces = re.compile('\  ')
    threeDots = re.compile('\...')
    twoDots = re.compile('\..')

    # Replace with...
    cleanedText = nrt.sub(' ', cont )
    cleanedText = quoteA.sub('', cleanedText )
    cleanedText = quoteB.sub('', cleanedText )
    cleanedText = emptySpaces.sub(' ', cleanedText )
    # cleanedText = threeDots.sub('.', cleanedText )
    # cleanedText = twoDots.sub(' ', cleanedText )
    
    # Strip and convert unicode
    cleanedText = cleanedText.strip()
    cleanedText = unicodedata.normalize('NFKD', unicode(cleanedText)).encode('ascii', 'ignore')

    return cleanedText

# Get a list of the keys in a dictionary
# 
def getKeys(dict):
    keys = []
    if dict:
        for key, value in dict.iteritems():
            key = unicodedata.normalize('NFKD', unicode(key)).encode('ascii', 'ignore')
            keys.append( key )

    # print keys
    return keys

# Write the given text line to the given file
# 
def writeToFile( filename, line ):

    filename = 'results/' + filename

    if os.path.isfile(filename):
        f = open( filename, 'a' )
    else:
        f = open( filename, 'w' )
    line = line + '\n'
    f.write(line)
    f.close()

# Translate content
# 
def translateText( text ):
    sent = sent_tokenize(text)
    str = ''
    for s in sent:
        str += translate( s, 'en', 'auto' ) + ' '
    return str



# Get a list of all category names from the entity replies file
# 
def getAllCategories():
    print 'Starting: getAllCategories'
    categories = []
    with open(entities) as f:
        for line in f:
            entity = json.loads(line)
            if not entity['stormfront_category'] in categories:
                categories.append( entity['stormfront_category'] )
        
    print 'Finished...'
    return categories

# Get a list of all entities from the entity replies file
# 
def getAllEntities():
    print 'Starting: getAllEntities'
    entList = []
    with open(entities) as f:
        for line in f:
            entity = json.loads(line)
            if entity['stormfront_entities']:
                for item in entity['stormfront_entities']:
                    item = unicodedata.normalize('NFKD', unicode(item)).encode('ascii', 'ignore')
                    if not item in entList:
                        entList.append( item )
        
    print 'Finished...'
    return entList

# Get a list of all topics from the entity replies file
# 
def getAllTopics():
    print 'Starting: getAllTopics'
    topics = []
    with open(entities) as f:
        for line in f:
            entity = json.loads(line)
            if not entity['stormfront_topic'] in topics:
                topics.append( entity['stormfront_topic'] )
        
    print 'Finished...'
    return topics

# Get a list of all topics from the entity replies file
# 
def getAllUsers():
    print 'Starting: getAllUsers'
    users = []
    with open(entities) as f:
        for line in f:
            entity = json.loads(line)
            if not entity['stormfront_user'] in users:
                users.append( entity['stormfront_user'] )
        
    print 'Finished...'
    return users




# Get the 4 main lists
#
allUsers = []
allTopics = []
allCategories = []
allEntities = []

def getAllData():
    print 'Starting: getAllData'
    with open(entities) as f:
        for line in f:
            entity = json.loads(line)
            if entity['stormfront_user'] and entity['stormfront_user'] not in allUsers and entity['stormfront_user'] != '[]':
                allUsers.append( entity['stormfront_user'] )
            if entity['stormfront_topic'] and entity['stormfront_topic'] not in allTopics:
                allTopics.append( entity['stormfront_topic'] )
            if entity['stormfront_category'] and entity['stormfront_category'] not in allCategories:
                allCategories.append( entity['stormfront_category'] )
            if entity['stormfront_entities']:
                for item in entity['stormfront_entities']:
                    if not item in allEntities:
                        allEntities.append( unicodedata.normalize('NFKD', unicode(item)).encode('ascii', 'ignore') )

    print 'Finished...'

# Run getAllData immediately
#
# getAllData()





# Get a dictionary with the most active users (username and total posts)
# 
def mostActiveUsers( top = False, date = False ):
    print 'Starting: mostActiveUsers'
    dict = {}

    for user in allUsers:
        user = unicodedata.normalize('NFKD', unicode(user)).encode('ascii', 'ignore')
        dict[user] = 0

    with open(entities) as f:
        for line in f:
            entity = json.loads(line)
            if date:
                entDate = entity['stormfront_publication_date'].split('-')[0] + '-' + entity['stormfront_publication_date'].split('-')[1]
                if date == entDate:
                    user = unicodedata.normalize('NFKD', unicode(entity['stormfront_user'])).encode('ascii', 'ignore')
                    dict[user] += 1
            else:
                if entity['stormfront_user'] != '[]':
                    user = unicodedata.normalize('NFKD', unicode(entity['stormfront_user'])).encode('ascii', 'ignore')
                    dict[user] += 1

    mostFirst = sorted(dict.items(), key=operator.itemgetter(1), reverse=True)

    print ' '

    if top:
        print 'The most '+ repr(top) +' active users are: '
        print mostFirst[:top]
        writeToFile('MostActiveUsers.txt', 'The most '+ repr(top) +' active users are: \n')
        writeToFile('MostActiveUsers.txt', repr(mostFirst[:top]) + '\n' )
        writeToFile('MostActiveUsers.txt', '------ \n' )
        print ' '
        print 'Finished...'
        return mostFirst[:top]
    else:
        print 'All Users are: '
        print mostFirst
        writeToFile('AllUsers.txt', repr(mostFirst) + '\n' )
        print ' '
        print 'Finished...'
        return mostFirst

# Get a dictionary with the most active categories (category and total posts)
# 
def mostActiveCategories( top, date = False ):
    print 'Starting: mostActiveCategories'
    dict = {}

    for category in allCategories:
        category = unicodedata.normalize('NFKD', unicode(category)).encode('ascii', 'ignore')
        dict[category] = 0

    # Open file and count totals per category
    with open(entities) as f:
        for line in f:
            entity = json.loads(line)
            if date:
                entDate = entity['stormfront_publication_date'].split('-')
                entDate = entDate[0] + '-' + entDate[1]
                if date == entDate:
                    category = unicodedata.normalize('NFKD', unicode(entity['stormfront_category'])).encode('ascii', 'ignore')
                dict[category] += 1
            else:
                category = unicodedata.normalize('NFKD', unicode(entity['stormfront_category'])).encode('ascii', 'ignore')
                dict[category] += 1

    mostFirst = sorted(dict.items(), key=operator.itemgetter(1), reverse=True)

    print ' '
    print 'The most '+ repr(top) +' active categories are: '
    print mostFirst[:top]
    print ' '

    writeToFile('MostActiveCategories.txt', 'The most '+ repr(top) +' active categories are: \n')
    writeToFile('MostActiveCategories.txt', repr(mostFirst[:top]) + '\n' )
    writeToFile('MostActiveCategories.txt', '------ \n' )

    print 'Finished...'
    return mostFirst[:top]

# Get a dictionary with the most active topics (topic and total posts)
# 
def mostActiveTopics( top, date = False ):
    print 'Starting: mostActiveTopics'
    dict = {}

    for topic in allTopics:
        topic = unicodedata.normalize('NFKD', unicode(topic)).encode('ascii', 'ignore')
        dict[topic] = 0

    # Open file and count totals per topic
    with open(entities) as f:
        for line in f:
            entity = json.loads(line)
            if date:
                entDate = entity['stormfront_publication_date'].split('-')
                entDate = entDate[0] + '-' + entDate[1]
                if date == entDate:
                    topic = unicodedata.normalize('NFKD', unicode(entity['stormfront_topic'])).encode('ascii', 'ignore')
                    dict[topic] +=1
            else:
                topic = unicodedata.normalize('NFKD', unicode(entity['stormfront_topic'])).encode('ascii', 'ignore')
                dict[topic] +=1

    mostFirst = sorted(dict.items(), key=operator.itemgetter(1), reverse=True)

    print ' '
    print 'The most '+ repr(top) +' active topics are: '
    print mostFirst[:top]
    print ' '

    writeToFile('MostActiveTopics.txt', 'The most '+ repr(top) +' active topics are: \n')
    writeToFile('MostActiveTopics.txt', repr(mostFirst[:top]) + '\n' )
    writeToFile('MostActiveTopics.txt', '------ \n' )

    print 'Finished...'
    return mostFirst[:top]


def mostActiveEntities( top, date = False ):
    print 'Starting: mostActiveEntities'
    dict = {}

    for stfEntity in allEntities:
        stfEntity = unicodedata.normalize('NFKD', unicode(stfEntity)).encode('ascii', 'ignore')
        dict[stfEntity] = 0

    # Open file and count totals per topic
    with open(entities) as f:
        for line in f:
            entity = json.loads(line)
            if entity['stormfront_entities']:
                for stfEntity in entity['stormfront_entities']:
                    if date:
                        entDate = entity['stormfront_publication_date'].split('-')
                        entDate = entDate[0] + '-' + entDate[1]
                        if date == entDate:
                            stfEntity = unicodedata.normalize('NFKD', unicode(stfEntity)).encode('ascii', 'ignore')
                            dict[stfEntity] +=1
                    else:
                        stfEntity = unicodedata.normalize('NFKD', unicode(stfEntity)).encode('ascii', 'ignore')
                        dict[stfEntity] +=1

    mostFirst = sorted(dict.items(), key=operator.itemgetter(1), reverse=True)

    print ' '
    print 'The most '+ repr(top) +' active entities are: '
    print mostFirst[:top]
    print ' '

    writeToFile('MostActiveEntities.txt', 'The most '+ repr(top) +' active entities are: \n')
    writeToFile('MostActiveEntities.txt', repr(mostFirst[:top]) + '\n' )
    writeToFile('MostActiveEntities.txt', '------ \n' )

    print 'Finished...'
    return mostFirst[:top]


def mostActiveData( date ):
    usersDict = {}
    topicsDict = {}
    categoriesDict = {}
    entitiesDict = {}

    for user in allUsers:
        user = unicodedata.normalize('NFKD', unicode(user)).encode('ascii', 'ignore')
        usersDict[user] = 0
    for topic in allTopics:
        topic = unicodedata.normalize('NFKD', unicode(topic)).encode('ascii', 'ignore')
        topicsDict[topic] = 0
    for category in allCategories:
        category = unicodedata.normalize('NFKD', unicode(category)).encode('ascii', 'ignore')
        categoriesDict[category] = 0
    for ent in allEntities:
        ent = unicodedata.normalize('NFKD', unicode(ent)).encode('ascii', 'ignore')
        entitiesDict[ent] = 0

    with open(entities) as f:
        for line in f:
            entity = json.loads(line)
            if date:
                entDate = entity['stormfront_publication_date'].split('-')[0] + '-' + entity['stormfront_publication_date'].split('-')[1]
                if date == entDate:
                    if entity['stormfront_user'] and entity['stormfront_user'] !='[]':
                        user = unicodedata.normalize('NFKD', unicode(entity['stormfront_user'])).encode('ascii', 'ignore')
                        usersDict[user] += 1
                    if entity['stormfront_topic']:
                        topic = unicodedata.normalize('NFKD', unicode(entity['stormfront_topic'])).encode('ascii', 'ignore')
                        topicsDict[topic] += 1
                    if entity['stormfront_category']:
                        category = unicodedata.normalize('NFKD', unicode(entity['stormfront_category'])).encode('ascii', 'ignore')
                        categoriesDict[category] += 1
                    if entity['stormfront_entities']:
                        for stfEntity in entity['stormfront_entities']:
                            stfEntity = unicodedata.normalize('NFKD', unicode(stfEntity)).encode('ascii', 'ignore')
                            entitiesDict[stfEntity] +=1
    
    mostUsers = sorted(usersDict.items(), key=operator.itemgetter(1), reverse=True)
    mostTopics = sorted(topicsDict.items(), key=operator.itemgetter(1), reverse=True)
    mostCategories = sorted(categoriesDict.items(), key=operator.itemgetter(1), reverse=True)
    mostEntities = sorted(entitiesDict.items(), key=operator.itemgetter(1), reverse=True)

    mostUsers = mostUsers[:5]
    mostTopics = mostTopics[:5]
    mostCategories = mostCategories[:5]
    mostEntities = mostEntities[:5]

    return { 'mostActiveUsers': mostUsers, 'mostDiscussedTopics': mostTopics, 'mostActiveCategories':  mostCategories, 'mostDiscussedEntities': mostEntities }




# Get a dictionary with posts per year
# 
def getContentsByYearAndMonth():
    print 'Starting: getContentsByYearAndMonth'
    dict = {}
    with open(entities) as f:
        for line in f:
            entity = json.loads(line)
            year = entity['stormfront_publication_date'].split('-')[0]
            month = entity['stormfront_publication_date'].split('-')[1]

            if not year in dict:
                dict[year] = {}
                dict[year]['yearTotal'] = 0

            if month not in dict[year]:
                dict[year][month] = {}
                dict[year][month]['monthTotal'] = 0
                dict[year][month]['contents'] = []

            dict[year]['yearTotal'] += 1
            dict[year][month]['monthTotal'] += 1
            content = basicCleanUp( entity['stormfront_content'] )
            # if entity['stormfront_category'] in categoriesToTranslate:
                # content = translateText(content)
            dict[year][month]['contents'].append( content )

    print 'Finished...'
    return dict

# Get a dictionary with posts per year from a specific category
# 
def getContentsByYearAndMonthFromCategory( category ):
    print 'Starting: getContentsByYearAndMonthFromCategory' + ' - ' + category
    dict = {}
    with open(entities) as f:
        for line in f:
            entity = json.loads(line)
            if category in entity['stormfront_category']:
                year = entity['stormfront_publication_date'].split('-')[0]
                month = entity['stormfront_publication_date'].split('-')[1]

                if not year in dict:
                    dict[year] = {}
                    dict[year]['yearTotal'] = 0

                if month not in dict[year]:
                    dict[year][month] = {}
                    dict[year][month]['monthTotal'] = 0
                    dict[year][month]['contents'] = []

                dict[year]['yearTotal'] += 1
                dict[year][month]['monthTotal'] += 1
                content = basicCleanUp( entity['stormfront_content'] )
                dict[year][month]['contents'].append( content )

    print 'Finished...'
    return dict
   
# Get contents from a given list of categories
# 
def getContentsByCategory( categories, save = False, filename = False ):
    print 'Starting: getContentsByCategory'

    dict = {}
    keysCategories = []
    emptySpace = re.compile('\ ')
    
    for key in categories:
        keysCategories.append(key)

    with open(entities) as f:
        for line in f:
            entity = json.loads(line)
            content = basicCleanUp(entity['stormfront_content'])
            if entity['stormfront_category'] in keysCategories:
                if not entity['stormfront_category'] in dict:
                    dict[entity['stormfront_category']] = []
                if content:
                    dict[entity['stormfront_category']].append( content )


    if save and filename: 
        filename = 'results/' +filename +'.json'
        with open(filename, 'w') as outfile:
            json.dump(dict, outfile)

    print 'Finished...'

    # for keyCat in dict:
    #     cont = dict[keyCat]
    #     print keyCat
    #     wc = wordCount( {keyCat: cont}, mostCommon = 500, filename = emptySpace.sub('_', keyCat ) + '-WordCount.txt' )

    return dict

# Get contents per Quarter or Season
# 
def getContentsBySeason( sample = False ):
    print 'Starting: getContentsBySeason'
    winter = []
    spring = []
    summer = []
    autumn = []
    count = 0

    with open(entities) as f:
        for line in f:
            if count < 100:
                entity = json.loads(line)
                content = basicCleanUp(entity['stormfront_content'])
                # if entity['stormfront_category'] in categoriesToTranslate:
                    # content = translateText(content)

                month = entity['stormfront_publication_date'].split('-')[1]
                month = int(month)

                if sample:
                    count += 1

                if (month < 3 or month == 12):
                    winter.append(content)
                elif (month > 2 and month < 6):
                    spring.append(content)
                elif (month > 5 and month < 9):
                    summer.append(content)
                else:
                    autumn.append(content)

    dict = {'winter': winter, 'spring': spring, 'summer': summer, 'autumn': autumn}
          
    print 'Finished...'
    return dict

# Get contents from a given list of topics
# 
def getContentsByTopic( topics ):
    print 'Starting: getContentsByTopic'
    dict = {}
    keysTopics = []
    
    for key, value in topics:
        keysTopics.append(key)

    with open(entities) as f:
        for line in f:
            entity = json.loads(line)
            content = basicCleanUp(entity['stormfront_content'])
            # if entity['stormfront_category'] in categoriesToTranslate:
                # content = translateText(content)

            if entity['stormfront_topic'] in keysTopics:
                if not entity['stormfront_topic'] in dict:
                    dict[entity['stormfront_topic']] = []
                if content:
                    dict[entity['stormfront_topic']].append( content )

    print 'Finished...'
    return dict

# Get contents from a given list of users
# 
def getContentsByUser( users ):
    print 'Starting: getContentsByUser'
    dict = {}
    keysUsers = []
    
    for key, value in users:
        keysUsers.append(key)

    with open(entities) as f:
        for line in f:
            entity = json.loads(line)
            content = basicCleanUp(entity['stormfront_content'])
            if entity['stormfront_user'] in keysUsers:
                if not entity['stormfront_user'] in dict:
                    dict[entity['stormfront_user']] = []
                if content:
                    dict[entity['stormfront_user']].append( content )

    print 'Finished...'
    return dict


def getDataByUser():
    print 'Starting: getDataByUser'
    dict = {}
    
    with open(entities) as f:
        for line in f:
            entity = json.loads(line)
            content = basicCleanUp(entity['stormfront_content'])
            if not entity['stormfront_user'] in dict:
                dict[entity['stormfront_user']] = []
            if content:
                dict[entity['stormfront_user']].append( content )

    with open('results/userContentData.json', 'w') as outfile:
        json.dump(dict, outfile)


    print 'Finished...'
    return dict




# Analyze a dictionary
# if you are providing a list instead of a dictionary use isContent = True and give Dataset name
# 
def getSentimentsFromDict( dict, isContent = False, filename = False, datasetName = ''):
    analyzer = SentimentIntensityAnalyzer()
    
    allPositives = []
    allNegatives = []
    allNeutral = []
    allCompound = []
    # per = 10

    if dict:

        positives = []
        negatives = []
        neutral = []
        compound = []
        results = ''
        if isContent:

            for post in dict:
                if post:
                    vs = analyzer.polarity_scores(post)
                    positives.append(vs['pos'])
                    negatives.append(vs['neg'])
                    neutral.append(vs['neu'])
                    compound.append(vs['compound'])

            results += 'The positive average in ' + datasetName +' is: ' + repr( py_.mean(positives) ) + '\n' + 'The negative average in ' + datasetName +' is: ' + repr( py_.mean(negatives) ) + '\n' + 'The neutral average in ' + datasetName +' is: ' + repr( py_.mean(neutral) ) + '\n' + 'The compound average in ' + datasetName +' is: ' + repr( py_.mean(compound) ) + '\n' + 'The total posts are: ' + repr( len(dict) ) + '\n' + '------------' + '\n'

            print results

        else:
            for category, posts in dict.iteritems():
                if posts:
                    for sentence in posts:
                        if sentence:
                            vs = analyzer.polarity_scores(sentence)
                            positives.append(vs['pos'])
                            negatives.append(vs['neg'])
                            neutral.append(vs['neu'])
                            compound.append(vs['compound'])
        
                    results += 'The positive average in ' + category +' is: ' + repr( py_.mean(positives) ) + '\n' + 'The negative average in ' + category +' is: ' + repr( py_.mean(negatives) ) + '\n' + 'The neutral average in ' + category +' is: ' + repr( py_.mean(neutral) ) + '\n' + 'The compound average in ' + category +' is: ' + repr( py_.mean(compound) ) + '\n' + 'The total posts are: ' + repr( len(dict) ) + '\n' + '------------' + '\n'
                    
                    
                    allPositives.append( py_.mean(positives) )
                    allNegatives.append( py_.mean(negatives) )
                    allNeutral.append( py_.mean(neutral) )
                    allCompound.append( py_.mean(compound) )

            aggregated = 'The aggregated positive average is: ' + repr( py_.mean(allPositives) ) + '\n' + 'The aggregated negative average is: ' + repr( py_.mean(allNegatives) ) + '\n' + 'The aggregated neutral average is: ' + repr( py_.mean(allNeutral) ) + '\n' + 'The aggregated compound average is: ' + repr( py_.mean(allCompound) ) + '\n' + 'The total posts are: ' + repr( len(dict) ) + '\n' + '------------' + '\n'

        print results
        
        if filename:
            writeToFile( filename, results)

        if not isContent:
            print aggregated
            if filename:
                writeToFile( filename, aggregated )
        
        if isContent:
            sent = { 'positives': py_.mean(positives), 'negatives': py_.mean(negatives), 'neutral': py_.mean(neutral), 'compound': py_.mean(compound) }
            return sent

def getSentimentsFromDictToJson( dict, filename = False ):
    print 'Starting: getSentimentsFromDictToJson'
    analyzer = SentimentIntensityAnalyzer()
    contents = {}

    if dict:
        for key, posts in dict.iteritems():
            
            positives = []
            negatives = []
            neutral = []
            compound = []
            results = ''

            if key not in contents:
                contents[key] = {}
            
            if posts:
                for sentence in posts:
                    if sentence:
                        vs = analyzer.polarity_scores(sentence)
                        positives.append(vs['pos'])
                        negatives.append(vs['neg'])
                        neutral.append(vs['neu'])
                        compound.append(vs['compound'])
    
                contents[key] = { 'positives': py_.mean(positives), 'negatives': py_.mean(negatives), 'neutral': py_.mean(neutral), 'compound': py_.mean(compound) }
        
        if filename:
            filename = 'results/' + filename
            with open(filename, 'w') as outfile:
                json.dump(contents, outfile)

        return contents


def doYearMonthSentiments():
    contents = getContentsByYearAndMonth()
    contents = sorted(contents.items(), key=operator.itemgetter(0), reverse=False)
    for year, months in contents:
        months = sorted(months.items(), key=operator.itemgetter(0), reverse=False)
        for monthKey, monthValue in months:
            if not monthKey == 'yearTotal':
                getSentimentsFromDict( monthValue['contents'], isContent = True, filename = 'SentimentsPerYearAndMonth.txt', datasetName = monthKey + '/' + year )


def doYearMonthSentimentsForCategory( category ):
    emptySpace = re.compile('\ ')
    contents = getContentsByYearAndMonthFromCategory( category )
    contents = sorted(contents.items(), key=operator.itemgetter(0), reverse=False)
    for year, months in contents:
        months = sorted(months.items(), key=operator.itemgetter(0), reverse=False)
        for monthKey, monthValue in months:
            if not monthKey == 'yearTotal':
                getSentimentsFromDict( monthValue['contents'], isContent = True, filename = emptySpace.sub('_', category ) + '-' + 'SentimentsPerYearAndMonth.txt', datasetName = monthKey + '/' + year )


def getTimelineData():
    print 'Starting: getTimelineData'

    dict = {}

    with open(entities) as f:
        
        for line in f:
            entity = json.loads(line)
            year = entity['stormfront_publication_date'].split('-')[0]
            month = entity['stormfront_publication_date'].split('-')[1]
            user = entity['stormfront_user']
            topic = entity['stormfront_topic']
            category = entity['stormfront_category']
            content = basicCleanUp( entity['stormfront_content'] )

            if not year in dict:
                dict[year] = {}
                dict[year]['yearlyTotalPosts'] = 0
                dict[year]['yearlyContents'] = []
                dict[year]['yearlySentiments'] = {}

            if month not in dict[year]:
                dict[year][month] = {}
                dict[year][month]['monthlyTotalPosts'] = 0
                dict[year][month]['monthlyContents'] = []
                dict[year][month]['monthlySentiments'] = {}

            dict[year]['yearlyTotalPosts'] += 1
            dict[year][month]['monthlyTotalPosts'] += 1

            if content:
                dict[year]['yearlyContents'].append( content )
                dict[year][month]['monthlyContents'].append( content )


        for year, data in dict.iteritems():
            dict[year]['yearlySentiments'] = getSentimentsFromDict( dict[year]['yearlyContents'], isContent = True )
            dict[year].pop('yearlyContents')
            for month, monData in data.iteritems():
                if month is not 'yearlyTotalPosts' and month is not 'yearlySentiments' and month is not 'yearlyContents':
                    date = year + '-' + month
                    monthlyData = mostActiveData( date )
                    for key, item in monthlyData.iteritems():
                        dict[year][month][key] = item
                    dict[year][month]['monthlySentiments'] = getSentimentsFromDict( dict[year][month]['monthlyContents'], isContent = True )
                    dict[year][month].pop('monthlyContents')

    print 'Finished...'


    with open('results/timelineData.json', 'w') as outfile:
        json.dump(dict, outfile)

    print dict
    # return dict


def getTimelineContents():
    print 'Starting: getTimelineContents'

    dict = {}

    with open(entities) as f:
        
        for line in f:
            entity = json.loads(line)
            year = entity['stormfront_publication_date'].split('-')[0]
            month = entity['stormfront_publication_date'].split('-')[1]
            user = entity['stormfront_user']
            topic = entity['stormfront_topic']
            category = entity['stormfront_category']
            content = basicCleanUp( entity['stormfront_content'] )

            if not year in dict:
                dict[year] = {}

            if month not in dict[year]:
                dict[year][month] = []

            if content:
                dict[year][month].append( content )

    print 'Finished...'


    with open('results/timelineContents.json', 'w') as outfile:
        json.dump(dict, outfile)

    print dict
    # return dict


def getCategoryContents():
    print 'Starting: getCategoryContents'

    dict = {}

    with open(entities) as f:
        
        for line in f:
            entity = json.loads(line)
            category = entity['stormfront_category']
            content = basicCleanUp( entity['stormfront_content'] )

            if not category in dict:
                dict[category] = []

            if content:
                dict[category].append( content )

    print 'Finished...'


    with open('results/categoryContents.json', 'w') as outfile:
        json.dump(dict, outfile)

    print dict
    # return dict



def makeWordCloud( data = False, include = False, exclude = False, filename = False ):
    print 'Starting: makeWordCloud'
    stopwords = STOPWORDS
    stopwords.add(repr("n't"))
    stopwords.add(repr("'d"))
    stopwords.add(repr("'s"))
    stopwords.add(repr("'m"))
    stopwords.add(repr("'ve"))
    stopwords.add(repr("'re"))
    stopwords.add(repr("'"))
    stopwords.add(repr("&"))
    stopwords.add(repr("|"))
    stopwords.add(repr("#"))
    stopwords.add(repr(";"))
    stopwords.add(repr("+"))
    stopwords.add(repr("http"))

    txt = ''

    if data:
        for word, times in data.iteritems():
            if word not in stopWords:
                times = int(times / 50)
                for i in range(times):
                    txt += unicodedata.normalize('NFKD', word).encode('ascii','ignore') + ' '
    else:
        with open(entities) as f:
            for line in f:
                entity = json.loads(line)

                if ( include and entity['stormfront_category'] in include ):
                    txt += basicCleanUp(entity['stormfront_content'])
                    txt += ' '
                elif ( exclude and entity['stormfront_category'] not in exclude ):
                    txt += basicCleanUp(entity['stormfront_content'])
                    txt += ' '
                else:
                    txt += basicCleanUp(entity['stormfront_content'])
                    txt += ' '

    print 'Starting: WordCloud'
    wc = WordCloud(max_words=100, stopwords=stopwords ).generate(txt)
    if filename:
        wc.to_file(filename)
    else:
        if include:
            wc.to_file('LadiesCloud.jpg')
        elif exclude:
            wc.to_file('MixedCategoriesCloud.jpg')
        else:
            wc.to_file('AllCategoriesCloud.jpg')
        
    print 'Finished...'
    

def userPostsRange(lowest, low, medium, high ):
    print 'Starting: userPostsRange'
    dict = {'lowest': 0, 'low': 0, 'medium': 0, 'high': 0, 'highest': 0, 'total': 0}
    dictContents = {'lowest': [], 'low': [], 'medium': [], 'high': [], 'highest': [], 'total': 0}

    with open(userContents) as f:
        for line in f:
            loadedUsers = json.loads(line)
            for key, posts in loadedUsers.iteritems():
                postsPerUser = len(loadedUsers[key])
                if postsPerUser <= lowest:
                    dict['lowest'] += 1
                    dictContents['lowest'] = dictContents['lowest'] + posts
                elif postsPerUser > lowest and postsPerUser <= low:
                    dict['low'] += 1
                    dictContents['low'] = dictContents['low'] + posts
                elif postsPerUser > low and postsPerUser <= medium:
                    dict['medium'] += 1
                    dictContents['medium'] = dictContents['medium'] + posts
                elif postsPerUser > medium and postsPerUser <= high:
                    dict['high'] += 1
                    dictContents['high'] = dictContents['high'] + posts
                else:
                    dict['highest'] += 1
                    dictContents['highest'] = dictContents['highest'] + posts
                

    dict['total'] = dict['lowest'] + dict['low'] + dict['medium'] + dict['high'] + dict['highest']

    dictContents['total'] = dict['total']

    print 'Lowest: ' + repr(lowest) + ' - ' + 'Low: ' + repr(low) + ' - ' + 'Medium: ' + repr(medium) + ' - ' + 'High: ' + repr(high) + ' - ' + 'Highest: ' + repr(high) + '+' + ' => ' + 'Total Users: ' + repr(dict['total'])
    print dict
    print float( 100 * dict['lowest'] ) / dict['total'] 
    print float( 100 * dict['low'] ) / dict['total'] 
    print float( 100 * dict['medium'] ) / dict['total'] 
    print float( 100 * dict['high'] ) / dict['total'] 
    print float( 100 * dict['highest'] ) / dict['total'] 

    print 'Finished...'
    return dictContents



def createCoRelPlot( x, y, filename, xlabel, ylabel, step ):
    x = np.array( x )
    y = np.array( y )

    # plt.figure(figsize=(12,5))
    plt.plot( x, y, 'o' )
    plt.plot( x, np.poly1d(np.polyfit( x, y, 1 ) )( x ) )

    plt.xlabel(xlabel, fontsize=14)
    plt.ylabel(ylabel, fontsize=16)
    plt.xticks(np.arange(min(x), max(x)+1, step))


    filename = 'results/' + filename

    plt.savefig( filename )

    print np.corrcoef( x, y )

def doPlotFromTimeline():
    dict = {}
    count=5
    with open(timelineData) as f:
        for line in f:
            data = json.loads(line)
            for year, values in data.iteritems():
                for month in data[year]:
                    if month != 'yearlyTotalPosts' and month != 'yearlySentiments':
                        compound = data[year][month]['monthlySentiments']['compound']
                        mm = year+month
                        dict[count] = compound
                        count+=1

    dict = sorted(dict.items(), key=operator.itemgetter(0), reverse=False)

    dates = []
    sents = []

    for date, sent in dict:
        dates.append( int(date) )
        sents.append( float(sent) )

    print np.corrcoef( dates, sents )
    # createCoRelPlot( dates, sents, filename = 'sentiTime.jpg', xlabel = 'Time from 2001-09 to 2015-02', ylabel = 'Compound Sentiments', step = 3.0 )

def doPlotFromUsersRange():
    dict = { 'lowest':{ 'postCount': 0, 'compound': '' }, 'low':{ 'postCount': 0, 'compound': '' }, 'medium':{ 'postCount': 0, 'compound': '' }, 'high':{ 'postCount': 0, 'compound': '' }, 'highest':{ 'postCount': 0, 'compound': '' } }

    userDict = {}

    with open(userContents) as f:
        for line in f:
            loadedUsers = json.loads(line)
            for key, posts in loadedUsers.iteritems():
                if not key in userDict:
                    userDict[key] = {}
                userDict[key]['totalPosts'] = len(posts)

                postsPerUser = len(loadedUsers[key])
                if postsPerUser <= 1:
                    dict['lowest']['postCount'] += len(posts)
                elif postsPerUser > 1 and postsPerUser <= 10:
                    dict['low']['postCount'] += len(posts)
                elif postsPerUser > 10 and postsPerUser <= 200:
                    dict['medium']['postCount'] += len(posts)
                elif postsPerUser > 200 and postsPerUser <= 800:
                    dict['high']['postCount'] += len(posts)
                else:
                    dict['highest']['postCount'] += len(posts)


    # print dict

    with open(sentiUsers) as f:
        for line in f:
            data = json.loads(line)
            for user, values in data.iteritems():
                if values:
                    userDict[user]['compound'] = values['compound']

    # print userDict

    # print dict

    # dict = sorted(dict.items(), key=operator.itemgetter(0), reverse=False)

    userPostsList = []
    sentiUsersList = []

    for user, values in userDict.iteritems():
        print user
        print values
        if values['totalPosts'] != 0:
            userPostsList.append( values['totalPosts'] )
            sentiUsersList.append( values['compound'] )

    print np.corrcoef( userPostsList, sentiUsersList )

    # createCoRelPlot( userPostsList, sentiUsersList, filename = 'sentiUserPosts.jpg', xlabel = 'Range', ylabel = 'Compound Sentiments', step = 1.0 )





def getSeasonSentiments():
    dict = {}
    winterData = []
    springData = []
    summerData = []
    autumnData = []
    with open(timelineData) as f:
        for line in f:
            data = json.loads(line)
            for year, values in data.iteritems():
                if year not in dict:
                    dict[year] = {}
                for month in data[year]:
                    if month != 'yearlyTotalPosts' and month != 'yearlySentiments':
                        compound = data[year][month]['monthlySentiments']['compound']
                        if month == '12' or month == '01' or month == '02':
                            winterData.append(compound)
                        elif month == '03' or month == '04' or month == '05':
                            springData.append(compound)
                        elif month == '06' or month == '07' or month == '08':
                            summerData.append(compound)
                        else:
                            autumnData.append(compound)
                if winterData:
                    dict[year]['winter'] = py_.mean(winterData)
                if springData:
                    dict[year]['spring'] = py_.mean(springData)
                if summerData:
                    dict[year]['summer'] = py_.mean(summerData)
                if autumnData:
                    dict[year]['autumn'] = py_.mean(autumnData)
                    
                winterData = []
                springData = []
                summerData = []
                autumnData = []

    print dict


    # dates = []
    # sents = []

    # for date, sent in dict:
    #     dates.append( int(date) )
    #     sents.append( float(sent) )








def doCorrelationMonthlySentsAndPosts():
    comps = []
    tps = []
    with open(timelineData) as f:
        for line in f:
            data = json.loads(line)
            for year, values in data.iteritems():
                for month in data[year]:
                    if month != 'yearlyTotalPosts' and month != 'yearlySentiments':
                        compound = data[year][month]['monthlySentiments']['compound']
                        totalPosts = data[year][month]['monthlyTotalPosts']

                    comps.append(compound)
                    tps.append(totalPosts)

            print np.corrcoef( tps, comps )
            createCoRelPlot( tps, comps, 'CorrelationMonthlySentsToPosts.jpg', 'Total Posts per month', 'Monthly Sentiment', step = 3000.0 )


#doCorrelationMonthlySentsAndPosts()

# 
# 
# Functions END-------

# wcNext = [('Events', 1), ('Local and Regional', 1), ('Lounge', 1), ('Opposing Views Forum', 1), ('Politics & Continuing Crises')]
# wcNextContent = getContentsByCategory( wcNext )
# wordCount( wcNextContent, mostCommon = 500 )

# politicalRegimesContent = getContentsByCategory( politicalRegimes )
# getSentimentsFromDict(politicalRegimesContent, filename = 'SentimentsForPoliticalRegimes.txt')

# populationContent = getContentsByCategory( population )
# getSentimentsFromDict(populationContent, filename = 'SentimentsForPopulation.txt')

# mac = mostActiveCategories(39)
# getSentimentsFromDictToJson(getContentsByCategory(mac), filename = 'SentimentsFor-' + repr(len(mac))+'-MostActiveCategories.json')

# mau = mostActiveUsers(50)
# getSentimentsFromDict(getContentsByUser(mau), filename = 'SentimentsFor-' + repr(len(mau))+'-MostActiveUsers.txt')

# au = mostActiveUsers()
# getSentimentsFromDict(getContentsByUser(au), filename = 'SentimentsFor-AllUsers.txt')

# mat = mostActiveTopics(50)
# getSentimentsFromDict(getContentsByTopic(mat), filename = 'SentimentsFor-' + repr(len(mat))+'-MostActiveTopics.txt')

# seasons = getContentsBySeason()
# getSentimentsFromDict(seasons, filename = 'SentimentsFromAllSeasons.txt')

# doYearMonthSentiments()

# print seasons
# wordCount( seasons, mostCommon = 500 )

# dwn = getContentsByCategory( cwc )
# doYearMonthSentimentsForCategory('For Stormfront Ladies Only')
# ae = getAllEntities()
# print ae


# getContentsByCategory(wcc)


# getTimelineData()

# makeWordCloud(include = ['For Stormfront Ladies Only'])
# makeWordCloud(exclude = ['For Stormfront Ladies Only'])
# makeWordCloud(exclude = ['For Stormfront Ladies Only', 'Stormfront en Francais', 'Stormfront en Espanol y Portugues', 'Stormfront Russia', 'Stormfront Baltic / Scandinavia', 'Stormfront Europe', 'Stormfront Italia', 'Stormfront Srbija', 'Stormfront Canada', 'Stormfront Croatia', 'Stormfront Hungary', 'Stormfront South Africa', 'Stormfront Nederland & Vlaanderen'], filename= 'results/NoCountryCloud.jpg')

# getDataByUser()



# with open(userContents) as f:
#     for line in f:
#         loadedUsers = json.loads(line)
#         getSentimentsFromDictToJson(loadedUsers, filename='SentimentsFromAllUsers.json')


# with open(wcLadies) as f:
#     for line in f:
#         loadedWC = json.loads(line)
#         makeWordCloud( data = loadedWC, filename = 'wcLadies.jpg' )



# with open(allCategoriesSentiments) as f:
#     allComp = []
#     for line in f:
#         loadedCat = json.loads(line)
#         for key, value in loadedCat.iteritems():
#             if key != 'For Stormfront Ladies Only':
#                 allComp.append(value['compound'])
#         print py_.mean(allComp)
#         print loadedCat['For Stormfront Ladies Only']['compound']


# wcWords = {}
# exclList = ["n't", "'d", "'s", "'m", "'ve", "'re", "'", "&", "|", "#", ";", "+","http"]
# for cat in wcLadiesCat:

#     with open('results/'+cat) as f:
#         for line in f:
#             wcss = json.loads(line)
#             for w, count in wcss.iteritems():
#                 if w not in exclList:
#                     if not w in wcWords:
#                         wcWords[w] = int(count)
#                     else:
#                         wcWords[w] = wcWords[w] + count
# wcWords = sorted(wcWords.items(), key=operator.itemgetter(1), reverse=True)
# wcWords = np.array(wcWords)
# wcWords = WordCloud().generate_from_frequencies( wcWords )
# wcWords.to_file('wcLadiesOnly.jpg')

# with open(categoryTfIdf) as f:
#     emptySpace = re.compile('\ ')
#     forwardSlash = re.compile('\/')
#     for line in f:
#         categoriesTfIdfs = json.loads(line)
#         for catTfIdf, words in categoriesTfIdfs.iteritems():
#             print catTfIdf
#             catDict = {}
#             for w, tfidf in words.iteritems():
#                 if w not in exclList:
#                     catDict[w] = tfidf
#                     # tfidf = repr(tfidf)
#                     # weight = tfidf.split('.')[1]
#             # print catDict

#             catTfIdf = emptySpace.sub('_', catTfIdf )
#             catTfIdf = forwardSlash.sub('', catTfIdf )
#             # catDict = sorted(catDict.items(), key=operator.itemgetter(1), reverse=True)
#             # catDict = np.array(catDict)
#             catDict = WordCloud().generate_from_frequencies( catDict )
#             catDict.to_file('results/'+catTfIdf+ '.jpg')

# with open(tfidfDatingAdvice) as f:
#     for line in f:
#         words = json.loads(line)
#         for word, tfValue in words.iteritems():
#             print word
#             # print tfValue
#             print float(tfValue)




# getSeasonSentiments()



# getSentimentsFromDictToJson( userPostsRange(1, 10, 200, 800), filename = 'SentimentsFromRange.json' )
# doPlotFromTimeline()
# doPlotFromUsersRange()
# userPostsRange(1, 10, 200, 800)

def getSeasonalityGeneralPopul():

    winterSentiments = []
    springSentiments = []
    summerSentiments = []
    autumnSentiments = []
    userSentiments = []
    okUsers = {}

    with open('results/timelineData.json') as f:
        for line in f:
            data = json.loads(line)
            for year, values in data.iteritems():
                if year != '2001' and year != '2015':
                    for month, monData in data[year].iteritems():
                        if month == '12' or month == '01' or month == '02':
                            winterSentiments.append(monData['monthlySentiments']['compound'])
                        if month == '03' or month == '04' or month == '05':
                            springSentiments.append(monData['monthlySentiments']['compound'])
                        if month == '06' or month == '07' or month == '08':
                            summerSentiments.append(monData['monthlySentiments']['compound'])
                        if month == '09' or month == '10' or month == '11':
                            autumnSentiments.append(monData['monthlySentiments']['compound'])

    with open('results/SentimentsFromAllUsers.json') as f:
        for line in f:
            allUsers = json.loads(line)
            
            for user, sentis in allUsers.iteritems():
                if sentis:
                    okUsers[user] = sentis
                        
            rUsers = random.sample( okUsers.items(), 39 )
            for u, value in rUsers:
                userSentiments.append(value['compound'])

    # print len(winterSentiments)
    # print len(springSentiments)
    # print len(summerSentiments)
    # print len(autumnSentiments)

    print np.corrcoef( userSentiments, winterSentiments )
    print np.corrcoef( userSentiments, springSentiments )
    print np.corrcoef( userSentiments, summerSentiments )
    print np.corrcoef( userSentiments, autumnSentiments )

#


def getSentAveragePerEntity():
    theEntities = getAllEntities()

    dict = {}
    entCompounds = {}

    for ent in theEntities:
        dict[ent] = []

    with open(entities) as f:
        for line in f:
            post = json.loads(line)
            postEntities = post['stormfront_entities']
            postContent  = basicCleanUp( post['stormfront_content'] )
            if postEntities:
                for pe in postEntities:
                    pe = unicodedata.normalize('NFKD', unicode(pe)).encode('ascii', 'ignore')
                    if postContent:
                        dict[pe].append(postContent)

    sentEnti = getSentimentsFromDictToJson(dict)

    for ent, sents in sentEnti.iteritems():
        for key, sent in sents.iteritems():
            if key == 'compound':
                entCompounds[ent] = sent
    entCompounds = sorted(entCompounds.items(), key=operator.itemgetter(1), reverse=False)
    print entCompounds
    entCompounds = repr(entCompounds)
    writeToFile( 'SortedEntityCompounds.txt', entCompounds )

# getSentAveragePerEntity()



# getSeasonalityGeneralPopul()

# getTimelineContents()
# doTFIDF()

# getContentsByCategory( ['For Stormfront Ladies Only'], save = True, filename = 'LadiesContent' )
# getContentsByCategory( ['Dating Advice'], save = True, filename = 'DatingAdviceContent' )
# getCategoryContents()
doTFIDFbyCategory()
