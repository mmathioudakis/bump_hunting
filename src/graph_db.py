from __future__ import print_function
import argparse as parse
from sys import stdout as stdout
import graph_utils as utils
import pymongo as pm
import networkx as nx
import numpy.random as random
import bingraph as bg

client = pm.MongoClient()

class Error(Exception):
	pass

class BasicGraph(object):

	def get_neighbors(self):
		raise Error("Abstract method. Should not be called.")

	def get_all_nodes(self):
		raise Error("Abstract method. Should not be called.")

class Graph_BG(BasicGraph):

	def __init__(self, graph_name):
		"""
		Loads a "binary graph" from disk. The graph is stored as
		three separate Numpy arrays, one for degrees, one for
		adjacency list offsets, and one for the adjacency lists itself.
		To load the graph, graph_name must specify the path
		(absolute or relative) to the files that contain the graph.
		These are
		 - /path/to/graph_name_degree.npy
		 - /path/to/graph_name_offset.npy
		 - /path/to/graph_name_adjlist.npy
		For example:
		GraphBG( '/path/to/graph_name' ) would load this graph.
		"""
		(d,o,a) = bg.load_graph( graph_name )
		self.d = d
		self.o = o
		self.a = a

	def get_neighbors(self, node):
		""" Returns a list with the neighbors of node. """

		return bg.neighborlist( node, self.d, self.o, self.a )

	def get_all_nodes(self):
		pass

class Graph_NX(BasicGraph):

	def __init__(self, graph):
		""" 
		Initialize Graph Database. 

		Args:
			graph: a networkx.Graph() instance

		"""
		self._graph = graph

	def get_neighbors(self, node):
		""" Returns a list with the neighbors of node. """							
		return self._graph.neighbors(node)

	def get_all_nodes(self):
		return self._graph.nodes()

class Graph_Mongo_Explicit(BasicGraph):

	def __init__(self, db_name, neighbors_coll):
		self._db_name = db_name
		self._coll_name = neighbors_coll

	def get_neighbors(self, author_id):
		# global client 
		coll = client[self._db_name][self._coll_name]
		entry = coll.find_one({'_id': author_id})
		if entry is not None:
			ans = entry['neighbors']
			#client.close()
			return ans
		else:
			# client.close()
			return []

	def get_all_nodes(self, min_degree = 0):
		coll = client[self._db_name][self._coll_name]
		all_nodes = [e['_id'] for e in coll.find({'degree': {'$gte': min_degree}})]
		return all_nodes

def get_query_nodes(mongo_coll, method, options = {'NUM': 1, 'KEYWORD': 'mining'}):
	matching_nodes = []

	if method == 'random':
		all_nodes = [e['_id'] for e in mongo_coll.find()]
		matching_nodes = random.choice(all_nodes, size = options['NUM'], replace = False)
	elif method == 'keyword_inv':
		matching_nodes = [auth for e in mongo_coll.find({'_id': options['KEYWORD']}) for auth in e['Authors']]
	elif method =='planted':
		all_nodes = [e['_id'] for e in mongo_coll.find()]
		n = random.choice(all_nodes)
		matching_nodes = mongo_coll.find_one({'_id': n})['neighbors']
	else:
		raise Error('You should not be here... Guards!')

	return matching_nodes

def load_explicit(db_name, neighbors_collection_name):
	graph = nx.Graph()
	# global client
	coll = client[db_name][neighbors_collection_name]
	i = 0
	for entry in coll.find():
		i = i+1
		if i%1000 == 0:
			print('.', end='')
			stdout.flush()
		auth = entry['_id']
		graph.add_edges_from([(auth, co_auth) for co_auth in entry['neighbors']])
	print()
	# client.close()
	return graph

def load_implicit(db_name, author_terms_collection_name, theta):
	graph = nx.Graph()
	# global client 
	coll = client[db_name][author_terms_collection_name]
	i = 0
	for entry in coll.find():
		i = i+1
		if i%1 == 0:
			print('.', end='')
			stdout.flush()

		auth = entry['_id']
		terms = entry['Term_Freq']
		for o in coll.find():
			o_auth = o['_id']
			o_terms = o['Term_Freq']
			if utils.cosine_similarity(terms, o_terms) >= theta:
				graph.add_edge(auth, o_auth)
	print()
	# client.close()
	return graph


