# Makefile for Soul Protocol paper.
# Usage: make (builds PDF), make clean
# Requires: tectonic (brew install tectonic)

MAIN = main

.PHONY: all clean

all: $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex references.bib neurips_2025.sty
	tectonic $(MAIN).tex

clean:
	rm -f $(MAIN).pdf
