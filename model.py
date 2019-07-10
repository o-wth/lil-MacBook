import pronouncing
import markovify
import re
import random
import numpy as np
import os
import keras
from keras.models import Sequential
from keras.layers import LSTM
from keras.layers.core import Dense

d = 4
ms = 16
train = False
rapper = "kanye_west"
f = "neural_rap.txt"

def create_network(d):
	rapModel = Sequential()
	rapModel.add(LSTM(4, input_shape=(2, 2), return_sequences=True))
	for i in range(d):
		rapModel.add(LSTM(8, return_sequences=True))
	rapModel.add(LSTM(2, return_sequences=True))
	rapModel.summary()
	rapModel.compile(optimizer='rmsprop',
              loss='mse')

	if rapper + ".rap" in os.listdir(".") and not train:
		rapModel.load_weights(str(rapper + ".rap"))
	return rapModel

def markov(text_file):
	read = open(text_file, "r").read()
	textM = markovify.NewlineText(read)
	return textM

def syllables(line):
	count = 0
	for word in line.split(" "):
		vowels = 'aeiouy'
		word = word.lower().strip(".:;?!")
		if word[0] in vowels:
			count +=1
		for index in range(1,len(word)):
			if word[index] in vowels and word[index-1] not in vowels:
				count +=1
		if word.endswith('e'):
			count -= 1
		if word.endswith('le'):
			count+=1
		if count == 0:
			count +=1
	return count / ms

def rhymeindex(lyrics):
	if str(rapper) + ".rhymes" in os.listdir(".") and train == False:
		print "loading saved rhymes from " + str(rapper) + ".rhymes"
		return open(str(rapper) + ".rhymes", "r").read().split("\n")
	else:
		rhyme_master_list = []
		print "Alright, building the list of all the rhymes"
		for i in lyrics:
			word = re.sub(r"\W+", '', i.split(" ")[-1]).lower()
			rhymeslist = pronouncing.rhymes(word)
			rhymeslist = [x.encode('UTF8') for x in rhymeslist]
			rhymeslistends = []
			for i in rhymeslist:
				rhymeslistends.append(i[-2:])
			try:
				rhymescheme = max(set(rhymeslistends), key=rhymeslistends.count)
			except Exception:
				rhymescheme = word[-2:]
			rhyme_master_list.append(rhymescheme)
		rhyme_master_list = list(set(rhyme_master_list))

		reverselist = [x[::-1] for x in rhyme_master_list]
		reverselist = sorted(reverselist)

		rhymelist = [x[::-1] for x in reverselist]

		f = open(str(rapper) + ".rhymes", "w")
		f.write("\n".join(rhymelist))
		f.close()
		print rhymelist
		return rhymelist

def rhyme(line, rhyme_list):
	word = re.sub(r"\W+", '', line.split(" ")[-1]).lower()
	rhymeslist = pronouncing.rhymes(word)
	rhymeslist = [x.encode('UTF8') for x in rhymeslist]
	rhymeslistends = []
	for i in rhymeslist:
		rhymeslistends.append(i[-2:])
	try:
		rhymescheme = max(set(rhymeslistends), key=rhymeslistends.count)
	except Exception:
		rhymescheme = word[-2:]
	try:
		float_rhyme = rhyme_list.index(rhymescheme)
		float_rhyme = float_rhyme / float(len(rhyme_list))
		return float_rhyme
	except Exception:
		return None


def split_lyrics_file(text_file):
	text = open(text_file).read()
	text = text.split("\n")
	while "" in text:
		text.remove("")
	return text


def generate_lyrics(textM, text_file):
	bars = []
	last_words = []
	lyriclength = len(open(text_file).read().split("\n"))
	count = 0
	markov_rapModel = markov(text_file)

	while len(bars) < lyriclength / 9 and count < lyriclength * 2:
		bar = markov_rapModel.make_sentence()

		if type(bar) != type(None) and syllables(bar) < 1:

			def get_last_word(bar):
				last_word = bar.split(" ")[-1]
				if last_word[-1] in "!.?,":
					last_word = last_word[:-1]
				return last_word

			last_word = get_last_word(bar)
			if bar not in bars and last_words.count(last_word) < 3:
				bars.append(bar)
				last_words.append(last_word)
				count += 1
	return bars

def build_dataset(lines, rhyme_list):
	dataset = []
	line_list = []
	for line in lines:
		line_list = [line, syllables(line), rhyme(line, rhyme_list)]
		dataset.append(line_list)

	x_data = []
	y_data = []

	for i in range(len(dataset) - 3):
		line1 = dataset[i    ][1:]
		line2 = dataset[i + 1][1:]
		line3 = dataset[i + 2][1:]
		line4 = dataset[i + 3][1:]

		x = [line1[0], line1[1], line2[0], line2[1]]
		x = np.array(x)
		x = x.reshape(2,2)
		x_data.append(x)

		y = [line3[0], line3[1], line4[0], line4[1]]
		y = np.array(y)
		y = y.reshape(2,2)
		y_data.append(y)

	x_data = np.array(x_data)
	y_data = np.array(y_data)

	return x_data, y_data

def compose_rap(lines, rhyme_list, lyrics_file, rapModel):
	rap_vectors = []
	human_lyrics = split_lyrics_file(lyrics_file)

	initial_index = random.choice(range(len(human_lyrics) - 1))
	initial_lines = human_lyrics[initial_index:initial_index + 2]

	starting_input = []
	for line in initial_lines:
		starting_input.append([syllables(line), rhyme(line, rhyme_list)])

	starting_vectors = rapModel.predict(np.array([starting_input]).flatten().reshape(1, 2, 2))
	rap_vectors.append(starting_vectors)

	for i in range(100):
		rap_vectors.append(rapModel.predict(np.array([rap_vectors[-1]]).flatten().reshape(1, 2, 2)))

	return rap_vectors

def vectors_into_song(vectors, generated_lyrics, rhyme_list):
	def last_word_compare(rap, line2):
		penalty = 0
		for line1 in rap:
			word1 = line1.split(" ")[-1]
			word2 = line2.split(" ")[-1]

			while word1[-1] in "?!,. ":
				word1 = word1[:-1]

			while word2[-1] in "?!,. ":
				word2 = word2[:-1]

			if word1 == word2:
				penalty += 0.2

		return penalty

	def calculate_score(vector_half, syllables, rhyme, penalty):
		desired_syllables = vector_half[0]
		desired_rhyme = vector_half[1]
		desired_syllables = desired_syllables * ms
		desired_rhyme = desired_rhyme * len(rhyme_list)

		score = 1.0 - (abs((float(desired_syllables) - float(syllables))) + abs((float(desired_rhyme) - float(rhyme)))) - penalty

		return score

	dataset = []
	for line in generated_lyrics:
		line_list = [line, syllables(line), rhyme(line, rhyme_list)]
		dataset.append(line_list)

	rap = []

	vector_halves = []

	for vector in vectors:
		vector_halves.append(list(vector[0][0]))
		vector_halves.append(list(vector[0][1]))





	for vector in vector_halves:
		scorelist = []
		for item in dataset:
			line = item[0]

			if len(rap) != 0:
				penalty = last_word_compare(rap, line)
			else:
				penalty = 0
			total_score = calculate_score(vector, item[1], item[2], penalty)
			score_entry = [line, total_score]
			scorelist.append(score_entry)

		fixed_score_list = []
		for score in scorelist:
			fixed_score_list.append(float(score[1]))
		max_score = max(fixed_score_list)
		for item in scorelist:
			if item[1] == max_score:
				rap.append(item[0])
				print str(item[0])

				for i in dataset:
					if item[0] == i[0]:
						dataset.remove(i)
						break
				break
	return rap

def train(x_data, y_data, rapModel):
	rapModel.fit(np.array(x_data), np.array(y_data),
			  batch_size=2,
			  epochs=5,
			  verbose=1)
	rapModel.save_weights(rapper + ".rap")

def main(d, train):
	rapModel = create_network(d)
	text_file = "lyrics.txt"
	textM = markov(text_file)

	if train == True:
		bars = split_lyrics_file(text_file)

	if train == False:
		bars = generate_lyrics(textM, text_file)

	rhyme_list = rhymeindex(bars)
	if train == True:
		x_data, y_data = build_dataset(bars, rhyme_list)
		train(x_data, y_data, rapModel)

	if train == False:
		vectors = compose_rap(bars, rhyme_list, text_file, rapModel)
		rap = vectors_into_song(vectors, bars, rhyme_list)
		f = open(f, "w")
		for bar in rap:
			f.write(bar)
			f.write("\n")

main(d, train)
