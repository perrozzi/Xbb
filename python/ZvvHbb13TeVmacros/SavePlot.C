{
 TFile* nf = new TFile("newfile.root","recreate");
 TFile *_file0 = TFile::Open("../env/ZvvHighPt_V21_MET.root");
 tree = (TTree*)  _file0->Get("tree");
 nf->cd();

 tree->Draw("Jet_eta:Jet_phi >> Under(128,-3.2,3.2,188,-4.7,4.7)","abs(TVector2::Phi_mpi_pi(met_phi-Jet_phi))<0.3 && Jet_pt>40 && Iteration$>=1","COLZ");
 tree->Draw("Jet_eta:Jet_phi >> Over(128,-3.2,3.2,188,-4.7,4.7)","abs(TVector2::Phi_mpi_pi(met_phi-Jet_phi))>3.1415-0.3 && Jet_pt>40 && Iteration$==0","COLZ");

 TFile *_file1 = TFile::Open("../env/ZvvHighPt_V21_QCD_HT700to1000_TuneCUETP8M1_13TeV-madgraphMLM-pythia8.root");
 treeQCD = (TTree*)  _file1->Get("tree");
 nf->cd();
 treeQCD->Draw("Jet_eta:Jet_phi >> UnderQCD(128,-3.2,3.2,188,-4.7,4.7)","abs(TVector2::Phi_mpi_pi(met_phi-Jet_phi))<0.3 && Jet_pt>40 && Iteration$>=1","COLZ");
 treeQCD->Draw("Jet_eta:Jet_phi >> OverQCD(128,-3.2,3.2,188,-4.7,4.7)","abs(TVector2::Phi_mpi_pi(met_phi-Jet_phi))>3.1415-0.3 && Jet_pt>40 && Iteration$==0","COLZ");

 nf->Write();
 nf->Close();
 _file0->Close();
}
