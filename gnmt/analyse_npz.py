import sys
import numpy as np
from contextlib import closing
import operator

def load_parameter_values(path):
    with closing(np.load(path)) as source:
        param_values = {}
        for name, value in source.items():
            if name != 'pkl':
                name_ = name.replace('-', '/')
                if not name_.startswith('/'):
                    name_ = '/' + name_
                param_values[name_] = value
    return param_values

params = load_parameter_values(sys.argv[1])
params['ALL'] = np.concatenate([mat.flatten() for mat in params.itervalues()])

std_bins = [float(i)/10.0+0.05 for i in range(-5,5)]
for field, mat in sorted(params.iteritems(), key=operator.itemgetter(0)):
    print("\n%s\n-----------------------" % field)
    print("SHAPE:\n%s" % (mat.shape,))
    print("HIST (auto-bins):")
    hist, bin_edges = np.histogram(mat)
    print("\n".join(["[%.2f,%.2f]\t%d" % (bin_edges[i], bin_edges[i+1], hist[i]) for i in xrange(len(hist))]))
    print("HIST (std-bins):")
    hist, bin_edges = np.histogram(mat, std_bins)
    print("\n".join(["[%.2f,%.2f]\t%d" % (bin_edges[i], bin_edges[i+1], hist[i]) for i in xrange(len(hist))]))
