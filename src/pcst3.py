import sys
import networkx as nx
from threading import Timer

class Component:
    def __init__(self, nodeset, graph, idnum, parentYsum=0 ):
        self.graph      = graph
        self.nodeset    = nodeset
        self.y          = 0
        self.active     = True
        self.top        = True
        self.parentYsum = parentYsum
        self.idnum      = idnum
        self.weight     = sum( [ self.graph.node[v].get('pi',0) for v in self.nodeset ] )
    def __str__( self ):
        return str(self.idnum) + ":" + str( self.nodeset )
    def __repr__( self ):
        return self.__str__()
    def __lt__( self, other ):
        return self.idnum < other.idnum
    def __gt__( self, other ):
        return self.idnum > other.idnum
    def __eq__( self, other ):
        return self.idnum == other.idnum
    def __ne__( self, other ):
        return self.idnum != other.idnum
    def __hash__( self ):
        return self.idnum
    def delta(self):
        for u in self.nodeset:
            for v in self.graph[u]:
                if v not in self.nodeset:
                    if u < v:
                        yield (u,v)
                    else:
                        yield (v,u)
    def incrementY( self, amount ):
        self.y += amount
    def disable( self ):
        self.active = False
    def containsEdge( self, (u,v) ):
        return (u in self.nodeset) and (v in self.nodeset)
    def totalY( self ):
        return self.y + self.parentYsum

class ComponentFactory:
    def __init__( self ):
        self.counter = 0
    def newcomp( self, nodeset, graph, parentYsum=0 ):
        self.counter += 1
        return Component( nodeset, graph, self.counter, parentYsum )
    def merge( self, C1, C2 ):
        C1.top = False
        C2.top = False
        return self.newcomp( C1.nodeset | C2.nodeset, C1.graph, C1.totalY() + C2.totalY() )
    def grow( self, C, edge ):
        C.top = False
        return self.newcomp( C.nodeset | set( edge ), C.graph, C.totalY() )

class Stopper:
    def __init__(self, maxRuntime):
        self.running = True
        self.thread  = Timer( maxRuntime, self.deactivate )
        self.thread.start()
    def deactivate(self):
        self.running = False

def edge_gap( components, load ):
    active = 0
    for C in components:
        active += C.active
    if active == 0:
        return sys.maxint
    return (1.0 - load)/active

def comp_gap( C ):
    return C.weight - C.totalY()

def update_duals( components, amount ):
    for C in components:
        C.incrementY( amount )

def update_loads( X, edge_load, amount ):
    for e in edge_load:
        active = 0
        for C in X[e]:
            active += C.active
        if active > 0:
            edge_load[e] += amount*active

def get_min_comp_gap( active_components ):
    return min( [(comp_gap( C ), C) for C in active_components ] )

def get_min_edge_gap( X, edge_load ):
    mingap = sys.maxint
    mine   = None
    for (e,components) in X.iteritems():
        g = edge_gap( components, edge_load[e] )
        if g < mingap:
            mingap = g
            mine   = e
    return (mingap, mine)

def update_Xdict( X, newcomp, edge_load ):
    for e in newcomp.delta():
        ecomp = [ C for C in X.get( e, [] ) if C.top ]
        ecomp.append( newcomp )
        X[e] = ecomp
        edge_load.setdefault( e, 0 )

def cleanup_Xdict( X, newcomp, edge_load ):
    for e in [ e for e in X if newcomp.containsEdge( e ) ]:
        del X[e]
        del edge_load[e]

# maxRuntime is in seconds
def pcst_solve( G, verbose=False, maxRuntime=300 ):
    F = nx.Graph()
    cf = ComponentFactory()
    active_components = [ cf.newcomp( set([v]), G ) for v in G.nodes_iter()
                          if G.node[v].get('pi',0) > 0 ]
    if verbose:
        print active_components
    X = {}
    edge_load = {}
    for C in active_components:
        for e in C.delta():
            X.setdefault( e, [] ).append( C )
            edge_load[e] = 0
    if verbose:
        print "edge_load =", edge_load
        print "X =", X
    s = Stopper( float(maxRuntime) )
    while len(active_components)>0 and len(X)>0 and s.running:
        # min_comp_gap tells for every active component C how much its
        # dual variable can still afford to increase
        min_comp_gap = get_min_comp_gap( active_components )
        if verbose:
            print "min_comp_gap =", min_comp_gap
        assert min_comp_gap[0] >= 0
        # min_edge_gap tells for every edge e how much is still missing from
        # its dual constraint becoming tight
        min_edge_gap = get_min_edge_gap( X, edge_load )
        assert min_edge_gap[0] >= 0
        if verbose:
            print "min_edge_gap =", min_edge_gap
        # we check which of the two constraints becomes tight:
        if min_edge_gap[0] <= min_comp_gap[0]:
            if verbose: 
                print "edge constraint became tight"
            # an edge constraint became tight
            gap  = min_edge_gap[0]
            edge = min_edge_gap[1]
            # make sure the edge will not create a cycle
            if F.has_node( edge[0] ) and F.has_node( edge[1] ):
                assert edge[1] not in nx.node_connected_component( F, edge[0] )
            # add edge to solution
            F.add_edge( *edge )
            update_duals( active_components, gap )
            update_loads( X, edge_load, gap )
            # find the topmost components adjacent to edge...
            comp = X[edge]
            assert len(comp) <= 2
            # and remove edge from the delta-edge dictionary
            del X[edge]
            del edge_load[edge]
            newcomp = None
            if len(comp) == 2:
                # we must merge the components to a new one.
                assert comp[0].active or comp[1].active
                comp[0].disable()
                comp[1].disable()
                if verbose:
                    print "merging", comp[0], comp[1]
                newcomp = cf.merge( comp[0], comp[1] )
            else:
                # there's only one component that grows into a new one
                # that contains the node at the other end of the edge
                comp[0].disable()
                if verbose:
                    print "growing", comp[0], edge
                newcomp = cf.grow( comp[0], edge )
            # and add the newly added component to the list
            active_components.append( newcomp )
            # update the delta edge dictionary so that it
            # has proper entries for delta edges of newcomp
            # (only "top" components may remain)
            update_Xdict( X, newcomp, edge_load )
            # also, remove such edges from X that are fully contained
            # within the new component
            cleanup_Xdict( X, newcomp, edge_load )
        else:
            if verbose:
                print "component constraint became tight"
            # a component constraint became tight
            gap = min_comp_gap[0]
            update_duals( active_components, gap )
            update_loads( X, edge_load, gap )
            comp = min_comp_gap[1]
            comp.disable()
        # keep only the components that are still active...
        active_components = [ C for C in active_components if C.active ]
        if verbose:
            print "active =", active_components
            print "X =", X
            print "edge_load =", edge_load
    s.thread.cancel()
    if s.running:
        return F
    else:
        return nx.Graph()

def main():
    w = 1.0
    G = nx.Graph()
    # G.add_edge( 1,2 )
    # G.add_edge( 1,3 )
    # G.add_edge( 2,3 )
    # G.add_edge( 3,4 )
    # G.add_edge( 4,5 )
    # G.add_edge( 5,6 )
    # G.add_edge( 6,7 )
    # G.add_edge( 6,8 )
    # G.node[1]['pi'] = w
    # G.node[2]['pi'] = w
    # G.node[3]['pi'] = w
    # G.node[6]['pi'] = w
    G.add_edge( 1,2 )
    G.add_edge( 2,3 )
    G.add_edge( 3,7 )
    G.add_edge( 4,5 )
    G.add_edge( 4,6 )
    G.add_edge( 5,6 )
    G.add_edge( 6,7 )
    G.node[2]['pi'] = w
    G.node[4]['pi'] = w
    G.node[5]['pi'] = w
    G.node[6]['pi'] = w
    print pcst_solve( G, True ).edges()

if __name__=='__main__':
    main()
