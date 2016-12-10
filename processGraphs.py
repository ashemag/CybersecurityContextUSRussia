#using python 2.7.x
import sys
sys.path.insert(0, '../')
from snap import *
import random 
import numpy as np 
import math 
from scipy.stats import kurtosis
from scipy.stats import skew
import csv 

########################################## PROCESS TEXT FILE #########################################

#Parses keywords file 
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

#Returns total edge counts 
def getCounts(edgeWeights): 
	examined = set() 
	counts = []
	for key in edgeWeights: 
		src, dst = key[0], key[1]
		if (src, dst) in examined: 
			continue 
		examined.add((src, dst))
		examined.add((dst, src))
		counts.append(int(edgeWeights[(src, dst)]))
	return counts

#parses through text file and creates graph, edgeWeights, IdMap, counts 
#edge weights is srcId, dstId 
def processFile(filename): 
	G = PUNGraph.New() 
	edgeWeights = {}
	IdMap = {}
	iterator = 0 
	f = open(filename, 'r')
	lines = f.readlines()
	f.close() 

	for i, line in enumerate(lines):
		if i == 0: 
			continue 
		elems = line.split(',')
		countStr = elems[2] 
		countStr = countStr[:-2]
		if countStr == '': #weird edge case 
			continue 
		src, dst = elems[0], elems[1]
		count = int(countStr)

		if src not in IdMap: #IdMap: name -> Id 
			IdMap[src] = iterator
			IdMap[str(iterator)] = src
			iterator = iterator + 1 
		if dst not in IdMap: 
			IdMap[dst] = iterator
			IdMap[str(iterator)] = dst 
			iterator = iterator + 1 

		srcId = IdMap[src]
		dstId = IdMap[dst]
		
		if G.IsNode(srcId) == False: 
			G.AddNode(srcId)
		if G.IsNode(dstId) == False: 
			G.AddNode(dstId)
		
		G.AddEdge(srcId, dstId)
		edgeWeights[(srcId, dstId)] = count 
		edgeWeights[(dstId, srcId)] = count 
		
	counts = getCounts(edgeWeights)
	return G, edgeWeights, IdMap, counts 

def createGraphs(words):
	print "Creating graphs..."
	s = {} 
	for word in words: 
		name1 = 'russian graphs/' + word + '_rus.csv'
		name2 = 'english graphs/' + word + '_eng.csv'
		G1, edgeWeights1, IdMap1, counts1 = processFile(name1)
		G2, edgeWeights2, IdMap2, counts2 = processFile(name2)

		processGraph(word + "_RUS", G1, counts1, edgeWeights1, IdMap1) 
		processGraph(word + "_ENG", G2, counts2, edgeWeights2, IdMap2) 

		if 'DIGITAL' in word: 
			print "Russian %s: %d" % (word, G1.GetNodes())
			print "English %s: %d" % (word, G2.GetNodes())

		s[word + "_RUS"] = (G1, edgeWeights1, IdMap1, word)
		s[word + "_ENG"] = (G2, edgeWeights2, IdMap2, word)

	print "Created %d graphs" % len(s)
	return s 

def getTotalWeight(G, edgeWeights): 
	total = 0 
	for edge in G.Edges(): 
		src, dst = edge.GetSrcNId(), edge.GetDstNId()
		count = edgeWeights[(src, dst)]
		total = total + int(count)
	return total 

#write processed version of graph to file 
def writeToFile(filename, G, idMap, edgeWeights): 
	print "Writing %s to file" % filename
	filename2 = "processedGraphCSVs/" + filename + "_proc.csv"
	f = open(filename2, 'w')
	fields = ('Source', 'Target', 'count', 'Type', 'Weight')
	wr = csv.DictWriter(f, fieldnames=fields, lineterminator = '\n')
	wr.writeheader()
	
	totalWeight = getTotalWeight(G, edgeWeights)

	for edge in G.Edges():
		src, dst = edge.GetSrcNId(), edge.GetDstNId()
		srcS = idMap[str(src)]
		dstS = idMap[str(dst)]
		count = edgeWeights[(src, dst)]
		weight = int(count) / float(totalWeight)
		wr.writerow({'Source':srcS, 'Target': dstS, 'count':str(count), 'Type': 'Undirected', 'Weight': str(weight)})
	f.close()

#Examine every edge that exists in the graph. If its count is < t, delete it 
def processGraph(filename, G, counts, edgeWeights, idMap): 
	t = math.floor(sum(counts) / float(len(counts)))
	for Edge in G.Edges(): 
		srcId, dstId = Edge.GetSrcNId(), Edge.GetDstNId() 
		count = edgeWeights[srcId, dstId]
		if count < t: 
			G.DelEdge(srcId, dstId)
	writeToFile(filename, G, idMap, edgeWeights)
############################################## FEATURE EXTRACTION / AGGREGATION ###############################################

#helper function 
def getNoNeighbors(node): 
	count = 0 
	for neighborId in node.GetOutEdges(): 
		count = count + 1
	return count 

#helper function 
def getAvgTwoHop(G, node): 
	dNeighbors = 0
	for neighborId in node.GetOutEdges(): 
		dNeighbors = dNeighbors + G.GetNI(neighborId).GetDeg() 
	if node.GetDeg() == 0: 
		return 0 
	return dNeighbors / float(node.GetDeg())

#helper function 
def getAvgNodeCC(G, node):
	cc = 0  
	for neighborId in node.GetOutEdges(): 
		cc = cc + GetNodeClustCf(G, neighborId)
	if node.GetDeg() == 0: 
		return 0 
	return cc / float(node.GetDeg())

#helper function 
def getNodeFeatures(G, m, centerNodeId): 
	for node in G.Nodes(): 
		nodeIdNo = node.GetId() 
		# if nodeIdNo == centerNodeId: No need to differentiate between centerNodeId for now *** 
		# 	continue 
		neighborNo = getNoNeighbors(node)
		nodeCC = GetNodeClustCf(G, nodeIdNo)
		avgTwoHop = getAvgTwoHop(G, node)
		avgNodeCC = getAvgNodeCC(G, node)
		f = [neighborNo, nodeCC, avgTwoHop, avgNodeCC]
		m.append(f)

#extracts features 
'''
features: 
1. number of neighbors 
2. clustering coefficient of node i 
3. average number of node i's two-hop away neighbors 
4. average clustering coefficient 
'''
def getFeatures(G, IdMap, centerNodeId): 
	featureMatrix = []
	getNodeFeatures(G, featureMatrix, centerNodeId)
	return featureMatrix 

#Iterates through features and returns a set of signature vectors 
# Returns matrix of median, mean, std, skew, kurtosis for each feature 
def aggregateFeatures(G, m, centerNode, IdMap): 
	sv = []
	neighborNo, nodeCC, avg2Hop, avgNodeCC = [], [], [], []
	for feat in m: 
		neighborNo.append(feat[0])
		nodeCC.append(feat[1])
		avg2Hop.append(feat[2])
		avgNodeCC.append(feat[3])

	features = [neighborNo, nodeCC, avg2Hop, avgNodeCC]
	
	#for each feature, add aggregators to sv   
	for feat in features: 
		sv.append(np.median(np.array(feat)))
		sv.append(np.mean(np.array(feat)))
		sv.append(np.std(np.array(feat)))
		sv.append(skew(feat))
		sv.append(kurtosis(feat))

	#add center node features
	centerNodeId = IdMap[centerNode]
	centerNodeObj = G.GetNI(centerNodeId)

	#get features 
	center_neighborCount = getNoNeighbors(centerNodeObj)
	center_nodeCC = GetNodeClustCf(G, centerNodeId)
	center_avgTwoHop = getAvgTwoHop(G, centerNodeObj)
	center_avgNodeCC = getAvgNodeCC(G, centerNodeObj)
	
	#append to sv 
	sv.append(center_neighborCount)
	sv.append(center_nodeCC)
	sv.append(center_avgTwoHop)
	sv.append(center_avgNodeCC)
	return sv 

def netSimile(graphs): #order is russian and then english 
	print "Starting net simile alg..."
	signatureVectors = {} 
	for i, key in enumerate(graphs): 	
		value = graphs[key]
		G, edgeWeights, IdMap, centerNode = value[0], value[1], value[2], value[3]
		m = getFeatures(G, IdMap, IdMap[centerNode])
		sv = aggregateFeatures(G, m, centerNode, IdMap)
		signatureVectors[key] = sv 
	return signatureVectors 
############################################## DISTANCE FUNCTION ###############################################

def evaluate(signatureVectors, keywords): 
	print "Evaluating distances..."

	allDistances = []
	for word in keywords: 
		rus = word + "_RUS"
		eng = word + "_ENG"
		svRus = signatureVectors[rus]
		svEng = signatureVectors[eng]
		d1 = getDistance(svRus, svEng) 
		allDistances.append([word, d1])

	allDistances = sorted(allDistances, key=lambda x: x[1],reverse=False)
	vals = []
	for d in allDistances: 
		vals.append(d[1])
	
	median = vals[len(vals) / 2]
	mean = sum(vals) / len(vals)
	print allDistances 
	print "Median: %d, Mean: %f" %(median, mean)

#Canberra distance function 
def getDistance(sv1, sv2): 
	d = 0

	for i in range(24): 
		elem1 = sv1[i]
		elem2 = sv2[i]
		if elem1 + elem2 != 0: #avoid the divide by 0 case
			d = d + abs(elem1 - elem2) / float(elem1 + elem2)
	return d 

def getDistanceContribution(sv1, sv2):
	d = 0 
	for i in range(len(sv1)): 
		elem1 = sv1[i]
		elem2 = sv2[i]
		if elem1 + elem2 != 0: #avoid the divide by 0 case
			d = d + abs(elem1 - elem2) / float(elem1 + elem2)
	return d 

#network distance analyis 
#find which feature is driving network distance 
def analysis(signatureVectors, keywords):
	features = [0, 0, 0, 0, 0]
	for word in keywords: 
		rus = word + "_RUS"
		eng = word + "_ENG"
		svRus = signatureVectors[rus]
		svEng = signatureVectors[eng]

		neighborNo = getDistanceContribution(svRus[0:5], svEng[0:5])
		nodeCC = getDistanceContribution(svRus[5:11], svEng[5:11])
		avg2Hop = getDistanceContribution(svRus[10:15], svEng[10:15])
		avgNodeCC = getDistanceContribution(svRus[15:20], svEng[15:20])
		centerNode = getDistanceContribution(svRus[20:], svEng[20:])

		featuresVals = [neighborNo, nodeCC, avg2Hop, avgNodeCC, centerNode]
		for i in range(len(features)): 
			features[i] = features[i] + featuresVals[i]

	featureKey = ["Number of Neighbors", "Node Clustering Coefficients", "Average Two Hop Number of Neighbors", "Average Node Clustering Coefficient", "Center Node Features"]
	output = []
	for i, elem in enumerate(features): 
		if i == 3: 
			continue 
		output.append([featureKey[i], features[i]])
		print "Contribution of %s: %d" % (featureKey[i], features[i])
	print output 
############################################## DRIVER ###############################################
key_words = keyWords() 
graphs = createGraphs(key_words)
# print len(graphs) 
signatureVectors = netSimile(graphs) 
# print len(signatureVectors)
evaluate(signatureVectors, key_words)
analysis(signatureVectors, key_words)
