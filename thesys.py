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
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import numpy as np


# For word count
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
userPosts = 'results/AllUsers.txt'
userContents = 'results/userContentData.json'
timelineData = 'results/timelineData.json'
sentiRange = 'results/SentimentsFromRange.json'

# Import word counts
wcLadies = 'results/For_Stormfront_Ladies_Only-WordCount.json'


# Constants
punchMarks = [".", ",", "''", "``", "...", ":", "(", ")", "{", "}", "[", "]", "?"]
stopWords = set(stopwords.words('english'))

# population = ['Politics & Continuing Crises', 'Lounge', 'Strategy and Tactics' ]
# politicalRegimes = ['Stormfront Canada','Stormfront Britain', 'Stormfront South Africa','Stormfront Italia', 'Stormfront Russia' ]

# categoriesToTranslate = ['Stormfront en Francais', 'Stormfront en Espanol y Portugues', 'Stormfront Russia', 'Stormfront Baltic / Scandinavia', 'Stormfront Europe', 'Stormfront Italia', 'Stormfront Srbija', 'Stormfront Canada', 'Stormfront Croatia', 'Stormfront Hungary', 'Stormfront South Africa', 'Stormfront Nederland & Vlaanderen', ]
#[('Opposing Views Forum', 813550), ('Politics & Continuing Crises', 166120), ('Lounge', 128560), ('Stormfront en Francais', 115393), ('Talk', 82808), ('Stormfront en Espanol y Portugues', 69502), ('Stormfront Russia', 62106), ('Questions about this Board', 59803), ('Stormfront Ireland', 51372), ('For Stormfront Ladies Only', 50098), ('Events', 45920), ('Local and Regional', 45715), ('Strategy and Tactics', 43944), ('Stormfront Baltic / Scandinavia', 41367), ('Ideology and Philosophy', 37159), ('Suggestions for this Board', 28289), ('Stormfront Europe', 28191), ('Stormfront Britain', 21551), ('Classified Ads', 19392), ('Newslinks & Articles', 18752), ('New Members Introduce Yourselves', 14722), ('eActivism and Stormfront Webmasters', 14661), ('Multimedia', 14598), ('Legal Issues', 12838), ('Stormfront Italia', 11991), ('Stormfront Srbija', 8208), ('Stormfront Canada', 4658), ('General Questions and Comments', 3940), ('The Truth About Martin Luther King', 3930), ('Stormfront Croatia', 3625), ('Stormfront Hungary', 3416), ('Stormfront South Africa', 3106), ('The Eternal Flame', 2604), ('Dating Advice', 1097), ('Announcements', 245), ('Introduction and FAQ', 236), ('Stormfront Nederland & Vlaanderen', 126), ('Fourth Annual Stormfront Smoky Mountain  Summit', 64), ('Stormfront Downunder', 48)]
# cwc = [('General Questions and Comments', 37159), ('Legal Issues', 37159), ('Multimedia', 37159), ('eActivism and Stormfront Webmasters', 37159), ('Classified Ads', 37159) ] 

wcc = [('For Stormfront Ladies Only', 353), ('Guidelines for Posting', 123), ('General Questions and Comments', 123), ('Fourth Annual Stormfront Smoky Mountain  Summit', 123), ('eActivism and Stormfront Webmasters', 123)]


# Functions START -----
# 
# 

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
                    if not item in entList:
                        entList.append( unicodedata.normalize('NFKD', unicode(item)).encode('ascii', 'ignore') )
        
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
def getContentsByCategory( categories ):
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



def makeWordCloud( data = False, include = False, exclude = False, filename = False ):
    print 'Starting: makeWordCloud'
    txt = ''

    if data:
        for word, times in data.iteritems():
            for i in range(times):
                txt += word + ' '
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


    wc = WordCloud().generate(txt)
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

    createCoRelPlot( dates, sents, filename = 'sentiTime.jpg', xlabel = 'Time from 2001-09 to 2015-02', ylabel = 'Compound Sentiments', step = 3.0 )

def doPlotFromUsersRange():
    dict = { 'lowest':{ 'postCount': 0, 'compound': '' }, 'low':{ 'postCount': 0, 'compound': '' }, 'medium':{ 'postCount': 0, 'compound': '' }, 'high':{ 'postCount': 0, 'compound': '' }, 'highest':{ 'postCount': 0, 'compound': '' } }

    with open(userContents) as f:
        for line in f:
            loadedUsers = json.loads(line)
            for key, posts in loadedUsers.iteritems():
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

    print dict

    with open(sentiRange) as f:
        for line in f:
            data = json.loads(line)
            for rng, values in data.iteritems():
                if data[rng]:
                    print data[rng]
                    compound = data[rng]['compound']
                    dict[rng]['compound'] = compound


    print dict

    # dict = sorted(dict.items(), key=operator.itemgetter(0), reverse=False)

    postCount = []
    sents = []

    # for score, values in dict:
    #     if key != 'total':
    #         for key in dict[score]:
    #             print key
    #             postCount.append( int(dict[score]['postCount']) )
    #             sents.append( float(dict[score]['compound']) )


# 'lowest': {'postCount': 19346, 'compound': 0.16979695027395791},
# 'high': {'postCount': 313159, 'compound': 0.035213245028882706},
# 'highest': {'postCount': 263467, 'compound': -0.030325970614915106},
# 'medium': {'postCount': 464993, 'compound': 0.07822665545503248},
# 'low': {'postCount': 91562, 'compound': 0.1513315469299454}}


    createCoRelPlot( [19346, 91562, 464993, 313159, 263467], [0.16979695027395791, 0.1513315469299454, 0.07822665545503248, 0.035213245028882706, -0.030325970614915106], filename = 'sentiRange.jpg', xlabel = 'Range', ylabel = 'Compound Sentiments', step = 1.0 )


# 
# 
# Functions END-------

wcNext = [('Events', 1), ('Local and Regional', 1), ('Lounge', 1), ('Opposing Views Forum', 1), ('Politics & Continuing Crises')]
wcNextContent = getContentsByCategory( wcNext )
wordCount( wcNextContent, mostCommon = 500 )

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

# getDataByUser()



# with open(userContents) as f:
#     for line in f:
#         loadedUsers = json.loads(line)
#         getSentimentsFromDictToJson(loadedUsers, filename='SentimentsFromAllUsers.json')


# with open(wcLadies) as f:
#     for line in f:
#         loadedWC = json.loads(line)
#         makeWordCloud( data = loadedWC, filename = 'wcLadies.jpg' )


# getSentimentsFromDictToJson( userPostsRange(1, 10, 200, 800), filename = 'SentimentsFromRange.json' )
# doPlotFromTimeline()
# doPlotFromUsersRange()
# userPostsRange(1, 10, 200, 800)
