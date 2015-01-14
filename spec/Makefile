TARGET=nineml_spec


# Temp while building AL spec doc
#all: Abstraction_Layer.pdf






all: main.tex main.dvi ${TARGET}.ps ${TARGET}.pdf Abstraction_Layer.pdf

long: main.tex long_main.dvi ${TARGET}.ps ${TARGET}.pdf



Abstraction_Layer.pdf: Abstraction_Layer.rst
	rst2pdf Abstraction_Layer.rst



#long_main.dvi: discussion.tex introduction.tex body.tex main.tex references.bib
#        latex main.tex
#        bibtex main
#        latex main.tex
#        latex main.tex

long_main.dvi:
	latex main.tex
	latex main.tex

main.dvi: main.tex
	latex main.tex


${TARGET}.pdf: ${TARGET}.ps
	ps2pdf ${TARGET}.ps ${TARGET}.pdf

${TARGET}.ps: main.dvi
	dvips main.dvi -t a4paper -Ppdf -G0 -o ${TARGET}.ps

clean:
	rm -f main.dvi main.aux main.bbl main.log ${TARGET}.ps ${TARGET}.pdf
	rm -rf Abstraction_Layer.pdf
