import sys
import numpy as np
from random import random
from bingraph_fast import bfs_innerloop

class Idmap:
    def __init__( self ):
        self.id = 0
        self.map = {}
    def getId( self, x ):
        i = self.map.get( x, -1 )
        if i == -1:
            i = self.id
            self.id += 1
            self.map[x] = i
        return i
    def iteritems( self ):
        return self.map.iteritems()

def from_edgefile( edgefile, getIdMap=False ):
    def fileiter():
        for row in open( edgefile ):
            edge = row.strip().split()
            yield (edge[0], edge[1])
    return from_edgeiter( fileiter(), getIdMap )

# Assumes all edges are present in input.
def from_edgefile_fast( edgefile, num_nodes ):
    # first compute degree of every node
    degree = np.zeros( num_nodes, np.int32 )
    edge_counter = 0
    for row in open( edgefile ):
        edge = row.strip().split( ' ' )
        u = int(edge[0])
        v = int(edge[1])
        degree[u] += 1
        edge_counter += 1
    # figure out offset for every node
    offset = np.zeros( num_nodes, np.int32 )
    for i in xrange(1, num_nodes):
        offset[i] = offset[i-1] + degree[i-1]
    # compute adjacency lists
    degree[:] = 0
    adjlist = np.zeros( edge_counter, np.int32 )
    for row in open( edgefile ):
        edge = row.strip().split(' ')
        u = int( edge[0] )
        v = int( edge[1] )
        adjlist[ offset[u] + degree[u] ] = v
        degree[u] += 1
    return (degree, offset, adjlist)

# NOTE: This will make all graphs undirected by default!!
def from_edgeiter( edgelist, getIdMap=False ):
    G = {}
    i = 0
    for (u,v) in edgelist:
        G.setdefault( u, set() ).add( v )
        G.setdefault( v, set() ).add( u )
        i += 1
        if i == 1000:
            sys.stderr.write( '.' )
            i = 0
    sys.stderr.write('\n')
    return from_adjlistdict( G, getIdMap )

def from_adjlistdict( adjlistdict, getIdMap=False ):
    n = len( adjlistdict )
    offset = np.zeros( n, np.int32 )
    degree = np.zeros( n, np.int32 )
    nodeid = Idmap()
    o = 0
    for u in adjlistdict:
        i = nodeid.getId( u )
        offset[i] = o
        degree[i] = len( adjlistdict[u] )
        o += degree[i]
    adjlist = np.zeros( o, np.int32 )
    i = 0
    for u in adjlistdict:
        for v in adjlistdict[u]:
            adjlist[i] = nodeid.getId( v )
            i += 1
    if getIdMap:
        return (degree, offset, adjlist, nodeid)
    else:
        return (degree, offset, adjlist)

# Note: the graph saving/loading routines do not take nodeids into account!
# You must store/load them separately if needed.
def save_graph( degree, offset, adjlist, graphname ):
    np.save( graphname + '_degree.npy', degree )
    np.save( graphname + '_offset.npy', offset )
    np.save( graphname + '_adjlist.npy', adjlist )

# Note: the graph saving/loading routines do not take nodeids into account!
# You must store/load them separately if needed.
def load_graph( path_to_graph ):
    degree  = np.load( path_to_graph + '_degree.npy' )
    offset  = np.load( path_to_graph + '_offset.npy' )
    adjlist = np.load( path_to_graph + '_adjlist.npy' )
    return (degree, offset, adjlist)

# Functions for accessing neighbors:
def neighborlist( u, degree, offset, adjlist ):
    return [ adjlist[i] for i in xrange(offset[u], offset[u]+degree[u]) ]

def neighbor_iter( u, degree, offset, adjlist ):
    for i in xrange(offset[u], offset[u]+degree[u]):
        yield adjlist[i]
	
def run_bfs( d, o, a, r ):
    # sys.stderr.write( 'running bingraph.run_bfs on %d nodes and %d edges...' % (d.shape[0], a.shape[0]) )
    queue = np.zeros( d.shape[0], np.int32 )
    seen  = np.zeros( d.shape[0], np.int32 )
    bfs_tree_edge_u = np.zeros( d.shape[0], np.int32 )
    bfs_tree_edge_v = np.zeros( d.shape[0], np.int32 )
    bfs_tree = bfs_innerloop( d, o, a, r, queue, seen,
                              bfs_tree_edge_u, bfs_tree_edge_v )
    # sys.stderr.write( 'done!\n' )
    return bfs_tree

def main():
    # converts a full edgelist (with vertex indices in the range 0..(n-1) to a bingraph
    edgefile = sys.argv[1]
    num_nodes = int( sys.argv[2] )
    outputname = sys.argv[3]
    (d,o,a) = from_edgefile_fast( edgefile, num_nodes )
    save_graph( d, o, a, outputname )

if __name__=='__main__':
    main()
