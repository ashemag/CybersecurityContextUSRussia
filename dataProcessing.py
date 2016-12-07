# -*- coding: utf-8 -*-
from subprocess import call
from itertools import combinations 
import csv 
def keyWords(): 
	keyWordsList = []
	f = open('key_words.csv')
	lines = f.readlines() 
	f.close() 
	for i, line in enumerate(lines): 
		if i == 0: 
			continue
		if i == len(lines) - 1: 
			continue 
		word = line.split(',')[0]
		keyWordsList.append(word)
	return keyWordsList

def examineKeyWordGraphs(words):
	eng_files = set() 
	rus_files = set() 
	for word in words: 
		if "CYBER_ATTACK" in word: 
			continue 
		name1 = 'russian graphs/' + word + '_rus.csv'
		name2 = 'english graphs/' + word + '_eng.csv'
		rus_files.add(name1)
		eng_files.add(name2)
	return eng_files, rus_files 

def processFile(filename): 
	f = open(filename, 'r')
	lines = f.readlines() 
	f.close() 
	nodes = set() 
	edges = {}

	for i, line in enumerate(lines): 
		if i == 0: #header 
			continue 
		elems = line.split(',')
		src, dst, count = elems[0], elems[1], elems[2]
		nodes.add(src)
		nodes.add(dst)
		edges[(src, dst)] = count 
	# if word in nodes: 	
	# 	nodes.remove(word)
	return nodes, edges 

def preprocess(key, keywords): 
	d = {}
	if key == 'eng': 
		first = 'english graphs/'
		third = '_eng.csv'
	else: 
		first = 'russian graphs/'
		third = '_rus.csv'

	for word in keywords: 
		filename = first + word + third
		f = open(filename, 'r')
		lines = f.readlines()
		for line in lines: 
			if line != '\n' and line != 'a_name,b_name,count\n': 
				elems = line.split(',')
				nodeA, nodeB, count = elems[0], elems[1], elems[2]
				d[(nodeA, nodeB)] = count 
				d[(nodeB, nodeA)] = count
	return d 

def getNodePairs(nodes):
	print "Number of nodes: %d" % len(nodes)
	nodePairs = [",".join(map(str, comb)) for comb in combinations(nodes, 2)]
	print "Number of node pairs: %d" % len(nodePairs)
	return nodePairs

def automaticBigQuerySearches(nodes, centerNode, d):
	# examinedPairs = getLines()
	examinedPairs = set() 
	#add all relevant csv numbers to random file 
	nodePairs = getNodePairs(nodes) 
	n = len(nodePairs)
	print "Length of existing d: %d" % len(d)
	start = 0

	for i in range(start, n): 
		f = open('new.txt', 'a')
		print "================="
		print "At index: %d" % i 
		print "================="
		nodes = nodePairs[i]
		nodesarr = nodes.split(',')
		nodeA, nodeB = nodesarr[0], nodesarr[1]
		if nodeA != nodeB and nodeA != centerNode and nodeB != centerNode: 
			if ((nodeA, nodeB) in examinedPairs) or ((nodeB, nodeA) in examinedPairs): 
				continue 
			print nodeA, nodeB 
			examinedPairs.add((nodeA, nodeB))
			examinedPairs.add((nodeB, nodeA))
			inputA = '%' + nodeA + '%'
			inputB = '%' + nodeB + '%'
			if (nodeA, nodeB) in d: 
				print "In existing data!"
				f.write(d[(nodeA, nodeB)]) 
			else: 
				lang = '%' + 'srclc:rus%'
				## RUSSIAN QUERY 
				# x = """bq query --format csv "SELECT a.name, b.name, COUNT(*) as count
				# FROM (FLATTEN(
				# SELECT GKGRECORDID, UNIQUE(REGEXP_REPLACE(SPLIT(V2Themes,';'), r',.*', '')) name
				# FROM [gdelt-bq:gdeltv2.gkg] 
				# WHERE DATE>20151101000000 and DATE < 20161101000000 and V2Themes like '%s' and TranslationInfo like '%s'
				# ,name)) a
				# JOIN EACH (
				# SELECT GKGRECORDID, UNIQUE(REGEXP_REPLACE(SPLIT(V2Themes,';'), r',.*', '')) name
				# FROM [gdelt-bq:gdeltv2.gkg] 
				# WHERE DATE>20151101000000 and DATE < 20161101000000 and V2Themes like '%s' and TranslationInfo like '%s'
				# ) b
				# ON a.GKGRECORDID=b.GKGRECORDID
				# WHERE a.name<b.name
				# GROUP EACH BY 1,2
				# ORDER BY 3 DESC
				# LIMIT 1" """ % (inputA, lang, inputB, lang)

				x = """bq query --format csv "SELECT a.name, b.name, COUNT(*) as count
				FROM (FLATTEN(
				SELECT GKGRECORDID, UNIQUE(REGEXP_REPLACE(SPLIT(V2Themes,';'), r',.*', '')) name
				FROM [gdelt-bq:gdeltv2.gkg] 
				WHERE DATE>20151101000000 and DATE < 20161101000000 and V2Themes like '%s' 
				,name)) a
				JOIN EACH (
				SELECT GKGRECORDID, UNIQUE(REGEXP_REPLACE(SPLIT(V2Themes,';'), r',.*', '')) name
				FROM [gdelt-bq:gdeltv2.gkg] 
				WHERE DATE>20151101000000 and DATE < 20161101000000 and V2Themes like '%s' 
				) b
				ON a.GKGRECORDID=b.GKGRECORDID
				WHERE a.name<b.name
				GROUP EACH BY 1,2
				ORDER BY 3 DESC
				LIMIT 1" """ % (inputA, inputB)

				call(x, shell=True,stdout=f)
				print "Done with query!"

			f.close() 

def appendToFile(filename): 
	f = open(filename, 'a')
	f2 = open('new.txt', 'r')
	count = 0 
	lines = f2.readlines() 
	for line in lines: 
		if line != '\n' and line != 'a_name,b_name,count\n': 
			f.write(line)
			count = count + 1 
	print count 
	f.close()  
	f2.close() 

def getTotalWeight(edges): 
	total = 0 
	for pair in edges: 
		total = total + int(edges[pair]) 
	return total 

def createNewFile(filename, edges):
	filename = filename[:-3]
	filename = filename + "_processed.csv"
	f = open(filename, 'w')

	fields = ('Source', 'Target', 'count', 'Type', 'Weight')
	wr = csv.DictWriter(f, fieldnames=fields, lineterminator = '\n')
	wr.writeheader()

	totalWeight = getTotalWeight(edges)
	for pair in edges: 
		count = int(edges[pair])
		weight = count / float(totalWeight)
		wr.writerow({'Source':pair[0], 'Target': pair[1], 'count':edges[pair], 'Type': 'Undirected', 'Weight': str(weight)})
	f.close() 


def choose(n, k):
    """
    A fast way to calculate binomial coefficients by Andrew Dalke (contrib).
    """
    if 0 <= k <= n:
        ntok = 1
        ktok = 1
        for t in xrange(1, min(k, n - k) + 1):
            ntok *= n
            ktok *= t
            n -= 1
        return ntok // ktok
    else:
        return 0

def addEdgesWithExistingData(filename, d, typePercent): 
	nodes, edges = processFile(filename)
	beforeCount = len(edges)
	examined = set() 
	for nodeA in nodes: 
		for nodeB in nodes: 
			if nodeA == nodeB or (nodeA, nodeB) in examined or (nodeB, nodeA) in examined: 
				continue
			if (nodeA, nodeB) in edges or (nodeB, nodeA) in edges: 
				continue 
			
			examined.add((nodeA, nodeB))
			#see if pair is in d_eng 
			if (nodeA, nodeB) in d: 
				pair = (nodeA, nodeB)
				count = d[pair]
				edges[pair] = count 

	afterCount = len(edges)
	createNewFile(filename, edges)
	print "Before: %d, After: %d" % (beforeCount, afterCount)
	percent = afterCount / float(choose(len(nodes), 2)) * 100 
	print "Calculated %f percent of complete graph" % (percent) 
	typePercent.append(percent)

def updateData(eng_files, rus_files): 
	d_eng = preprocess('eng', keyWords())
	d_rus = preprocess('rus', keyWords())
	engPercent = []
	rusPercent = []
	for eng_file in eng_files: 
		print "On file: %s" % eng_file 
		addEdgesWithExistingData(eng_file, d_eng, engPercent)
	for rus_file in rus_files: 
		print "On file: %s" % rus_file 
		addEdgesWithExistingData(rus_file, d_rus, rusPercent)

	print "On average, English graphs added %f percent of edges out of all edges needed to form a complete graph" % (sum(engPercent) / float(len(engPercent)))
	print "On average, Russian graphs added %f percent of edges out of all edges needed to form a complete graph" % (sum(rusPercent) / float(len(rusPercent)))

	# value = files[fileKey]
	# nodes, centerNode = value[0], value[1]

	# automaticBigQuerySearches(nodes, centerNode, d) #can no longer do automatic big query searches, out of account $$$ 

	# print '=================='
	# print "Appending to file..."
	# print '=================='
	# appendToFile(fileKey)
	# print "Finished with file: %s" % (fileKey)

eng_files, rus_files = examineKeyWordGraphs(keyWords())
'''
Using complete graph of CYBER_ATTACK and information in every 
other graph of a language, add edges between nodes in each graph 
where we have that information stored 
'''
updateData(eng_files, rus_files)

