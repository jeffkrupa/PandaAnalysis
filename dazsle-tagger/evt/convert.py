#!/usr/bin/env python

from PandaCore.Tools.script import * 
from PandaCore.Tools.root_interface import Selector 
import PandaCore.Tools.Functions
import numpy as np
import json 
import os

args = parse('--out', '--name', '--json')

try:
    os.makedirs(args.out)
except OSError:
    pass

with open(args.json) as jsonfile:
    payload = json.load(jsonfile)
    weight = payload['weight']
    basedir = payload['base']
    features = payload['features']
    cut = payload['cut']
    substructure_vars = payload['substructure_vars']
    for i,s in enumerate(payload['samples']):
        if s['name'] == args.name:
            samples = s['samples']
            y = i
            break
    else:
        logger.error(sys.argv[0], 'Could not identify process '+args.name)
        sys.exit(1)

s = Selector()
chain = root.TChain('Events')
for sample in samples:
    chain.AddFile(basedir + '/' + sample + '.root')

logger.info(sys.argv[0], 'Reading files for process '+args.name)
s.read_tree(chain, branches=(features+substructure_vars+[weight]), cut=cut)
#s.read_tree(chain, branches=(features+[weight]), cut=cut)
#print s['fj_cpf_pt'].T[0:30,:].shape
sortinds = s['fj_cpf_pt'].T[0:30,:].argsort(axis=0)
print s['fj_cpf_pt'].T[0:30,:][:,sortinds[::-1]]
print sortinds	
X = np.vstack([s[f].T[0:30,:] for f in features]).T 
W = s[weight]
#W *= 1000 / W.sum()
Y = y * np.ones(shape=W.shape)
substructure_varss = np.vstack([s[var] for var in substructure_vars]).T

def save(arr, label):
    fout = args.out+'/'+args.name+'_'+label+'.npy'
    np.save(fout, arr)
    logger.info(sys.argv[0], 'Saved to '+fout)

save(substructure_varss, 'ss_vars')
save(X, 'x')
save(Y, 'y')
save(W, 'w')
