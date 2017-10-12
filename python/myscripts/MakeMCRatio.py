import ROOT
import sys



#first iteration
#input_file_ = '/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_3/src/Xbb/python/logs_v24/PLOT_All_2/Plots/root/comp_Zll_CRZlight__Etabb_125.root'
#second iteration
#wQCD
#path_ = '/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_3/src/Xbb/python/logs_v24/SVPLOT_v22_NLO_LO_wQCD/Plots/root/'
#noQCD
#path_ = '/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_3/src/Xbb/python/logs_v24/SVPLOT_v22_NLO_LO_noQCD/Plots/root/'

#Z+light
#wQCD
#path_ = '/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_3/src/Xbb/python/logs_v24/SVPLOT_v22_Zll_CRZlightforWeight_DYonly/Plots/root/'
#noQCD
#path_ = '/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_3/src/Xbb/python/logs_v24/SVPLOT_v22_Zll_CRZlightforWeight_DYonly_noQCD/Plots/root/'

#Closure
#path_ = '/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_3/src/Xbb/python/logs_v24/SVPLOT_v22_CR_Zlight_NLOweight_wAllWeight_5/Plots/root/'
#DY+light wiht weights
#path_ = '/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_3/src/Xbb/python/logs_v24/SVPLOT_v22_CR_Zlight_wAllWeight_6/Plots/root/'
#DY+light no weights
#path_ = '/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_3/src/Xbb/python/logs_v24/SVPLOT_v22_CR_Zlight_withoutAllWeight_2/Plots/root/'

#from 8/11/16
#DY+light no QCD
#path_ = '/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_3/src/Xbb/python/logs_v24/SVPLOT_v22_lonoQCD_nlo_allWeights/Plots/root/'
#path_ = '/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_3/src/Xbb/python/logs_v24/SVPLOT_v22_lonoQCD_nlo_allWeights_2/Plots/root/'
#DY+light with QCD
#path_ = '/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_3/src/Xbb/python/logs_v24/SVPLOT_v22_lowQCD_nlo_allWeights/Plots/root/'

#For "per b categories" reweighting
#path_ = '/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_3/src/Xbb/python/logs_v24/SVPLOT_v22_lo_BasicCuts_Etabbjb/Plots/root/'
#with borader bins
#path_ = '/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_3/src/Xbb/python/logs_v24/SVPLOT_v22_lo_BasicCuts_Etabbjb_8bin_2/Plots/root/'
#including EWK in bfilter/benriched
#path_ = "/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_3/src/Xbb/python/logs_v24/SVPLOT_v22_lo_BasicCuts_Etabbjb_bgenewk_v2_10_11_16_5/Plots/root/"
#with 8 bins
#path_ = "/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_3/src/Xbb/python/logs_v24/SVPLOT_v22_lo_BasicCuts_Etabbjb_bgenewk_8bin_v4_10_11_16_5/Plots/root/"
#with fixed pu, nlo ewk 400tl650
path_ = "/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_3/src/Xbb/python/logs_v24/PLOT_v22_lo_BasicCuts_Etabbjb_bgenewk_pu_ewknlo400to650_32and8bin_10_11_16_5/Plots/root/"



#filename_ = 'comp_Zll_BasicCuts__Etabb_.root'
#filename_ = 'comp_Zll_BasicCuts__genEtabb_.root'
#filename_ = 'comp_Zll_BasicCuts__genEtabbPtJ_.root'

#QCD_ = 'wQCD'
#QCD_ = 'noQCD'

#filename_ = 'comp_Zll_CRZlightforWeight__Etabb_125.root'
#filename_ = 'comp_Zll_CRZlightforWeight__genEtabb_125.root'
#filename_ = 'comp_Zll_CRZlightforWeight__genEtabbPtJ_125.root'

#filename_ = 'comp_Zll_CRZlight__Etabb_125.root'

#For "per b categories" reweighting
#filename_ = 'comp_Zll_BasicCuts__Etabb0b_.root'
#filename_ = 'comp_Zll_BasicCuts__Etabb1b_.root'
filename_ = 'comp_Zll_BasicCuts__Etabb2b_.root'

#QCD_ = 'wQCD_Zlf'
#QCD_ = 'noQCD_Zlf'

#QCD_ = 'closure'
#QCD_ = 'noWclosure'

#from 8/11/16
#QCD_ = 'noQCD'
#QCD_ = 'wQCD'

#from 9/11/16
#QCD_ = '0b'
#QCD_ = '1b'
#QCD_ = '2b'
#broader bins
#QCD_ = '0b_bin8'
#QCD_ = '1b_bin8'
#QCD_ = '2b_bin8'
#including ewk in bgen and benriched
#QCD_ = '0b_ewk'
#QCD_ = '1b_ewk'
#QCD_ = '2b_ewk'
#including ewk in bgen and benriched
#QCD_ = '0b_8bin_ewk'
#QCD_ = '1b_8bin_ewk'
#QCD_ = '2b_8bin_ewk'
#including ewk in bgen and benriched
#QCD_ = '0b_32bin_puewk'
#QCD_ = '1b_32bin_puewk'
QCD_ = '2b_8bin_puewk'

input_file_ = path_ + filename_

f = ROOT.TFile.Open(input_file_, 'read')

ROOT.gStyle.SetOptStat(0)

for key in ROOT.gDirectory.GetListOfKeys():
    if not 'TCanvas' in key.GetClassName(): continue
    print 'The key is', key.GetName()
    canvas = f.Get(key.GetName())
    print 'gonna print the canvas'
    #canvas.Draw()
    print 'the primitives are'
    #canvas.GetListOfPrimitives().ls()
    print ''
    #canvas.SaveAs('c.pdf')
    ##for prim in canvas.GetListOfPrimitives():
    ##    print 'the prim name is', prim.GetName()
    ##    print 'the prim name is', prim.GetTitle()
    ##    if not 'ZJets' in prim.GetName(): continue
    ##    if 'amc' in prim.GetTitle():
    ##        print 'yeah'
    ##        H_nlo = canvas.GetPrimitive(prim.GetName())
    ##    else:
    ##        print 'yeah man'
    ##        H_lo = canvas.GetPrimitive(prim.GetName())

    if filename_ == 'comp_Zll_BasicCuts__Etabb_.root': h_name = 'Etabb'
    elif filename_ == 'comp_Zll_BasicCuts__genEtabb_.root': h_name = 'genEtabb'
    elif filename_ == 'comp_Zll_BasicCuts__genEtabbPtJ_.root': h_name = 'genEtabbPtJ'
    elif filename_ == 'comp_Zll_CRZlightforWeight__Etabb_125.root': h_name = 'Etabb'
    elif filename_ == 'comp_Zll_CRZlightforWeight__genEtabb_125.root': h_name = 'genEtabb'
    elif filename_ == 'comp_Zll_CRZlightforWeight__genEtabbPtJ_125.root': h_name = 'genEtabbPtJ'
    elif filename_ == 'comp_Zll_CRZlight__Etabb_125.root': h_name = 'Etabb'
    elif filename_ == 'comp_Zll_BasicCuts__Etabb2b_.root': h_name = 'Etabb2b'
    elif filename_ == 'comp_Zll_BasicCuts__Etabb1b_.root': h_name = 'Etabb1b'
    elif filename_ == 'comp_Zll_BasicCuts__Etabb0b_.root': h_name = 'Etabb0b'
    else:
        print '@ERROR: no correct filename found. Abort'
        sys.exit()
    #H_stack = canvas.GetPrimitive('genEtabb')
    H_stack = canvas.GetPrimitive(h_name)
    for h in H_stack.GetHists():
        print 'h name is', h.GetTitle()
        h.SetDirectory(0)
        if 'amc' in h.GetTitle():
            H_nlo = h
        else:
            H_lo = h

    #nlo/lo ratio histogram
    H_nlo.Divide(H_lo)
    #H_nlo.Scale(1.*H_nlo.GetXaxis().GetNbins()/H_nlo.Integral())

    #fit the histogram using various functions
    #f = ROOT.TF1('f1', 'pol6*[0]*sin([1]*x + [2])', 0, 5)
    #f = ROOT.TF1('f1', 'pol4', 0, 5)
    #f = ROOT.TF1('f1', 'pol3', 0, 5)
    #f = ROOT.TF1('f1', '(pol2)*(1-[3]*exp(-[4]*x))', 0, 5)
    f = ROOT.TF1('f1', '(pol3)*(exp(-[4]*x))', 0, 5)
    #f = ROOT.TF1('f1', '([0]+[1]*x+[2]*x*x)', 0, 5)
    f.SetParameters(1, 0.01, 10)
    f.SetParameters(0, 0.01, 10)
    #f = ROOT.TF1('f1', 'pol6', 0, 5)
    #H_nlo.Fit("pol4")
    H_nlo.Fit("f1","0")
    #fit = H_nlo.GetFunction("pol4")
    fit = H_nlo.GetFunction("f1")
    hfit = H_nlo.Clone('hfit')
    ratio = H_nlo.Clone('ratio')
    print 'bins', hfit.GetXaxis().GetNbins()

    axis = H_nlo.GetXaxis()
    nbins = axis.GetNbins()

    print 'nbins is', nbins
    print 'bins', hfit.GetXaxis().GetNbins()

    for bin in range(0, nbins):
        print 'bin is', bin
        #Jprint 'Print: bin is', bin
        #Jprint 'Low, high, content are', H_nlo.GetBinLowEdge(bin), H_nlo.GetBinLowEdge(bin+1), H_nlo.GetBinContent(bin)
        eval = fit.Eval(H_nlo.GetBinCenter(bin))
        #print 'eval is', eval
        hfit.SetBinContent(bin, eval)

    print 'debug0'

    c = ROOT.TCanvas("c", "canvas", 800, 800)
    pad1 = ROOT.TPad('pad1','pad1', 0, 0.3, 1, 1.0)
    pad1.SetBottomMargin(0)
    pad1.SetGridx()
    pad1.Draw()
    pad1.cd()

    print 'debug1'

    #func = 'pol6'
    #func = 'pol6psin'
    #func = 'polxpsin'
    #func = 'pol2xexp'
    func = 'pol3xexp'
    #func = 'pol3'
    #func = 'pol4'

    H_nlo.Draw()
    H_nlo.GetYaxis().SetRangeUser(0.4,3)
    fit.Draw('same')
    H_nlo.SetTitle('NLO/LO')
    H_nlo.SetLineWidth(4)
    leg = ROOT.TLegend(0.15, 0.65, 0.35 , 0.85)
    leg.AddEntry(H_nlo, 'NLO/LO', "LP");
    leg.AddEntry(fit, func ,"LP");
    leg.Draw()
    print 'debug2'
    #hfit.Draw('same')
    #hfit.SetLineColor(2)
    #hfit.SetLineWidth(1)
    #hfit.SetMarkerColor(2)

    c.cd()
    pad2 = ROOT.TPad('pad2', 'pad2', 0, 0.05, 1, 0.3)
    pad2.SetTopMargin(0)
    pad2.SetBottomMargin(0.2)
    pad2.SetGridx()
    pad2.Draw()
    pad2.cd()

    #ratio histogram
    #ratio = TH1(H_nlo)
    ratio.Divide(hfit)
    ratio.Draw()
    ratio.SetTitle('')
    ratio.GetYaxis().SetNdivisions(505)
    ratio.GetYaxis().SetRangeUser(0.9, 1.1)
    ratio.GetYaxis().SetLabelFont(43)
    ratio.GetYaxis().SetLabelSize(20)
    ratio.GetXaxis().SetLabelFont(43)
    ratio.GetXaxis().SetLabelSize(20)

    c.SaveAs('ratio_%s_%s_%s.png' %(func,QCD_,h_name))
    c.SaveAs('ratio_%s_%s_%s.pdf' %(func,QCD_,h_name))
    c.SaveAs('ratio_%s_%s_%s.root' %(func,QCD_,h_name))
