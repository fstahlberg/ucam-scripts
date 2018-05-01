import sys
import numpy as np
from contextlib import closing

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

params1 = load_parameter_values(sys.argv[1])
params2 = load_parameter_values(sys.argv[2])

if len(params1) != len(params2):
    sys.exit("Number of parameters differ: %d vs %d" %  (len(params1), len(params2)))

for field in params1.iterkeys():
    m1 = params1[field]
    m2 = params2[field]
    if m1.shape != m2.shape:
        print("%s: SHAPE DIFFERS: %s vs %s" %  (field, m1.shape, m2.shape))
    else:
        d = np.abs(m1 - m2)
        print("%s: max=%f avg=%f" % (field, np.max(d), np.mean(d)))
