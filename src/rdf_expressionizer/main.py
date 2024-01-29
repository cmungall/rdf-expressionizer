"""Main python file."""

import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Tuple, Union

import curies
from curies import Converter
from pyoxigraph import BlankNode, NamedNode, Quad, Store, Triple, parse

RDF_TYPE = NamedNode("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
OWL_RESTRICTION = NamedNode("http://www.w3.org/2002/07/owl#Restriction")
OWL_ON_PROPERTY = NamedNode("http://www.w3.org/2002/07/owl#onProperty")
OWL_SOME_VALUES_FROM = NamedNode("http://www.w3.org/2002/07/owl#someValuesFrom")
SUBCLASS_OF = "http://www.w3.org/2000/01/rdf-schema#subClassOf"
EQUIVALENT_CLASS = "http://www.w3.org/2002/07/owl#equivalentClass"

PREFIX_MAP = Dict[str, str]

OBJECT_PROPERTY = NamedNode
REPLACEMENT_MAP = Dict[NamedNode, Tuple[OBJECT_PROPERTY, NamedNode]]


@dataclass
class ClassReplacement:
    named_class: str
    replacement_class: str
    replacement_property: str


def create_expression(replacement: Tuple[OBJECT_PROPERTY, NamedNode]) -> Tuple[BlankNode, List[Triple]]:
    """
    Generate triples for a class expression (some values from).

    >>> from pyoxigraph import NamedNode
    >>> ex = "http://example.com/"
    >>> bnode, triples = create_expression((NamedNode(f"{ex}p"), NamedNode(f"{ex}d1")))
    >>> for s, p, o in triples:
    ...     print("<BLANK>", p, o)
    ...     assert s == bnode
    <BLANK> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Restriction>
    <BLANK> <http://www.w3.org/2002/07/owl#onProperty> <http://example.com/p>
    <BLANK> <http://www.w3.org/2002/07/owl#someValuesFrom> <http://example.com/d1>

    :param named_entity:
    :param replacement_property:
    :param replacement_entity:
    :return:
    """
    bnode = BlankNode()
    triples = []
    triples.append(Triple(bnode, RDF_TYPE, OWL_RESTRICTION))
    triples.append(Triple(bnode, OWL_ON_PROPERTY, replacement[0]))
    triples.append(Triple(bnode, OWL_SOME_VALUES_FROM, replacement[1]))
    return bnode, triples


def create_logical_definition(term: NamedNode, replacement: Tuple[OBJECT_PROPERTY, NamedNode]) -> List[Triple]:
    """
    Create a logical definition for a term.

    >>> from pyoxigraph import NamedNode
    >>> ex = "http://example.com/"
    >>> term = NamedNode(f"{ex}c1")
    >>> triples = create_logical_definition(term, (NamedNode(f"{ex}p"), NamedNode(f"{ex}d1")))
    >>> len(triples)
    4

    :param term:
    :param replacement:
    :return:
    """
    bnode, triples = create_expression(replacement)
    triples.append(Triple(term, NamedNode(EQUIVALENT_CLASS), bnode))
    return triples


def expressionify_triples(
    triple_it: Iterable[Triple], replacement_map: REPLACEMENT_MAP, equivalence_map: REPLACEMENT_MAP = None
) -> Iterator[Triple]:
    """
    Replace named entities in triples.

    :param triple_it:
    :param replacement_map:
    :param replacement_property:
    :return:
    """
    nodes = set()
    for s, p, o in triple_it:
        if s in replacement_map:
            s, new_triples = create_expression(replacement_map[s])
            yield from new_triples
            nodes.add(s)
        if p in replacement_map:
            p, new_triples = create_expression(replacement_map[p])
            yield from new_triples
            nodes.add(p)
        if o in replacement_map:
            o, new_triples = create_expression(replacement_map[o])
            yield from new_triples
            if isinstance(o, NamedNode):
                nodes.add(o)
        yield Triple(s, p, o)
    if equivalence_map:
        for node in nodes:
            if node in equivalence_map:
                yield from create_logical_definition(node, equivalence_map[node])


def generate_equivalence_axioms(triple_it: Iterable[Triple], equivalence_map: REPLACEMENT_MAP) -> Iterator[Triple]:
    """
    Generate an equivalence axiom for each used term in the equivalence map.

    :param triple_it:
    :param replacement_map:
    :param replacement_property:
    :return:
    """
    nodes = set()
    for s, p, o in triple_it:
        nodes.add(s)
        nodes.add(p)
        if isinstance(o, NamedNode):
            nodes.add(o)
        yield Triple(s, p, o)
    for node in nodes:
        if node in equivalence_map:
            yield from create_logical_definition(node, equivalence_map[node])


def file_replace(
    path: Union[str, Path],
    replacement_map: REPLACEMENT_MAP,
    input_type="application/rdf+xml",
    replace=True,
    output_path: Union[str, Path] = None,
    output_type=None,
):
    """
    Replace named entities in a file.

    :param path:
    :param replacement_map:
    :return:
    """
    triple_it = parse(str(path), input_type)
    store = Store()
    if replace:
        for triple in expressionify_triples(triple_it, replacement_map):
            store.add(Quad(*triple))
    else:
        for triple in generate_equivalence_axioms(triple_it, replacement_map):
            store.add(Quad(*triple))
    if output_type is None:
        output_type = input_type
    store.dump(str(output_path), output_type)


@lru_cache()
def get_curie_converter(prefix_map: PREFIX_MAP = None) -> Converter:
    """
    Create a converter

    :param prefix_map:
    :return:
    """
    converter = curies.get_obo_converter()
    if prefix_map is None:
        prefix_map = {}
    if "XBFO" not in prefix_map:
        prefix_map["XBFO"] = "https://w3id.org/xbfo/"
    for k, v in prefix_map.items():
        converter.add_prefix(k, v)
    return converter


def named_node(n: str, prefix_map: PREFIX_MAP = None) -> NamedNode:
    """
    Create a named node

    :param n:
    :return:
    """
    curie_converter = get_curie_converter(prefix_map)
    return NamedNode(curie_converter.expand(n, passthrough=True))


def load_replacement_map(
    path: Union[str, Path],
    delimiter=",",
    prefix_map: PREFIX_MAP = None,
    exclude_subsets: Optional[List] = None,
    include_subsets: Optional[List] = None,
) -> REPLACEMENT_MAP:
    """
    Load a replacement map from a CSV.

    :param path:
    :return:
    """
    rmap = {}
    with open(path) as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            if row["source"] == "ID":
                # allow robot templates
                continue
            subsets = row["subsets"].split("|") if row.get("subsets", []) else []
            if exclude_subsets is not None and any([subset in exclude_subsets for subset in subsets]):
                # if the row is in a subset to be excluded
                continue
            if include_subsets is not None and not any([subset in include_subsets for subset in subsets]):
                # if the row is not in a subset to be includes
                continue
            rmap[named_node(row["source"], prefix_map)] = (
                named_node(row["property"], prefix_map),
                named_node(row["mapping"], prefix_map),
            )
    return rmap
