#!/usr/bin/env python

from PandaCore.Tools.script import * 
from PandaCore.Tools.root_interface import Selector 
import PandaCore.Tools.Functions
import numpy as np
import json 
import os
import ROOT 
from ROOT import gStyle

args = parse('--out', '--json')

try:
    os.makedirs(args.out)
except OSError:
    pass

samples = []
with open(args.json) as jsonfile:
    payload = json.load(jsonfile)
    weight = payload['weight']
    basedir = payload['base']
    features = payload['features']
    cut = payload['cut']
    for i,s in enumerate(payload['samples']):
        print i, s['samples']
        for n in s['samples']: samples.append(n)


files = {} 
trees = {}
for f in samples:
   files[f] = ROOT.TFile.Open(basedir + '/' + f + '.root')
   trees[f] = files[f].Get('Events')

for fe in features:
    h0 = ROOT.TH1F("h0","h0",1000000,-5000.,5000.)
    trees['VectorDiJet1Jet_madgraph_Mphi115Mchi3000_13TeV_withPF'].Draw("%s>>h0"%fe,cut,"")
  
    firstbin = h0.FindFirstBinAbove(0.01,1)
    lastbin  = h0.FindLastBinAbove(0.01,1)

    minloc = h0.GetBinLowEdge(h0.FindFirstBinAbove(0.01,1))
    maxloc = h0.GetBinLowEdge(h0.FindLastBinAbove(0.01,1) + 1)

    h0.Reset()

    col = 0 
    maxval = []

    hists = {} 

    for k, tr in trees.iteritems():
       hists[k] = ROOT.TH1F(k, k, 100, minloc, maxloc) 
       #hists[k] = ROOT.TH1F(k, k, 10000, -2000., 2000.) 
       #print hists[k].Print("v all")
       tr.Draw("%s>>%s"%(fe,k),cut,"")
       hists[k].SetLineColor(col)
       hists[k].SetLineWidth(2)
       hists[k].SetTitle("")
       hists[k].GetXaxis().SetTitle(fe)
       col += 1
 
    QCD = ROOT.TH1F("QCD","QCD",100, minloc, maxloc)
    #QCD = ROOT.TH1F("QCD","QCD",10000, -2000., 2000.)
    QCD.SetLineColor(1)
    QCD.SetLineWidth(2)
    QCD.SetTitle("")
    QCD.GetXaxis().SetTitle(fe) 

    for k, hi in hists.iteritems():
        if 'QCD' not in k: continue
        QCD.Add(hi)

    for k in hists.keys():
       if 'QCD' in k: del hists[k]; continue

    #for k, hi in hists.iteritems():
    #   maxval.append(hists[k].GetMaximum()/hists[k].Integral())

    hists['QCD'] = QCD

    l0 = ROOT.TLegend(0.2,0.8,0.9,0.9)
    gStyle.SetLegendTextSize(0.04) 
    c0 = ROOT.TCanvas("c0","c0",800,600)
    print hists

    maxX = []
    minX = []

    for k, hi in hists.iteritems():
       maxval.append(hists[k].GetMaximum()/hists[k].Integral())
       maxX.append(hi.GetBinLowEdge(hi.FindLastBinAbove(0.01,1) + 1))
       minX.append(hi.GetBinLowEdge(hi.FindFirstBinAbove(0.01,1)))

    for k, hi in hists.iteritems():
       hists[k].Scale(1./hists[k].Integral())
       hists[k].GetYaxis().SetRangeUser(0.001,max(maxval)*1.3)
       #hists[k].GetXaxis().SetRangeUser(min(minX),max(maxX))
       hists[k].Draw("hist same")
       l0.AddEntry(hists[k], k)

    l0.Draw()
    c0.Draw()
    c0.SaveAs('plots/' + fe + ".png")
    c0.SaveAs('plots/' + fe + ".pdf")

    del h0; del c0; del l0
