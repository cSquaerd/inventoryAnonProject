import csv
import csvHelper as helper
import random

# Load in a CSV File using a DictReader from the standard library csv module
def loadDataset(filename : str) -> list:
	file = open(filename, 'r')
	dia = csv.Sniffer().sniff(file.read(1024)); file.seek(0)
	data = list(csv.DictReader(file, dialect = dia))
	file.close()

	return data

# Produce a subset with beta% (< 100%) of the original dataset
def betaSample(dataset : list, beta : float) -> list:
	return random.sample(dataset, int(round(len(dataset) * beta)))

# Generalization map for particular generalizable attributes
generMapGames = {
	"Genre": {
		"Adventure": "Quest",
		"Platformer": "Quest",
		"Platventure": "Quest",
		"RPG": "Quest",
		"Fighting": "Action",
		"Shooter": "Action",
		"Strategy": "Action",
		"Puzzle": "Fun",
		"Racing": "Fun",
		"Sports": "Fun"
	},
	"Release Year": {
		"1980": "80s",
		"1981": "80s",
		"1982": "80s",
		"1983": "80s",
		"1984": "80s",
		"1985": "80s",
		"1986": "80s",
		"1987": "80s",
		"1988": "80s",
		"1989": "80s",
		"1990": "90s",
		"1991": "90s",
		"1992": "90s",
		"1993": "90s",
		"1994": "90s",
		"1995": "90s",
		"1996": "90s",
		"1997": "90s",
		"1998": "90s",
		"1999": "90s"
	}
}

# k-Anonymize a single row, supressing all columns not in keys,
# and optionally generalizing certain keys
def tuplizeData(
	instance : dict, keys : list,
	generalize : bool = False, generMaps : dict = None
) -> tuple:
	return tuple(
		[
			instance[k]
			if not (generalize and k in generMaps.keys())
			else generMaps[k][instance[k]]
			for k in keys
		]
	)

# Calculate the unique set of rows under a given k-Anonymization keyset
def getAnonTuples(
	dataset : list, keys : list, sortKey : int = 0,
	generalize : bool = False, generMaps : dict = None
) -> list:
	return sorted(
		list(
			set([
				tuplizeData(d, keys, generalize, generMaps)
				for d in dataset
			])
		),
		key = lambda t : t[sortKey]
	)

# Calculate the k value under a given keyset
def getKLevel(
	dataset : list, keys : list,
	generalize : bool = False, generMaps : dict = None
) -> int:
	allKAnonTuples = [tuplizeData(d, keys, generalize, generMaps) for d in dataset]
	return min([
		allKAnonTuples.count(t)
		for t in getAnonTuples(dataset, keys, 0, generalize, generMaps)
	])

# Calculate a proportion of how many rows constitute the dataset
# that match exact values across a set of keys
# (aka how many copies under k-Anonymization are present as a ratio)
# Now with support for optional generalization
def kaGetProb(
	dataset : list, keys : list, values : list,
	generalize : bool = False, generMaps : dict = None
) -> float:
	if len(keys) != len(values):
		print("Error: mismatch in corresponding keys and values!")
		return 0.

	count = 0
	for d in dataset:
		mismatched = False
		for k in range(len(keys)):
			if (
				d[keys[k]] != values[k] and (
					not generalize or \
					keys[k] not in generMaps.keys()
				)
			) or (
				generalize and keys[k] in generMaps.keys() and \
				generMaps[keys[k]][d[keys[k]]] != values[k]
			):
				mismatched = True
				break
		
		if not mismatched:
			count += 1

	return count / len(dataset)

# Calculate all proportions under a given keyset
def computeProbs(
	dataset : list, keys : list, sortKey : int = 0,
	generalize : bool = False, generMaps : dict = None
) -> dict:
	tuples = getAnonTuples(dataset, keys, sortKey, generalize, generMaps)
	return {t : kaGetProb(dataset, keys, t, generalize, generMaps) for t in tuples}

# Scammer Algorithm:
# Try to guess whether every superset game is in the curated set;
# Scammer only has access to a sampled, k-Anonymized subset of curated;
# Scammer flips a coin per game in superset, and either:
# Guesses proportionally randomly (size of curated over size of superset)
# or Guesses with statistics computed from the subset;
# High accuracy is undesireable from a curator's perspective
def guessTupleInclusion(
	dataSuperset : list, dataset : list, dataSampled : list,
	keys : list, alwaysRandom : bool = False, doDebugPrint : bool = False,
	generalize : bool = False, generMaps : dict = None
) -> dict:
	randPropThresh = len(dataset) / len(dataSuperset)

	superProbs = computeProbs(dataSuperset, keys, 0, generalize, generMaps)
	probs = computeProbs(dataSampled, keys, 0, generalize, generMaps)

	correctTrue = 0
	guessesTrue = 0
	for d in dataSuperset:
		if alwaysRandom or random.random() < 0.5:
			if random.random() < randPropThresh:
				guess = True
			else:
				guess = False
		else:
			t = tuplizeData(d, keys, generalize, generMaps)
			if t in probs.keys() and probs[t] >= superProbs[t]:
				guess = True
			else:
				guess = False

		if guess:
			guessesTrue += 1
		if guess and d in dataset:
			correctTrue += 1

	retDict = {
		"sampleSize": len(dataSampled),
		"guessesForTrue": guessesTrue,
		"correctGuesses": correctTrue,
		"accuracy": correctTrue / guessesTrue
	}
	if doDebugPrint:
		print(retDict)
	
	return retDict

# For a dataset with a price attribute, calculate the sum of the price column
def calcTotalPrice(dataset : list, priceKey : str = "Price") -> int:
	try:
		gross = sum([int(d[priceKey]) for d in dataset])
		return gross
	except ValueError as v:
		print(v)
		return 0

# For a k-Anonymous dataset, calculate a candidate price;
# Either the min, max, or average of all prices in rows
# That satisfy all values across a set of keys
# (aka rows that match at under the given k-Anonymization)
def kaGetPrice(
	dataset : list, keys : list, values: list,
	mode : str = "min", priceKey : str = "Price",
	generalize : bool = False, generMaps : dict = None
) -> float:
	if len(keys) != len(values):
		print("Error: mismatch in corresponding keys and values!")
		return 0.

	prices = []
	for d in dataset:
		mismatched = False
		for k in range(len(keys)):
			if (d[keys[k]] != values[k]  and (
					not generalize or \
					keys[k] not in generMaps.keys()
				)
			) or (
				generalize and keys[k] in generMaps.keys() and \
				generMaps[keys[k]][d[keys[k]]] != values[k]
			):
				mismatched = True
				break

		if not mismatched:
			prices.append(d[priceKey])

	if mode == "min":
		return float(min(prices))
	elif mode == "max":
		return float(max(prices))
	else:
		return sum(prices) / len(prices)

# Appraiser Algorithm
# Like the Scammer, the Appraiser only has the superset and a subset of curated;
# However, no randomizaiton occurs, as Appraiser acts in good faith;
# Appraiser knows the beta value for the sampling of the subset, and uses
# statistics from the subset and superset to estimate the value of curated;
# Both underestimation and overestimation are undesireable
def guessAppraisal(
	dataSuperset : list, dataset : list,
	dataSampled : list, keys : list,
	doDebugPrint : bool = False,
	generalize : bool = False, generMaps : dict = None
) -> dict:
	scaleFactor = len(dataset) / len(dataSampled)
	if doDebugPrint:
		print("IN guessAppraisal\nKEYS:", keys)

	accumulator = 0.
	for d in dataSampled:
		t = tuplizeData(d, keys, generalize, generMaps)
		accumulator += kaGetPrice(
			dataSuperset, keys, t,
			generalize = generalize, generMaps = generMaps
		)
		if doDebugPrint:
			print(format(accumulator, " >8.2f"), t)

	return {
		"appraisal": accumulator * scaleFactor,
		"actual": calcTotalPrice(dataset)
	}

