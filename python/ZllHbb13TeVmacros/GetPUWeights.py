import ROOT

pupath = '/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_3/src/Xbb/python/PU/'
f_mc = ROOT.TFile.Open(pupath+"mcpu.root","read")
hist_mc = f_mc.Get("pileup")
intmc = hist_mc.Integral()
hist_mc.Scale(1./intmc)
f_data= ROOT.TFile.Open(pupath+"outputData.root","read")
#f_data= ROOT.TFile.Open(pupath+"outputDataP.root","read")
#f_data= ROOT.TFile.Open(pupath+"outputDataM.root","read")
hist_data= f_data.Get("pileup")
intdata = hist_data.Integral()
hist_data.Scale(1./intdata)

#hist_data.Divide(hist_mc)

#Read all the histgrams entry

print hist_data.GetXaxis().GetNbins() == hist_mc.GetXaxis().GetNbins()

mc_sum = 0
data_sum = 0
for b in range(0,hist_data.GetXaxis().GetNbins()):
    print 'The low edge is', hist_data.GetBinLowEdge(b)
    #print 'reading bin n', b
    #print 'bin center', hist_data.GetXaxis().GetBinCenter(b)
    #print 'bin low edge', hist_data.GetXaxis().GetBinLowEdge(b)
    #if print hist_data.GetBinContent(b)/hist_mc.GetBinContent(b)
    print 'data content'
    print hist_data.GetBinContent(b)
    print 'mc content'
    print hist_mc.GetBinContent(b)
    if hist_mc.GetBinContent(b) != 0:
        mc_sum += hist_mc.GetBinContent(b)
        data_sum += hist_data.GetBinContent(b)
        print 'ratio', hist_data.GetBinContent(b)/hist_mc.GetBinContent(b)
    else:
        print 'ratio', 0
print 'mc_sum is', mc_sum
print 'data_sum is', data_sum
