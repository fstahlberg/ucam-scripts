import cPickle as pickle
import sys
import pprint

#132650d04aad49e89ad3f25bd9a72446
obj = pickle.load(open(sys.argv[1], "rb" ))
pprint.pprint(obj)
