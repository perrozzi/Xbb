
import ROOT
ROOT.gStyle.SetOptStat(0)
ROOT.gROOT.SetBatch()

#pathin_ = 'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V24/singlesys_22_test_v5/ZmmH.BestCSV.heppy.DYJetsToLL_M-50_HT-200to400_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext1.root'
#pathin_ = 'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V24/TEST/ZmmH.BestCSV.heppy.DYJetsToLL_M-50_HT-200to400_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext1.root'
#pathin_ = 'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V24/TEST/DYJetsToLL_M-50_HT-200to400_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext1/tree_VHBB_HEPPY_V24_DYJetsToLL_M-50_HT-200to400_TuneCUETP8M1_13TeV-madgraphMLM-Py8__spr16MAv2-puspr16_80r2as_2016_MAv2_v0_ext1-v1_70_1bd625da610d27dc2fec62bfc9ac74b33588f1fba2e6441645fd9c51.root'
#pathin_ = 'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V24/TEST2/ZmmH.BestCSV.heppy.DYJetsToLL_M-50_HT-200to400_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_ext1.root'
#pathin_ = 'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V25b/sys_test_JES//ggZH_HToBB_ZToLL_M125_13TeV_powheg_pythia8_ext1/tree_VHBB_HEPPY_V25_ggZH_HToBB_ZToLL_M125_13TeV_powheg_Py8__RunIISummer16MAv2-PUMoriond17_80r2as_2016_TrancheIV_v6_ext1-v1_15_939abb159fc830426dc23d69faa8879ffe7368ca6335454ca837ca5b.root'
#pathin_ = 'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V25b/sys_test_JES_v16//ggZH_HToBB_ZToLL_M125_13TeV_powheg_pythia8_ext1/tree_VHBB_HEPPY_V25_ggZH_HToBB_ZToLL_M125_13TeV_powheg_Py8__RunIISummer16MAv2-PUMoriond17_80r2as_2016_TrancheIV_v6_ext1-v1_2_fbed43b47595a1cc25dc19e73aad98be133b83c2b51562c8f376e529.root'
#pathin_ = 'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V25b/sys_test_JES_v17//ggZH_HToBB_ZToLL_M125_13TeV_powheg_pythia8_ext1/tree_VHBB_HEPPY_V25_ggZH_HToBB_ZToLL_M125_13TeV_powheg_Py8__RunIISummer16MAv2-PUMoriond17_80r2as_2016_TrancheIV_v6_ext1-v1_4_a4085e20b6f3529b24861250b2d0c6748eed84fb3c9aaa402e946fba.root'
#pathin_ = 'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V25b/sys_test_JES_v18//ggZH_HToBB_ZToLL_M125_13TeV_powheg_pythia8_ext1/tree_VHBB_HEPPY_V25_ggZH_HToBB_ZToLL_M125_13TeV_powheg_Py8__RunIISummer16MAv2-PUMoriond17_80r2as_2016_TrancheIV_v6_ext1-v1_9_7f43c75a51e986047797368d61b0e129bd516cb6bbc352c27f45b9d5.root'
#pathin_ = 'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V25b/sys_test_JES_v19//ggZH_HToBB_ZToLL_M125_13TeV_powheg_pythia8_ext1/tree_VHBB_HEPPY_V25_ggZH_HToBB_ZToLL_M125_13TeV_powheg_Py8__RunIISummer16MAv2-PUMoriond17_80r2as_2016_TrancheIV_v6_ext1-v1_4_a4085e20b6f3529b24861250b2d0c6748eed84fb3c9aaa402e946fba.root'
#pathin_ = 'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V25b/sys_v6_testJES3//ggZH_HToBB_ZToLL_M125_13TeV_powheg_pythia8_ext1/tree_VHBB_HEPPY_V25_ggZH_HToBB_ZToLL_M125_13TeV_powheg_Py8__RunIISummer16MAv2-PUMoriond17_80r2as_2016_TrancheIV_v6_ext1-v1_9_7f43c75a51e986047797368d61b0e129bd516cb6bbc352c27f45b9d5.root'
pathin_ = 'root://t3dcachedb03.psi.ch:1094//pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V25b/sys_v6_testJES5//ggZH_HToBB_ZToLL_M125_13TeV_powheg_pythia8_ext1/tree_VHBB_HEPPY_V25_ggZH_HToBB_ZToLL_M125_13TeV_powheg_Py8__RunIISummer16MAv2-PUMoriond17_80r2as_2016_TrancheIV_v6_ext1-v1_9_7f43c75a51e986047797368d61b0e129bd516cb6bbc352c27f45b9d5.root'

f = ROOT.TFile.Open(pathin_)
t = f.Get("tree")


#VarList = ['HCMVAV2_reg_mass','HCMVAV2_reg_pt','HCMVAV2_reg_eta','HCMVAV2_reg_phi']
VarList = ['HCMVAV2_reg_mass','HCMVAV2_reg_pt','HCMVAV2_reg_eta','HCMVAV2_reg_phi','hJetCMVAV2_pt_reg_0','hJetCMVAV2_pt_reg_1','hJetCMVAV2_pt_reg']
#VarList = ['hJetCMVAV2_pt_reg']
UDList = ['Up','Down']

SysList = [
    "JER",
    "PileUpDataMC",
    "PileUpPtRef",
    "PileUpPtBB",
    "PileUpPtEC1",
    #"PileUpPtEC2",
    #"PileUpPtHF",
    "RelativeJEREC1",
    #"RelativeJEREC2",
    #"RelativeJERHF",
    "RelativeFSR",
    "RelativeStatFSR",
    "RelativeStatEC",
    #"RelativeStatHF",
    "RelativePtBB",
    "RelativePtEC1",
    #"RelativePtEC2",
    #"RelativePtHF",
    "AbsoluteScale",
    "AbsoluteMPFBias",
    "AbsoluteStat",
    "SinglePionECAL",
    "SinglePionHCAL",
    "Fragmentation",
    "TimePtEta",
    "FlavorQCD"
    ]


#VarList = ['HCSV_reg_corrSYSUD_mass_CAT','HCSV_reg_corrSYSUD_pt_CAT', 'HCSV_reg_corrSYSUD_eta_CAT', 'HCSV_reg_corrSYSUD_phi_CAT','Jet_pt_reg_corrSYSUD_CAT_INDEX0','Jet_pt_reg_corrSYSUD_CAT_INDEX1', 'Sum$(Jet_pt_reg_corrSYSUD_CAT>30&&abs(Jet_eta)<2.4&&Jet_puId==7&&Jet_id>0&&aJCidx!=(hJCidx[0])&&(aJCidx!=(hJCidx[1])))']
#SysList = ['JER','JEC']
#CatList = ['HighCentral','LowCentral','HighForward','LowForward']
AxisList = {'mass':[20,0,400],'HCMVAV2_reg_pt':[20,0,400],'phi':[20,-3.2, 3.2],'eta':[20,0,5],'hJet':[20,0,300]}
for var in VarList:
    for syst in SysList:
        for j in range(0,10):
            if 'hJetCMVAV2_pt_reg' in var and not 'hJetCMVAV2_pt_reg_0' in var and not 'hJetCMVAV2_pt_reg_1' in var:
                if var[-1] == ']':
                    var = var[:var.find('[')] + '['+str(j)+']'
                else:
                    var = var + '['+str(j)+']'
            #for cat in CatList:
            c = ROOT.TCanvas('c','c',800,800)
            pad1 = ROOT.TPad('pad1','pad1', 0, 0.3, 1, 1.0)
            pad1.SetBottomMargin(0)
            pad1.SetGridx()
            pad1.Draw()
            pad1.cd()

            nbin = 0
            xmin = 0
            xmax = 0
            #var_nom = var.replace('SYSUD','').replace('_CAT','').replace('_corr','')
            for axis in AxisList:
                if axis in var:
                    nbin = AxisList[axis][0]
                    xmin = AxisList[axis][1]
                    xmax = AxisList[axis][2]

            h_nom = ROOT.TH1D('h_nom','h_nom',nbin, xmin, xmax)
            #print 'var nom is', var_nom
            t.Draw(var+'>>h_nom')
            #if var == 'hJetCMVAV2_pt_reg'
            #for j in range(0,10):
            #    if '_INDEX0'in var_nom: t.Draw(var_nom.replace('_INDEX0','[hJCidx[0]]')+'>>h_nom')
            #    elif '_INDEX1'in var_nom: t.Draw(var_nom.replace('_INDEX1','[hJCidx[1]]')+'>>h_nom')
            #else:
            #    t.Draw(var_nom+'>>h_nom')
            h_nom.SetLineColor(1)
            h_nom.SetMarkerStyle(20)
            h_nom.SetMarkerColor(1)
            h_nom.SetLineWidth(2)
            h_nom.Sumw2()

            h_ud = {}
            for ud in UDList:
                ##fill Dic
                #SysDic = {}
                #SysDic['var'] = var
                #SysDic['sys'] = syst
                #SysDic['UD'] = ud
                #SysDic['cat'] = cat
                #SysDic['varname'] = var.replace('SYS',syst).replace('UD',ud).replace('CAT',cat)
                h_ud[ud] = ROOT.TH1D('h_%s'%ud,'h_%s'%ud,nbin, xmin, xmax)
                #if 'Jet_pt' in SysDic['varname']:
                #    if '_INDEX0'in SysDic['varname']:
                #        t.Draw(SysDic['varname'].replace('_INDEX0','[hJCidx[0]]')+'>>h_%s'%ud)
                #    elif '_INDEX1'in SysDic['varname']:
                #        t.Draw(SysDic['varname'].replace('_INDEX1','[hJCidx[1]]')+'>>h_%s'%ud)
                #else:
                #    t.Draw(SysDic['varname']+'>>h_%s'%ud)
                t.Draw(var+'_corr'+syst+ud+'>>h_%s'%ud)
                h_ud[ud].Draw('same')
                #t.Draw(SysDic['varname'])

            h_nom.Draw()
            h_nom.GetXaxis().SetTitle(var)
            h_ud['Up'].Draw('same')
            h_ud['Up'].SetLineColor(4)
            h_ud['Up'].SetLineStyle(4)
            h_ud['Up'].SetLineWidth(2)
            h_ud['Up'].GetYaxis().SetNdivisions(505)
            h_ud['Up'].GetYaxis().SetTitleSize(20)
            h_ud['Up'].GetYaxis().SetTitleFont(43)
            h_ud['Up'].GetYaxis().SetTitleOffset(1.55)
            h_ud['Up'].GetYaxis().SetLabelFont(43)
            h_ud['Up'].GetYaxis().SetLabelSize(15)
            h_ud['Up'].GetXaxis().SetTitleSize(20)
            h_ud['Up'].GetXaxis().SetTitleFont(43)
            h_ud['Up'].GetXaxis().SetTitleOffset(4.)
            h_ud['Up'].GetXaxis().SetLabelFont(43)
            h_ud['Up'].GetXaxis().SetLabelSize(15)
            h_ud['Up'].GetXaxis().SetTitle(var)

            h_ud['Down'].Draw('same')
            h_ud['Down'].SetLineColor(2)
            h_ud['Down'].SetLineStyle(3)
            h_ud['Down'].SetLineWidth(2)


            leg = ROOT.TLegend(0.7, 0.8, 1 , 1)
            leg.AddEntry(h_nom,'nominal')
            leg.AddEntry(h_ud['Up'],'up')
            leg.AddEntry(h_ud['Down'],'down')
            leg.Draw('same')

            c.cd()
            pad2 = ROOT.TPad("pad2", "pad2", 0, 0.05, 1, 0.3)
            pad2.SetTopMargin(0)
            pad2.SetBottomMargin(0.2)
            pad2.SetGridx()
            pad2.SetGridy()
            pad2.Draw()
            pad2.cd()

            ratio_up =  h_ud['Up'].Clone()
            ratio_up.Divide(h_nom)
            ratio_up.Draw()
            ratio_up.GetYaxis().SetRangeUser(0.9,1.1)
            ratio_down =  h_ud['Down'].Clone()
            ratio_down.Divide(h_nom)
            ratio_down.Draw('same')

            #if j == 1: continue
            #print 'VAR is', var

            c.SaveAs('BtagSplitNumUpDown/'+var+'_'+syst+'.pdf')
            c.SaveAs('BtagSplitNumUpDown/'+var+'_'+syst+'.png')
            c.SaveAs('BtagSplitNumUpDown/'+var+'_'+syst+'.root')
            c.SaveAs('BtagSplitNumUpDown/'+var+'_'+syst+'.C')
            if not 'hJetCMVAV2_pt_reg' in var or 'hJetCMVAV2_pt_reg_0' in var or 'hJetCMVAV2_pt_reg_1' in var:
                break

