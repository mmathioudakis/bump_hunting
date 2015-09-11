import sys
import networkx as nx
import bingraph as bg
import graph_utils as utilz
import graph_db as graph_db 
import numpy.random, random
from pcst3 import pcst_solve
from heapq import heappush, heappop, heapify
import pymongo as pm
import time


class Error(Exception):
	pass

class Our_Tree():

	def __init__(self):
		self.adj_lists = dict()

	def neighbors(self, u):
		neighbors = self.adj_lists.get(u, [])
		return neighbors

	def add_edges_from(self, edges):
		for (u,v) in edges:
			self.add_edge( u, v )

	def add_edge( self, u, v ):
		self.adj_lists.setdefault(u,[]).append(v)
		self.adj_lists.setdefault(v,[]).append(u)

def pcst_heur(graph, query_nodes, a = 1, include_solution = False):
	# return tree that approximately solves PCST
	# set 'pi' attribute to a+1 for every v \in query_nodes
	for v in query_nodes:
		graph.node[v]['pi'] = a + 1
	try:
		forest = pcst_solve( graph )
	except:
		print(graph.edges(), query_nodes)
		raise Error
	best = [0, set()]
	for subtree in nx.connected_component_subgraphs( forest ):
		# print(subtree.edges())
		# call tree_offline for subtree, and keep the
		# best solution found.
		solution = tree_offline(subtree, query_nodes, None, a, include_solution)
		if solution[0] > best[0]:
			best = solution
	return best

def tree_offline(tree, query_nodes, root = None, a = 1, include_solution = False):
	""" Maximize linear discrepancy for tree. """

	if len(tree.nodes()) == 0:
		return (0, [])

	if root == None:
		root = tree.nodes()[0];

	solution = _tree_offline(tree, root, query_nodes,
							None, a, include_solution)[1]

	return solution

def _tree_offline(tree, root, query_nodes, parent, a = 1,
									include_solution = False):
	""" Auxilliary function. """

	best_with = [-1, set()] # score, solution (as set of nodes)
	if root in query_nodes:
		best_with[0] = a

	best_under = [0, set()] # score, solution (as set of nodes)	

	if include_solution:
		best_with[1] = set([root])
		
	children = tree.neighbors(root)

	# recursively perform discrepancy maximization on subtree
	for c in children:
		if c != parent:

			best_of = _tree_offline(tree, c, query_nodes,
				root, a, include_solution)

			if best_of[0][0] > 0:
				best_with[0] = best_with[0] + best_of[0][0]
				if include_solution:
					for node in best_of[0][1]:
						best_with[1].add(node)

			if best_of[1][0] > best_under[0]:
				best_under[0] = best_of[1][0]
				if include_solution:
					best_under[1] = best_of[1][1]

	if best_under[0] <= best_with[0]:
		best_under[0] = best_with[0]
		if include_solution:
			best_under[1] = best_with[1]

	return (tuple(best_with), tuple(best_under))

def bfs_heur(graph, query_nodes, a = 1, include_solution = False):
	""" Approximately maximize discrepancy on graph. """
	
	best_root = None
	best_d    = -1
	for root in query_nodes:
		sys.stderr.write('.')
		tree = nx.bfs_tree(graph, root)
		d, solution_graph = tree_offline(tree, query_nodes, root, a, False)
		if d > best_d:
			best_d = d
			best_root = root
	tree = nx.bfs_tree(graph, best_root)
	sys.stderr.write('\n')
	return tree_offline(tree, query_nodes, best_root, a, include_solution)

def bfs_heur_fast(graph, query_nodes, a = 1, include_solution = False):
	""" Approximately maximize discrepancy on graph. """
	
	best_root = None
	best_d    = -1

	# Note: if a query node appears as a singleton in graph
	# (not sure how, but maybe it can happen),
	# it will not appear in the binary representation at all,
	# because this is built only from the edges.
	(deg, off, adj, m) = bg.from_edgeiter( graph.edges_iter(), getIdMap=True)
	invmap = dict( (v,u) for (u,v) in m.iteritems() )

	t0 = time.clock()
	t1 = t0
	for root in query_nodes:
		# This assertion will fail if root has no neighbors in graph.
		# assert len( graph[root] ) > 0
		if len( graph[root] ) <= 0:
			continue
		sys.stderr.write( '.' )
		tree = _bfs_fast( deg, off, adj, invmap, m.getId(root) )
		d, solution_graph = _tree_offline(tree, root, query_nodes,
						  None, a, False)
		if d > best_d:
			best_d = d
			best_root = root
		t1 = time.clock()
		if t1 - t0 > 300:
			best_d = 0
			break
	sys.stderr.write( '\n' )
	if best_d > 0:
		tree = _bfs_fast( deg, off, adj, invmap, m.getId(best_root) )
		return _tree_offline(tree, best_root, query_nodes, None, a,
			include_solution)[1]
	else:
		return (0, set())

def _bfs_fast( d, o, a, invmap, r ):
	assert r < d.shape[0]
	bfs_tree_edges = bg.run_bfs( d, o, a, r )
	# sys.stderr.write( '_bfs_fast: building Our_Tree...' )
	T = Our_Tree()
	for (u,v) in bfs_tree_edges:
		T.add_edge( invmap[u], invmap[v] )
	# sys.stderr.write( 'done!\n' )
	return T

def mst_heur(graph, query_nodes, a = 1, include_solution = False):
	""" Approximately maximize discrepancy on graph. """

	mst = (-1, None)

	msf = utilz.get_minimum_spanning_forest(graph)
	for tree in msf:
		d, solution_graph = tree_offline(tree, query_nodes, None, a, include_solution)
		if d > mst[0]:
			mst = (d, solution_graph)

	return mst

def random_mst_heur(graph, query_nodes, a = 1, include_solution = False):
	""" Approximately maximize discrepancy on graph. """

	best_d = -1
	best_r = None
	count_no_change = 0
	t0 = time.clock()
	t1 = t0
	for i in range(1,100):
		w_graph = nx.Graph()
		current_r = []
		for e in graph.edges():
			r = numpy.random.uniform()
			current_r.append( r )
			w_graph.add_edge(*e, weight=r)
		d, solution = mst_heur(w_graph, query_nodes, a, False)
		if d > best_d:
			best_d = d
			best_r = current_r
			count_no_change = 0
		else:
			count_no_change += 1
		if count_no_change >= 5:
			break
		t1 = time.clock()
		if t1 - t0 > 300:
			best_d = -1
			break
	if best_d > 0:
		w_graph = nx.Graph()
		for (r, e) in zip( best_r, graph.edges() ):
			w_graph.add_edge( *e, weight=r )
		return mst_heur( w_graph, query_nodes, a, include_solution )
	else: 
		return (0, set())

def mst_heur_scheme(graph, query_nodes, a = 1, include_solution = False):
	""" Approximately maximize discrepancy on graph. """

	w_graph = nx.Graph()
	for e in graph.edges():
		r = 2 
		if e[0] in query_nodes:
			r = r - 1
		if e[1] in query_nodes:
			r = r - 1
		w_graph.add_edge(*e, weight=r)
	w_graph.add_nodes_from(graph.nodes())
	d, solution_graph = mst_heur(w_graph, query_nodes, a, include_solution)
	return (d, solution_graph)

def _get_new_frontier(graph, opened_nodes, query_nodes, budget):

	query_sp = dict([(q, nx.shortest_path_length(graph, q)) for q in query_nodes])
	for q in query_nodes:
		query_sp[q][q] = 0
	candidate_frontier = set(graph.nodes()) - opened_nodes
	frontier = []
	for cf in candidate_frontier:	
		dq = [query_sp[q].get(cf,-1) for q in query_nodes]
		dq = [x for x in dq if x >= 0]
		if max(dq) <= len(dq) * budget:
			frontier.append(cf)	
	return frontier

def expand_query_nodes(graph_db, query_nodes, a = 1):
	api_calls = 0
	budget = a + 1

	# initialize graph
	graph = nx.Graph()
	if len(query_nodes) == 0:
		return graph

	# we add query nodes
	for node in query_nodes:
		graph.add_node(node)
	# graph.add_nodes_from(query_nodes)
	
	opened_nodes = set([])
	frontier = _get_new_frontier(graph, opened_nodes, query_nodes, budget)
	
	while frontier:
		for f in frontier:
			neighbors = graph_db.get_neighbors(f)
			if neighbors:
				graph.add_edges_from([(f,n) for n in neighbors])
		api_calls = api_calls + len(frontier)

		opened_nodes |= set(frontier)
		frontier = _get_new_frontier(graph, opened_nodes, query_nodes, budget)

		# print(api_calls)
		# if api_calls > 10000:
		# 	sys.exit()

	#print(frontier)
	return (graph, api_calls)

class Component:
	def __init__( self, C1, C2=None ):
		self.active = True
		if C2 == None:
			# when C2=None C1 is in fact just a set, NOT a component!
			self.S = C1
			self.tree = []
			self.nodes_to_expand = [(random.random(), x) for x in C1]
		else:
			self.S = C1.S | C2.S
			self.tree = C1.tree + C2.tree
			self.nodes_to_expand = C1.nodes_to_expand + C2.nodes_to_expand
		heapify(self.nodes_to_expand)
		self.partial_solution = None
	def add(self, u):
		self.S.add( u )
		self.partial_solution = None
	def add_edge(self, u, v):
		self.tree.append( (u,v) )
	def contains( self, u ):
		return u in self.S
	def get_partial_solution(self, graph, query_nodes, a, samples):
		if self.partial_solution == None:
			unexpanded_frontier = self._get_unexpanded_frontier()
			if len(unexpanded_frontier) > 0:
				set_of_roots = random.sample(unexpanded_frontier, min(samples, len(unexpanded_frontier)))
				t = self._make_tree()
				best_discrepancy = 0
				for r in set_of_roots:
					temp = _tree_offline( t, r, query_nodes, None, a)
					if temp[1][0] > best_discrepancy:
						best_discrepancy = temp[1][0]
						self.partial_solution = temp
		return self.partial_solution

	def _get_unexpanded_frontier(self):
		unexpanded_frontier = [ x for (priority,x) in self.nodes_to_expand if x in self.S ]
		return unexpanded_frontier

	def _make_tree(self):
		t = Our_Tree()
		t.add_edges_from(self.tree)
		# t = nx.Graph()
		# t.add_nodes_from( self.S )
		# t.add_edges_from( self.tree )
		return t

	def set_inactive(self):
		self.active = False

	def is_active(self):
		return self.active

def would_you_expand(components):
	would_expand = False
	for c in components:
		if c.nodes_to_expand:
			would_expand = True
			break
	return would_expand

def smart_expand(graph_db, query_nodes, a = 1, approx_threshold = 1.00, samples = 1):

	api_calls = 0
	num_of_edges = 0
	schedule = 64
	schedule_multiplier = 2

	# initialize graph
	graph = nx.Graph()
	if len(query_nodes) == 0:
		return (graph, 0)

	# we add query nodes
	for node in query_nodes:
		graph.add_node(node)

	# maintain a list of nodes on the frontier
	
	nodes_seen = set(query_nodes)

	nodeComponent = {}
	components    = []
	for q in query_nodes:
		comp = Component( set([q]) )
		components.append( comp )
		nodeComponent[q] = comp

	current_best = 1.0
	upper_bound = 1.0 * len(query_nodes)
	approx_ratio = current_best / upper_bound
	# print(approx_ratio, current_best, upper_bound)

	while would_you_expand(components) and len(components) > 1 and (approx_ratio < approx_threshold):
		# select the next node to expand
		next_components = []

		for c in components:

			if not c.is_active() or len(c.nodes_to_expand) == 0:
				continue

			lucky_node = heappop( c.nodes_to_expand )[1]
	
			comp_of_lucky_node = nodeComponent.get(lucky_node, None)
			assert comp_of_lucky_node != None
		
			neighbors = graph_db.get_neighbors(lucky_node)
			if neighbors == None:
				neighbors = []
	
			api_calls += 1
			for nbor in neighbors:
				if not nbor in nodes_seen:
					# nodes_to_expand.add(nbor)
					heappush( c.nodes_to_expand, (random.random(), nbor) )
					nodes_seen.add(nbor)
					nodeComponent[nbor] = comp_of_lucky_node
					comp_of_lucky_node.add(nbor)
					comp_of_lucky_node.add_edge( lucky_node, nbor )
				else:
					comp_of_nbor = nodeComponent.get(nbor,None)
					assert comp_of_nbor != None
					if comp_of_lucky_node != comp_of_nbor:
						union = Component( comp_of_lucky_node, comp_of_nbor )
						union.add_edge( lucky_node, nbor )
						comp_of_lucky_node.set_inactive()
						comp_of_nbor.set_inactive()
						next_components.append(union)

						for u in union.S:
							nodeComponent[u] = union
						comp_of_lucky_node = union
		
				graph.add_edge(lucky_node, nbor)
				num_of_edges += 1		

		components = [c for c in components + next_components if c.is_active()]

		if api_calls >= schedule:	
			
			if schedule >= 8192:
				schedule += 8192
			else:
				schedule *= schedule_multiplier
	
			best_with = [1]
			best_ever = [1]
	
			# for each connected component, pick one node at the frontier
			for comp in components:
				partial_solution = comp.get_partial_solution( graph, query_nodes, a, samples)
				if partial_solution != None:
					best_with.append(partial_solution[0][0])
					best_ever.append(partial_solution[1][0])
	
			current_best = max(current_best, max(best_ever))
			upper_bound = sum([sc for sc in best_with if sc > 0])
			approx_ratio = 1.0 * current_best / upper_bound

			sys.stderr.write(str(api_calls) + '\t' + str(len(components)) + '\t' 
				+ str(num_of_edges) + '\t'
				+ str(approx_ratio) + '\n')
			comp_sizes = [len(c.S) for c in components]
			comp_sizes.sort(reverse = True)
			sys.stderr.write(str(comp_sizes) + '\n')

	return (graph, api_calls)

def naively_expand_query_nodes(graph_db, query_nodes, a = 1):
	api_calls = 0
	budget = a + 1

	# initialize graph
	graph = nx.Graph()
	if len(query_nodes) == 0:
		return graph

	# we add query nodes
	for node in query_nodes:
		graph.add_node(node)

	opened_nodes = set([])
	frontier = set(query_nodes[:])

	step = 0
	while step < budget and frontier:
		for f in frontier:
			neighbors = graph_db.get_neighbors(f)
			if neighbors:
				graph.add_edges_from([(f,n) for n in neighbors])
		api_calls = api_calls + len(frontier)
		opened_nodes |= frontier
		frontier = set(graph.nodes()) - opened_nodes
		step = step + 1

	return (graph, api_calls)
