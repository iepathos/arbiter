#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
	rates.py contains ratesWalker.  Retrieves and writes
	current rates, creates digraphs of rates and images 
	of digraphs.

"""
import requests, json
import gv
from pygraph.classes.digraph import digraph
from pygraph.readwrite.dot import write
from math import log

STREAM_URL = 'http://fx.priceonomics.com/v1/rates/'

def createImageFromDiGraph(input_digraph, name):
	dot = write(input_digraph)
	gvv = gv.readstring(dot)
	gv.layout(gvv, 'dot')
	gv.render(gvv, 'png', name+'_digraph.png')

def convertDictToDiGraph(initial_dict):
	"""
		Utility function for converting a processed rates dictionary
		into a directed graph.

	"""
	dg = digraph()
	dg.add_nodes(initial_dict.keys()) # Adds a node for each market
	#print 'Dictionary passed to convert:', initial_dict
	for i in initial_dict:
		for j in initial_dict:
			if i != j:
				weight = initial_dict[i][j]
				dg.add_edge((i, j), wt=float(weight), label=str(weight))
	return dg

class RatesWalker(object):
	total_walked = 0
	recent_rates_json = {}
	recent_rates_digraph = {}

	def getRates(self, url=STREAM_URL):
		"""
			Retrieves the rates JSON at the specified url.

		"""
		try:
			r  = requests.get(url)
			self.recent_rates_json = r.json
			self.total_walked += 1
			return r.json
		except:
			print 'Error connecting to the rates API.'

	def rateWalk(self, steps=20):
		"""
			Loop wrapper for retrieving the rates.  
			rateWalk will retrieve the rates as many 
			times as it is told to.

		"""
		walked = 0
		while walked < steps:
			data = self.getRates()
			if data:
				#print json.dumps(data, sort_keys=True, indent=4, separators=('',' : '))
				walked += 1
				return data
			else:
				walked += 1

	def processRates(self, rates):
		"""
			The rates dictionary passed in from getRates()
			will have information laid out like:

				 [USD][EUR][JPY][BTC]
			[USD][ 1 ][   ][   ][   ]
			[EUR][   ][ 1 ][   ][   ]
			[JPY][   ][   ][ 1 ][   ]
			[BTC][   ][   ][   ][ 1 ]

			Where the currencies are separated by an underscore '_'
			which determines to _ and from.

			processRates() takes the JSON from getRates() and
			returns a dictionary of the information setup like
			the 2d matrix above.
			
			Example:
				rates_proper['USD']['USD'] = 1
				rates_proper['EUR']['EUR'] = 1
				rates_proper['JPY']['JPY'] = 1
				rates_proper['BTC']['BTC'] = 1

		"""

		rates_proper = {}

		if rates:
			for key in rates:
				key_split = str(key).split('_')
				#if key_split[0] != key_split[1]:
				if key_split[0] not in rates_proper:
					rates_proper[key_split[0]] = {}
				rates_proper[key_split[0]][key_split[1]] = float(rates[key])
		return rates_proper

	def createRatesImage(self, name, rates):
		"""
			Creates 'rates_digraph.png' from rates dictionary.

		"""
		name = str(name) # safety dance

		# Creating a digraph - directed graph - from rates dictionary
		rates_digraph = convertDictToDiGraph(rates)
		self.recent_rates_digraph = rates_digraph
		#print 'Rates DiGraph:', rates_digraph
		
		createImageFromDiGraph(rates_digraph, name+'_rates')

	def createNegativeLogRatesImage(self, name, rates):
		"""
			Creates 'negative_log_rates_digraph.png' from rates 
			dictionary. 

		"""
		# Set rates equal to the negative log so we can search for
		# negative cycles with bellman_ford algorithm to determine
		# arbitrage opportunities

		name = str(name) # safety dance

		for i in rates:
			for j in rates:
				# transform the graph
				rates[i][j] = -log(rates[i][j])

		# Creating a digraph - directed graph - from rates dictonary
		rates_digraph = convertDictToDiGraph(rates)

		#print 'Rates DiGraph:', rates_digraph
		
		createImageFromDiGraph(rates_digraph, 'negative_log_'+name)