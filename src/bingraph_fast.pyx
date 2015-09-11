import cython
cimport cython
import numpy as np
cimport numpy as np

@cython.boundscheck(False)
@cython.wraparound(False)
def bfs_innerloop( np.ndarray[np.int32_t, ndim=1] d,
                   np.ndarray[np.int32_t, ndim=1] o,
                   np.ndarray[np.int32_t, ndim=1] a,
                   Py_ssize_t r,
                   np.ndarray[np.int32_t, ndim=1] queue,
                   np.ndarray[np.int32_t, ndim=1] seen,
                   np.ndarray[np.int32_t, ndim=1] bfs_tree_edge_u,
                   np.ndarray[np.int32_t, ndim=1] bfs_tree_edge_v ):
    cdef Py_ssize_t queue_write_pos = 0
    cdef Py_ssize_t queue_read_pos  = 0
    cdef Py_ssize_t edge_write_pos = 0
    cdef Py_ssize_t u, v, k
    queue[ queue_write_pos ] = r
    queue_write_pos += 1
    seen[r] = 1
    while queue_write_pos > queue_read_pos:
        u = queue[ queue_read_pos ]
        queue_read_pos += 1
        for k in xrange( o[u], o[u] + d[u] ):
            v = a[k]
            if seen[v] == 0:
                seen[v] = 1
                queue[ queue_write_pos ] = v
                queue_write_pos += 1
                bfs_tree_edge_u[ edge_write_pos ] = u
                bfs_tree_edge_v[ edge_write_pos ] = v
                edge_write_pos += 1
    bfs_tree = []
    for k in xrange( edge_write_pos ):
        bfs_tree.append( (bfs_tree_edge_u[k], bfs_tree_edge_v[k]) )
    return bfs_tree
