# Local Discrepancy Maximization on Graphs

This is the code repository for our [ICDE 2015](http://www.icde2015.kr) paper:

Aristides Gionis, Michael Mathioudakis, Antti Ukkonen, *"Bump Hunting in the Dark - Local Discrepancy Maximization on Graphs*", in the Proceedings of the 31st International Conference on Data Engineering (ICDE 2015), April 13th - 17th, 2015, Seoul, Korea

## Setup

The instructions below describe how to setup the code to run on a Mac and have been tested on Mac OS X v 10.10 Yosemite.

* Clone the repository on your computer. In what follows, we assume that the repository is installed in folder 'bump_hunting' on your machine, and you've opened a terminal at that directory.
* Install [python 2.7](https://www.python.org).
* Install and setup [mongodb](http://www.mongodb.org) and its python driver, [pymongo](http://api.mongodb.org/python/current/).
* Install [cython](http://cython.org). Then run the following in *bump_hunting/src* to generate file *bump_hunting/src/bingraph_fast.so*.

```
my_mac:bump_hunting/src $ python setup_bingraph_fast.py build_ext --inplace
```
* [Optional] Use mongoimport to import the datasets into mongodb. The datasets are provided as files that contain one json document per line (see also next section).

```
my_mac:bump_hunting $ mongoimport -d bumphunting -c geo --file data/geo.json
my_mac:bump_hunting $ mongoimport -d bumphunting -c grid --file data/grid.json
my_mac:bump_hunting $ mongoimport -d bumphunting -c ba --file data/ba.json
my_mac:bump_hunting $ mongoimport -d bumphunting -c pokec --file data/pokec.json
my_mac:bump_hunting $ mongoimport -d bumphunting -c livejournal --file data/livejournal.json
my_mac:bump_hunting $ mongoimport -d bumphunting -c patents --file data/patents.json
```

The lines above import each dataset in its own collection in database 'bumphunting'.


## Datasets

In our paper, we evaluate the studied algorithms on six graphs, three synthetic and three real ones.
The synthetic ones, 'grid', 'geo', and 'ba', were generated using [networkx]() and its [generators](http://networkx.github.io/documentation/networkx-1.9.1/reference/generators.html) for [two-dimensional grid](http://networkx.github.io/documentation/networkx-1.9.1/reference/generated/networkx.generators.classic.grid_2d_graph.html#networkx.generators.classic.grid_2d_graph), [geographical](http://networkx.github.io/documentation/networkx-1.9.1/reference/generated/networkx.generators.geometric.geographical_threshold_graph.html#networkx.generators.geometric.geographical_threshold_graph), and [barabasi-albert graph](http://networkx.github.io/documentation/networkx-1.9.1/reference/generated/networkx.generators.random_graphs.barabasi_albert_graph.html#networkx.generators.random_graphs.barabasi_albert_graph).
The real ones, 'pokec', 'livejournal', and 'patents', were collected from [SNAP](http://snap.stanford.edu).

In the interest of reproducibility of our results, we provide all of them in json format under folder *bump_hunting/data*.
Each line of each data file is a json document with three fields, '_id', 'neighbors', 'degree', that correspond to the id of a node in the respective graph, its list of neighbors (as a list of node-ids), and the degree of the node (the length of its neighbor list), respectively. For example, the following line is a json document that contains the id, neighbors, and degree of one node.

```
{ "_id" : 8, "neighbors" : [  1,  247089,  869832,  880477 ], "degree" : 4 }
```

## Running the code
File *bump_hunting/src/experiments/experiments.sh* contains the commands we used to run the experiments in our paper. For example, in the command

```
python src/experiments/measure.py -db bumphunting -coll grid -b 1 -r 4 -signal 20 -noise 0 --full --adaptive --oblivious -repeats 20 --solution
```
the arguments to *measure.py* have the following meaning:

* **-db bumphunting -coll grid**: use the 'grid' dataset, that can be found in mongodb database 'bumphunting' and collection 'grid',

*  **-b 1 -r 4 -signal 20 -noise 0**: plant one sphere (-b 1) of query nodes, of radius 4 (-r 4), with 20 query nodes inside the sphere (-signal 20), and 0 query nodes outside the sphere (-noise 0),

* **--full --adaptive --naive**: try 'full', 'adaptive' and 'oblivious' expansion,

* **-repeats 20**: repeat 20 times,

* **--solution**: store the solution for each instance (i.e. the set of nodes in the identified bump).

## Contributors

[Aristides Gionis](http://users.ics.aalto.fi/gionis/), 
[Michael Mathioudakis](http://michalis.co),
[Antti Ukkonen](http://www.anttiukkonen.com)
