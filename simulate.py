import sampling
import numpy as np
import pickle
import sys
np.set_printoptions(linewidth = 96, precision = 4)

# Perform many randomized scammer attacks,
# returning the average accuracy
def singleSim(
	allGames : list, games : list, sample : list,
	keys : list, reruns : int,
	fullRandom : bool = False,
	debugPrint : bool = False,
	generalize : bool = False, generMaps : dict = None
) -> float:
	return sum(
		[
			sampling.guessTupleInclusion(
				allGames, games, sample, keys,
				fullRandom, debugPrint,
				generalize, generMaps
			)["accuracy"]
			for x in range(reruns)
		]
	) / reruns

def simulate(
	allGames : list, games : list,
	samples : int, reruns : int,
	resultsBasename : str,
	betas : np.array = np.linspace(0.25, 0.75, 11),
	debugPrint : bool = False
):
	nonAnonTuples = [
		["Genre"],
		["Genre"],
		["Developer(s)"],
		["Publisher(s)"],
		["Release Year"],
		["Release Year"],
		["Platform"],
		["Genre", "Release Year"],
		["Genre", "Release Year"],
		["Genre", "Developer(s)"],
		["Genre", "Developer(s)"],
		["Genre", "Developer(s)", "Publisher(s)"],
		["Genre", "Developer(s)", "Publisher(s)"],
		["Genre", "Developer(s)", "Platform"],
		["Genre", "Developer(s)", "Platform"],
		["Genre", "Developer(s)", "Release Year"],
		["Genre", "Developer(s)", "Release Year"],
		["Genre", "Developer(s)", "Release Year", "Platform"],
		["Genre", "Developer(s)", "Release Year", "Platform"]
	]
	generalizeFlags = [
		False,
		True,
		False,
		False,
		False,
		True,
		False,
		False,
		True,
		False,
		True,
		False,
		True,
		False,
		True,
		False,
		True,
		False,
		True,
	]

	groupName = lambda l, g : ("Gener. " if g else '') + ''.join([s[:2] for s in l])
	groupNameVerbose = lambda l, g : ', '.join(l) + (" (Genericized)" if g else '')
	allAccuracies = np.zeros((betas.shape[0], len(nonAnonTuples) + 1), np.float64)
	allAppraisals = np.zeros((betas.shape[0], len(nonAnonTuples)), np.float64)
	allK = np.zeros((betas.shape[0], len(nonAnonTuples)), np.int16)
	
	for beta in betas:
		print("Beta:", format(beta, " ^6.2f"))
		accuracyAccumulator = np.zeros(len(nonAnonTuples) + 1, np.float64)
		appraisalAccumulator = np.zeros(len(nonAnonTuples), np.float64)
		kAccumulator = np.zeros(len(nonAnonTuples), np.int16)

		for s in range(samples):
			print("\tSample", s)
			sample = sampling.betaSample(games, beta)

			print(
				"\t\t" + ' ' * 16 + \
				format("Scammer", " ^8s") + \
				format("Appraiser", " ^12s") + \
				format("k-Level", " ^8s")
			)

			accu = singleSim(
				allGames, games, sample, nonAnonTuples[0], reruns, True, debugPrint
			)
			accuracyAccumulator[0] += accu
			print(
				"\t\t" + format("Control:", " >16s"), format(accu, " ^8.4f")
			)

			for l in range(len(nonAnonTuples)):
				accu = singleSim(
					allGames, games, sample, nonAnonTuples[l], reruns,
					False, debugPrint, generalizeFlags[l], sampling.generMapGames
				)
				accuracyAccumulator[l + 1] += accu
			
				appraisalResult = sampling.guessAppraisal(
					allGames, games, sample, nonAnonTuples[l], debugPrint,
					generalizeFlags[l], sampling.generMapGames
				)
				appraisal = appraisalResult["appraisal"] / appraisalResult["actual"]
				appraisalAccumulator[l] += appraisal

				k = sampling.getKLevel(
					sample, nonAnonTuples[l],
					generalizeFlags[l], sampling.generMapGames
				)
				kAccumulator[l] += k

				print(
					"\t\t" + format(groupName(nonAnonTuples[l], generalizeFlags[l]) + ':', " >16s"),
					format(accu, " ^8.4f") + format(appraisal, " ^8.4f"), format(k, " >8d"),
					flush = True
				)
			print()

		accuracyAccumulator /= samples
		appraisalAccumulator /= samples
		kAccumulator = kAccumulator // samples

		allAccuracies[betas.tolist().index(beta)] = accuracyAccumulator
		allAppraisals[betas.tolist().index(beta)] = appraisalAccumulator
		allK[betas.tolist().index(beta)] = kAccumulator

		print("\tAverage Accuracy across Samples:")
		print(
			"\t" + ' ' * 16 + \
			format("Scammer", " ^8s") + \
			format("Appraiser", " ^12s") + \
			format("k-Level", " ^8s")
		)
		for i in range(len(nonAnonTuples) + 1):
			print(
				"\t" + format(
					(
						"Control" if i == 0
						else groupName(nonAnonTuples[i - 1], generalizeFlags[i - 1])
					) + ':',
					" >16s"
				), format(accuracyAccumulator[i], " ^8.4f") + \
				(
					'' if i < 1 else
					format(appraisalAccumulator[i - 1], " ^8.4f") + \
					format(kAccumulator[i - 1], " >8d")
				)
			)

		print(20 * '-')
		print(flush = True)

	betasFilename = resultsBasename + "_betas.dat"
	accuFilename = resultsBasename + "_accuracies.dat"
	apprFilename = resultsBasename + "_appraisals.dat"
	kFilename = resultsBasename + "_k.dat"

	betasFile = open(betasFilename, "wb")
	accuFile = open(accuFilename, "wb")
	apprFile = open(apprFilename, "wb")
	kFile = open(kFilename, "wb")

	pickle.dump(betas, betasFile)
	pickle.dump(allAccuracies, accuFile)
	pickle.dump(allAppraisals, apprFile)
	pickle.dump(allK, kFile)

	betasFile.close()
	accuFile.close()
	apprFile.close()
	kFile.close()

	print("k-Anonymization Levels per Attribute Group in Curated Set:")
	for i in range(len(nonAnonTuples)):
		l = nonAnonTuples[i]
		print(
			sampling.getKLevel(
				games, l, generalizeFlags[i], sampling.generMapGames
			), ':', groupNameVerbose(l, generalizeFlags[i])
		)
	
	print("Saved the beta values, average accuracies, average appraisals, and average k-levels to pickle files.")
	print(betas)
	print()
	print(allAccuracies)
	print()
	print(allAppraisals)
	print()
	print(allK)

if __name__ == "__main__":
	try:
		if len(sys.argv) < 4:
			print("Error: need reruns, samples, and results base filename as command line args!")
			exit(-1)

		reruns = int(sys.argv[1])
		samples = int(sys.argv[2])
		resultsBasename = sys.argv[3]
		
		doDebug = False
		if len(sys.argv) >= 5:
			if "debug" in sys.argv[4]:
				doDebug = True

	except ValueError as v:
		print("Error: Arg Parsing Failed!", v)
		exit(-1)

	print("Now running with", samples, "samples and", reruns, "reruns per sample.")
	
	allGames = sampling.loadDataset("gamesChosen.csv")
	games = sampling.loadDataset("gamesCollection.csv")
	simulate(allGames, games, samples, reruns, resultsBasename, debugPrint = doDebug)

