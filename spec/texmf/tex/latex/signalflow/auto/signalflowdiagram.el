(TeX-add-style-hook "signalflowdiagram"
 (lambda ()
    (LaTeX-add-environments
     "signalflow")
    (TeX-add-symbols
     '("textbelowof" 2)
     '("textrightof" 2)
     '("textaboveof" 2)
     '("vbullets" 1)
     "pathdrawcolor"
     "pathfillcolor"
     "operatordrawcolor"
     "operatorfillcolor"
     "blockdrawcolor"
     "blockfillcolor"
     "diagramlinewidth"
     "pathlinewidth"
     "operatorlinewidth"
     "blocklinewidth"
     "nodesize"
     "terminalsize"
     "operatorsize"
     "delaysize"
     "blockwidth"
     "blockheight"
     "blocktextwidth"
     "filterwidth"
     "filterheight"
     "filtertextwidth"
     "pathlineextend"
     "textleftof"
     "tikzgrid"
     "tikz")
    (TeX-run-style-hooks
     "tikz")))

