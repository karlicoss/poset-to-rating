#!/usr/bin/env python3
import csv
from enum import Enum
import json
import random
from typing import Dict, List, Set, Tuple

def invmap(d: Dict) -> Dict:
    res = {v: k for (k, v) in d.items()}
    if len(d) != len(d):
        raise RuntimeError("Dictionary is not bijective!")
    return res


class Movie:
    def __init__(self, title: str, rating: str) -> None:
        self.title = title
        self.rating = rating


class Edge(Enum):
    WORSE = "worse" # <
    BETTER = "better" # >
    SAME = "same" # = presumably, movies in same category, but use it any time you know you just can't choose which one is best
    INCOMPARABLE = "incomparable" # ? e.g. for movies in completely different categories (e.g) documentary vs action
    IGNORE = "ignore" # use ignore if you don't really remember the movie, e.g. for later handling

sym2edge = {
    '<': Edge.WORSE,
    '>': Edge.BETTER,
    '=': Edge.SAME,
    '?': Edge.INCOMPARABLE,
    'i': Edge.IGNORE,
}

edge2sym = invmap(sym2edge)


class RatingGraph:
    def __init__(self, id2movie: Dict[str, Movie], graph: Dict[str, List[str]]) -> None:
        self.id2movie = id2movie
        self.graph = graph

    @classmethod
    def load(cls, imdb_fname: str, ratings_fname: str):
        id2movie = {}
        with open(imdb_fname, 'r') as fo:
            reader = csv.DictReader(fo)
            for i, line in enumerate(reader):
                title = line['Title']
                rating = line['You rated']
                id_ = "n" + str(i)
                id2movie[id_] = Movie(title, rating)

        title2id = invmap({k: v.title for k, v in id2movie.items()})
        graph = {id_: [] for id_ in id2movie} # type: Dict[str, List[str]]
        with open(ratings_fname, 'r') as fo:
            for line in fo:
                [st, a, b] = line.split(';')
                st = st.strip()
                a = a.strip()
                b = b.strip()
                ida = title2id[a]
                idb = title2id[b]
                edge = None
                if st not in sym2edge:
                    print("State for {}; {} is invalid!".format(a, b))
                else:
                    edge = sym2edge[st]
                if edge == Edge.WORSE:
                    graph[ida].append(idb)
                elif edge == Edge.BETTER:
                    graph[idb].append(ida)
                else:
                    pass # can't do mych at this point?
        return cls(id2movie, graph)


    # TODO tred: transitive reduction
    # dot -Tpng graph.dot  -o graph.png 
    # TODO update dynamically, you can see the nodes moving and laying out.
    def plot(self, dot_fname: str) -> None:
        for id_ in sorted(self.id2movie.keys(), key=lambda s: int(s[1:])):
            print(id_, self.id2movie[id_].title)

        dot_contents = ""
        def app(s):
            nonlocal dot_contents
            dot_contents += s + "\n"
        app('digraph test {')
        app('rankdir=BT;')
        app('size="20, 5";')
        app('dpi="500";')
        app('ratio="fill";')

        edges = []
        for from_, tos in sorted(self.graph.items()):
            for to in tos:
                edges.append('  {} -> {};'.format(from_, to))
        for e in edges:
            app(e)
        # dsu = Dsu(mmap.values())
            # elif st == Edge.SAME:
            #     ma = mmap[a]
            #     mb = mmap[b]
            #     # dsu.merge(ma, mb)

        vcolor = {}
        # groups = dsu.get_groups()
        # groups = {k: v for (k, v) in groups.items() if len(v) > 1}
        # colors = ['yellow', 'red', 'green', 'blue', 'magenta']
        # for col, g in zip(colors, groups.values()):
        #     for v in g:
        #         vcolor[v] = col

        rat2color = {
            "10": "red",
            "9": "green",
            "8": "blue",
            "7": "yellow",
        }
        for id_, movie in self.id2movie.items():
            vcolor[id_] = rat2color.get(movie.rating, 'white')

        for id_ in self.graph:
            # label = name
            # rating = ratings[id2name[id_]]
            label = id_

            fillc = vcolor.get(id_, 'white')

            app('  {} [shape=circle, fillcolor={} style=filled label = "{}"];'.format(id_, fillc, label))

        app('}')
        with open(dot_fname, 'w') as fo:
            fo.write(dot_contents)

state_fname = 'state.txt'
ratings_fname = 'ratings.csv'
graph = RatingGraph.load(ratings_fname, state_fname)

class Dsu:
    def __init__(self, items: List) -> None:
        self.parents = {i: i for i in items}

    def merge(self, i, j):
        pi = self.get_parent(i)
        pj = self.get_parent(j)
        if pi == pj:
            return
        else:
            self.parents[pj] = pi

    def get_parent(self, i):
        pp = self.parents[i]
        if pp == i:
            return i
        else:
            return self.get_parent(pp)

    def get_groups(self):
        groups = {}
        for k in self.parents:
            rp = self.get_parent(k)
            l = groups.get(rp, [])
            l.append(k)
            groups[rp] = l
        return groups


def add_more(seed: int):
    stats = {k: len(v) for k, v in graph.graph.items()}
    for from_, tos in graph.graph.items():
        for to in tos:
            stats[to] += 1
    stats_by_count = list(p[0] for p in sorted(stats.items(), key = lambda k: (k[1], k[0])))
    sample = stats_by_count[:15]
    print("Lowest stats:", sample)

    gen = random.Random(x=seed)

    # sample = gen.sample(all_movies, 7)
    # import itertools
    # tuples = set((a, b) for (a, b) in itertools.product(sample, sample) if a < b)
    # tsample = gen.sample(tuples, 10)

    tuples = set()
    for a in sample:
        b = gen.choice(list(graph.id2movie.keys()))
        if a == b or b in graph.graph[a]:
            print("COLLISION, SKIPPING {} {}".format(a, b))
            continue
        ta = graph.id2movie[a].title
        tb = graph.id2movie[b].title # TODO get_title
        tp = (ta, tb) if ta < tb else (tb, ta)
        tuples.add(tp)

    with open(state_fname, 'a') as fo:
        for a, b in tuples:
            fo.write(" ;{};{}\n".format(a, b)) # TODO separator?

graph.plot('graph.dot')
# add_more(4362376737)

# TODO right now, the best movies get priority since they dont have out
# TODO Fake edges to enforce lower bound on marks
# TODO even better strategy: connect unconnected components to build a spanning tree?
# TODO compare with IMDB ratings afterwards. correlation?
# TODO split marks uniformly by weight? So 10% of the movies get 1 point 
# TODO I didn't watch some of the movies for a while, so some movies rated 10 end up having low rating.
#      perhaps some sort of 'confidence'? Depending on how long ago you watched the movie
