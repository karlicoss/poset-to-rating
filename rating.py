#!/usr/bin/env python3
import csv
import json
import random
from typing import Dict, List, Set, Tuple

j = None
with open('data.json', 'r') as fo:
    j = json.load(fo)

titles = j['titles']

class Movie:
    def __init__(self, stuff: dict) -> None:
        self.stuff = stuff

    def genres(self) -> List[str]:
        return self.stuff['metadata']['genres']

    def title(self) -> str:
        return self.stuff['primary']['title']

    def id(self) -> str:
        return self.stuff['id']

    def __repr__(self, *args, **kwargs):
        return self.title()

def get_ratings_map(fname: str) -> Dict[str, float]:
    with open(fname, 'r') as fo:
        reader = csv.DictReader(fo)
        res = {}
        for line in reader:
            res[line['Title']] = float(line['You rated'])
        return res

class Ratings:
    def __init__(self, ratings: dict) -> None:
        self.ratings = ratings

    def register(self, m1: str, m2: str, res: str):
        key = (m1, m2)
        old = self.ratings.get(key)
        if old is None or old == res:
            self.ratings[key] = res
        else:
            print("UGH")

    def to_json(self) -> str:
        jform = {str(k): v for k, v in self.ratings.items()}
        return json.dumps(jform, indent=2)

    @staticmethod
    def from_json(jstr: str) -> 'Ratings':
        jform = json.loads(jstr)
        return Ratings({tuple(k.split(',')): v for k, v in jform.items()})

from enum import Enum
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

edge2sym = {
    v: k for k, v in sym2edge.items()
}

# movies = [Movie(v) for k, v in sorted(titles.items())]

# gen.shuffle(movies)

# sample = movies[:5]

# def compare_prompt():
#     pass

def load_state(fname: str) -> Dict[Tuple[str, str], Edge]:
    with open(fname, 'r') as fo:
        res = {} # type: Dict[Tuple[str, str], Edge]
        for line in fo:
            [st, a, b] = line.split(';')
            st = st.strip()
            a = a.strip()
            b = b.strip()
            if st not in ['>', '<', '?', '=', 'i']:
                print("State for {}; {} is invalid!".format(a, b))
                res[(a, b)] = None
            else:
                res[(a, b)] = sym2edge[st]
        return res

def plot():
    state_fname = 'state.txt'
    ratings_fname = 'ratings.csv'
    old_state = load_state(state_fname)
    ratings = get_ratings_map(ratings_fname)
    all_movies = list(sorted(ratings.keys())) # TODO use movie ids instead?..
    stats = {m: 0 for m in all_movies}
    for (a, b), s in old_state.items():
        # TODO only count if not ignored?
        if s in [Edge.BETTER, Edge.WORSE]:
            stats[a] += 1
            stats[b] += 1
    marked = list(sorted(m for (m, c) in stats.items() if c > 0))
    mmap = {}
    for i, m in enumerate(marked):
        mmap[m] = "n" + str(i)

# TODO 
# TODO neato looks nicer
# TODO tred: transitive reduction
# neato -Tpng graph.dot  -o graph.png 

    with open('graph.dot', 'w') as fo:
        fo.write('digraph test {')

        fo.write('size="20,20";\n')
        fo.write('dpi="600";\n')
        fo.write('ratio="fill";\n')
        for name, id_ in mmap.items():
            fo.write('  {} [label = "{}"];\n'.format(id_, name))
        for (a, b), st in old_state.items(): # TODO sorted order..
            if st == Edge.WORSE:
                fo.write('  {} -> {};\n'.format(mmap[a], mmap[b]))
            elif st == Edge.BETTER:
                fo.write('  {} -> {};\n'.format(mmap[b], mmap[a]))
        # TODO rest of edges?
        fo.write('}')

def add_more(seed: int):
    state_fname = 'state.txt'
    ratings_fname = 'ratings.csv'
    old_state = load_state(state_fname)
    ratings = get_ratings_map(ratings_fname)
    all_movies = list(sorted(ratings.keys())) # TODO use movie ids instead?..
    stats = {m: 0 for m in all_movies}
    for a, b in old_state:
        # TODO only count if not ignored?
        stats[a] += 1
        stats[b] += 1
    stats_by_edges = list(p[0] for p in sorted(stats.items(), key = lambda k: k[1]))

    gen = random.Random(x=seed)

    # sample = gen.sample(all_movies, 7)
    # import itertools
    # tuples = set((a, b) for (a, b) in itertools.product(sample, sample) if a < b)
    # tsample = gen.sample(tuples, 10)

    sample = stats_by_edges[:10]
    print("Lowerst stats:", sample)
    tuples = set()
    for a in sample:
        b = gen.choice(all_movies)
        if a == b:
            continue
        tp = (a, b) if a < b else (b, a)
        tuples.add(tp)

    for t in tuples:
        if t in old_state:
             print("COLLISION!", t)
             tuples.remove(t)
    tsample = tuples

    with open(state_fname, 'a') as fo:
        for a, b in tsample:
            fo.write(" ;{};{}\n".format(a, b)) # TODO separator?

plot()
# add_more(1122343)

# TODO plot a dot graph?
# TODO better strategy: for each movie, pick a random one, iterate util you are satisfied with the graph
# TODO Fake edges to enforce lower bound on marks
