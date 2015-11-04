#include "TLorentzVector.h"

double SimpleDeltaR(double v1_pt,double v1_eta,double v1_phi,double v1_mass,double v2_pt,double v2_eta,double v2_phi,double v2_mass){

  TLorentzVector v1,v2;

  v1.SetPtEtaPhiM(v1_pt,v1_eta,v1_phi,v1_mass);
  v2.SetPtEtaPhiM(v2_pt,v2_eta,v2_phi,v2_mass);

  return v1.DeltaR(v2);

}
/*
double SimpleDeltaR(Float_t v1_pt,Float_t v1_eta,Float_t v1_phi,Float_t v1_mass,Float_t v2_pt,Float_t v2_eta,Float_t v2_phi,Float_t v2_mass){

  TLorentzVector v1,v2;
  
  v1.SetPtEtaPhiM(v1_pt,v1_eta,v1_phi,v1_mass);
  v2.SetPtEtaPhiM(v2_pt,v2_eta,v2_phi,v2_mass);

  return v1.DeltaR(v2);

}
*/


