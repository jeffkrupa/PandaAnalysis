#include "../interface/PandaAnalyzer.h"
#include "TVector2.h"
#include "TMath.h"
#include <algorithm>
#include <vector>


using namespace panda;
using namespace std;

/***** miscellaneous helper functions *****/

// Register triggers
// Responsible: S. Narayanan
void PandaAnalyzer::RegisterTriggers() 
{
  for (auto &th : triggerHandlers) {
    unsigned N = th.paths.size();
    for (unsigned i = 0; i != N; i++) {
      unsigned panda_idx = event.registerTrigger(th.paths.at(i));
      th.indices[i] = panda_idx;
      if (DEBUG) PDebug("PandaAnalyzer::RegisterTriggers",
        Form("Got index %d for trigger path %s", panda_idx, th.paths.at(i).Data())
      );
    }
  }
}

// Match an object at arbitrary eta,phi to a gen particle with specific pdgid
// Responsible: S. Narayanan
panda::GenParticle const *PandaAnalyzer::MatchToGen(double eta, double phi, double radius, int pdgid) 
{
  panda::GenParticle const* found=NULL;
  double r2 = radius*radius;
  pdgid = abs(pdgid);

  for (map<panda::GenParticle const*,float>::iterator iG=genObjects.begin();
      iG!=genObjects.end(); ++iG) {
    if (found!=NULL)
      break;
    if (pdgid!=0 && abs(iG->first->pdgid)!=pdgid)
      continue;
    if (DeltaR2(eta,phi,iG->first->eta(),iG->first->phi())<r2)
      found = iG->first;
  }

  return found;
}


double PandaAnalyzer::GetCorr(CorrectionType ct, double x, double y) 
{
  if (h1Corrs[ct]!=0) {
    return h1Corrs[ct]->Eval(x); 
  } else if (h2Corrs[ct]!=0) {
    return h2Corrs[ct]->Eval(x,y);
  } else if (f1Corrs[ct]!=0) {
    return f1Corrs[ct]->Eval(x);
  } else {
    PError("PandaAnalyzer::GetCorr",
       TString::Format("No correction is defined for CorrectionType=%u",ct));
    return 1;
  }
}

double PandaAnalyzer::GetError(CorrectionType ct, double x, double y) 
{
  if (h1Corrs[ct]!=0) {
    return h1Corrs[ct]->Error(x); 
  } else if (h2Corrs[ct]!=0) {
    return h2Corrs[ct]->Error(x,y);
  } else {
    PError("PandaAnalyzer::GetError",
       TString::Format("No correction is defined for CorrectionType=%u",ct));
    return 1;
  }
}


bool PandaAnalyzer::PassPresel(Selection::Stage stage) 
{
  if (selections.size() == 0)
    return true;

  bool pass = false;
  for (auto* s : selections) {
    if (s->anded())
      continue;
    if (s->accept(stage)) {
      pass = true;
      break;
    }
  }

  for (auto* s : selections) {
    if (s->anded()) {
      pass = pass && s->accept(stage);
    }
  }

  return pass;
}


/***** common physics methods *****/

// Create a new auxillary file for gen info
// Responsible: S. Narayanan
void PandaAnalyzer::IncrementGenAuxFile(bool close)
{
  if (fAux) {
    fAux->WriteTObject(tAux, "inputs", "Overwrite");
    TString path = TString::Format(auxFilePath.Data(),auxCounter);
    if (DEBUG) PDebug("PandaAnalyzer::IncrementAuxFile", "Closing "+path);
    fAux->Close();
  }
  if (close)
    return;

  TString path = TString::Format(auxFilePath.Data(),auxCounter++);
  fAux = TFile::Open(path.Data(), "RECREATE");
  if (DEBUG) PDebug("PandaAnalyzer::IncrementAuxFile", "Opening "+path);
  tAux = new TTree("inputs","inputs");
  
  genJetInfo.particles.resize(NMAXPF);
  for (int i = 0; i != NMAXPF; ++i) {
    genJetInfo.particles[i].resize(NGENPROPS);
  }

  genJetInfo.ecfs.resize(3);
  for (int o = 0; o != 3; ++o) {
    genJetInfo.ecfs.at(o).resize(4);
    for (int N = 0; N != 4; ++N) {
      genJetInfo.ecfs.at(o).at(N).resize(4);
    }
  }

  tAux->Branch("eventNumber",&(gt->eventNumber),"eventNumber/l");
  if (!analysis->deepExC) {
    tAux->Branch("nprongs",&(genJetInfo.nprongs),"nprongs/I");
    tAux->Branch("partonpt",&(genJetInfo.partonpt),"partonpt/F");
    tAux->Branch("partonm",&(genJetInfo.partonm),"partonm/F");
    tAux->Branch("pt",&(genJetInfo.pt),"pt/F");
    tAux->Branch("msd",&(genJetInfo.msd),"msd/F");
    tAux->Branch("eta",&(genJetInfo.eta),"eta/F");
    tAux->Branch("phi",&(genJetInfo.phi),"phi/F");
    tAux->Branch("m",&(genJetInfo.m),"m/F");
    tAux->Branch("tau3",&(genJetInfo.tau3),"tau3/F");
    tAux->Branch("tau2",&(genJetInfo.tau2),"tau2/F");
    tAux->Branch("tau1",&(genJetInfo.tau1),"tau1/F");
    tAux->Branch("tau3sd",&(genJetInfo.tau3sd),"tau3sd/F");
    tAux->Branch("tau2sd",&(genJetInfo.tau2sd),"tau2sd/F");
    tAux->Branch("tau1sd",&(genJetInfo.tau1sd),"tau1sd/F");
    for (int o = 1; o != 4; ++o) {
      for (int N = 1; N != 5; ++N) {
        for (int beta = 1; beta != 3; ++beta) {
          TString bname = Form("%i_%i_%i",o,N,beta);
          tAux->Branch(bname,&(genJetInfo.ecfs[o-1][N-1][beta-1]),bname+"/F");
        }
      }
    }
  }
  tAux->Branch("kinematics",&(genJetInfo.particles));

  fOut->cd();

  if (tr)
    tr->TriggerEvent("increment aux file");
}

// Create a new auxillary file for reco info
// Responsible: S. Narayanan
void PandaAnalyzer::IncrementAuxFile(bool close)
{
  if (fAux) {
    fAux->WriteTObject(tAux, "inputs", "Overwrite");
    fAux->Close();
  }
  if (close)
    return;

  TString path = TString::Format(auxFilePath.Data(),auxCounter++);
  fAux = TFile::Open(path.Data(), "RECREATE");
  if (DEBUG) PDebug("PandaAnalyzer::IncrementAuxFile", "Opening "+path);
  tAux = new TTree("inputs","inputs");
  
  pfInfo.resize(NMAXPF);
  for (int i = 0; i != NMAXPF; ++i) {
    pfInfo[i].resize(NPFPROPS);
  }
  tAux->Branch("kinematics",&pfInfo);
  
  svInfo.resize(NMAXSV);
  for (int i = 0; i != NMAXSV; ++i) {
    svInfo[i].resize(NSVPROPS);
  }
  tAux->Branch("svs",&svInfo);

  tAux->Branch("msd",&fjmsd,"msd/F");
  tAux->Branch("pt",&fjpt,"pt/F");
  tAux->Branch("rawpt",&fjrawpt,"rawpt/F");
  tAux->Branch("eta",&fjeta,"eta/F");
  tAux->Branch("phi",&fjphi,"phi/F");
  tAux->Branch("rho",&(gt->fjRho),"rho/f");
  tAux->Branch("rawrho",&(gt->fjRawRho),"rawrho/f");
  tAux->Branch("rho2",&(gt->fjRho2),"rho2/f");
  tAux->Branch("rawrho2",&(gt->fjRawRho2),"rawrho2/f");
  tAux->Branch("nPartons",&(gt->fjNPartons),"nPartons/I");
  tAux->Branch("nBPartons",&(gt->fjNBPartons),"nBPartons/I");
  tAux->Branch("nCPartons",&(gt->fjNCPartons),"nCPartons/I");
  tAux->Branch("partonM",&(gt->fjPartonM),"partonM/f");
  tAux->Branch("partonPt",&(gt->fjPartonPt),"partonPt/f");
  tAux->Branch("partonEta",&(gt->fjPartonEta),"partonEta/f");
  tAux->Branch("tau32",&(gt->fjTau32),"tau32/f");
  tAux->Branch("tau32SD",&(gt->fjTau32SD),"tau32SD/f");
  tAux->Branch("tau21",&(gt->fjTau21),"tau21/f");
  tAux->Branch("tau21SD",&(gt->fjTau21SD),"tau21SD/f");
  tAux->Branch("eventNumber",&(gt->eventNumber),"eventNumber/l");
  tAux->Branch("maxcsv",&(gt->fjMaxCSV),"maxcsv/f");
  tAux->Branch("mincsv",&(gt->fjMinCSV),"mincsv/f");
  tAux->Branch("doubleb",&(gt->fjDoubleCSV),"doubleb/f");

  gt->SetAuxTree(tAux);

  fOut->cd();

  if (tr)
    tr->TriggerEvent("increment aux file");
}

// Calculate various trigger efficiencies
// Responsible: S. Narayanan, D. Hsu
void PandaAnalyzer::TriggerEffs()
{

    // trigger efficiencies
    gt->sf_metTrig = GetCorr(cTrigMET,gt->pfmetnomu[jes2i(shiftjes::kNominal)]);
    gt->sf_metTrigZmm = GetCorr(cTrigMETZmm,gt->pfmetnomu[jes2i(shiftjes::kNominal)]);

    if (gt->nLooseElectron>0) {
      panda::Electron *ele1=0, *ele2=0;
      if (gt->nLooseLep>0) ele1 = dynamic_cast<panda::Electron*>(looseLeps[0]);
      if (gt->nLooseLep>1) ele2 = dynamic_cast<panda::Electron*>(looseLeps[1]);
      float eff1=0, eff2=0;
      if (ele1 && ele1->tight) {
        eff1 = GetCorr(cTrigEle, ele1->eta(), ele1->pt());
        if (ele2 && ele2->tight)
          eff2 = GetCorr(cTrigEle, ele2->eta(), ele2->pt());
        gt->sf_eleTrig = 1 - (1-eff1)*(1-eff2);
      }
    } // done with ele trig SF
    if (gt->nLooseMuon>0) {
      panda::Muon *mu1=0, *mu2=0;
      if (gt->nLooseLep>0) mu1 = dynamic_cast<panda::Muon*>(looseLeps[0]);
      if (gt->nLooseLep>1) mu2 = dynamic_cast<panda::Muon*>(looseLeps[1]);
      float eff1=0, eff2=0;
      if (mu1 && mu1->tight) {
        eff1 = GetCorr(
          cTrigMu,
          fabs(mu1->eta()),
          TMath::Max((float)26.,TMath::Min((float)499.99,(float)mu1->pt()))
        );
        if (mu2 && mu2->tight)
          eff2 = GetCorr(
            cTrigMu,
            fabs(mu2->eta()),
            TMath::Max((float)26.,TMath::Min((float)499.99,(float)mu2->pt()))
          );
        gt->sf_muTrig = 1 - (1-eff1)*(1-eff2);
      }
    } // done with mu trig SF

    if (gt->nLoosePhoton>0 && gt->loosePho1IsTight)
      gt->sf_phoTrig = GetCorr(cTrigPho,gt->loosePho1Pt);

    if (analysis->vbf) {
      gt->sf_metTrigVBF = GetCorr(cVBF_TrigMET,gt->barrelHTMiss);
      gt->sf_metTrigZmmVBF = GetCorr(cVBF_TrigMETZmm,gt->barrelHTMiss);
    }
    tr->TriggerEvent("triggers");
}

// Calculate various flavors of recoil
// Responsible: S. Narayanan
void PandaAnalyzer::Recoil()
{
    TLorentzVector vObj1, vObj2;
    gt->whichRecoil = 0; // -1=photon, 0=MET, 1,2=nLep
    if (gt->nLooseLep>0) {
      panda::Lepton *lep1 = looseLeps.at(0);
      vObj1.SetPtEtaPhiM(lep1->pt(),lep1->eta(),lep1->phi(),lep1->m());

      // one lep => W
      JESLOOP {
        auto& jets = jesShifts[shift]; 

        jets.vpuppiUW = jets.vpuppiMET + vObj1;
        gt->puppiUWmag[shift] = jets.vpuppiUW.Pt(); 
        gt->puppiUWphi[shift] = jets.vpuppiUW.Phi(); 

        jets.vpfUW = jets.vpfMET + vObj1;
        gt->pfUWmag[shift] = jets.vpfUW.Pt(); 
        gt->pfUWphi[shift] = jets.vpfUW.Phi(); 
      }

      if (gt->nLooseLep>1 && looseLep1PdgId+looseLep2PdgId==0) {
        // two OS lep => Z
        panda::Lepton *lep2 = looseLeps.at(1);
        vObj2.SetPtEtaPhiM(lep2->pt(),lep2->eta(),lep2->phi(),lep2->m());

        JESLOOP {
          auto& jets = jesShifts[shift]; 

          jets.vpuppiUZ = jets.vpuppiUW + vObj2;
          gt->puppiUZmag[shift] = jets.vpuppiUZ.Pt(); 
          gt->puppiUZphi[shift] = jets.vpuppiUZ.Phi(); 

          jets.vpfUZ = jets.vpfUW + vObj2;
          gt->pfUZmag[shift] = jets.vpfUZ.Pt(); 
          gt->pfUZphi[shift] = jets.vpfUZ.Phi(); 
        }

        gt->whichRecoil = 2;
      } else {
        gt->whichRecoil = 1;
      }
    }
    if (gt->nLoosePhoton>0) {
      panda::Photon *pho = loosePhos.at(0);
      vObj1.SetPtEtaPhiM(pho->pt(),pho->eta(),pho->phi(),0.);

      JESLOOP {
        auto& jets = jesShifts[shift]; 

        jets.vpuppiUA = jets.vpuppiMET + vObj1;
        gt->puppiUAmag[shift] = jets.vpuppiUA.Pt(); 
        gt->puppiUAphi[shift] = jets.vpuppiUA.Phi(); 

        jets.vpfUA = jets.vpfMET + vObj1;
        gt->pfUAmag[shift] = jets.vpfUA.Pt(); 
        gt->pfUAphi[shift] = jets.vpfUA.Phi(); 
      }

      if (gt->nLooseLep==0) {
        gt->whichRecoil = -1;
      }
    }
    if (gt->nLooseLep==0 && gt->nLoosePhoton==0) {
      gt->whichRecoil = 0;
    }

    tr->TriggerEvent("recoils");
}

// count heavy flavor in an event/jet
// Responsible: D. Hsu, B. Maier
void PandaAnalyzer::HeavyFlavorCounting() 
{
  // Simple B and C counting stored in nB, nHF
  for (auto* genptr : validGenP) {
    auto& gen = pToGRef(genptr);
    float pt = gen.pt();
    int pdgid = gen.pdgid;
    if (gen.parent.isValid() && gen.parent->pdgid==gen.pdgid)
      continue;
    //count bs and cs
    int apdgid = abs(pdgid);
    if (apdgid!=5 && apdgid!=4) 
      continue;
    if (pt>5) {
      gt->nHF++;
      if (apdgid==5)
        gt->nB++;
    }
  }

  // Gen B jet counting stored in nBGenJets
  for (auto &gen : event.ak4GenJets) {
    if (gen.pt() > 20 && std::abs(gen.eta()) < 2.4 && (gen.numB != 0 || abs(gen.pdgid)==5))
      gt->nBGenJets++;
  }
}

// MET sig
// Responsible: D. Hsu
void PandaAnalyzer::GetMETSignificance()
{
  gt->pfmetsig = event.pfMet.significance;
  gt->puppimetsig = event.puppiMet.significance;

  tr->TriggerEvent("MET significance");
}

