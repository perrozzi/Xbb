#ifndef BTAGRESHAPHING_H
#define BTAGRESHAPHING_H

#include <iostream>
#include <math.h>
#include <utility>
#include <vector>

#include <TFile.h>
#include <TGraph.h>
#include <TH1F.h>
#include <TSpline.h>
#include "Math/Interpolator.h"

#include "btag_payload_b.h"
#include "btag_payload_light.h"


#define MAXPOINTS 200

class BTagShape {

 public:

  BTagShape();

  BTagShape(TFile* file, const char* name, const std::vector<std::pair<float,float>>& cutsAndSF, float boundX, float boundY) {
    TH1F* m_h = (TH1F*) file->Get(name);

    // compute equivalents
    std::vector<std::pair<float,float>> eq;
    int lastbin = 2001;

    for (unsigned int i = 0; i < cutsAndSF.size(); ++i) {
      float oldCut = cutsAndSF[i].first;
      float sf = cutsAndSF[i].second;
      float originalIntegral = m_h->Integral(m_h->FindBin(oldCut), lastbin);
      float originalLowEdge = m_h->GetBinLowEdge(m_h->FindBin(oldCut));
      float target = originalIntegral * sf;

      for (int j = lastbin; j > -1; --j) {
        if (m_h->Integral(j, lastbin) >= target) {
          eq.push_back(std::pair<float,float>(m_h->GetBinLowEdge(j), originalLowEdge));
          break;
        }
      }
    }

    // Interpolator
    std::vector<double> x, y;
    x.push_back(0.);
    y.push_back(0.);

    for (unsigned int i = 0; i < eq.size(); ++i) {
      x.push_back(eq[eq.size()-i-1].first);
      y.push_back(eq[eq.size()-i-1].second);
    }

    x.push_back(boundX);
    y.push_back(boundY);

    m_i = new ROOT::Math::Interpolator(x, y, ROOT::Math::Interpolation::kLINEAR);
  }

  float eval(float x) { return m_i->Eval(x); }

 private:

  ROOT::Math::Interpolator* m_i;
};

class EtaPtBin {

 public:

  EtaPtBin();

  EtaPtBin(float emin, float emax, float ptmin, float ptmax)
      : etaMin(emin), etaMax(emax), ptMin(ptmin), ptMax(ptmax) {}

  bool contains(float eta, float pt) { return eta < etaMax && eta >= etaMin && pt < ptMax && pt >= ptMin; }

  float centerEta() { return (etaMax+etaMin)/2.; }

  float centerPt() { return (ptMax+ptMin)/2.; }

  float etaMin, etaMax, ptMin, ptMax;
};

class BinnedBTagShape {

 public:

  BinnedBTagShape();

  BinnedBTagShape(std::vector<EtaPtBin>& bins, std::vector<std::vector<std::pair<float,float>>>& cutsAndSF,
                  TFile* f, const char* name, float boundX, float boundY)
      : m_bins(bins) {

    for (unsigned int i = 0; i < bins.size(); ++i) {
      m_shapes.push_back(BTagShape(f, name, cutsAndSF[i], boundX, boundY));
    }

  }

  float eval(float eta, float pt, float x) {
    for (unsigned int i = 0; i < m_bins.size(); ++i) {
      if (m_bins[i].contains(fabs(eta), pt)) return m_shapes[i].eval(x);
    }
    return x;
  }

  std::vector<BTagShape> m_shapes;

  std::vector<EtaPtBin> m_bins;
};

class BTagShapeInterface {

 public:

  BTagShapeInterface();

  BTagShapeInterface(const char* file, float scaleBC, float scaleL, bool use4points = false,
                     float boundX = 1.001, float boundY = 1.001, unsigned int maxbins = 9999)
      : m_file(new TFile(file)) {

    std::vector<EtaPtBin> binsBC;
    std::vector<std::vector<std::pair<float,float>>> cutsAndSFB, cutsAndSFC;

    // Addtional uncertainty for charm
    float charmFactor = 2. - 1.0;

    if (maxbins > beff::bins) maxbins = beff::bins;

    for (unsigned int i = 0; i < maxbins; ++i) {
      EtaPtBin bin(-2.5, 2.5, beff::ptmin[i], beff::ptmax[i]);
      binsBC.push_back(bin);

      std::vector<std::pair<float,float>> cutsAndSFbinB, cutsAndSFbinC;
      float sft = 0.94;

      if (use4points) {
        // add error
        sft += scaleBC * beff::CSVT_SFb_error[i];
        cutsAndSFbinB.push_back(std::pair<float,float>(0.98, sft));
        // additional charm error
        sft += scaleBC * beff::CSVT_SFb_error[i] * charmFactor;
        cutsAndSFbinC.push_back(std::pair<float,float>(0.98, sft));
      }

      sft = beff::CSVT_SFb(bin.centerPt());
      // add error
      sft += scaleBC * beff::CSVT_SFb_error[i];
      cutsAndSFbinB.push_back(std::pair<float,float>(0.898, sft));
      // additional charm error
      sft += scaleBC * beff::CSVT_SFb_error[i] * charmFactor;
      cutsAndSFbinC.push_back(std::pair<float,float>(0.898, sft));

      float sfm = beff::CSVM_SFb(bin.centerPt());
      // add error
      sfm += scaleBC * beff::CSVM_SFb_error[i];
      cutsAndSFbinB.push_back(std::pair<float,float>(0.679, sfm));
      // additional charm error
      sfm += scaleBC * beff::CSVM_SFb_error[i] * charmFactor;
      cutsAndSFbinC.push_back(std::pair<float,float>(0.679, sfm));

      float sfl = beff::CSVL_SFb(bin.centerPt());
      // add error
      sfl += scaleBC * beff::CSVL_SFb_error[i];
      cutsAndSFbinB.push_back(std::pair<float,float>(0.244, sfl));
      // additional charm error
      sfl += scaleBC * beff::CSVL_SFb_error[i] * charmFactor;
      cutsAndSFbinC.push_back(std::pair<float,float>(0.244, sfl));

      cutsAndSFB.push_back(cutsAndSFbinB);
      cutsAndSFC.push_back(cutsAndSFbinC);
    }

    // Underflow
    {
      std::vector<std::pair<float,float>> cutsAndSFbinC, cutsAndSFbinB;

      binsBC.push_back(EtaPtBin(-2.5, 2.5, -9e99, beff::ptmin[0]));

      float sft = beff::CSVT_SFb(beff::ptmin[0]);
      // add error
      sft += scaleBC * 0.12;
      cutsAndSFbinB.push_back(std::pair<float,float>(0.898, sft));
      // additional charm error
      sft += scaleBC * 0.12 * charmFactor;
      cutsAndSFbinC.push_back(std::pair<float,float>(0.898, sft));

      float sfm = beff::CSVM_SFb(beff::ptmin[0]);
      // add error
      sfm += scaleBC * 0.12;
      cutsAndSFbinB.push_back(std::pair<float,float>(0.679, sfm));
      // additional charm error
      sfm += scaleBC * 0.12 * charmFactor;
      cutsAndSFbinC.push_back(std::pair<float,float>(0.679, sfm));

      float sfl = beff::CSVL_SFb(beff::ptmin[0]);
      // add error
      sfl += scaleBC * 0.12;
      cutsAndSFbinB.push_back(std::pair<float,float>(0.244, sfl));
      // additional charm error
      sfl += scaleBC * 0.12 * charmFactor;
      cutsAndSFbinC.push_back(std::pair<float,float>(0.244, sfl));

      cutsAndSFB.push_back(cutsAndSFbinB);
      cutsAndSFC.push_back(cutsAndSFbinC);
    }

    // Overflow
    {
      std::vector<std::pair<float,float>> cutsAndSFbinC, cutsAndSFbinB;

      binsBC.push_back(EtaPtBin(-2.5, 2.5, beff::ptmax[maxbins-1], 9e99));

      float sft = beff::CSVT_SFb(beff::ptmax[maxbins-1]);
      // add error
      sft += scaleBC * beff::CSVT_SFb_error[maxbins-1] * 2;
      cutsAndSFbinB.push_back(std::pair<float,float>(0.898, sft));
      // additional charm error
      sft += scaleBC * beff::CSVT_SFb_error[maxbins-1] * charmFactor;
      cutsAndSFbinC.push_back(std::pair<float,float>(0.898, sft));

      float sfm = beff::CSVM_SFb(beff::ptmax[maxbins-1]);
      // add error
      sfm += scaleBC * beff::CSVM_SFb_error[maxbins-1] * 2;
      cutsAndSFbinB.push_back(std::pair<float,float>(0.679, sfm));
      // additional charm error
      sfm += scaleBC * beff::CSVM_SFb_error[maxbins-1] * charmFactor;
      cutsAndSFbinC.push_back(std::pair<float,float>(0.679, sfm));

      float sfl = beff::CSVL_SFb(beff::ptmax[maxbins-1]);
      // add error
      sfl += scaleBC * beff::CSVL_SFb_error[maxbins-1] * 2;
      cutsAndSFbinB.push_back(std::pair<float,float>(0.244, sfl));
      // additional charm error
      sfl += scaleBC * beff::CSVL_SFb_error[maxbins-1] * charmFactor;
      cutsAndSFbinC.push_back(std::pair<float,float>(0.244, sfl));

      cutsAndSFB.push_back(cutsAndSFbinB);
      cutsAndSFC.push_back(cutsAndSFbinC);
    }

    m_b = new BinnedBTagShape(binsBC, cutsAndSFB, m_file, "hb", boundX, boundY);
    m_c = new BinnedBTagShape(binsBC, cutsAndSFC, m_file, "hc", boundX, boundY);

    std::vector<EtaPtBin> binsL;
    std::vector<std::vector<std::pair<float,float>>> cutsAndSFL;

    // 20-30 is also covered for mistag
    float ptmin[] = {20, 30, 40, 50, 60, 70, 80, 100, 120, 160, 210, 260, 320, 400, 500};
    float ptmax[] = {30, 40, 50, 60, 70, 80, 100, 120, 160, 210, 260, 320, 400, 500, 670};
    float etamin[] = {0, 0.5, 1.0, 1.5};
    float etamax[] = {0.5, 1.0, 1.5, 2.5};
    size_t bins = 15;

    for (unsigned int j = 0; j < 4; ++j) {
      for (unsigned int i = 0; i < bins; ++i) {
        EtaPtBin bin(etamin[j], etamax[j], ptmin[i], ptmax[i]);
        binsL.push_back(bin);

        std::vector<std::pair<float,float>> cutsAndSFbinL;
        float sft = mistag_CSVT(bin.centerEta(), bin.centerPt(), scaleL);
        cutsAndSFbinL.push_back(std::pair<float,float>(0.898, sft));

        float sfm = mistag_CSVM(bin.centerEta(), bin.centerPt(), scaleL);
        cutsAndSFbinL.push_back(std::pair<float,float>(0.679, sfm));

        float sfl = mistag_CSVL(bin.centerEta(), bin.centerPt(), scaleL);
        cutsAndSFbinL.push_back(std::pair<float,float>(0.244, sfl));

        cutsAndSFL.push_back(cutsAndSFbinL);
      }

      // Overflow
      {
        std::vector<std::pair<float,float>> cutsAndSFbinL;
        binsL.push_back(EtaPtBin(etamin[j], etamax[j], ptmax[bins-1], 9e99));

        float sft = mistag_CSVT((etamin[j]+etamax[j])/2., ptmax[bins-1], scaleL*2);
        cutsAndSFbinL.push_back(std::pair<float,float>(0.898, sft));

        float sfm = mistag_CSVM((etamin[j]+etamax[j])/2., ptmax[bins-1], scaleL*2);
        cutsAndSFbinL.push_back(std::pair<float,float>(0.679, sfm));

        float sfl = mistag_CSVL((etamin[j]+etamax[j])/2., ptmax[bins-1], scaleL*2);
        cutsAndSFbinL.push_back(std::pair<float,float>(0.244, sfl));

        cutsAndSFL.push_back(cutsAndSFbinL);
      }
    }

    m_l = new BinnedBTagShape(binsL, cutsAndSFL, m_file, "hl", boundX, boundY);
  }

  float reshape(float eta, float pt, float csv, int flav) {
   if (csv < 0 || csv > 1 || flav == 0) {
     return csv;
   } else if (fabs(flav) == 5) {
     return m_b->eval(eta, pt, csv);
   } else if (fabs(flav) == 4) {
     return m_c->eval(eta, pt, csv);
   } else if (fabs(flav) != 4 && fabs(flav) != 5) {
     return m_l->eval(eta, pt, csv);
   } else {
     return -10000;
   }
 }

 TFile* m_file;

 BinnedBTagShape* m_b, m_c, m_l;
};

#endif
