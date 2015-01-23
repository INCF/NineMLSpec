s/nineml/al/g
s/SpikeOutputEvent/OutputEvent('spikeoutput')/g
s/SpikeInputEvent/'spikeoutput'/g
s/Component/ComponentClass/g
s/ports/analog_ports/g
s/op=/reduce_op=/g
s/al.abstraction_layer/nineml.abstraction_layer/g

#sed -f automatic_update.sed --in-place='.bak' components/
