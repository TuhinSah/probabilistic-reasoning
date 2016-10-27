import sys, copy, decimal, itertools

def splitQuery(query, start):
	query = query[start:-1].split(' | ')
	query[0] = query[0].split(', ')
	for i, q in enumerate(query[0]):
		query[0][i] = query[0][i].split(' = ')
	if len(query) > 1:
		query[1] = query[1].split(', ')
		for i, q in enumerate(query[1]):
			query[1][i] = query[1][i].split(' = ')
	return query

def calculateUtility(probabilities, utilities, variables, indices, query, ncolumns):
	binRow = ['' for x in range(ncolumns)]
	for q in query[0]:
		binRow[indices[q[0]]] = getBits(q[1])
	if len(query) > 1:
		for q in query[1]:
			binRow[indices[q[0]]] = getBits(q[1])
	d = calculateProbability(probabilities, variables, indices, binRow, ncolumns, 0)
	util = 0
	for row in [' '.join(x) for x in itertools.product('+-', repeat=len(utilities[0]))]:
		if len(set([q[0] for q in query[0]]) & set(utilities[0])) == 0\
		or all(row.split()[utilities[0].index(q[0])] is q[1] for q in query[0] if q[0] in utilities[0]):
			for i,y in enumerate(row.split()):
				binRow[indices[utilities[0][i]]] = getBits(y)
			n = calculateProbability(probabilities, variables, indices, binRow, ncolumns, 0)
			for u in utilities[1:]:
				if row in u:
					util = util + (n/d * float(u.split()[0]))
					break
	return util

def calculateProbability(probabilities, variables, indices, binRow, ncolumns, col):
	if binRow[col] == '':
		if col == ncolumns - 1:
			return 1.0
		else:
			binRow1 = copy.deepcopy(binRow)
			binRow1[col] = '1'
			binRow0 = copy.deepcopy(binRow)
			binRow0[col] = '0'
			return calculateProbability(probabilities, variables, indices, binRow1, ncolumns, col) +\
			calculateProbability(probabilities, variables, indices, binRow0, ncolumns, col)

	for idx, probability in enumerate(probabilities):
		if isinstance(probability, list):
			if probability[0] == variables[col]:
				offset = 1
				if len(probability) > 1:
					perm = ''
					ngivens = len(probability[1])
					for i,given in enumerate(probabilities[idx][1]):
						if binRow[indices[given]] is not '1':
							offset = offset + 2**(ngivens - i - 1)
							perm = perm + '- '
						else:
							perm = perm + '+ '
					perm = perm.rstrip()
					for p in probabilities[idx + 1 : idx + 2**ngivens + 1]:
						if perm in p:
							prob = float(p.split()[0])
							break
				else:
					prob = float(probabilities[idx + 1].split()[0])
				index = idx
				break
	if col == ncolumns - 1:
		if binRow[col] is '1':
			return prob
		elif binRow[col] is '0':
			return 1.0 - prob
	else:
		if binRow[col] is '1':
			return prob * calculateProbability(probabilities, variables, indices, binRow, ncolumns, col + 1)
		elif binRow[col] is '0':
			return (1.0 - prob) * calculateProbability(probabilities, variables, indices, binRow, ncolumns, col + 1)

if __name__ == '__main__':
	queries = []
	probabilities = []
	utilities = []

	with open(sys.argv[-1], 'r') as file:
		line = file.readline().rstrip()

		while line != "******":
			queries.append(line)
			line = file.readline().rstrip()

		for line in iter(lambda: file.readline().rstrip(), ''):
			if line == "******":
				break
			if line != "***":
				probabilities.append(line)

		for line in iter(lambda: file.readline().rstrip(), ''):
			if line != "***":
				utilities.append(line)

	output = open('output.txt','w')

	variables = []
	indices = {}

	i = 0
	for idx, probability in enumerate(probabilities):
		if not probability[0].isdigit():
			if probability == "decision":
				probabilities[idx] = '0.5'
			else:
				probabilities[idx] = probability.split(' | ')
				if probabilities[idx][0] not in variables:
					variables.append(probabilities[idx][0])
					indices[probabilities[idx][0]] = i
					i = i + 1
				if len(probabilities[idx]) > 1:
					probabilities[idx][1] = probabilities[idx][1].split()
					for x in probabilities[idx][1]:
						if x not in variables:
							variables.append(x)
							indices[x] = i
							i = i + 1

	for idx, utility in enumerate(utilities):
		if utility[0].isalpha():
			utilities[idx] = utility.split(' | ')[1].split()

	ncolumns = len(variables)
	nrows = 2**ncolumns

	getBits = lambda t: '1' if t is '+' else '0'
	for idx, query in enumerate(queries):
		if (query[0] is 'P'):
			query = splitQuery(query, 2)
			binRow = ['' for x in range(ncolumns)]
			if len(query) is 1:
				for q in query[0]:
					binRow[indices[q[0]]] = getBits(q[1])
				prob = decimal.Decimal(str(calculateProbability(probabilities, variables, indices, binRow, ncolumns, 0)))
				output.write(str(decimal.Decimal(prob.quantize(decimal.Decimal('.01'), rounding=decimal.ROUND_HALF_UP))) + '\n')
			else:
				for q in query[1]:
					binRow[indices[q[0]]] = getBits(q[1])
				d = calculateProbability(probabilities, variables, indices, binRow, ncolumns, 0)
				for q in query[0]:
					binRow[indices[q[0]]] = getBits(q[1])
				n = calculateProbability(probabilities, variables, indices, binRow, ncolumns, 0)
				prob = decimal.Decimal(str(n/d))
				output.write(str(decimal.Decimal(prob.quantize(decimal.Decimal('.01'), rounding=decimal.ROUND_HALF_UP))) + '\n')
		elif (query[0] is 'E'):
			query = splitQuery(query, 3)
			output.write(str(int(round(calculateUtility(probabilities, utilities, variables, indices, query, ncolumns)))) + '\n')
		else:
			query = splitQuery(query, 4)
			for q in query[0]:
				q.append('')
			meu = decimal.Decimal('-Infinity')
			meuperm = ''
			for perm in [' '.join(x) for x in itertools.product('+-', repeat=len(query[0]))]:
				for i,q in enumerate(query[0]):
					q[1] = perm.split()[i]
				util = calculateUtility(probabilities, utilities, variables, indices, query, ncolumns)
				if util > meu:
					meu = util
					meuperm = perm
			output.write(meuperm + ' ' + str(int(round(meu))) + '\n')