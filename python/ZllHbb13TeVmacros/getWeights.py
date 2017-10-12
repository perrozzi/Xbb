import ROOT

#prefix = "root://t3dcachedb03.psi.ch:1094/pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V21/prep_v1/ZmmH.BestCSV.heppy."
#prefix = "root://t3dcachedb03.psi.ch:1094/pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V21bis/singlesys_eandmu/ZmmH.BestCSV.heppy."
#prefix = "root://t3dcachedb03.psi.ch:1094/pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V21bis/prep_eandmu/ZmmH.BestCSV.heppy."
#prefix = "root://t3dcachedb03.psi.ch:1094/pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V21bis/singlesys_eandmu_v3/ZmmH.BestCSV.heppy."
#prefix = "root://t3dcachedb03.psi.ch:1094/pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V24/prepv2/ZmmH.BestCSV.heppy."
#prefix = "root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V24/mva_v9/ZmmH.BestCSV.heppy."
#prefix = "root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V24/singlesys_v5/ZmmH.BestCSV.heppy."
#prefix = "root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V24/singlesys_v10/ZmmH.BestCSV.heppy."
prefix = "root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V25/sys_v5_2/ZmmH.BestCSV.heppy."


def getWeight(fileInc, fileB, region):

    countInc=0
    # print 'region',region,'\n'
    for file in fileInc:
        print 'file inc is', file
        f = ROOT.TFile.Open(prefix+file+".root")
        # print 'adding',file
        tree = f.Get("tree")
        if file in SampleCuts:
            print'taking additional', SampleCuts[file], ' cut for', file
            region = region +'&('+SampleCuts[file]+')'
        countInc    = countInc + 1.* tree.Draw("",region)
        #print 'countInc',countInc,'\n'
        #countInc    = 1.* tree.GetEntries(region)
        f.Close()

    countB=0
    for file in fileB:
        print 'fileB inc is', file
        f = ROOT.TFile.Open(prefix+file+".root")
        # print 'adding',file
        tree = f.Get("tree")
        if file in SampleCuts:
            print'taking additional', SampleCuts[file], ' cut for', file
            #region = region +'&('+SampleCuts[file]+')'
            countB      = countB + 1.* tree.Draw("",region +'&('+SampleCuts[file]+')')
        else:
            countB      = countB + 1.* tree.Draw("",region)
        print 'nEvents for file', file, 'is:', countB
        #print 'countB',countB,'\n'
        #countB      = 1.* tree.GetEntries(region)
        f.Close()
    print 'countInc is', countInc
    print 'countB is', countB
    weight = countInc/(countB+countInc)
    return weight

def getExtWeight(files):

    Weights = []

    countWeights = 0
    for file in files:
        f = ROOT.TFile.Open(prefix+file+".root")
        tree = f.Get("tree")
        nevents = 1.* tree.Draw("","1")
        print '#Events for', file, ' are', nevents
        countWeights = countWeights + nevents
        Weights.append(nevents)
        f.Close()

#    print 'countWeights is'
    for weight, file in zip(Weights, files):
        print 'Weight for sample', file, 'is', weight/countWeights


######
#Samples
######

###V25
#ZLLjetsHT0       = ["DYJetsToLL_M-50_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext1","DYJetsToLL_M-50_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext2"]
#ZLLjetsHT70      = ["DYJetsToLL_M-50_HT-70to100_TuneCUETP8M1_13TeV-madgraphMLM-pythia8"]
#ZLLjetsHT100     = ["DYJetsToLL_M-50_HT-100to200_TuneCUETP8M1_13TeV-madgraphMLM-pythia8","DYJetsToLL_M-50_HT-100to200_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext1"]
#ZLLjetsHT200     = ["DYJetsToLL_M-50_HT-200to400_TuneCUETP8M1_13TeV-madgraphMLM-pythia8","DYJetsToLL_M-50_HT-200to400_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext1"]
#ZLLjetsHT400     = ["DYJetsToLL_M-50_HT-400to600_TuneCUETP8M1_13TeV-madgraphMLM-pythia8","DYJetsToLL_M-50_HT-400to600_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext1"]
#ZLLjetsHT600     = ["DYJetsToLL_M-50_HT-600to800_TuneCUETP8M1_13TeV-madgraphMLM-pythia8"]
#ZLLjetsHT800     = ["DYJetsToLL_M-50_HT-800to1200_TuneCUETP8M1_13TeV-madgraphMLM-pythia8"]
#ZLLjetsHT1200    = ["DYJetsToLL_M-50_HT-1200to2500_TuneCUETP8M1_13TeV-madgraphMLM-pythia8"]
#ZLLjetsHT2500    = ["DYJetsToLL_M-50_HT-2500toInf_TuneCUETP8M1_13TeV-madgraphMLM-pythia8"]

ZlljetsHTbinned = [
        "DYJetsToLL_M-50_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext1",
        #"DYJetsToLL_M-50_HT-70to100_TuneCUETP8M1_13TeV-madgraphMLM-pythia8",
        "DYJetsToLL_M-50_HT-100to200_TuneCUETP8M1_13TeV-madgraphMLM-pythia8",
        "DYJetsToLL_M-50_HT-100to200_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext1",
        "DYJetsToLL_M-50_HT-200to400_TuneCUETP8M1_13TeV-madgraphMLM-pythia8",
        "DYJetsToLL_M-50_HT-200to400_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext1",
        "DYJetsToLL_M-50_HT-400to600_TuneCUETP8M1_13TeV-madgraphMLM-pythia8",
        "DYJetsToLL_M-50_HT-400to600_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext1",
        "DYJetsToLL_M-50_HT-600to800_TuneCUETP8M1_13TeV-madgraphMLM-pythia8",
        "DYJetsToLL_M-50_HT-800to1200_TuneCUETP8M1_13TeV-madgraphMLM-pythia8",
        "DYJetsToLL_M-50_HT-1200to2500_TuneCUETP8M1_13TeV-madgraphMLM-pythia8",
        "DYJetsToLL_M-50_HT-2500toInf_TuneCUETP8M1_13TeV-madgraphMLM-pythia8"]


#b-enriched
#V25 only
ZLLBjets         = ["DYBJetsToLL_M-50_TuneCUETP8M1_13TeV-madgraphMLM-pythia8","DYBJetsToLL_M-50_Zpt-100to200_TuneCUETP8M1_13TeV-madgraphMLM-pythia8","DYBJetsToLL_M-50_Zpt-200toInf_TuneCUETP8M1_13TeV-madgraphMLM-pythia8"]

#ZLLBjets         = ["DYBJetsToLL_M-50_Zpt-100to200_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext1","DYBJetsToLL_M-50_Zpt-200toInf_TuneCUETP8M1_13TeV-madgraphMLM-pythia8","DYBJetsToLL_M-50_Zpt-200toInf_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext1"]

#V24
#ZLLjetsHT0       = ["DYJetsToLL_M-50_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext1"]
#ZLLjetsHT100     = ["DYJetsToLL_M-50_HT-100to200_TuneCUETP8M1_13TeV-madgraphMLM-pythia8","DYJetsToLL_M-50_HT-100to200_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext1"]
#ZLLjetsHT200     = ["DYJetsToLL_M-50_HT-200to400_TuneCUETP8M1_13TeV-madgraphMLM-pythia8","DYJetsToLL_M-50_HT-200to400_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext1"]
#ZLLjetsHT400     = ["DYJetsToLL_M-50_HT-400to600_TuneCUETP8M1_13TeV-madgraphMLM-pythia8","DYJetsToLL_M-50_HT-400to600_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext1"]
#ZLLjetsHT600     = ["DYJetsToLL_M-50_HT-600toInf_TuneCUETP8M1_13TeV-madgraphMLM-pythia8","DYJetsToLL_M-50_HT-600toInf_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext1"]

#ZLLNlojetsVPTINCL       = ["DYJetsToLL_M-50_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8"]
#ZLLNlojetsVPT150     = ["DYJetsToLL_Pt-100To250_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8_ext1"]
#ZLLNlojetsVPT250     = ["DYJetsToLL_Pt-250To400_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8_ext1"]
#ZLLNlojetsVPT400     = ["DYJetsToLL_Pt-400To650_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8_ext1"]
#ZLLNlojetsVPT650     = ["DYJetsToLL_Pt-650ToInf_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8_ext1"]

#ZLLBjets         = ["DYBJetsToLL_M-50_TuneCUETP8M1_13TeV-madgraphMLM-pythia8"]
#ZLLjetsBGenFilter= ["DYJetsToLL_BGenFilter_M-50_TuneCUETP8M1_13TeV-madgraphMLM-pythia8"]

####
#Phase-space cuts
####

DYBJets          = "(lheNb>0)"
DYJetsBGenFilter = "(lheNb==0 && nGenStatus2bHad>0)"


VPT0              = "(lheV_pt<100)"
VPT100            = "(lheV_pt>100 && lheV_pt<200)"
VPT200            = "(lheV_pt>200)"

SampleCuts = {"DYBJetsToLL_M-50_TuneCUETP8M1_13TeV-madgraphMLM-pythia8":"lheV_pt<100","DYJetsToLL_M-50_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext1":"(lheHT<100)"}

#V24
#HT0              = "(lheHT<70)"
#HT0              = "(lheHT<100)"
#HT100            = "(lheHT>100 && lheHT<200)"
#HT200            = "(lheHT>200 && lheHT<400)"
#HT400            = "(lheHT>400 && lheHT<600)"
#HT400            = "(lheHT>600 && lheHT<800)"
#HT600            = "(lheHT>600)"
#VPT100            = "(lheV_pt>100 && lheV_pt<250)"
#VPT250            = "(lheV_pt>250 && lheV_pt<400)"
#VPT400            = "(lheV_pt>400 && lheV_pt<650)"
#VPT650            = "(lheV_pt>650)"

########
#ZLL
########

#print "weightZBjetsVpt0=\t%.2f\n"   %getWeight(ZlljetsHTbinned, ZLLBjets, VPT0)
#print "weightZBjetsVpt100=\t%.2f\n"   %getWeight(ZlljetsHTbinned, ZLLBjets, VPT100)
#print "weightZBjetsVpt200=\t%.2f\n"   %getWeight(ZlljetsHTbinned, ZLLBjets, VPT200)

#For ext.

#getExtWeight(["DYJetsToLL_M-50_HT-100to200_TuneCUETP8M1_13TeV-madgraphMLM-pythia8","DYJetsToLL_M-50_HT-100to200_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext1"])
#getExtWeight(["DYJetsToLL_M-50_HT-200to400_TuneCUETP8M1_13TeV-madgraphMLM-pythia8","DYJetsToLL_M-50_HT-200to400_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext1"])
#getExtWeight(["DYJetsToLL_M-50_HT-400to600_TuneCUETP8M1_13TeV-madgraphMLM-pythia8","DYJetsToLL_M-50_HT-400to600_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext1"])

#getExtWeight(["ZH_HToBB_ZToLL_M125_13TeV_powheg_pythia8","ZH_HToBB_ZToLL_M125_13TeV_powheg_pythia8_ext1"])

#V25
#DYB
#print "weightZBjetsHT0=\t%.2f\n"   %getWeight(ZLLjetsHT0,     ZLLBjets, HT0+"&&"+DYBJets)
#print "weightZBjetsHT100=\t%.2f\n" %getWeight(ZLLjetsHT100,   ZLLBjets, HT100+"&&"+DYBJets)
#print "weightZBjetsHT200=\t%.2f\n" %getWeight(ZLLjetsHT200,   ZLLBjets, HT200+"&&"+DYBJets)
#print "weightZBjetsHT400=\t%.2f\n" %getWeight(ZLLjetsHT400,   ZLLBjets, HT400+"&&"+DYBJets)
#print "weightZBjetsHT600=\t%.2f\n" %getWeight(ZLLjetsHT600,   ZLLBjets, HT600+"&&"+DYBJets)
#
#print "weightZBGenjetsHT0=\t%.2f\n"   %getWeight(ZLLjetsHT0,     ZLLjetsBGenFilter, HT0+"&&"+DYJetsBGenFilter)
#print "weightZBGenjetsHT100=\t%.2f\n" %getWeight(ZLLjetsHT100,   ZLLjetsBGenFilter, HT100+"&&"+DYJetsBGenFilter)
#print "weightZBGenjetsHT200=\t%.2f\n" %getWeight(ZLLjetsHT200,   ZLLjetsBGenFilter, HT200+"&&"+DYJetsBGenFilter)
#print "weightZBGenjetsHT400=\t%.2f\n" %getWeight(ZLLjetsHT400,   ZLLjetsBGenFilter, HT400+"&&"+DYJetsBGenFilter)
#print "weightZBGenjetsHT600=\t%.2f\n" %getWeight(ZLLjetsHT600,   ZLLjetsBGenFilter, HT600+"&&"+DYJetsBGenFilter)
#
#print "weightNloHT100=\t%.2f\n" %getWeight(ZLLNlojetsVPTINCL, ZLLNlojetsVPT150 , VPT100)
#print "weightNloHT250=\t%.2f\n" %getWeight(ZLLNlojetsVPTINCL, ZLLNlojetsVPT250 , VPT250)
#print "weightNloHT400=\t%.2f\n" %getWeight(ZLLNlojetsVPTINCL, ZLLNlojetsVPT400 , VPT400)
#print "weightNloHT650=\t%.2f\n" %getWeight(ZLLNlojetsVPTINCL, ZLLNlojetsVPT650 , VPT650)


##
##If you use extension only
##
#getExtWeight(['ZH_HToBB_ZToLL_M125_13TeV_powheg_pythia8','ZH_HToBB_ZToLL_M125_13TeV_powheg_pythia8_ext1'])
#getExtWeight(['ggZH_HToBB_ZToLL_M125_13TeV_powheg_pythia8','ggZH_HToBB_ZToLL_M125_13TeV_powheg_pythia8_ext1','ggZH_HToBB_ZToLL_M125_13TeV_powheg_pythia8_ext2'])
#getExtWeight(['DYJetsToLL_M-5to50_HT-100to200_TuneCUETP8M1_13TeV-madgraphMLM-pythia8','DYJetsToLL_M-5to50_HT-100to200_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext1'])
#getExtWeight(['DYJetsToLL_M-5to50_HT-200to400_TuneCUETP8M1_13TeV-madgraphMLM-pythia8','DYJetsToLL_M-5to50_HT-200to400_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext1'])
#getExtWeight(['DYJetsToLL_M-5to50_HT-400to600_TuneCUETP8M1_13TeV-madgraphMLM-pythia8','DYJetsToLL_M-5to50_HT-400to600_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext1'])
#getExtWeight(['DYJetsToLL_M-5to50_HT-600toInf_TuneCUETP8M1_13TeV-madgraphMLM-pythia8','DYJetsToLL_M-5to50_HT-600toInf_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext1'])
##
#getExtWeight(['DYJetsToLL_M-50_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext1'])
#getExtWeight(['DYJetsToLL_M-50_HT-100to200_TuneCUETP8M1_13TeV-madgraphMLM-pythia8','DYJetsToLL_M-50_HT-100to200_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext1'])
#getExtWeight(['DYJetsToLL_M-50_HT-200to400_TuneCUETP8M1_13TeV-madgraphMLM-pythia8','DYJetsToLL_M-50_HT-200to400_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext1'])
#getExtWeight(['DYJetsToLL_M-50_HT-400to600_TuneCUETP8M1_13TeV-madgraphMLM-pythia8','DYJetsToLL_M-50_HT-400to600_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext1'])
#getExtWeight(['DYJetsToLL_M-50_HT-600toInf_TuneCUETP8M1_13TeV-madgraphMLM-pythia8','DYJetsToLL_M-50_HT-600toInf_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext1'])
#getExtWeight(['ST_t-channel_4f_leptonDecays_13TeV-amcatnlo-pythia8_TuneCUETP8M1','ST_t-channel_4f_leptonDecays_13TeV-amcatnlo-pythia8_TuneCUETP8M1_ext1'])


