RUN = poetry run
CODE = src/rdf_expressionizer

all: test

test: pytest doctest test-unsat


pytest:
	$(RUN) pytest

apidoc:
	$(RUN) sphinx-apidoc -f -M -o docs/ $(CODE)/ && cd docs && $(RUN) make html

doctest:
	$(RUN) python -m doctest --option ELLIPSIS --option NORMALIZE_WHITESPACE $(CODE)/*.py

%-doctest: %
	$(RUN) python -m doctest --option ELLIPSIS --option NORMALIZE_WHITESPACE $<

XBFO = $(CODE)/ontology/xbfo.owl

# create the xbfo ontology from the robot template, which shadows BFO, adding "nature" as a suffix
$(XBFO): $(CODE)/ontology/xbfo_template.csv
	robot template -p "XBFO: https://w3id.org/xbfo/" -t $< -o $@

# bridge between bfo and xbfo; simple shadow DP
$(CODE)/ontology/bfo_bridge.owl: $(CODE)/mappings/bfo_xbfo_mappings.csv
	robot template --merge-before -i $(XBFO) -p "XBFO: https://w3id.org/xbfo/" -t $< -o $@

$(CODE)/ontology/ro-rewired.owl: tests/input/ro.owl
	$(RUN) rdf-expressionizer replace -x COB -m bfo_xbfo_mappings $< -o $@
$(CODE)/ontology/ro-rewired-tidy.owl: $(CODE)/ontology/ro-rewired.owl $(XBFO)
	robot merge -i $< -i $(XBFO) -o $@

$(CODE)/ontology/cob-augmented.owl: tests/input/cob.owl
	$(RUN) rdf-expressionizer augment -m bfo_xbfo_mappings $< -o $@
$(CODE)/ontology/cob-augmented-tidy.owl: $(CODE)/ontology/cob-augmented.owl $(XBFO)
	robot merge -i $< -i $(XBFO) -o $@



# tidy-cob;
# subset_COB_ecob.owl comes from pytest
tests/output/cob2.owl: tests/output/subset_COB_ecob.owl $(XBFO)
	robot merge -i $< -i $(XBFO) -o $@

tests/output/cob2_plus_ro.owl: tests/output/cob2.owl tests/output/xro.owl
	robot merge $(patsubst %, -i %, $^) -o $@

tests/output/merged-%.owl: tests/output/%.owl $(XBFO)
	robot merge -i $< -i $(XBFO) -o $@

tests/output/%-explanations.md: tests/output/merged-%.owl
	robot explain -M unsatisfiability -i $< -u all -e $@

# check rewired ontology is entailment-preserving
test-unsat: tests/output/xro_unsat-explanations.md
	grep -F '[cell](http://purl.obolibrary.org/obo/CL_0000000) SubClassOf [Nothing](http://www.w3.org/2002/07/owl#Nothing)' $<
