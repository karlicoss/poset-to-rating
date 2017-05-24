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


class States:
    BETTER = "better"
    WORSE = "worse"
    SAME = "same"
    INCOMPARABLE = "incomparable"
    IGNORE = "ignore"

# movies = [Movie(v) for k, v in sorted(titles.items())]

# gen.shuffle(movies)

# sample = movies[:5]

# def compare_prompt():
#     pass

def load_state(fname: str) -> Dict[Tuple[str, str], str]:
    with open(fname, 'r') as fo:
        res = {}
        for line in fo:
            [st, a, b] = line.split(';')
            st = st.strip()
            a = a.strip()
            b = b.strip()
            if st not in ['>', '<', '?', '=', 'i']:
                print("State for {}; {} is invalid!".format(a, b))
                res[(a, b)] = None
            else:
                res[(a, b)] = st
        return res

def add_more(seed: int):
    state_fname = 'state.txt'
    old_state = load_state(state_fname)

    ratings = get_ratings_map("ratings.csv")
    all_movies = list(sorted(ratings.keys())) # TODO use movie ids instead?..

    gen = random.Random(x=seed)
    sample = gen.sample(all_movies, 7)

    import itertools
    tuples = set((a, b) for (a, b) in itertools.product(sample, sample) if a < b)
    for a, b in old_state.keys():
        if (a, b) in tuples:
            print("COLLISION!", a, b)
            tuples.remove((a, b))

    tsample = gen.sample(tuples, 10)

    with open(state_fname, 'a') as fo:
        for a, b in tsample:
            fo.write(" ;{};{}\n".format(a, b)) # TODO separator?

add_more(1123)

# TODO plot a dot graph?
# TODO better strategy: for each movie, pick a random one, iterate util you are satisfied with the graph
# TODO Fake edges to enforce lower bound on marks
