###################################

#Goal: Loops for all the samples in the PREPouts and list their size

###################################

import os
import ROOT

#V20
#_path1 = '/pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V24/prepv3/'
#_path1 = '/pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V24/singlesys_v10/'
#_path1 = '/pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V25/prep_v4_dataonly_test/'
_path1 = '/pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V25/sys_v5_2/'
#V24
#_path2 = '/pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V24/singlesys_23/'
#_path2 = '/pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V24/singlesys_23_nolimit_v3/'
#_path2 = '/pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V24/singlesys_23_final/'
#_path2 = '/pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V24/singlesys_23_final_wbTag/'
#_path2 = '/pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V25/prep_v4_dataonly_test/'
_path2 = '/pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V25/sys_v5_2/'


dummy_cut = ''
SR_low_cut = '(V_mass>75&V_mass<105&(HCSV_reg_mass>90&HCSV_reg_mass<150)&Jet_btagCSV[hJCidx[0]]>0.46&Jet_btagCSV[hJCidx[1]]>0.46&(1)&sys_puID&sys_LooseIso&(Jet_puId[hJCidx[1]]>=4)&(Jet_puId[hJCidx[0]]>=4)&vLeptons_pt[0]>20&vLeptons_pt[1]>20&abs(Jet_eta[hJCidx[0]])<2.4&abs(Jet_eta[hJCidx[1]])<2.4&V_pt>50&sys_puID&V_pt>20&V_pt>30&(((Vtype==0)&(run<=276811))||((Vtype==1)&(run<=276811)))&(V_pt>50&V_pt<150))'

#CUTLISTV20 = [dummy_cut,SR_low_cut]
#CUTLISTV21 = [dummy_cut,SR_low_cut]
#LISTNAME = ['Cut','SR_low']
CUTLISTV20 = [dummy_cut]
CUTLISTV21 = [dummy_cut]
LISTNAME = ['Cut']

#Define list of cuts
#CSV_Loose = '0.46'
#CSV_Medium = '0.8'
#CSV_Tight = '0.935'
#pT20 = '(vLeptons_pt[0] > 20. & vLeptons_pt[1] > 20.)'
#addjetV20 = 'Sum$(Jet_pt>20 && abs(Jet_eta)<2.4 && Jet_puId == 1)'
#addjetV21 = 'Sum$(Jet_pt>20 && abs(Jet_eta)<2.4 && Jet_puId ==7)'
#LooseIso =  '(vLeptons_relIso04[0] < 0.25 & vLeptons_relIso04[1] < 0.25)'
#
#CRZlightV20 = '(V_mass > 75. & V_mass < 105. & Jet_pt[hJCidx[0]] > 20 & Jet_pt[hJCidx[1]] > 20 & HCSV_pt > 100 & Jet_btagCSV[hJCidx[0]] < '+ CSV_Tight + ' & Jet_btagCSV[hJCidx[1]] < '+ CSV_Tight + ' & ' + addjetV20 + ' == 2 & abs(HVdPhi) > 2.9 & ' + pT20 + ' & ' + LooseIso + ')'
#
#CRZlightV21 = '(V_mass > 75. & V_mass < 105. & Jet_pt[hJCidx[0]] > 20 & Jet_pt[hJCidx[1]] > 20 & HCSV_pt > 100 & Jet_btagCSV[hJCidx[0]] < '+ CSV_Tight + ' & Jet_btagCSV[hJCidx[1]] < '+ CSV_Tight + ' & ' + addjetV21 + ' == 2 & abs(HVdPhi) > 2.9 & ' + pT20 + ' & ' + LooseIso + ')'
#
#CRZb_incl = '(V_mass > 85. & V_mass < 97. & met_pt < 60 & Jet_pt[hJCidx[0]] > 20 & Jet_pt[hJCidx[1]] > 20 & (HCSV_mass < 90 || HCSV_mass > 145) & Jet_btagCSV[hJCidx[0]] > '+CSV_Tight + '& Jet_btagCSV[hJCidx[1]] > '+CSV_Loose+ ' & abs(HVdPhi) > 2.9 & '+pT20 + ' & ' + LooseIso + ')'
#
#CRttbar_incl = '(Jet_pt[hJCidx[0]] > 20 & Jet_pt[hJCidx[1]] > 20 & HCSV_pt > 100 & V_mass > 10 & (V_mass < 75 || V_mass > 120) & Jet_btagCSV[hJCidx[0]] > ' + CSV_Tight + ' & Jet_btagCSV[hJCidx[1]] > ' +CSV_Loose + ' & ' + pT20 + ' & ' + LooseIso +')'
#
#ZllBDThighVptcut = 'V_mass > 75 & V_mass < 105 & Jet_pt[hJCidx[0]] > 20 & Jet_pt[hJCidx[1]] > 20 & (HCSV_mass > 40 & HCSV_mass < 250) & V_pt > 100 & Jet_btagCSV[hJCidx[0]] > ' +CSV_Loose + ' & Jet_btagCSV[hJCidx[1]] > ' + CSV_Loose
#
#CUTLISTV20 = [CRZlightV20, CRZb_incl, CRttbar_incl, ZllBDThighVptcut]
#CUTLISTV21 = [CRZlightV21, CRZb_incl, CRttbar_incl, ZllBDThighVptcut]
#LISTNAME = ['Zlf', 'Zhf', 'ttbar', 'SR']



FILE1 = os.listdir(_path1)
FILE2 = os.listdir(_path2)

FAILED = []
MISSING = []

total = 0

for file1 in FILE1:
    if not '.root' in file1: continue
    #if not 'TT_Tune' in file1: continue
    #if not 'Single' in file1: continue
    ###if 'TT' in file1: continue
    #if 'SingleElectron' in file1 or 'SingleMuon' in file1: continue
    #if not 'SingleMuon__Run2016E-PromptReco-v2' in file1: continue
    #if 'SingleElectron' in file1: continue
    #if not 'DoubleMuon' in file1: continue
    print '#events in sample', file1
    print 'file is', file1
    file_found = False
    for k in range(0, len(CUTLISTV20)):
        f = ROOT.TFile.Open('root://t3dcachedb03.psi.ch:1094/' + _path1 + file1)
        t = f.Get("tree")
        print 'for cut', LISTNAME[k]
        #print len(f)
        n1 = t.GetEntries(CUTLISTV20[k])
        print ' V20', n1
        found = False
        for file2 in FILE2:
            if not '.root' in file2: continue
            if file2 != file1: continue
            found = True
            file_found = True
            f = ROOT.TFile.Open('root://t3dcachedb03.psi.ch:1094/' + _path2 + file2)
            t = f.Get("tree")
            #print len(f)
            n2 = t.GetEntries(CUTLISTV21[k])
            total += n2
            print ' V21', n2
            if n1 != n2:
                FAILED.append(file1)
        if not found:
            MISSING.append(file1)

    if not file_found: print 'No such file in V20'
    print ''

if len(FAILED) > 0:
    print 'FAILED SAMPLES:'
    for f in FAILED:
        print f
if len(MISSING) > 0:
    print 'MISSING SAMPLES:'
    for f in MISSING:
        print f



print 'total is', total
