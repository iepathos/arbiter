#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Arbiter finds arbitrage opportunities in data sets.
#
#	arbiter = Arbiter()
#	arbiter.getBestPolygonFromPermutate( \
#				permutateRatesAroundEdge( \
#					findOpportunity(
#						processed_rates)))
#
# Where processed_rates is a dictionary of rates from
# rates.RatesWalker()

# Written by Glen Baker - iepathos@gmail.com

from math import log

import gv
from pygraph.classes.digraph import digraph
from pygraph.readwrite.dot import write

from pygraph.algorithms.minmax import shortest_path

from pprint import pprint

from itertools import permutations

from rates import convertDictToDiGraph, createImageFromDiGraph

#from pygraph.algorithms.minmax import shortest_path_bellman_ford
def shortest_path_bellman_ford(graph, source):
    """
	    This algorithm is modified from the original shortest_path_bellman_ford
	    found in the wonderful and open source pygraph.

	    from pygraph.algorithms.minmax import shortest_path_bellman_ford

	    Modified to return the negative weight cycles rather than raising
	    an exception and returning predecessor and distance dictionaries.

    """
    # initialize the required data structures       
    distance = {source : 0}
    predecessor = {source : None}
    
    # iterate and relax edges    
    for i in range(1,graph.order()-1):
        for src,dst in graph.edges():
            if (src in distance) and (dst not in distance):
                distance[dst] = distance[src] + graph.edge_weight((src,dst))
                predecessor[dst] = src
            elif (src  in distance) and (dst in distance) and \
            distance[src] + graph.edge_weight((src,dst)) < distance[dst]:
                distance[dst] = distance[src] + graph.edge_weight((src,dst))
                predecessor[dst] = src
                
    # detect negative weight cycles
    for src,dst in graph.edges():
        if src in distance and \
           dst in distance and \
           distance[src] + graph.edge_weight((src,dst)) < distance[dst]:
           return src, dst
            #raise NegativeWeightCycleError("Detected a negative weight cycle on edge (%s, %s)" % (src,dst))
        
    #return predecessor, distance

class Arbiter(object):
	"""
		Arbitrage can occur if the product of a cycle's 
		edge weights is greater than 1.

			w1 * w2 * w3 * ... > 1

		The log of the product

			=> log (w1 * w2 * w3 ... ) > log(1)

			=> log(w1) + log(w2) + log(w3) ... > 0

		The negative log

			=> log(w1) + log(w2) + log(w3) ... < 0 
								(inequality flipped)

		Now with the Bellman-Ford algorithm we can
		find negative weight cycles in the graph.

		Once the negative weight cycles are identified, arbiter
		creates and tests permutations of polygons of n size
		that contain the identified edge.

		The best possible arbitrage opportunity in the market 
		is returned.

	"""


	def findOpportunity(self, rates):
		"""
			Expects rates passed in to be a processed
			dictionary from rates.RatesWalker.processRates()

		"""
		# Set rates equal to the negative log so we can search for
		# negative cycles with bellman_ford algorithm to determine
		# arbitrage opportunities

		neg_log_rates = rates
		for i in rates:
			for j in rates:
				if i != j:
					#print i
					#print j
					#print rates[i][j]
					if rates[i][j] > 0:
						# transform the graph
						neg_log_rates[i][j] = -log(rates[i][j])

		# Creating a digraph - directed graph - from rates dictionary
		rates_digraph = convertDictToDiGraph(neg_log_rates)
		#print 'Rates DiGraph:', rates_digraph

		#print '         Performing the Bellman Ford Shortest Path Algorithm on -log(rates)\n'

		src = ''
		dst = ''
		
		# Need to add ability to pick target base currency
		for currency in neg_log_rates:
			#print 'Source:', currency
			src, dst = shortest_path_bellman_ford(rates_digraph, currency)
			#print 'Negative Weight Cycle detected on edge: (', src+',', dst, ')'
		edge = (src, dst)
		return edge

		# Sample solved with test triangle: EUR -> JPY -> USD
		# (141.7157261)*(0.0109074)*(0.6864105) = 1.06101910647
		# Arbitrage Possible

	def permutateRatesAroundEdge(self, rates, target_edge, edges=3):
		"""
			Expecting to use this function in conjunction with
			getBestPolygonFromPermutate()

			@returns a list of possible polygons in the 'rates' data set that have
			the target_edge in them.  For large data sets, this function can save
			getBestPolygonFromPermutate() some time. 

			target_edge should be a tuple for a directed edge of a graph 
			like: ('USD', 'JPY') - (src, dst) - rates[src][dst]

			getBestPolygonFromPermutate(permutateRatesAroundEdge(findOpportunity(processed_rates)))
		"""
		edge_permutate = []
		for polygon in permutations(rates, edges):
			if target_edge[0] in polygon:
				if polygon.index(target_edge[0]) < len(polygon)-1:
					if polygon[ polygon.index(target_edge[0])+1 ] == target_edge[1]:
						edge_permutate.append(polygon)
				elif polygon.index(target_edge[0]) == len(polygon)-1:
					if polygon[0] == target_edge[1]:
						edge_permutate.append(polygon)

		#print 'Edge Permutate:', edge_permutate
		return edge_permutate
		
	def getBestPolygonFromPermutate(self, rates, permutate, edges=3):
		"""
			Receives a list of polygons and returns the polygon 
			with the best ratio.  Also returns the ratio itself.

			@returns best_polygon, best_ratio in permutate

		"""
		if len(permutate) >= edges:
			best_ratio = 0
			best_polygon = []

			for polygon in permutate:
				polygon_edge_weights = 1
				for i in range(edges):
					if i+1 < edges:
						polygon_edge_weights *= rates[polygon[i]][polygon[i+1]]
					elif i == edges - 1:
						polygon_edge_weights *= rates[polygon[-1]][polygon[0]]

				if polygon_edge_weights > best_ratio:
					best_ratio = polygon_edge_weights
					best_polygon = polygon
					#print 'Best Ratio:', best_ratio
					#print 'Best Polygon:', best_polygon

			return best_polygon, best_ratio
		else:
			print 'Not enough currencies in data set to create rates polygon.'

	def getRatesPolygonRatio(self, rates, edges=3):
		"""
			This function takes all of the rates and tries all of the
			possible ratios with polygons with 'edges=3'.  It returns 
			the best_polygon and best_ratio.

			This algorithm is too inefficient for larger data sets.

		"""
		if len(rates) >= edges:
			best_ratio = 0
			best_polygon = []

			currency_permutate = permutations(rates, edges)

			for polygon in currency_permutate:
				polygon_edge_weights = 1
				for i in range(edges):
					if i+1 < edges:
						#print 'Edge: (', polygon[i]+',', polygon[i+1], ')'
						#print 'Edge Weight:', rates[polygon[i]][polygon[i+1]]
						polygon_edge_weights *= rates[polygon[i]][polygon[i+1]]

					elif i == edges - 1:
						#print 'Edge: (', polygon[-1]+',', polygon[0], ')'
						#print 'Edge Weight:', rates[polygon[-1]][polygon[0]]
						polygon_edge_weights *= rates[polygon[-1]][polygon[0]]
				#print 'Polygon:', polygon
				#print 'Polygon Weight:', polygon_edge_weights, '\n'

				if polygon_edge_weights > best_ratio:
					best_ratio = polygon_edge_weights
					best_polygon = polygon
					#print 'Best Ratio:', best_ratio
					#print 'Best Polygon:', best_polygon

					#print 'rates[polygon[i]]', rates[polygon[i]]

			return best_polygon, best_ratio
		else:
			print 'Not enough currencies in data set to create rates polygon.'

	def createCircularDiGraph(self, polygon_tup, rates):
		"""
			Takes a polygon tuple and creates a circular directed graph
			of the tuple.

			returns the directed graph
		"""
		# Creating a digraph - directed graph - from rates dictionary
		#rates_digraph = convertDictToDiGraph(rates)
		dg = digraph()
		dg.add_nodes(polygon_tup)
		for i in range(len(polygon_tup)):
			if i < len(polygon_tup)-1:
				#polygon_tup[i]
				weight = rates[polygon_tup[i]][polygon_tup[i+1]]
				dg.add_edge((polygon_tup[i], polygon_tup[i+1]), wt=float(weight), label=str(weight))
			elif i == len(polygon_tup)-1:
				weight = rates[polygon_tup[-1]][polygon_tup[0]]
				dg.add_edge((polygon_tup[-1], polygon_tup[0]), wt=float(weight), label=str(weight))
		
		#self.createImageFromDiGraph(dg, 'best_polygon_solution_digraph.png')

		return dg