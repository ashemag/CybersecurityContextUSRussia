import sys
sys.path.insert(0, '../')
from snap import *
import random 
import numpy as np 
import math 
from scipy.stats import kurtosis
from scipy.stats import skew

########################################## PROCESS TEXT FILE #########################################

#Parses keywords file 
def keyWords(): 
	keyWordsList = []
	f = open('total word search/results-20161106-145517.csv')
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
	s = {} 
	for word in words: 
		name1 = 'russian graphs/' + word + '_rus.csv'
		name2 = 'english graphs/' + word + '_eng.csv'
		G1, edgeWeights1, IdMap1, counts1 = processFile(name1)
		G2, edgeWeights2, IdMap2, counts2 = processFile(name2)
		
		# processGraph(G1, counts1, edgeWeights1, IdMap1) 
		processGraph(G2, counts2, edgeWeights2, IdMap2) 
		exit() 
		s[word + "_RUS"] = (G1, edgeWeights1, IdMap1, word)
		s[word + "_ENG"] = (G2, edgeWeights2, IdMap2, word)

		break 
	return s 

def writeToFile(G, idMap, edgeWeights): 
	f = open("proc.csv", 'w')
	for edge in G.Edges():
		src, dst = edge.GetSrcNId(), edge.GetDstNId()
		srcS = idMap[str(src)]
		dstS = idMap[str(dst)]
		count = edgeWeights[(src, dst)]
		f.write(srcS + ',' + dstS + ',' + str(count) + '\n')
	f.close()

#Examine every edge that exists in the graph. If its count is < t, delete it 
def processGraph(G, counts, edgeWeights, idMap): 
	t = math.floor(sum(counts) / float(len(counts)))
	for Edge in G.Edges(): 
		srcId, dstId = Edge.GetSrcNId(), Edge.GetDstNId() 
		count = edgeWeights[srcId, dstId]
		if count < t: 
			G.DelEdge(srcId, dstId)
	writeToFile(G, idMap, edgeWeights)
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
def aggregateFeatures(m): 
	sv = []
	for feat in m: 
		feat2 = np.array(feat)
		sv.append(np.median(feat2))
		sv.append(np.mean(feat2))
		sv.append(np.std(feat2))
		sv.append(skew(feat))
		sv.append(kurtosis(feat))
		# feat2= np.array(feat)
		# sf = [np.median(feat2), np.mean(feat2), np.std(feat2), skew(feat), kurtosis(feat)]
		# signatureVectors.append(sf)
	#[median, mean, std, skew, kurtosis]	
	return sv

def netSimile(graphs): #order is russian and then english 
	signatureVectors = {} 
	for i, key in enumerate(graphs): 	
		value = graphs[key]
		G, edgeWeights, IdMap, centerNode = value[0], value[1], value[2], value[3]
		m = getFeatures(G, IdMap, IdMap[centerNode])
		sv = aggregateFeatures(m)
		signatureVectors[key] = sv 
	return signatureVectors 
############################################## DISTANCE FUNCTION ###############################################

def evaluate(signatureVectors): 
	pairs = []
	for key in signatureVectors: 
		pairs.append(key)
	n = len(pairs)
	print n 
	print pairs 
	for i in range(0, n, 2):
		print i   
		rus = pairs[i]
		eng = pairs[i + 1]
		svRus = signatureVectors[rus]
		svEng = signatureVectors[eng]
		d1 = getDistance(svRus, svEng) 
		print "Distance: %d" % d1  
		exit() 

#Canberra distance function 
def getDistance(sv1, sv2): 
	n = len(sv1) if len(sv1) < len(sv2) else len(sv2)
	d = 0 
	for i in range(n): 
		elem1, elem2 = sv1[i], sv2[i]
		if elem1 > 0 or elem2 > 0: 
			d = d + abs(elem1 - elem2) / float(elem1 + elem2)
	return d 


############################################## DRIVER ###############################################
graphs = createGraphs(keyWords())
# print len(graphs) 
signatureVectors = netSimile(graphs) 
# print len(signatureVectors)
evaluate(signatureVectors)
