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

def save_parameter_values(param_values, path):
    param_values = {name.replace("/", "-"): param
                    for name, param in param_values.items()}
    np.savez(path, **param_values)

params = []

for path in sys.argv[1].split(','):
    params.append(load_parameter_values(path))

n = 0.0 + len(params)
avg_params = {}

for field in params[0]:
    avg_params[field] = np.mean([p[field] for p in params], axis=0)

save_parameter_values(avg_params, sys.argv[-1])

