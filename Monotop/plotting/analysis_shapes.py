#!/usr/bin/env python

from os import system,getenv
from sys import argv
import argparse

### SET GLOBAL VARIABLES ###
baseDir = getenv('PANDA_FLATDIR')+'/' 
dataDir = baseDir#.replace('0_4','0_4_egfix')
parser = argparse.ArgumentParser(description='plot stuff')
parser.add_argument('--outdir',metavar='outdir',type=str,default=None)
parser.add_argument('--cut',metavar='cut',type=str,default='1==1')
parser.add_argument('--region',metavar='region',type=str,default=None)
parser.add_argument('--tt',metavar='tt',type=str,default='')
args = parser.parse_args()
lumi = 35800.
blind=True
region = args.region
sname = argv[0]

argv=[]
import ROOT as root
root.gROOT.SetBatch()
from PandaCore.Tools.Misc import *
import PandaCore.Tools.Functions
#import PandaAnalysis.Monotop.MonojetSelection as sel
#import PandaAnalysis.Monotop.LooseSelection as sel
#import PandaAnalysis.Monotop.TightSelection as sel
import PandaAnalysis.Monotop.OneFatJetSelection as sel
#import PandaAnalysis.Monotop.TestSelection as sel
from PandaCore.Drawers.plot_utility import *

### DEFINE REGIONS ###

cut = tAND(sel.cuts[args.region],args.cut)

### LOAD PLOTTING UTILITY ###
plot = PlotUtility()
plot.Stack(False)
plot.SetTDRStyle()
plot.InitLegend()
plot.DrawMCErrors(True)
#plot.AddCMSLabel()
plot.cut = cut
plot.SetEvtNum("eventNumber")
plot.SetLumi(lumi/1000)
plot.SetNormFactor(True)
plot.AddSqrtSLabel()
plot.do_overflow = True
plot.do_underflow = True

weight = sel.weights[region]%lumi
plot.mc_weight = weight

#logger.info('cut',plot.cut)
#logger.info('weight',plot.mc_weight)

#plot.add_systematic('QCD scale','scaleUp','scaleDown',root.kRed+2)
#plot.add_systematic('PDF','pdfUp','pdfDown',root.kBlue+2)

### DEFINE PROCESSES ###
zjets         = Process('Z+jets',root.kZjets)
wjets         = Process('W+jets',root.kWjets)
ttbar         = Process('t#bar{t}',root.kTTbar)
signal1        = Process('m_{V}=1.75 TeV, m_{#chi}=1 GeV',root.kSignal)
signal2        = Process('m_{#phi}=2.9 TeV, m_{#psi}=100 GeV',root.kSignal2)
processes = [ttbar,wjets, zjets, signal1, signal2]

### ASSIGN FILES TO PROCESSES ###
zjets.add_file(baseDir+'ZtoNuNu.root')
ttbar.add_file(baseDir+'TTbar.root')
wjets.add_file(baseDir+'WJets.root')
signal1.add_file(baseDir+'Vector_MonoTop_NLO_Mphi-1750_Mchi-1_gSM-0p25_gDM-1p0_13TeV-madgraph.root')
signal2.add_file(baseDir+'Scalar_MonoTop_LO_Mphi-2900_Mchi-100_13TeV-madgraph.root')

for p in processes:
    plot.add_process(p)

recoilBins = [250,280,310,350,400,450,600,1000]
nRecoilBins = len(recoilBins)-1

recoil=VDistribution("pfmet",recoilBins,"p_{T}^{miss} [GeV]","Arbitrary units")
plot.add_distribution(recoil)

# plot.add_distribution(FDistribution('nJet',0.5,6.5,6,'N_{jet}','Events'))
# plot.add_distribution(FDistribution('npv',0,45,45,'N_{PV}','Events'))
plot.add_distribution(FDistribution('fj1MSD',0,250,20,'fatjet m_{SD} [GeV]','Arbitrary units'))
plot.add_distribution(FDistribution('fj1Pt',250,1000,20,'fatjet p_{T} [GeV]','Arbitrary units'))
plot.add_distribution(FDistribution('top_ecf_bdt',-1,1,20,'Top BDT','Arbitrary units'))
# plot.add_distribution(FDistribution('fj1MaxCSV',0,1,20,'fatjet max CSV','Events'))
# plot.add_distribution(FDistribution('fj1Tau32',0,1,20,'fatjet #tau_{32}','Events'))
# plot.add_distribution(FDistribution('fj1Tau32SD',0,1,20,'fatjet #tau_{32}^{SD}','Events'))
# plot.add_distribution(FDistribution('jet1CSV',0,1,20,'jet 1 CSV','Events',filename='jet1CSV'))
# plot.add_distribution(FDistribution('dphipfmet',0,3.14,20,'min#Delta#phi(jet,E_{T}^{miss})','Events'))
#plot.add_distribution(FDistribution("1",0,2,1,"dummy","dummy"))

### DRAW AND CATALOGUE ###
plot.draw_all(args.outdir+'/'+region+'_')
