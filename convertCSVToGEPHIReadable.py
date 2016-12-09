# -*- coding: utf-8 -*-
from subprocess import call
from itertools import combinations 
import csv 
import sys 

def getTotalWeight(lines): 
	total = 0 
	for i, line in enumerate(lines):
		if i == 0: 
			continue 
		elems = line.split(',')
		count = elems[2]
		total = total + int(count) 
	return total 

def createFile(filename): 
	f = open(filename, 'r')
	lines = f.readlines() 
	f.close() 
	filename2 = "GEPHI/" + filename[:-4] + "_G.csv"
	f2 = open(filename2, 'w')

	totalWeight = getTotalWeight(lines)

	fields = ('Source', 'Target', 'count', 'Type', 'Weight')
	wr = csv.DictWriter(f2, fieldnames=fields, lineterminator = '\n')
	wr.writeheader()

	for i, line in enumerate(lines): 
		if i == 0: #header 
			continue 
		elems = line.split(',')
		src, dst, count = elems[0], elems[1], elems[2]
		count = int(count)
		weight = int(count) / float(totalWeight)
		wr.writerow({'Source':src, 'Target': dst, 'count':str(count), 'Type': 'Undirected', 'Weight': str(weight)})

	f2.close() 

createFile(sys.argv[1])