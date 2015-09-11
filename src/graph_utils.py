import networkx as nx
import math

class Error(Exception):
	pass

def is_linear(graph):
	""" 
	Checks if the graph is linear.

	The graph is linear if the maximum degree of any node is at most two.

	Args:
		graph: networkx.Graph instance

	"""

	if len(graph.nodes()) == 0:
		return True

	max_degree = max(self._graph.degree().values())
	return max_degree < 3


def is_tree(graph):
	"""
	Checks whether graph is a tree.

	A graph is a tree if it is 
		(i) undirected - always, in our setting 
		(ii) connected, and 
		(iii) contains no cycles.

	Args:
		graph: networkx.Graph instance

	Return a boolean that indicates whether this graph is a tree.
	"""

	if len(graph.nodes()) == 0:
		return True

	if not nx.is_connected(graph):
		return False

	if len(nx.cycle_basis(graph)) > 0:
		return False

	return True

def get_minimum_spanning_forest(graph):
	"""Returns a minimum spanning forest as a set of connected subgraphs."""
	edges = nx.minimum_spanning_tree(graph)
	forest = nx.connected_component_subgraphs(edges)
	return forest

def cosine_similarity(dict_a, dict_b):
	length_a = math.sqrt(sum([v*v for v in dict_a.values()]))
	length_b = math.sqrt(sum([v*v for v in dict_b.values()]))

	if length_a * length_b == 0:
		return 0

	common_keys = set(dict_a.keys()) & set(dict_b.keys())
	product = sum([ dict_a[key] * dict_b[key] for key in common_keys ])

	cosine = product / (length_a * length_b)
	return cosine

def jaccard_similarity(set_a, set_b):

	jacc = 1.0 * len(set_a & set_b) / len(set_a | set_b)

	return jacc