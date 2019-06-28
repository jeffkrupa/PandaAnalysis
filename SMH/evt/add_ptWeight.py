from __future__ import division

import ROOT
from ROOT import gROOT, TFile, TTree, TChain, gPad, gDirectory, AddressOf, TLorentzVector
from multiprocessing import Process
from optparse import OptionParser
from operator import add
import math 
import sys
import time
import array
import numpy as np
import os

gROOT.ProcessLine(
"struct TreeStruct {\
Float_t sf_ptWeight;\
}")

##############################################################################

from ROOT import TreeStruct

treestruct = TreeStruct()


def main(options,args):
        
  ifile = options.ifile
  tf = ROOT.TFile(ifile);
  tt = tf.Get("Events");
  nent = int(tt.GetEntries())

  histfile = ROOT.TFile(options.weightfile)#ratio histogram
  hist = histfile.Get(options.uhist)


  Apply = True;

  if Apply: applyRenormalization(tt,ifile,hist);


def applyRenormalization(tt,ifile,hist):

  nent = int(tt.GetEntries())
        
  #if (0!=tt.FindBranch("sf_metTrig")):
  #  tt.SetBranchStatus("sf_metTrig",0);

  output = ifile + "_tmp"
  ofile = ROOT.TFile(output,"RECREATE");

  otree = tt.CloneTree()
  
  sf_ptWeight = array.array( 'f', [-1.0])
  o_sf_ptWeight = otree.Branch("sf_ptWeight" , AddressOf(treestruct,'sf_ptWeight'), "sf_ptWeight/F" )

  for i in range(int(tt.GetEntries())):

    tt.GetEntry(i)
    
    treestruct.sf_ptWeight = -99.

    if(i % (1 * nent/100) == 0):
      sys.stdout.write("\r[" + "="*int(20*i/nent) + " " + str(round(100.*i/nent,0)) + "% done")
      sys.stdout.flush()

    #sf_metTrig = hist.Eval(tt.pfmet)

    #print (tt.fj_pt, hist.GetBinContent(hist.FindBin(tt.fj_pt)))
    if 'QCD' in ifile: treestruct.sf_ptWeight = max(hist.GetBinContent(hist.FindBin(tt.fj_pt)) , 0.01)
    else: treestruct.sf_ptWeight = 1.0
    
    o_sf_ptWeight.Fill()
            
  ofile.Write()
  ofile.Close()
  os.system("mv -f %s %s" % (output, ifile))
  

if __name__ == '__main__':
  parser = OptionParser()
  parser.add_option('-i','--ifile', dest='ifile', default = 'file.root',help='MC/data file to add the N2DDT branch to', metavar='ifile')
  parser.add_option('-t','--weightfile', dest='weightfile', default = 'files.root',help='MC/data file to add the pt weight to', metavar='weightfile')
  parser.add_option('-u','--uhist', dest='uhist', default = 'hi',help='MC/data file to add the N2DDT branch to', metavar='uhist')
        #parser.add_option('-ddt','--ddtfile', dest='ddtfile', default = '/home/bmaier/cms/MonoHiggs/higgstagging/N2DDT/h3_n2ddt.root',help='n2ddr.root file', metavar='ddtfile')
  
  (options, args) = parser.parse_args()
  
  main(options,args)
