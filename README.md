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
bump_hunting/src $ python setup_bingraph_fast.py build_ext --inplace
```

## Datasets

In our paper, we evaluate the studied algorithms on synthetic and real graphs. Due to github's file size constraints, we cannot post the datasets here. However, we've made them available on the project's page on [bitbucket](https://bitbucket.org/mmathioudakis/bump_hunting/wiki/Home), under folder *bump_hunting/data*.

### Data file format
Each line of each data file is a json document with three fields, '_id', 'neighbors', 'degree', that correspond to the id of a node in the respective graph, its list of neighbors (as a list of node-ids), and the degree of the node (the length of its neighbor list), respectively. For example, the following line is a json document that contains the id, neighbors, and degree of one node.

```
{ "_id" : 8, "neighbors" : [  1,  247089,  869832,  880477 ], "degree" : 4 }
```

### Importing the datasets into mongodb
You can import into mongodb the json file containing a graph (*'mygraph.json'*) with the following command.
`bump_hunting $ mongoimport -d bumphunting -c dataset --file mygraph.json`
The line above imports the dataset in its own collection in database 'bumphunting'.

## Running the code
File *bump_hunting/src/experiments/experiments.sh* contains the commands we used to run the experiments in our paper. For example, in the command

```
python src/experiments/measure.py -db bumphunting -coll mygraph -b 1 -r 4 -signal 20 -noise 0 --full --adaptive --oblivious -repeats 20 --solution
```
the arguments to *measure.py* have the following meaning:

* **-db bumphunting -coll grid**: use the dataset stored in mongodb database 'bumphunting' and collection 'mygraph',

*  **-b 1 -r 4 -signal 20 -noise 0**: plant one sphere (-b 1) of query nodes, of radius 4 (-r 4), with 20 query nodes inside the sphere (-signal 20), and 0 query nodes outside the sphere (-noise 0),

* **--full --adaptive --naive**: try 'full', 'adaptive' and 'oblivious' expansion,

* **-repeats 20**: repeat 20 times,

* **--solution**: store the solution for each instance (i.e. the set of nodes in the identified bump).

## Contributors

[Aristides Gionis](http://users.ics.aalto.fi/gionis/), 
[Michael Mathioudakis](http://michalis.co),
[Antti Ukkonen](http://www.anttiukkonen.com)
