from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import json
from pydash import py_
import re
import operator
import unicodedata
import sys  

reload(sys)  
sys.setdefaultencoding('latin-1')

# GLOBALS
entities = '/var/scratch/schristo/data/201607_vox-pol_jonathan/stormfront_replies_entities.jsons'
usersInfo = '/var/scratch/schristo/data/201607_vox-pol_jonathan/stormfront_users_info_v2.jsons'

categoriesList = ['New Members Introduce Yourselves', 'Events', 'For Stormfront Ladies Only', 'Politics & Continuing Crises', 'Questions about this Board', 'Stormfront Baltic / Scandinavia', 'Stormfront Britain', 'Stormfront Canada', 'Stormfront Croatia', 'Stormfront Downunder', 'Stormfront Europe', 'Stormfront Hungary', 'Stormfront Ireland', 'Stormfront Italia', 'Stormfront Nederland & Vlaanderen', 'Stormfront Russia', 'Stormfront South Africa', 'Stormfront Srbija', 'Strategy and Tactics']
population = ['Politics & Continuing Crises','Lounge', 'Strategy and Tactics' ]
politicalRegimes = ['Stormfront Canada','Stormfront Britain', 'Stormfront South Africa','Stormfront Italia', 'Stormfront Russia' ]

# Functions START -----
# 
# 


# Clean up how it looks premium stage
# 
def basicCleanUp( cont ):
    # Clean Up regex
    nrt = re.compile(r'[\n\r\t\_\-\-\~\*\!\@\$\%\^]')
    quoteA = re.compile('\[QUOTE=.*]')
    quoteB = re.compile('\Quote:           Originally Posted by .*   ')
    emptySpaces = re.compile('\  ')

    cleanedText = nrt.sub(' ', cont )
    cleanedText = quoteA.sub('', cleanedText )
    cleanedText = quoteB.sub('', cleanedText )
    cleanedText = emptySpaces.sub(' ', cleanedText )
    
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



# Get a list of all category names from the users info file
# 
def getCategoriesFromUsersInfo():
    categories = []
    with open(usersInfo) as f:
        for line in f:
            user = json.loads(line)
            if user['categories']:
                keyCategories = getKeys( user['categories'] )
                for keyCat in keyCategories:
                    if not keyCat in categories:
                        categories.append( keyCat )
    
    print 'All categories from Users:'
    print categories
    print ' '
    return categories

# Get a list of all topics from the users info file
# 
def getTopicsFromUsersInfo():
    topics = []
    with open(usersInfo) as f:
        for line in f:
            user = json.loads(line)
            if user['topics']:
                keyTopics = getKeys( user['topics'] )
                for keyTopic in keyTopics:
                    if not keyTopic in topics:
                        topics.append( keyTopic )
    
    print 'All topics from Users:'
    print topics
    print ' '
    return topics

# Get a list of all category names from the entity replies file
# 
def getCategoriesFromEntities():
    categories = []
    with open(entities) as f:
        for line in f:
            entity = json.loads(line)
            if not entity['stormfront_category'] in categories:
                categories.append( entity['stormfront_category'] )
        
    print 'All categories from Entities:'
    print categories
    print ' '
    return categories

# Get a list of all topics from the entity replies file
# 
def getTopicsFromEntities():
    topics = []
    with open(entities) as f:
        for line in f:
            entity = json.loads(line)
            if not entity['stormfront_topic'] in topics:
                topics.append( entity['stormfront_topic'] )
        
    print 'All topics from Entities:'
    print topics
    print ' '
    return topics

# def getTopicsPerCategory():
    # {'category': {'Topic': 34}, {'Topic2': 24}}




# Get a dictionary with the most active users (username and total posts)
# 
def mostActiveUsers( top ):
    dict = {}
    with open(usersInfo) as f:
        for line in f:
            user = json.loads(line)
            total = int(0)
            for key, numberOfPosts in user['categories'].iteritems():
                total += numberOfPosts

            dict[user['user']] = total

    mostFirst = sorted(dict.items(), key=operator.itemgetter(1), reverse=True)

    return mostFirst[:top]

# Get a dictionary with the most active categories (category and total posts)
# 
def mostActiveCategories( top ):

    # Initialize dict
    dict = {}
    allCategories = getCategoriesFromUsersInfo()

    for category in allCategories:
        category = unicodedata.normalize('NFKD', unicode(category)).encode('ascii', 'ignore')
        dict[category] = 0

    # Open file and count totals per category
    with open(usersInfo) as f:
        for line in f:
            user = json.loads(line)
            for key, numberOfPosts in user['categories'].iteritems():
                key = unicodedata.normalize('NFKD', unicode(key)).encode('ascii', 'ignore')
                # print key
                dict[key] += numberOfPosts

    mostFirst = sorted(dict.items(), key=operator.itemgetter(1), reverse=True)

    print 'The most '+ repr(top) +' active categories are: '
    print mostFirst[:top]
    print ' '

    return mostFirst[:top]

# Get a dictionary with the most active topics (topic and total posts)
# 
def mostActiveTopics( top ):
    dict = {}
    allTopics = getTopicsFromUsersInfo()

    for topic in allTopics:
        topic = unicodedata.normalize('NFKD', unicode(topic)).encode('ascii', 'ignore')
        dict[topic] = 0

    # Open file and count totals per category
    with open(usersInfo) as f:
        for line in f:
            user = json.loads(line)
            for key, numberOfPosts in user['topics'].iteritems():
                key = unicodedata.normalize('NFKD', unicode(key)).encode('ascii', 'ignore')
                # print key
                dict[key] += numberOfPosts

    mostFirst = sorted(dict.items(), key=operator.itemgetter(1), reverse=True)

    print 'The most '+ repr(top) +' active topics are: '
    print mostFirst[:top]
    print ' '

    return mostFirst[:top]






# Get a dictionary with posts per year (year and total posts)
# 
def getContentsByYear( mostPosts = False ):
    dict = {}
    with open(entities) as f:
        for line in f:
            entity = json.loads(line)
            year = entity['stormfront_publication_date'].split('-')[0]
            if not year in dict:
                dict[year] = {}
                dict[year]['total'] = 0
                dict[year]['contents'] = []
            dict[year]['total'] += 1
            dict[year]['contents'].append( basicCleanUp( entity['stormfront_content'] ) )

    # print dict

    if mostPosts:
        # print sorted(dict.items(), key=operator.itemgetter(1), reverse=True)
        # return sorted(dict.items(), key=operator.itemgetter(1), reverse=True)
        return dict
    else:
        # print sorted(dict.items(), key=operator.itemgetter(0))
        # return sorted(dict.items(), key=operator.itemgetter(0))
        return dict
   
# Get contents from a given list of categories
# 
def getContentByCategory( categories ):
    content = {}
    with open(entities) as f:
        for line in f:
            entity = json.loads(line)
            if ( entity['stormfront_category'] in categories ):
                cat = entity['stormfront_category']
                if not cat in content:
                    content[cat] = []
                txt = basicCleanUp( entity['stormfront_content'] )
                txt.strip()
                content[entity['stormfront_category']].append(txt)
    
    return content

# Seasons-criminality and extreme content
# 
def getContentsByQuarter( season = False ):
    Q1 = []
    Q2 = []
    Q3 = []
    Q4 = []

    with open(entities) as f:
        for line in f:
            entity = json.loads(line)
            content = basicCleanUp(entity['stormfront_content'])
            month = entity['stormfront_publication_date'].split('-')[1]
            month = int(month)
            if season:
                if (month < 3 or month == 12):
                    Q1.append(content)
                elif (month > 2 and month < 6):
                    Q2.append(content)
                elif (month > 5 and month < 9):
                    Q3.append(content)
                else:
                    Q4.append(content)
            else:
                if (month < 4):
                    Q1.append(content)
                elif (month > 3 and month < 7):
                    Q2.append(content)
                elif (month > 6 and month < 10):
                    Q3.append(content)
                else:
                    Q4.append(content)

    if season:
        dict = {'winter': Q1, 'spring': Q2, 'summer': Q3, 'autumn': Q4}
    else:
        dict = {'q1': Q1, 'q2': Q2, 'q3': Q3, 'q4': Q4}
                
    return dict

# Get contents from a given list of topics
# 
def getContentsByTopic( topics ):
    dict = {}
    keysTopics = []
    
    for key, value in topics:
        keysTopics.append(key)

    with open(entities) as f:
        for line in f:
            entity = json.loads(line)
            content = basicCleanUp(entity['stormfront_content'])
            if entity['stormfront_topic'] in keysTopics:
                if not entity['stormfront_topic'] in dict:
                    dict[entity['stormfront_topic']] = []
                dict[entity['stormfront_topic']].append( content )

    print 'The contents of the most popular topics are:'
    print dict
    print ' '
    return dict





# Analyze a dictionary
# 
def getSentimentsFromDict( dict, isContent = False ):

    analyzer = SentimentIntensityAnalyzer()
    allPositives = []
    allNegatives = []
    allNeutral = []
    allCompound = []

    if dict:

        if isContent:
            positives = []
            negatives = []
            neutral = []
            compound = []

            for sentence in dict:
                if sentence:
                    vs = analyzer.polarity_scores(sentence)
                    positives.append(vs['pos'])
                    negatives.append(vs['neg'])
                    neutral.append(vs['neu'])
                    compound.append(vs['compound'])

            print 'The positive average is: ' + repr( py_.mean(positives) )
            print 'The negative average is: ' + repr( py_.mean(negatives) )
            print 'The neutral average is: ' + repr( py_.mean(neutral) )
            print 'The compound average is: ' + repr( py_.mean(compound) )
            print 'The total sentences are: ' + repr( len(dict) )
            print '---------'

            allPositives.append( py_.mean(positives) )
            allNegatives.append( py_.mean(negatives) )
            allNeutral.append( py_.mean(neutral) )
            allCompound.append( py_.mean(compound) )
        else:
            for category, sentences in dict.iteritems():

                positives = []
                negatives = []
                neutral = []
                compound = []

                for sentence in sentences:
                    if sentence:
                        vs = analyzer.polarity_scores(sentence)
                        positives.append(vs['pos'])
                        negatives.append(vs['neg'])
                        neutral.append(vs['neu'])
                        compound.append(vs['compound'])

                print 'The positive average in ' + category +' is: ' + repr( py_.mean(positives) )
                print 'The negative average in ' + category +' is: ' + repr( py_.mean(negatives) )
                print 'The neutral average in ' + category +' is: ' + repr( py_.mean(neutral) )
                print 'The compound average in ' + category +' is: ' + repr( py_.mean(compound) )
                print 'The total sentences are: ' + repr( len(sentences) )
                print '---------'

                allPositives.append( py_.mean(positives) )
                allNegatives.append( py_.mean(negatives) )
                allNeutral.append( py_.mean(neutral) )
                allCompound.append( py_.mean(compound) )

            print 'The aggregated positive average is: ' + repr( py_.mean(allPositives) )
            print 'The aggregated negative average is: ' + repr( py_.mean(allNegatives) )
            print 'The aggregated neutral average is: ' + repr( py_.mean(allNeutral) )
            print 'The aggregated compound average is: ' + repr( py_.mean(allCompound) )
            print '---------'

# 
# 
# Functions END-------

      



# allContent = getContentByCategory( categoriesList )
# populationContent = getContentByCategory( population )
# politicalRegimesContent = getContentByCategory( politicalRegimes )


# seasons = getContentsByQuarter(season = True)
# getSentimentsFromDict(seasons)
# quarters = getContentsByQuarter()
# getSentimentsFromDict(quarters)
# print quarters


# getSentimentsFromDict(allContent)
# getSentimentsFromDict(populationContent)
# getSentimentsFromDict(politicalRegimesContent)
# yolo = mostActiveUsers(25)
# print yolo
# mostActiveCategories(14)
# mat = mostActiveTopics(12)
# getContentsByTopic(mat)
# getSentimentsFromDict(getContentsByTopic(mat))
# getTopicsFromUsersInfo()
# print lala

yearlyActivity = getContentsByYear()
for year in getContentsByYear():
    print 'The ' + year + ' sentiments are:'
    getSentimentsFromDict( yearlyActivity[year]['contents'], isContent = True )

# usersUniqueCategories = getCategoriesFromUsersInfo()
# print usersUniqueCategories

# entitiesUniqueCategories = getCategoriesFromEntities()
# print entitiesUniqueCategories
# getCategoriesFromEntities()
# getTopicsFromEntities()



