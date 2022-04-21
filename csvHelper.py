import csv
# Used to combine the NES and SNES games into one big list
def loadFiles(
	filenames : list, consoles: list,
	sortKeys : list = ["Developer(s)", "Release Year"],
	filterUnreleased : bool = True, doPrint : bool = False
) -> list:
	if len(filenames) != len(consoles):
		print("Error: length mismatch of filenames and game console names!")
		return []

	games = []
	for i in range(len(filenames)):
		if doPrint:
			print("Now loading", filenames[i])
		csvFile = open(filenames[i], 'r')
		
		dia = csv.Sniffer().sniff(csvFile.read(1024))
		csvFile.seek(0)
		
		newGames = list(csv.DictReader(csvFile, dialect = dia))
		
		if filterUnreleased:
			if doPrint:
				print("Filtering out unreleased games from", filenames[i])
			newGames = [g for g in newGames if g["Release Year"].isnumeric()]

		if doPrint:
			print("Setting console field for each game from", filenames[i])
		for n in newGames:
			n["Platform"] = consoles[i]

		if doPrint:
			print()

		games += newGames
	
	for k in sortKeys:
		if doPrint:
			print("Sorting final list by", k)
		games = sorted(games, key = lambda g : g[k])

	return games

# Write out the file once processing is finished;
# Use semicolon as the delimiter since some fields will use commas in their string
def writeNewFile(games : list, filename : str):
	csv.register_dialect("semi", delimiter = ';')
	dia = csv.get_dialect("semi")
	file = open(filename, 'w')

	printer = csv.DictWriter(file, games[0].keys(), dialect = dia)
	printer.writeheader()

	for g in games:
		printer.writerow(g)

	file.close()
	print("Wrote games to", filename)

# Useful for printing a whole table of games
def gameToString(game : dict, titleLen : int = 64, devLen : int = 36) -> str:
	s = "[ '" + game["Release Year"][-2:] + ", "
	s += format(game["Platform"], " ^6s") + "] "
	if "Genre" in game.keys():
		s += '[' + format(game["Genre"], " ^16s") + "] "
	if "Price" in game.keys():
		s += '(' + format(game["Price"], " ^4s") + ") "
	s += format(game["Title"], " ^" + str(titleLen) + 's') + ' '
	s += '(' + format(game["Developer(s)"], " ^" + str(devLen) + 's') + ")"

	return s

# Runs the above function across a whole list
def printGames(games : list):
	for g in games:
		print(gameToString(g))

# Perform a grep-like operation on a single column to look for certain games
def filterGames(games : list, key : str, subString : str) -> list:
	return [g for g in games if subString in g[key]]

# Ease-of-use function for adding the genre column
def addGenres(
	games : list, genres : list = [
		"Platformer",
		"Adventure",
		"Platventure",
		"Shooter",
		"Fighting",
		"Puzzle",
		"Racing",
		"RPG",
		"Sports",
		"Strategy"
	]
) -> list:
	genredGames = []
	for g in games:
		decided = False
		while not decided:
			print(gameToString(g), '\n')
			for i in range(len(genres)):
				print(format(i, " >2d") + '.', genres[i])

			try:
				choice = int(input("\nSelect a genre for the above game: "))
				if choice < 0 or choice >= len(genres):
					print("Error: bad index! Select again...\n")
				else:
					g["Genre"] = genres[choice]
					genredGames.append(g)
					decided = True
			except ValueError as v:
				print(v, "Select again...\n")
	
	return genredGames

# Ease-of-use for adding the price column
def addPrices(games : list):
	pricedGames = []
	for g in games:
		priced = False
		while not priced:
			print(gameToString(g), '\n')

			try:
				price = int(
					input("Enter a price (in whole dollars) for the above game: ")
				)
				g["Price"] = price
				pricedGames.append(g)
				priced = True
			except ValueError as v:
				print(v, "Enter again...")
	
	return pricedGames

