import sys
import bump_hunting.src.bump_hunting as bh
import bump_hunting.src.graph_db as graph_db
import networkx as nx
import time, json, argparse as parse, random
from collections import OrderedDict as OD

_CENTRAL_BUMP_NODE_MIN_DEGREE = 4
_BUMP_TRIAL_BUDGET = 10

class Error(Exception):
	pass

def calculate_accuracy(query_dict, solution):
	query_nodes = extract_query_nodes(query_dict)
	query_in_solution = set(query_nodes) & set(solution)

	best_jacc = 0
	best_sphere_size = 0
	for i in xrange(0, len(query_dict['bumps'])):
		bump = query_dict['bumps'][i]
		s_size = query_dict['sphere_sizes'][i]
		len_intersection = len(set(bump) & query_in_solution)
		len_union = len(set(bump) | query_in_solution)
		jacc = 0.0
		if len_union > 0:
			jacc = 1.0 * len_intersection / len_union
		if jacc > best_jacc:
			best_jacc = jacc
			best_sphere_size = s_size
	return (best_jacc, s_size)

def _evaluate_algorithm(algo_func, alg_name, expanded_graph,
						query_dict, alpha, include_solution, partial_result):
	sys.stderr.write(alg_name + '\n')
	t0 = time.clock()
	query_nodes = extract_query_nodes(query_dict)
	result = algo_func(expanded_graph, query_nodes, alpha, include_solution)
	t1 = time.clock()

	discrepancy = result[0]
	solution = result[1]

	accuracy_res = calculate_accuracy(query_dict, solution)
	accuracy = accuracy_res[0]
	sphere_size = accuracy_res[1]
	
	alg_result = OD(partial_result)
	_populate_results(alg_result, alg_name, int(1000 * (t1 - t0)),
		discrepancy, accuracy, sphere_size, query_nodes, list(solution))
	return alg_result

def _get_random_bumps(graph_api, num_of_bumps, radius,
					signal_nodes, noise_nodes, repeats):

	all_nodes =  graph_api.get_all_nodes(min_degree =\
							 _CENTRAL_BUMP_NODE_MIN_DEGREE)

	print(len(all_nodes))

	result_collection = []
	for i in range(repeats):
		result = {'bumps': [], 'noise': None, 'sphere_sizes': []}
		for j in range(num_of_bumps):

			trials = 0
			while True:

				lucky_pos = random.randint(0, len(all_nodes) - 1)
				lucky = all_nodes[lucky_pos]
				ext_neighbors = graph_api.get_neighbors(lucky) + [lucky]
	
				pivot_pos = random.randint(0, len(ext_neighbors) - 1)
				pivot = ext_neighbors[pivot_pos]
			
				opened_nodes = set([])
				frontier = set([pivot])
			
				sphere = nx.Graph()
				step = 0
				while step < radius and frontier:
					for f in frontier:
						neighbors = graph_api.get_neighbors(f)
						if neighbors:
							sphere.add_edges_from([(f,n) for n in neighbors])
					opened_nodes |= frontier
					frontier = set(sphere.nodes()) - opened_nodes
					step = step + 1
			
				s_nodes = sphere.nodes()
	
				if len(s_nodes) < signal_nodes:
					trials += 1
					if trials <= _BUMP_TRIAL_BUDGET or len(s_nodes) == 0:
						continue
					else:
						bump = random.sample(s_nodes, min(len(s_nodes),
							signal_nodes))
						result['bumps'].append(bump)
						result['sphere_sizes'].append(len(s_nodes))
						break
				else:
					bump = random.sample(s_nodes, signal_nodes)
					result['bumps'].append(bump)
					result['sphere_sizes'].append(len(s_nodes))
					break

		all_bumps = set()
		for bump in result['bumps']:
			all_bumps |= set(bump)
		out_nodes = list(set(all_nodes) - all_bumps)
		result['noise'] = random.sample(out_nodes, min(noise_nodes,
			len(out_nodes)))
		result_collection.append(result)
	
	return result_collection

def _populate_results(alg_result, alg_name, time_ms,
		discrepancy, accuracy, sphere_size, query_nodes, solution):
	# p_nodes, b_nodes, solution_edges, 
	alg_result['algorithm'] = alg_name
	alg_result['alg_time'] = time_ms
	alg_result['discrepancy'] = discrepancy
	alg_result['accuracy'] = accuracy
	alg_result['sphere_size'] = sphere_size
	alg_result['solution'] = solution
	alg_result['query_nodes'] = query_nodes

def extract_query_nodes(query_dict):
	all_query_nodes = set()
	for bump in query_dict['bumps']:
		all_query_nodes |= set(bump)
	all_query_nodes |= set(query_dict['noise'])
	return list(all_query_nodes)


if __name__=='__main__':

	parser = parse.ArgumentParser(description = \
			 'Evaluate local discrepancy maximization algorithms on graphs.')
	parser.add_argument('-db', 
		help = 'Name of the mongodb database that contains the graph.')
	parser.add_argument('-coll',
		help = 'Name of the mongodb collection that contains'\
							'  the Adjacency List of the input graph')
	parser.add_argument('-b', '--bumps', type = int, default = 1,
		help = 'Number of bumps.')
	parser.add_argument('-r', '--radius', type = int,
		help = 'Radius of the bump')
	parser.add_argument('-signal', type = int,
		help = 'Number of query nodes within bump spheres.')
	parser.add_argument('-noise', type = int,
		help = 'Bumber of query nodes outside bump spheres.')
	parser.add_argument('-repeats', type = int, default = 1,
		help = 'How many times to use the same graph '\
								' with different query nodes.')
	parser.add_argument('-qb', '--bump_nodes', type = int,
		help = 'Number of query nodes in bump.')
	parser.add_argument('-a', '--alpha', type = float,
		default = 1.0, help = 'Value for alpha.')
	parser.add_argument('-thresh', type = float, nargs='*',
		default = [1.0], help = 'Threshold for adaptive expansion.')
	parser.add_argument('-samples', type = int, default = 5,
		help = 'Number of samples used for upper bound estimation' \
											' during adaptive expansion.')
	parser.add_argument('--full', action = 'store_true')
	parser.add_argument('--adaptive', action = 'store_true')
	parser.add_argument('--oblivious', action = 'store_true')
	parser.add_argument('--solution', action = 'store_true')
	parser.add_argument('--append', action = 'store_true')

	# parse command line arguments
	args = parser.parse_args()

	# open output file
	filename = args.db + '_' + args.coll + \
				'_' + str(args.alpha) + '_' + str(args.bumps) + \
				'_' + str(args.radius) + '_' + str(args.signal) + \
				'_' + str(args.noise) + '.json'

	if args.append:
		json_file = open(filename, 'a')
	else:
		json_file = open(filename, 'w')

	# connect to database that contains graph
	graph_api = graph_db.Graph_Mongo_Explicit(args.db, args.coll)
	# generate query sets - one query set for each repetition of the algorithm
	print(graph_api, args.bumps, args.radius,
			args.signal, args.noise, args.repeats)
	query_collection =  _get_random_bumps(graph_api, args.bumps, args.radius,
										args.signal, args.noise, args.repeats)

	for repetition in range(args.repeats):

		query_dict = query_collection[repetition]
		query_nodes = extract_query_nodes(query_dict)
		sys.stderr.write('Generated %d query nodes.\n'%(len(query_nodes), ))
		
		# store statistics about the graph
		result = OD([('alpha', args.alpha)])
		result['q_size'] = len(query_nodes)
		result['bumps'] = args.bumps
		result['radius'] = args.radius
		result['signal'] = args.signal
		result['noise'] = args.noise
	
		if args.full:
			# FULL Expansion
			t0 = time.clock()
			full = bh.expand_query_nodes(graph_api,
											query_nodes, a=args.alpha)
			t1 = time.clock()
			full_exp = full[0]
		
			# gather statistics about the expansion
			exp_result = OD(result)
			exp_result['expansion_name'] = 'full'
			exp_result['approx_threshold'] = 1.0
			exp_result['exp_nodes'] = len(full_exp.nodes())
			exp_result['exp_edges'] = len(full_exp.edges())
			exp_result['exp_time'] = int(1000 * (t1 - t0))
			exp_result['api_calls'] = full[1]

		
			# employ algorithms
			bfs_res = _evaluate_algorithm(bh.bfs_heur_fast, 'bfs',
								full_exp, query_dict, args.alpha,
								args.solution, exp_result)	
			json_file.write(json.dumps(bfs_res) + '\n')
		
			mst_res = _evaluate_algorithm(bh.random_mst_heur,
								'mst', full_exp, query_dict, args.alpha,
								args.solution, exp_result)	
			json_file.write(json.dumps(mst_res) + '\n')
		
			scheme_res = _evaluate_algorithm(bh.mst_heur_scheme,
								'scheme', full_exp, query_dict, args.alpha,
								args.solution, exp_result)	
			json_file.write(json.dumps(scheme_res) + '\n')
		
			pcst_res = _evaluate_algorithm(bh.pcst_heur, 'pcst',
								full_exp, query_dict, args.alpha, args.solution,
								exp_result)	
			json_file.write(json.dumps(pcst_res) + '\n')

			json_file.flush()
	
		if args.adaptive:
			for approx_threshold in args.thresh:
				# SMART Expansion
				t0 = time.clock()
				smart = bh.smart_expand(graph_api, query_nodes,
									args.alpha, approx_threshold, args.samples)
				t1 = time.clock()
				smart_exp = smart[0]

				exp_result = OD(result)
				exp_result['expansion_name'] = 'smart'
				exp_result['approx_threshold'] = approx_threshold
				exp_result['exp_nodes'] = len(smart_exp.nodes())
				exp_result['exp_edges'] = len(smart_exp.edges())
				exp_result['exp_time'] = int(1000 * (t1 - t0))
				exp_result['api_calls'] = smart[1]
			
				## Employ Algorithms
				bfs_res = _evaluate_algorithm(bh.bfs_heur_fast,
									'bfs', smart_exp, query_dict,
									args.alpha, args.solution, exp_result)
				json_file.write(json.dumps(bfs_res) + '\n')
			
				mst_res = _evaluate_algorithm(bh.random_mst_heur,
									'mst', smart_exp, query_dict, args.alpha,
									args.solution, exp_result)	
				json_file.write(json.dumps(mst_res) + '\n')
			
				scheme_res = _evaluate_algorithm(bh.mst_heur_scheme,
									'scheme', smart_exp, query_dict,
									args.alpha, args.solution, exp_result)
				json_file.write(json.dumps(scheme_res) + '\n')
			
				pcst_res = _evaluate_algorithm(bh.pcst_heur, 'pcst',
									smart_exp, query_dict, args.alpha,
									args.solution, exp_result)	
				json_file.write(json.dumps(pcst_res) + '\n')
		
				json_file.flush()
	
		if args.oblivious:
			# NAIVE Expansion
			t0 = time.clock()
			naive = bh.naively_expand_query_nodes(graph_api, query_nodes, a=args.alpha)
			t1 = time.clock()
			naive_exp = naive[0]

			exp_result = OD(result)
			exp_result['expansion_name'] = 'naive'
			exp_result['approx_threshold'] = 1.0
			exp_result['exp_nodes'] = len(naive_exp.nodes())
			exp_result['exp_edges'] = len(naive_exp.edges())
			exp_result['exp_time'] = int(1000 * (t1 - t0))
			exp_result['api_calls'] = naive[1]
		
			## Employ Algorithm
			bfs_res = _evaluate_algorithm(bh.bfs_heur_fast, 'bfs', naive_exp,
				query_dict, args.alpha, args.solution, exp_result)	
			json_file.write(json.dumps(bfs_res) + '\n')
		
			mst_res = _evaluate_algorithm(bh.random_mst_heur, 'mst', naive_exp,
				query_dict, args.alpha, args.solution, exp_result)	
			json_file.write(json.dumps(mst_res) + '\n')
		
			scheme_res = _evaluate_algorithm(bh.mst_heur_scheme, 'scheme', naive_exp,
				query_dict, args.alpha, args.solution, exp_result)	
			json_file.write(json.dumps(scheme_res) + '\n')
		

			pcst_res = _evaluate_algorithm(bh.pcst_heur, 'pcst', naive_exp,
				query_dict, args.alpha, args.solution, exp_result)	
			json_file.write(json.dumps(pcst_res) + '\n')
	
			json_file.flush()

	json_file.close()
