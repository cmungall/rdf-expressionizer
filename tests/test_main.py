from pathlib import Path
from typing import Any

import pytest
from pyoxigraph import NamedNode, Triple, BlankNode

from rdf_expressionizer.main import expressionify_triples, SUBCLASS_OF, RDF_TYPE, OWL_ON_PROPERTY, \
    OWL_SOME_VALUES_FROM, OWL_RESTRICTION, file_replace, load_replacement_map
from rdf_expressionizer.mappings import BFO_MAPPINGS

THIS_DIR = Path(__file__).parent
INPUT_DIR = THIS_DIR / "input"
OUTPUT_DIR = THIS_DIR / "output"

EX = "http://example.com/"

C1 = f"{EX}c1"
C2 = f"{EX}c2"
D1 = f"{EX}d1"
D2 = f"{EX}d2"
MIXIN_P = f"{EX}mixin_p"
BNODE1 = BlankNode()
BNODE2 = BlankNode()


def triple(s: Any, p: Any, o: Any) -> Triple:
    """
    Create a triple
    :param s:
    :param p:
    :param o:
    :return:
    """
    if isinstance(s, str):
        s = NamedNode(s)
    if isinstance(p, str):
        p = NamedNode(p)
    if isinstance(o, str):
        o = NamedNode(o)
    return Triple(s, p, o)


def triple_with_blank_conflated(triple: Triple) -> Triple:
    """
    Create a triple minus blank node
    :param triple:
    :return:
    """
    def conflate_blank(node: Any) -> Any:
        if isinstance(node, BlankNode):
            return NamedNode("http://example.com/FAKE_BLANK")
        return node
    return Triple(*[conflate_blank(node) for node in triple])

@pytest.mark.parametrize("name,triples,replacement_map,expected", [
    (
        "gci",
        [triple(C1, SUBCLASS_OF, C2)],
        {C1: (MIXIN_P, D1),
         C2: (MIXIN_P, D2)},
        [triple(BNODE1, SUBCLASS_OF, BNODE2),
            triple(BNODE1, RDF_TYPE, OWL_RESTRICTION),
            triple(BNODE1, OWL_ON_PROPERTY, MIXIN_P),
            triple(BNODE1, OWL_SOME_VALUES_FROM, D1),
            triple(BNODE2, RDF_TYPE, OWL_RESTRICTION),
            triple(BNODE2, OWL_ON_PROPERTY, MIXIN_P),
            triple(BNODE2, OWL_SOME_VALUES_FROM, D2),
        ],
     ),
     (
        "named_class",
        [triple(C1, SUBCLASS_OF, C2)],
        {
         C2: (MIXIN_P, D2)},
        [triple(C1, SUBCLASS_OF, BNODE2),
            triple(BNODE2, RDF_TYPE, OWL_RESTRICTION),
            triple(BNODE2, OWL_ON_PROPERTY, MIXIN_P),
            triple(BNODE2, OWL_SOME_VALUES_FROM, D2),
        ],
     ),
    (
        "none",
        [triple(C1, SUBCLASS_OF, C2)],
        {},
        [triple(C1, SUBCLASS_OF, C2)
        ],
     ),
])
def test_replacement(name, triples, replacement_map, expected):
    """
    Test replacement
    :param triples:
    :param replacement_map:
    :return:
    """
    replacement_map = {NamedNode(k): (NamedNode(v[0]), NamedNode(v[1])) for k, v in replacement_map.items()}
    results = list(expressionify_triples(triples, replacement_map))
    for result in results:
        print(result)
        found = False
        if result in expected:
            expected.remove(result)
            found = True
        else:
            for e in expected:
                if triple_with_blank_conflated(e) == triple_with_blank_conflated(result):
                    expected.remove(e)
                    found = True
                    break
        assert found, f"Could not find {result} in {expected}"
    assert len(expected) == 0, f"Did not find {expected}"


@pytest.mark.parametrize("subset,expected_size", [
    (None, 35),
    ("COB", 26),
])
def test_load_replacement_map(subset, expected_size):
    """
    Test loading a replacement map
    :return:
    """
    rmap = load_replacement_map(BFO_MAPPINGS, exclude_subsets=[subset] if subset else None)
    print(subset)
    print(rmap)
    assert len(rmap) == expected_size

@pytest.mark.parametrize("input_name,mappings_path,replace,subset", [
    ("ro.owl", BFO_MAPPINGS, True, None),
    ("ro_unsat.owl", BFO_MAPPINGS, True, None),
    ("bfo.owl", BFO_MAPPINGS, True, None),
    ("cob.owl", BFO_MAPPINGS, True, None),
    ("cob.owl", BFO_MAPPINGS, True, "COB"),
    ("cob.owl", BFO_MAPPINGS, False, None),
    ("cob.owl", BFO_MAPPINGS, False, "COB"),
])
def test_file_replacement(input_name, mappings_path: str, replace, subset):
    """
    Test replacement on a file

    TODO: Add checks so this is not TestByGuru
    """
    if subset:
        subsets = [subset]
        if replace:
            replacement_map = load_replacement_map(mappings_path, exclude_subsets=subsets)
        else:
            replacement_map = load_replacement_map(mappings_path, include_subsets=subsets)
    else:
        replacement_map = load_replacement_map(mappings_path)
    print(input_name, len(replacement_map))
    OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
    outname = f"x{input_name}"
    if not replace:
        outname = f"e{input_name}"
    if subset:
        outname = f"subset_{subset}_{outname}"
    file_replace(INPUT_DIR / input_name, replacement_map, replace=replace, output_path=OUTPUT_DIR / outname)
