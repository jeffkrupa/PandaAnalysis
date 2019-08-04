import ROOT
from ROOT import TFile, TTree, TChain, gPad, gDirectory
from multiprocessing import Process
from optparse import OptionParser
from operator import add
import math
import sys
import time
import array
import numpy
##############################################################################
## binning
nrho  = 81;
rholo = -5.5;
rhohi = -2.;
npt   = 81;
ptlo  = 400;
pthi  = 1000;
nn2   = 100;
n2lo  = 0.0;
n2hi = 1.0;
QOI = 0.95


def main(args):
	
	sf = 1;
        tf = ROOT.TFile(args.infile)
	tt = tf.Get("Events");
	nent = int(tt.GetEntries())

	build = True;
	validate = True;

	if build: buildDDTMap(tt,args);
	if validate: validateTransformation(tt,args);

######--------------------------------------------------------------------------------------------------------
######--------------------------------------------------------------------------------------------------------
def buildDDTMap(tt,args):

	sf = 1;

	h3map = ROOT.TH3F("h3map",";#rho = log(#it{m}^{2}/#it{p}_{T}^{2});#it{p}_{T} (GeV);dazsle-tagger", 
					nrho,rholo,rhohi,
					npt,ptlo,pthi,
					nn2,n2lo,n2hi)

	h2ddt = ROOT.TH2F("h2ddt",";#rho = log(#it{m}^{2}/#it{p}_{T}^{2});#it{p}_{T} (GeV)", 
					nrho,rholo,rhohi,
					npt,ptlo,pthi);

	nent = int(tt.GetEntries())
	for i in range(int(tt.GetEntries())):

		if i % sf != 0: continue;
		
		tt.GetEntry(i)

		if(i % (1 * nent/100) == 0):
			sys.stdout.write("\r[" + "="*int(20*i/nent) + " " + str(round(100.*i/nent,0)) + "% done")
			sys.stdout.flush()

		weight = 1
		jmsd_8 = tt.fj_msd
		jpt_8  = tt.fj_pt			
		if jmsd_8 <= 0: jmsd_8 = 0.01

		rh_8 = math.log(jmsd_8*jmsd_8/jpt_8/jpt_8)
		jtN2b1sd_8 = tt.grudt_std

		h3map.Fill(rh_8,jpt_8,jtN2b1sd_8,weight);	

	print "\n total integral: ", h3map.Integral();
	nXbins = h3map.GetXaxis().GetNbins();
	nYbins = h3map.GetYaxis().GetNbins();	
	for ix in range(nXbins):
		for iy in range(nYbins):
			tmpzproj = h3map.ProjectionZ(h3map.GetName()+str(ix)+str(iy),ix+1,ix+1,iy+1,iy+1);
			print ix+1, iy+1, tmpzproj.Integral();
			probSum = array.array('d', [QOI])
			q = array.array('d', [0.0]*len(probSum))
			tmpzproj.GetQuantiles(len(probSum), q, probSum)
			h2ddt.SetBinContent( ix+1, iy+1, q[0] );		

	makeCanvas2D(h2ddt);

	fo =  ROOT.TFile(args.figdir+"h3_n2ddt.root","RECREATE");
	h3map.Write();
	h2ddt.Write();
	fo.Close();

######--------------------------------------------------------------------------------------------------------
######--------------------------------------------------------------------------------------------------------
def validateTransformation(tt,args):

	sf = 1;

	f_h2ddt = ROOT.TFile(args.figdir+"h3_n2ddt.root");
	trans_h2ddt = f_h2ddt.Get("h2ddt");

	h_rho = ROOT.TH1F("h_rho","; #rho = log(#it{m}^{2}/#it{p}_{T}^{2}); N", nrho, rholo, rhohi);
	h_jtN2b1sd = ROOT.TH1F("h_jtN2b1sd","; dazsle-tagger; N", 50, n2lo, n2hi);
	h_jtN2b1sdddt = ROOT.TH1F("h_jtN2b1sdddt","; dazsle-taggerDDT; N", 50, n2lo-0.2, n2hi-0.2);
	h2_rhoVpt_fail = ROOT.TH2F("h2_rhoVpt_fail","; #rho = log(#it{m}^{2}/#it{p}_{T}^{2}); #it{p}_{T} (GeV)", nrho, rholo, rhohi, npt, ptlo, pthi);
	h2_rhoVpt_pass = ROOT.TH2F("h2_rhoVpt_pass","; #rho = log(#it{m}^{2}/#it{p}_{T}^{2}); #it{p}_{T} (GeV)", nrho, rholo, rhohi, npt, ptlo, pthi);
	h2_rhoVpt_pafa = ROOT.TH2F("h2_rhoVpt_pafa","; #rho = log(#it{m}^{2}/#it{p}_{T}^{2}); #it{p}_{T} (GeV)", nrho, rholo, rhohi, npt, ptlo, pthi);
	h_rhos = [];
	h_rhos_fail = [];
	h_rhos_pass = [];
	h_rhos_pafa = [];
	h2s_n2Vrho = [];
	h2s_n2ddtVrho = [];
	for j in range(npt):
		h_rhos.append( ROOT.TH1F("h_rho"+str(j),"; #rho; N", nrho, rholo, rhohi) );
		h_rhos_fail.append( ROOT.TH1F("h_rhos_fail"+str(j),"; #rho = log(#it{m}^{2}/#it{p}_{T}^{2}); N", nrho, rholo, rhohi) );
		h_rhos_pass.append( ROOT.TH1F("h_rhos_pass"+str(j),"; #rho = log(#it{m}^{2}/#it{p}_{T}^{2}); N", nrho, rholo, rhohi) );
		h_rhos_pafa.append( ROOT.TH1F("h_rhos_pafa"+str(j),"; #rho = log(#it{m}^{2}/#it{p}_{T}^{2}); N", nrho, rholo, rhohi) );
		h2s_n2Vrho.append( ROOT.TH2F("h2s_n2Vrho"+str(j),"; #rho = log(#it{m}^{2}/#it{p}_{T}^{2}); dazsle-tagger", nrho, rholo, rhohi, 50, n2lo, n2hi) );
		h2s_n2ddtVrho.append( ROOT.TH2F("h2s_n2ddtVrho"+str(j),"; #rho = log(#it{m}^{2}/#it{p}_{T}^{2}); dazsle-taggerDDT", nrho, rholo, rhohi, 50, n2lo-0.2, n2hi-0.2) );

	nent = int(tt.GetEntries())
	for i in range(int(tt.GetEntries())):

		if i % sf != 0: continue;
		tt.GetEntry(i)

		if(i % (1 * nent/100) == 0):
			sys.stdout.write("\r[" + "="*int(20*i/nent) + " " + str(round(100.*i/nent,0)) + "% done")
			sys.stdout.flush()


		weight = 1
		jmsd_8 = tt.fj_msd
		jpt_8  = tt.fj_pt		
		if jmsd_8 <= 0: jmsd_8 = 0.01

		rh_8 = math.log(jmsd_8*jmsd_8/jpt_8/jpt_8)
		jtN2b1sd_8 = tt.grudt_std
		cur_rho_index = trans_h2ddt.GetXaxis().FindBin(rh_8);
		cur_pt_index  = trans_h2ddt.GetYaxis().FindBin(jpt_8);
		if rh_8 > trans_h2ddt.GetXaxis().GetBinUpEdge( trans_h2ddt.GetXaxis().GetNbins() ): cur_rho_index = trans_h2ddt.GetXaxis().GetNbins();
		if rh_8 < trans_h2ddt.GetXaxis().GetBinLowEdge( 1 ): cur_rho_index = 1;
		if jpt_8 > trans_h2ddt.GetYaxis().GetBinUpEdge( trans_h2ddt.GetYaxis().GetNbins() ): cur_pt_index = trans_h2ddt.GetYaxis().GetNbins();
		if jpt_8 < trans_h2ddt.GetYaxis().GetBinLowEdge( 1 ): cur_pt_index = 1;

		# print trans_h2ddt.GetBinContent(cur_rho_index,cur_pt_index),cur_rho_index,cur_pt_index,rh_8,jpt_8
		jtN2b1sdddt_8 = jtN2b1sd_8 - trans_h2ddt.GetBinContent(cur_rho_index,cur_pt_index);

		h_rho.Fill(rh_8,weight);
		h_jtN2b1sd.Fill(jtN2b1sd_8,weight);
		h_jtN2b1sdddt.Fill(jtN2b1sdddt_8,weight);
		if jtN2b1sdddt_8 < 0:
			h2_rhoVpt_pafa.Fill(rh_8,jpt_8,weight);
			h2_rhoVpt_pass.Fill(rh_8,jpt_8,weight);
		if jtN2b1sdddt_8 > 0:
			h2_rhoVpt_fail.Fill(rh_8,jpt_8,weight);

		for j in range(npt):
			# print trans_h2ddt.GetYaxis().GetBinLowEdge(j+1),jpt_8
			if jpt_8 > trans_h2ddt.GetYaxis().GetBinLowEdge(j+1) and jpt_8 < trans_h2ddt.GetYaxis().GetBinUpEdge(j+1): 
				h_rhos[j].Fill(rh_8,weight); 
				h2s_n2Vrho[j].Fill(rh_8,jtN2b1sd_8,weight);
				h2s_n2ddtVrho[j].Fill(rh_8,jtN2b1sdddt_8,weight);
				if jtN2b1sdddt_8 < 0: 
					h_rhos_pass[j].Fill(rh_8,weight);
					h_rhos_pafa[j].Fill(rh_8,weight);
				if jtN2b1sdddt_8 > 0: 
					h_rhos_fail[j].Fill(rh_8,weight);
				break;

	print "\n";

	h2_rhoVpt_pafa.Sumw2();
	h2_rhoVpt_fail.Sumw2();
	h2_rhoVpt_pafa.Divide(h2_rhoVpt_fail);
	#h2_rhoVpt_pafa.SetMaximum(0.5);
	#h2_rhoVpt_pafa.SetMinimum(0.0);
	h2_rhoVpt_pafa.SetMaximum(0.37);
	h2_rhoVpt_pafa.SetMinimum(0.17);
	for j in range(npt):
	    h_rhos_pafa[j].Sumw2();
	    h_rhos_fail[j].Sumw2();
	    h_rhos_pafa[j].Divide(h_rhos_fail[j]);
	    h_rhos_pafa[j].SetMaximum(0.5);
	    h_rhos_pafa[j].SetMinimum(0.0);

	makeCanvas(h_rho);
	makeCanvas(h_jtN2b1sd);
	makeCanvas(h_jtN2b1sdddt);
	makeCanvases(h_rhos);
	makeCanvases(h_rhos_fail);
	makeCanvases(h_rhos_pass);
	makeCanvases(h_rhos_pafa,False);

	for h2 in h2s_n2Vrho: makeCanvasViolin(h2);
	for h2 in h2s_n2ddtVrho: makeCanvasViolin(h2);
	makeCanvas2D(h2_rhoVpt_pafa);


def makeCanvas(h):

	c = ROOT.TCanvas("c","c",1000,800);
	h.Draw('hist');
	c.SaveAs(args.figdir+h.GetName()+".pdf");
	c.SaveAs(args.figdir+h.GetName()+".png");

def makeCanvasViolin(h):

	h1 = {}
	q5 = []
	bins = []

	nbinsx = h.GetXaxis().GetNbins();
	for i in range(nbinsx):
		h1[i] = h.ProjectionY("From %s to %s+1"%(str(i),str(i)), i+1, i+1);

		probSum = array.array('d', [QOI])
		q = array.array('d', [0.0]*len(probSum))
		h1[i].GetQuantiles(len(probSum), q, probSum)
		q5.append(q[0])

	xlo = h.GetXaxis().GetBinLowEdge(1);
	xhi = h.GetXaxis().GetBinUpEdge( h.GetXaxis().GetNbins() );
	hprof = ROOT.TH1F("hv_N2sdb1",";#rho = log(m^{2}/p_{T}^{2});dazsle-taggerDDT",nbinsx,xlo,xhi)
	numpy.round(q5,3)

	for i in range(nbinsx):
		hprof.SetBinContent(i+1,q5[i])

	c = ROOT.TCanvas("c","c",1000,800);
	h.SetFillColor(622);
	h.SetLineColor(622);

	h.Draw('VIOLIN');
	hprof.SetMarkerColor(634)
	hprof.SetLineColor(622)
	hprof.SetMarkerStyle(20)
	hprof.Draw("psames");    
	txta = ROOT.TLatex(0.18,0.92,"CMS#scale[0.8]{#it{ #bf{Simulation Preliminary}}}");
	txta.SetNDC();
	txta.SetTextSize(0.035);
	txta.Draw()
	c.SaveAs(args.figdir+h.GetName()+".pdf");
	c.SaveAs(args.figdir+h.GetName()+".png");

def makeCanvas2D(h):

	c = ROOT.TCanvas("c","c",1000,800);
	h.Draw('COLZ');
	c.SaveAs(args.figdir+h.GetName()+".pdf");
	c.SaveAs(args.figdir+h.GetName()+".png");


def makeCanvases(hs,norm=True):

	colors = range(80)#[1,2,4,6,7,3,8,9,29,20,41];
	for i,h in enumerate(hs): h.SetLineColor(colors[i]);
	if norm:
		for i,h in enumerate(hs): 
			if h.Integral() > 0: h.Scale( 1/h.Integral() );
	# hmax = -99;
	# for i,h in enumerate(hs): 
	# 	if hmax < h.GetMaximum(): hs[0].SetMaximum(h.GetMaximum()*1.2);

	c = ROOT.TCanvas("c","c",1000,800);
	for i,h in enumerate(hs):
		option = 'hist';
		if i > 0: option = 'histsames';
		h.Draw(option);
	c.SaveAs(args.figdir+hs[0].GetName()+"s.pdf");
	c.SaveAs(args.figdir+hs[0].GetName()+"s.png");

def makeProfile(h2):

	h1 = {}
	q5 = []
	bins = []

	nbinsx = h2.GetXaxis().GetNbins();
	for i in range(nbinsx):
		h1[i] = h2.ProjectionY("From %s to %s+1"%(str(i),str(i)), i, i+1);

		probSum = array.array('d', [QOI])
		q = array.array('d', [0.0]*len(probSum))
		h1[i].GetQuantiles(len(probSum), q, probSum)
		q5.append(q[0])
	
	xlo = h2.GetXaxis().GetBinLowEdge(1);
	xhi = h2.GetXaxis().GetBinUpEdge( h2.GetXaxis().GetNbins() );
	hprof = ROOT.TH1F("h2_N2sdb1",";#rho = log(m^{2}/p_{T}^{2});dazsle-taggerDDT",nbinsx,xlo,xhi)
	numpy.round(q5,3)

	for i in range(0,nbinsx):
		hprof.SetBinContent(i+1,q5[i])

	g1 = ROOT.TF1("m2","pol3",-6,-2);
	hprof.Fit(g1,"RL");

	print "check the fit..."
	print "evaluating function...", g1.Eval(-2.);
	byhand = -2.42531e-06 + 1.47639e-01*2. - 3.27902e-02*4 + 2.43034e-03*8 
	print "now by hand...",byhand

	print q5

	c = ROOT.TCanvas("c","c",1000,800);
	txta = ROOT.TLatex(0.16,0.95,"CMS");
	txta.SetNDC();
	txtb = ROOT.TLatex(0.22,0.95,"Simulation Preliminary");
	txtb.SetNDC(); txtb.SetTextFont(52);
	txta.SetTextSize(0.035);
	txtb.SetTextSize(0.035);

	leg = ROOT.TLegend(0.5,0.65,0.9,0.9);
	leg.SetBorderSize(0);
	leg.SetFillStyle(0)
	leg.AddEntry(hprof,"5% eff",'pl')
	leg.AddEntry(h2,'50% eff','pl')

	h2.Draw('VIOLIN');
	hprof.SetMarkerColor(ROOT.kBlue)
	hprof.SetMarkerStyle(20)
	hprof.SetLineColor(ROOT.kBlue)
	hprof.SetMarkerSize(1)
	hprof.SetMaximum(0.4);
	hprof.SetMinimum(0.1);
	hprof.Draw("psames");
	txta.Draw();
	txtb.Draw();
	leg.SetTextSize(0.035);
	leg.Draw();

	c.SaveAs(args.figdir+h2.GetName()+"_20eff.pdf");
	c.SaveAs(args.figdir+h2.GetName()+"_20eff.png");

	fout = ROOT.TFile(args.figdir+"n2ddt.root","RECREATE");
	hprof.SetName("h_n2ddt_transformation");
	hprof.Write();
	fout.Close();

	return q5

##----##----##----##----##----##----##
if __name__ == '__main__':
    
        import argparse
	parser = argparse.ArgumentParser()
        parser.add_argument('-figdir','--figdir',dest="figdir",action="store")
        parser.add_argument('-infile','--infile',dest="infile",action="store")
	args = parser.parse_args()

        print args
	 
	import tdrstyle
	tdrstyle.setTDRStyle()
	ROOT.gStyle.SetPadTopMargin(0.10)
	ROOT.gStyle.SetPadLeftMargin(0.16)
	ROOT.gStyle.SetPadRightMargin(0.15)
	ROOT.gStyle.SetPalette(1)
	ROOT.gStyle.SetPaintTextFormat("1.1f")
	ROOT.gStyle.SetOptFit(0000)
	ROOT.gROOT.SetBatch()
	
	main(args)
##----##----##----##----##----##----##




