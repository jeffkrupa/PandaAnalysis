#!/usr/bin/env python

from os import getenv

from PandaCore..Utils.root import root 
from PandaCore.Tools.Misc import *
from PandaCore.Utils.load import *
import PandaAnalysis.T3.job_utilities as utils
from PandaAnalysis.Flat.analysis import *

Load('PandaAnalyzer')
data_dir = getenv('CMSSW_BASE') + '/src/PandaAnalysis/data/'


def fn(input_name, isData, full_path):
    # now we instantiate and configure the analyzer
    a = monotop(True)
    a.recalcECF = True 
    a.varyJESTotal = True
    a.mcTriggers = True
    a.inpath = input_name
    a.outpath = utils.input_to_output(input_name)
    a.datapath = data_dir
    a.isData = isData
    utils.set_year(a, 2016)
    a.processType = utils.classify_sample(full_path, isData)	

    skimmer = root.pa.PandaAnalyzer(a)
    skimmer.AddPresel(root.pa.FatJetSel())

    return utils.run_PandaAnalyzer(skimmer, isData, a.outpath)


if __name__ == "__main__":
    utils.wrapper(fn, post_fn=utils.BDTAdder())
