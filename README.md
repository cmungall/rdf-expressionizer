# rdf-expressionizer

Translates named classes to equivalent class expressions.

The primary use case for this is rewiring ontologies that use upper ontologies such as BFO,
preserving semantic entailment, and hiding upper ontology classes in an orthogonal hierarchy.

## Installation

```bash
pipx install rdf-expressionizer
rdf-expressionizer --help
```

## Example Workflows

### Rewiring an ontology that uses BFO

```bash
rdf-expressionizer replace -m bfo_xbfo_mappings ro.owl -o ro-rewired.owl
```

Note that the semantics of axioms are preserved, but structurally rewritten.

For example, the following axiom:

 - [occurs in](http://purl.obolibrary.org/obo/BFO_0000066) Domain [occurrent nature](https://w3id.org/xbfo/0000003)

Is rewritten to:

 - [occurs in](http://purl.obolibrary.org/obo/BFO_0000066) Domain [has characteristic](http://purl.obolibrary.org/obo/RO_0000053) some [occurrent nature](https://w3id.org/xbfo/0000003)

TODO: decide on which ObjectProperty to use for `bfo_xbfo_mappings`

Note the resulting ontology has dangling flat label-less classes. These are semantically correct, but
to give them labels and hierarchy, merge with  [XBFO](https://w3id.org/xbfo).


```bash
robot merge -i ro-rewired.owl -i src/rdf-expressionizer/xbfo.owl -o ro-rewired-pretty.owl
```

### Rewiring an ontology preserving COB subset

```bash
rdf-expressionizer replace -x COB -m bfo_xbfo_mappings ro.owl -o ro-rewired.owl
```

This excludes (`-x` or `--exclude-subset`) the COB subset of BFO from the rewiring.

### Augmenting COB with equivalence axioms

```bash
rdf-expressionizer augment  -m bfo_xbfo_mappings cob.owl -o cob-augmented.owl
```

## Testing

```bash
git clone <this repo>
poetry install
make test
```

This runs internal unit tests, and additional tests.

One of the tests does the following:

- injects an invalid axiom into RO
    - `Cell occurs-in some 'Multi-cellular organism'`
    - this axiom is designed to cause incoherency when combined with upper level BFO disjointness axioms
- creates a rewired version of RO
- runs `robot explain`
- checks the intended unsatisfiable axiom is detected

* [cell](http://purl.obolibrary.org/obo/CL_0000000) SubClassOf [Nothing](http://www.w3.org/2002/07/owl#Nothing) ##

  - [cell](http://purl.obolibrary.org/obo/CL_0000000) SubClassOf [anatomical structure](http://purl.obolibrary.org/obo/UBERON_0000061)
    - [anatomical structure](http://purl.obolibrary.org/obo/UBERON_0000061) SubClassOf [material anatomical entity](http://purl.obolibrary.org/obo/UBERON_0000465)
      - [material anatomical entity](http://purl.obolibrary.org/obo/UBERON_0000465) SubClassOf [anatomical entity](http://purl.obolibrary.org/obo/UBERON_0001062)
        - [anatomical entity](http://purl.obolibrary.org/obo/UBERON_0001062) SubClassOf [has characteristic](http://purl.obolibrary.org/obo/RO_0000053) some [independent continuant nature](https://w3id.org/xbfo/0000004)
          - [independent continuant nature](https://w3id.org/xbfo/0000004) SubClassOf [continuant nature](https://w3id.org/xbfo/0000002)
  - [cell](http://purl.obolibrary.org/obo/CL_0000000) SubClassOf [occurs in](http://purl.obolibrary.org/obo/BFO_0000066) some [multicellular anatomical structure](http://purl.obolibrary.org/obo/UBERON_0010000)
    - [occurs in](http://purl.obolibrary.org/obo/BFO_0000066) Domain [has characteristic](http://purl.obolibrary.org/obo/RO_0000053) some [occurrent nature](https://w3id.org/xbfo/0000003)
  - [has characteristic](http://purl.obolibrary.org/obo/RO_0000053) some [continuant nature](https://w3id.org/xbfo/0000002) DisjointWith [has characteristic](http://purl.obolibrary.org/obo/RO_0000053) some [occurrent nature](https://w3id.org/xbfo/0000003)



## Limitations

- Ontology must be in RDF serialization
   - TODO: add options for non RDF/XML serializations