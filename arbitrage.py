#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Solution to: http://priceonomics.com/jobs/puzzle/
# See Bitcoin Arbitrage Coding Puzzle.txt for more 
# information.

# Written by Glen Baker - iepathos@gmail.com


import gevent
import json

from gevent.event import Event, AsyncResult
from gevent.queue import JoinableQueue

import signal

from time import gmtime, strftime
import time
def timeCheck():
	print 'Time check:', time.time()

import curses

from pygraph.classes.digraph import digraph

from rates import RatesWalker, createImageFromDiGraph

from arbiter import Arbiter

if __name__ == '__main__':
	#gevent.signal(signal.SIGTERM, gevent.shutdown)
	#gevent.signal(signal.SIGQUIT, gevent.shutdown)
	#gevent.signal(signal.SIGINT, gevent.shutdown)

	# Initialize Curses UI
	stdscr = curses.initscr()
	curses.noecho()
	curses.cbreak()
	stdscr.keypad(1)
	
	# RatesWalker UI
	rw_begin_x = 0
	rw_begin_y = 2
	rw_height = 23
	rw_width = 40
	rates_window = curses.newwin(rw_height, rw_width, rw_begin_y, rw_begin_x)
	
	# Arbiter UI
	arb_begin_x = 0
	arb_begin_y = 25
	arb_height = 15
	arb_width = 80
	arbiter_window = curses.newwin(arb_height, arb_width, arb_begin_y, arb_begin_x)

	# Transactions UI
	trans_begin_x = 0
	trans_begin_y = 40
	trans_height = 10
	trans_width = 40
	trans_window = curses.newwin(trans_height, trans_width, trans_begin_y, trans_begin_x)


	### Gevent Threads
	#
	#	ratesTracking() - arbiterTracking() - transactionTracking()

	### These variables handle synchronization between threads

	#async_result_rates = AsyncResult()
	rates_started = Event()

	#async_result_opportunity = AsyncResult()
	#arbitrage_opportunity = Event()

	rates_q = JoinableQueue()

	rates_tracking = True
	arbiter_tracking = True

	## Rates Thread
	def ratesTracking():
		rates_started.set()
		
		if rates_tracking:
			rw = RatesWalker()
			rates_window.addstr(2, 1, 'RatesWalker', curses.A_UNDERLINE)

			rates_window.addstr(3, 1, 'Currency Exchange Rates')
			#rates_window.refresh()

			current_rates = rw.getRates()
			processed_rates = rw.processRates(current_rates)
			rates_q.put(processed_rates)

			rates_window.addstr(4, 0, json.dumps(current_rates, sort_keys=True, indent=4))
			rates_window.border()
			rates_window.refresh()

			#print 'Total number of currencies in data set:', len(processed_rates), '\n'

			# Create DiGraph Image of Rates
			#print '         Creating Image of DiGraph of Rates Data Set\n'
			#rw.createRatesImage('recent', processed_rates)
			#print ' - Created image recent_rates_digraph.png\n'

			# Create DiGraph Image of -log(Rates)
			#print '         Creating Image of DiGraph of -log(Rates Data Set)\n'
			#rw.createNegativeLogRatesImage('recent', processed_rates)
			#print ' - Created image negative_log_recent_rates_digraph.png\n'


	## Arbiter Thread
	def arbiterTracking():
		rates_started.wait()
		processed_rates = rates_q.get()

		arbiter = Arbiter()
		#print 'Initialized Arbiter....\n'
		arbiter_window.addstr(0, 1, 'Arbiter', curses.A_UNDERLINE)
		if arbiter_tracking:
			#arbiter_window.addstr(1, 1, 'Searching for arbitrage opportunities....')
			#arbiter_window.addstr(2, 1, str(processed_rates))
			#arbiter_window.refresh()
			
			if processed_rates != {}:
				#print 'Processed Rates passed to Arbiter Tracking:', processed_rates
				#edge = arbiter.findOpportunity(processed_rates)
				#print edge

				best_polygon, best_ratio = arbiter.getBestPolygonFromPermutate(processed_rates, \
											 arbiter.permutateRatesAroundEdge(processed_rates, \
											 arbiter.findOpportunity(processed_rates)))

				#best_polygon, best_ratio = arbiter.getRatesPolygonRatio(processed_rates)
				if best_polygon:
					if best_ratio:
						arbiter_window.addstr(1, 1, 'The most profitable arbitrage opportunity is:')
						arbiter_window.addstr(2, 1, str(best_polygon), curses.A_STANDOUT)
						arbiter_window.addstr(3, 1, 'With a rate of return of:')
						arbiter_window.addstr(4, 1, str(best_ratio), curses.A_STANDOUT)
						arbiter_window.addstr(' %')
						arbiter_window.refresh()

						rates_q.task_done()

						# Create DiGraph of best polygon

						arb_dg = arbiter.createCircularDiGraph(best_polygon, processed_rates)

						# Create image of best polygon digraph
						#print '         Creating Image of DiGraph of Best Arbitrage Opportunity\n'
						#createImageFromDiGraph(arb_dg, 'best_opportunity')
						#print ' - Created image best_opportunity_digraph.png\n'

	## Transaction Thread
	def transactionTracking():
		print 'Initialized transactionTracking....\n'

		#arbitrage_opportunity.wait()
		arbitrage_dg = async_result_opportunity.get()
		#print 'transactionTracking() received arbitrage polygon:', arbitrage_dg, '\n'
		print '         Ready to begin transaction....'		
	
	# Input Tracking
	while 1:
		stdscr.addstr(0, 1, 'Arbitrage Program created by Glen Baker', curses.A_REVERSE)
		stdscr.addstr(1, 1, "- Press enter to continue, 'q' to quit")
		c = stdscr.getch()
		if c == ord('q'):
			# Shutdown Curses UI
			curses.nocbreak(); stdscr.keypad(0); curses.echo()
			curses.endwin()

			rates_q = JoinableQueue() # Clear Gevent Queue
			break
		if c == ord('r'):
			rates_tracking = not rates_tracking

		gevent.joinall([
			gevent.spawn(ratesTracking),
			gevent.spawn(arbiterTracking),
			#gevent.spawn(transactionTracking),
		])

	rates_q.join()