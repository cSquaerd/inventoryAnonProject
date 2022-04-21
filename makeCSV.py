from lxml import etree
import sys
# Read in an HTML file with just a <table> element and use etree to parse it
def parseTable(filename : str) -> etree.Element:
	try:
		docFile = open(filename, 'r')
		doc = docFile.read()
		docFile.close()
		return etree.HTML(doc).find("body/table")
	except FileNotFoundError as e:
		print(e)
		return None

# Extract various columns from the parsed table by number (contained in cols arg)
# For this experiment, the needed columns are the same on the NES and SNES tables
def toCSV_selectiveCols(table : etree.Element, cols : list):
	result = "Title;Developer(s);Publisher(s);Release Year\n"

	for row in table:
		col = 0
		row = [row[i] for i in cols]
		for el in row:
			col += 1
			#print(el, el.tag)
			while len(el) > 0 and (el.text is None or len(el.text.strip()) == 0):
				el = el[0]
				#print(el, el.tag)
			if col != len(cols):
				result += el.text.strip() + ';'
			else:
				result += el.text.strip()[-4:] + '\n'

	return result

# Command line handling
if __name__ == "__main__":
	if len(sys.argv) == 3:
		inFilename = sys.argv[1]
		outFilename = sys.argv[2]
	else:
		print("Error: Bad args!\nUsage:\n\tpython makeCSV.py [html file with table] [.csv filename]")
		exit(-1)

	outFile = open(outFilename, "w")
	outFile.write(toCSV_selectiveCols(parseTable(inFilename)[1], [0, 1, 2, 4]))
	outFile.close()
	print("Wrote new file at", outFilename)

