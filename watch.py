#! /usr/bin/env python

#import all the things we need
import re, random, os, glob
import tweetstream, requests, numpy
from nltk import word_tokenize, WordNetLemmatizer, NaiveBayesClassifier, classify
from nltk.corpus import stopwords

#Some code and ideas taken from Shankar Ambady
#https://github.com/shanbady/NLTK-Boston-Python-Meetup
username = 'doctoboggan'
password = 'trixie'

wordlemmatizer = WordNetLemmatizer() #finds the root word in a word
commonwords = stopwords.words('english') #list of common words that usually mean nothing

#initialize lists to hold the text dumps of pos and neg reviews
posreviews = []
negreviews = []

#append the text from each pos review
for infile in glob.glob( os.path.join('pos/', '*.txt') ):
  text_file = open(infile, "r")
  posreviews.append(text_file.read())
  text_file.close()

#append the text from each neg review to another list
for infile in glob.glob( os.path.join('neg/', '*.txt') ):
  text_file = open(infile, "r")
  negreviews.append(text_file.read())
  text_file.close()

#Make a list of tuples. Each tuple contains review text and a score ('pos' or 'neg')
mixedreviews = []
for review in posreviews:
  mixedreviews.append((review,'pos'))
for review in negreviews:
  mixedreviews.append((review,'neg'))
random.shuffle(mixedreviews) #randomly shuffle the list

#this function returns a dictionary where each key is a word and the value is True
def findFeatures(review):
  features = {}
  wordtokens = [wordlemmatizer.lemmatize(word.lower()) for word in word_tokenize(review)]
  for word in wordtokens:
    if word not in commonwords:
      features[word] = True
  return features

#build a list of tuples with the above dictionary and the score for each review
print 'Building featuresets... ',
featuresets = [(findFeatures(reviewText), score) for (reviewText,score) in mixedreviews]
print 'Done'

#build the classifier with the training set
print 'Training classifier... ',
classifier = NaiveBayesClassifier.train(featuresets)
print 'Done'

#initialize an empty list to hold all the TV shows we find
currentTvShows = []

r = requests.get('http://www.locatetv.com/listings')
for line in r.iter_lines():
  if '  <a href="/tv/' in line or '  <a href="/movie/' in line:
    splitline = line.split('                    ')
    match = re.search('>([\w\s]+)</a>', splitline[1])
    if match:
      if match.group(1) not in currentTvShows:
        currentTvShows.append(match.group(1))

totalCount = numpy.zeros(len(currentTvShows))
sentiment = {}
for show in currentTvShows:
  sentiment[show] = {'pos':0, 'neg':0, 'tot':0}

stream = tweetstream.TrackStream(username, password, currentTvShows)
for tweet in stream:
  if tweet.has_key('text'):    
    print 'NEWEST TWEET: ', tweet['text']
    features = findFeatures(tweet['text'])
    classification = classifier.classify(features)
    for show in currentTvShows:
      if show.lower() in tweet['text'].lower():
        sentiment[show]['tot'] += 1
        sentiment[show][classification] += 1
      totals = [sentiment[show]['tot'] for show in sentiment.keys()]
      for count in sorted(totals, reverse=True)[:5]:
        show = sentiment.keys()[totals.index(count)]
        print show, ' -> ', sentiment[show]
      print '------------------------------------------------'


