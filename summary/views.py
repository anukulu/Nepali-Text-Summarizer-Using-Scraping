from django.shortcuts import render
import math
from collections import Counter
from bs4 import BeautifulSoup
import requests
import re
import heapq
import nltk

# building numerical vectors for the keyword and words in the topic 
def build_vector(iterable1, iterable2):
	counter1 = Counter(iterable1)
	counter2 = Counter(iterable2)
	all_items = set(counter1.keys()).union(set(counter2.keys()))
	vector1 = [counter1[k] for k in all_items]
	vector2 = [counter2[k] for k in all_items]
	return vector1, vector2

# finding the cosine similarity between the keyword and the topic
def cosim(v1, v2):
	dot_product = sum(n1 * n2 for n1, n2 in zip(v1, v2) )
	magnitude1 = math.sqrt(sum(n ** 2 for n in v1))
	magnitude2 = math.sqrt(sum(n ** 2 for n in v2))
	if((magnitude1 * magnitude2) != 0):
		return dot_product / (magnitude1 * magnitude2)
	else:
		return 0

# function for finding the summary of the articles
def summarize(urlOfTheTopic):
	articles = ""
	# this code scrapes the whole text from given url using a lxml parser 
	source = requests.get(urlOfTheTopic).text
	soup = BeautifulSoup(source, 'lxml')

	# for all the text contained inside p tags of the html, we get only the text written inside 
	if("onlinekhabar.com" in urlOfTheTopic):
		for article in soup.find_all('p'):
			newsArticle = str(article.get_text())
			articles = articles + " " + newsArticle
			
	elif ("ujyaaloonline.com" in urlOfTheTopic):
		for article in soup.find_all('p', style="text-align: justify;"):
			newsArticle = str(article.get_text())
			articles = articles + " " + newsArticle

	# remove all numbers using regular expression
	articleText = re.sub(r'\[[0-9]*\]', r' ', articles)  
	articleText = re.sub(r'\s+', r' ', articleText)

	# removing all the unnecessary characters from the text
	for letter in 'abcdefghijklmnopqrstuvwxyz0123456789+|}{<>~-_[]@#$^&*.·"\\':
		articleText = articleText.replace(letter, '')

	# refining the text again
	articleText = re.sub(r'\[[0-9]*\]', ' ', articleText)  
	articleText = re.sub(r'\s+', ' ', articleText)

	# creating list of sentences from the given text using । as the separator for nepalese language
	sentenceList = articleText.split(' । ')
	stopwords = open('summary/stopwordsNepali.txt' , encoding="UTF-8").read().split()

	# removing all the bibhaktis and extra unnecessary symbols from the words
	articleText2 = ""
	articleText2 = re.sub(r'(मा|को|ले|बाट|का|हरु|हरुसँग|सँग|लाई|हरू|हरूसँग|हरू)|(हरु|हरू)|(मा|को|ले|बाट|का|सँग|लाई)', r' ', articleText)
	articleText2 = re.sub(r'(०|१|२|३|५|६|७|८| । |-|,|"|/|\')', r'', articleText2)
	articleText2 = re.sub(r'(“|”|‘|’|‘|’)', r'', articleText2)

	formattedText = articleText2.split()

	# creating a dictionary with the list of words in the sentences with their frequencies 
	wordFrequencies = {}  
	for word in formattedText:  
		if word not in stopwords:
			if word not in wordFrequencies.keys():
				wordFrequencies[word] = 1
			else:
				wordFrequencies[word] += 1

	if (len(wordFrequencies) == 0):
		return ""
	# finding the maximum frequency and calculating weighted frequency for all the words in the sentence 
	maxFrequency = max(wordFrequencies.values())
	for word in wordFrequencies.keys():  
		wordFrequencies[word] = float(wordFrequencies[word]/maxFrequency)

	# calculating the total score for each sentence in the article
	sentScores = {}  
	for sent in sentenceList:  
		for word in nltk.word_tokenize(sent):
			#we do not want to keep sentences with words more than 30
			if len(sent.split(' ')) < 30:
				if word in wordFrequencies.keys():
					if sent not in sentScores.keys():
						sentScores[sent] = wordFrequencies[word]
					else:
						sentScores[sent] += wordFrequencies[word]
	
	# calculating the ratio of the sentence score to the length of the sentence and assigning the value as the sentence score
	for sent in sentScores.keys():
		sentScores[sent] = float(sentScores[sent]/len(sent.split()))

	# finding the top 5 sentences with the highest scores among all the sentences
	summarizedSentences = heapq.nlargest(5, sentScores, key=sentScores.get)

	# combining the sentences with the highest scores, excluding the repeated sentences from the finalsummary
	finalSummary = sentenceList[0] + " । " + '\n'
	for sentence in sentenceList:
		if sentence in summarizedSentences:
			if sentence not in finalSummary: 
				finalSummary = finalSummary + sentence + ' । ' + '\n'
	return finalSummary

def home(request):

	# defining a keyword variable to take the input from the user
	keyword = ""
	keyword2 = ""
	if request.method == 'POST':
		keyword = request.POST['nepaliWords']
		keyword2 = keyword

		# if the given input is not empty, only then start working
		if(keyword != ""):
			
			# opening and initializing the count to zero
			l1 = keyword.split()	
			file = open('summary/topics.txt', 'r', encoding="UTF-8")
			count = 0
			summary = ""

			counterForNumberOfArticles = 0
			# for each topic in topics.txt, we find the cosine similarity between the word and the topic
			for line in file.readlines():
				l2 = line.split()
				v1, v2 = build_vector(l1, l2)
				
				# the threshold is that the cosine similarity must be greater than zero
				if (cosim(v1, v2) > 0):

					# limiting the number of articles to 10
					if(counterForNumberOfArticles < 10):
					# if the similarity is greater than zero then summarize the article for the related topic using its
					# corresponding topic
						file2 = open('summary/urls.txt', 'r', encoding="UTF-8")
						urlOfTheTopic = file2.read().split()[count]

					# passing the url of the topic for summarization of that article
						finalSummary = summarize(urlOfTheTopic)

					# we do not want repeated articles to be included in the summary 
						if (finalSummary not in summary): 
							summary = summary + line + '\n' + finalSummary + '\n\n'

						counterForNumberOfArticles += 1
					else:
						break
				count += 1

			# if the summary is empty print a message saying that the article could not be found
			if(summary != ""):
				keyword = summary
			else:
				keyword = "माथी लेखिएको शब्दहरु शम्बन्धित समाचार भेटााउन नसकिएकोमा माफी चाहअन्छौ ।"

	# passing the summary to the template so that it can be printed
	return render(request, "summary/home.html", {'text' : keyword, 'text2': keyword2})

