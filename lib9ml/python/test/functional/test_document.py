import os.path
from nineml.document import read

loaded_9ml = read(os.path.join(os.path.dirname(__file__),
                               '..', '..', 'examples', 'HodgkinHuxley.xml'))
