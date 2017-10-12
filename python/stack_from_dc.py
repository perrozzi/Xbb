#!/usr/bin/env python
impor pickle
import sys, os
from optparse import OptionParser
from copy import copy,deepcopy
from math import sqrt
import math
from HiggsAnalysis.CombinedLimit.DatacardParser import *
from HiggsAnalysis.CombinedLimit.ShapeTools     import *
from ROOT import *


# import ROOT with a fix to get batch mode (http://root.cern.ch/phpBB3/viewtopic.php?t=3198)
hasHelp = False
argv = sys.argv
for X in ("-h", "-?", "--help"):
    if X in argv:
        hasHelp = True
        argv.remove(X)
argv.append( '-b-' )
#import ROOT
from myutils import StackMaker, BetterConfigParser

ROOT.gROOT.SetBatch(True)
ROOT.gSystem.Load("libHiggsAnalysisCombinedLimit.so")
argv.remove( '-b-' )
if hasHelp: argv.append("-h")

#CONFIGURE
parser = OptionParser()
parser.add_option("-D", "--datacard", dest="dc", default="",
                      help="Datacard to be plotted")
parser.add_option("-B", "--bin", dest="bin", default="",
                      help="DC bin to plot")
parser.add_option("-M", "--mlfit", dest="mlfit", default="",
                      help="mlfit file for nuisances")
parser.add_option("-F", "--fitresult", dest="fit", default="s",
                      help="Fit result to be used, 's' (signal+background)  or 'b' (background only), default is 's'")
parser.add_option("-C", "--config", dest="config", default=[], action="append",
                      help="configuration file")
parser.add_option("-V", "--variable", dest="var", default="",
                      help="variable to be fitted")
parser.add_option("-R", "--region", dest="region", default="",
                  help="region to be plotted")
parser.add_option("-A", "--blind", dest="blind", default="",
                  help="if the blind cut need to be applied")

(opts, args) = parser.parse_args(argv)

print opts

def readBestFit(theFile):

    file = TFile.Open(theFile,'read')

    if file == None: raise RuntimeError, "Cannot open file %s" % theFile

    print '\n\n-----> Fit File: ',file

    fit_s  = file.Get('fit_s')
    fit_b  = file.Get('fit_b')
    prefit = file.Get("nuisances_prefit")

    print '\n\n-----> Fit_s : ', fit_s

    if fit_s == None or fit_s.ClassName()   != "RooFitResult": raise RuntimeError, "File %s does not contain the output of the signal fit 'fit_s'"     % args[0]
    if fit_b == None or fit_b.ClassName()   != "RooFitResult": raise RuntimeError, "File %s does not contain the output of the background fit 'fit_b'" % args[0]
    if prefit == None or prefit.ClassName() != "RooArgSet":    raise RuntimeError, "File %s does not contain the prefit nuisances 'nuisances_prefit'"  % args[0]

    isFlagged = {}
    table = {}
    fpf_b = fit_b.floatParsFinal()
    fpf_s = fit_s.floatParsFinal()
    nuiVariation = {}

    print '\nReading Best Fits...'

    for i in range(fpf_s.getSize()):
        nuis_s = fpf_s.at(i)
        name   = nuis_s.GetName();
        nuis_b = fpf_b.find(name)
        nuis_p = prefit.find(name)

        print 'Name:', name
        print 'nuis_b:', nuis_b
        print 'nuis_p:', nuis_b

        if nuis_p != None:
            mean_p, sigma_p = (nuis_p.getVal(), nuis_p.getError())
        for fit_name, nuis_x in [('b', nuis_b), ('s',nuis_s)]:
            if nuis_p != None:
                valShift = (nuis_x.getVal() - mean_p)/sigma_p
                sigShift = nuis_x.getError()/sigma_p
                print fit_name, name
                print valShift
                nuiVariation['%s_%s'%(fit_name,name)] = [valShift,sigShift]
                #print valShift
    return nuiVariation

def getBestFitShapes(procs,theShapes,shapeNui,theBestFit,DC,setup,opts,Dict):

    print 'Finding Best Shapes...'
    print 'bin:', opts.bin
    print 'procs:', procs
    #print 'theShapes:', theShapes

    b = opts.bin

    for p in procs:
        counter = 0
        nom = theShapes[p].Clone()

        print '\n Shape Process:', p
        print 'Nominal Integral:', nom.Integral()

        for (lsyst,nofloat,pdf,pdfargs,errline) in DC.systs:
            if errline[b][p] == 0: continue
            if ("shape" in pdf):
                if shapeNui[p+lsyst] > 0.:
                    theVari = 'Up'
                else:
                    theVari = 'Down'
                bestNuiVar = theShapes[p+lsyst+theVari].Clone()
                bestNuiVar.Add(nom, -1)

                #print p,lsyst,abs(shapeNui[p+lsyst]),bestNuiVar.Integral()

                bestNuiVar.Scale(abs(shapeNui[p+lsyst]))
                if counter == 0:
                    bestNui = bestNuiVar.Clone()
                else:
                    bestNui.Add(bestNuiVar)
                counter +=1

        nom.Add(bestNui)

        # Add the rateParam here
        #if p == 'TT': nom.Scale(0.94684)
        #if p == 'Zj0b': nom.Scale(1.0027)
        #if p =='Zj1b': nom.Scale(0.98815)
        #if p == 'Zj2b': nom.Scale(0.78818)
        print 'b is', b
        #if 'high' in b:
        #    if 'TT' in p: nom.Scale(1.1333)
        #    if 'Zj0b' in p: nom.Scale(1.1501)
        #    if 'Zj1b' in p: nom.Scale(0.70356)
        #    if 'Zj2b' in p  : nom.Scale(0.98518)
        #if 'low' in b:
        #    if 'TT' in p: nom.Scale(1.1534)
        #    if 'Zj0b' in p: nom.Scale(1.1280)
        #    if 'Zj1b' in p: nom.Scale(1.1594)
        #    if 'Zj2b' in p  : nom.Scale(0.90958)

        if opts.mlfit:
            print '@INFO: mlfit is present, gonna apply SF'
            if 'high' in b:
                if 'TT' in p: nom.Scale(1.1580)
                if 'Zj0b' in p: nom.Scale(1.3629)
                if 'Zj1b' in p: nom.Scale(0.83681)
                if 'Zj2b' in p  : nom.Scale(1.5287)
            elif 'low' in b:
                if 'TT' in p: nom.Scale(1.2711)
                if 'Zj0b' in p: nom.Scale(1.2830)
                if 'Zj1b' in p: nom.Scale(0.98643)
                if 'Zj2b' in p: nom.Scale(1.2769)
            else:
                print '@ERROR: nothing was scaled'
                sys.exit()
        else: print '@INFO: no mlfit present. No SF applied'

        #nom.Scale(theShapes[p].Integral()/nom.Integral()*theBestFit[p])


        print 'Nominal shape :', nom
        print 'best Fit shape Integral:', nom.Integral()
        print 'nBins:', nom.GetNbinsX()


        nBins = nom.GetNbinsX()
        for bin in range(1,nBins+1):
            nom.SetBinError(bin,theShapes[p].GetBinError(bin))
        theShapes['%s_%s'%(opts.fit,p)] = nom.Clone()

        # NEW METHOD to get the final fit
        #file = TFile.Open(opts.mlfit)
        #hist  = file.Get('shapes_fit_b/Zlf/'+p)
        #nBins = hist.GetNbinsX()
        #for bin in range(1,nBins+1):
        #    hist.SetBinError(bin,theShapes[p].GetBinError(bin))
        #theShapes['%s_%s'%(opts.fit,p)] = hist.Clone()



    histos = []
    typs = []
    sigCount = 0
    signalList = []
    #signalList = ['ggZHbb','qqZHbb']
    if 'VV' in opts.bin:
        signalList = ['VVb','VVlight']
    else:
        #signalList = ['Zbb']
        signalList = ['qqZHbb','ggZHbb']
    print 'Signal List:',signalList
    print 'Setup:', setup
    for s in setup:
        print s
        if s in signalList:
            if sigCount ==0:
                Overlay=copy(theShapes[Dict[s]])
                print 'Overlay is',Overlay
            else:
                Overlay.Add(theShapes[Dict[s]])
                print 'again, Overlay is',Overlay
            sigCount += 1
        #else:
        print 'Appending Histos with:', opts.fit, Dict[s]
        histos.append(theShapes['%s_%s'%(opts.fit,Dict[s])])
        typs.append(s)

    #print '\n\nOVERLAY!!!', Overlay
    print 'Histos:', histos
    print 'Types:', typs

    return histos,Overlay,typs





def drawFromDC():

    config = BetterConfigParser()
    config.read(opts.config)

    region = opts.region

    print "\nopts.config:",opts.config
    print "opts:", opts
    print "var:", opts.var
    print "bin:", opts.bin


    #dataname = 'Zll'
    #dataname = 'SingleElectron_Run2016B_PromptReco'
    dataname = ['SingleElectron_Run2016B_PromptReco','SingleElectron_Run2016C_PromptReco','SingleElectron_Run2016D_PromptReco','SingleElectron_Run2016F_PromptReco','SingleElectron_Run2016G_PromptReco']

    #if 'Zuu' in opts.bin: dataname = 'Zuu'
    #elif 'Zee' in opts.bin: dataname = 'Zee'
    #elif 'Wmunu' in opts.bin: dataname = 'Wmn'
    #elif 'Wenu' in opts.bin: dataname = 'Wen'
    #elif 'Znunu' in opts.bin: dataname = 'Znn'
    #elif 'Wtn' in opts.bin: dataname = 'Wtn'

    #if (opts.var == ''):
    #    var = 'BDT'
    #    if dataname == 'Zmm' or dataname == 'Zee': var = 'BDT_Zll'
    #    elif dataname == 'Wmn' or dataname == 'Wen': var = 'BDT_Wln'
    #    elif dataname == 'Znn':
    #        if 'HighPt' in opts.bin: var = 'BDT_ZnnHighPt'
    #        if 'LowPt' in opts.bin: var = 'BDT_ZnnLowPt'
    #        if 'LowCSV' in opts.bin: var = 'BDT_ZnnLowCSV'
    #    if dataname == '' or var == 'BDT': raise RuntimeError, 'Did not recognise mode or var from '+opts.bin
    #else:
    #    var = opts.var


    if opts.var == 'BDT':
        if 'LowPt' in opts.bin: var = 'gg_plus_ZH125_low_Zpt'
        if 'MedPt' in opts.bin: var = 'gg_plus_ZH125_med_Zpt'
        if 'HighPt' in opts.bin: var = 'gg_plus_ZH125_high_Zpt'
        if 'VV' in opts.bin: var = 'VV_bdt'


    #if 'BDT' in var:
    #    region = 'BDT'
    #else:

    region = opts.bin

    var = opts.var

    ws_var = config.get('plotDef:%s'%var,'relPath')

    if 'gg_plus' in var:
        ws_var = ROOT.RooRealVar(ws_var,ws_var,-1.,1.)
    else:
        ws_var = ROOT.RooRealVar(ws_var,ws_var, 0, 1)

    #blind = eval(config.get('Plot:%s'%region,'blind'))
    #blind = True
    #blind = False
    blind = eval(opts.blind)

    print 'config:', config
    print 'var: ', var
    print 'region: ', region



    Stack=StackMaker(config,var,region,True)

    if 'LowPt' in opts.bin or 'ch1_Wenu' == opts.bin or 'ch2_Wmunu' == opts.bin:
        Stack.addFlag2 = 'Low p_{T}(V)'
    elif 'MedPt' in opts.bin or 'ch1_Wenu2' == opts.bin or 'ch2_Wmunu2' == opts.bin:
        Stack.addFlag2 = 'Intermediate p_{T}(V)'
    elif 'HighPt' in opts.bin or 'ch1_Wenu3' == opts.bin or 'ch2_Wmunu3' == opts.bin:
        Stack.addFlag2 = 'High p_{T}(V)'


    # check for pre or post fit options
    preFit = False
    addName = 'PostFit_%s' %(opts.fit)
    if not opts.mlfit:
        addName = 'PreFit'
        preFit = True

    print '\n-----> Fit Type(opts.fit)  : ', opts.fit
    print '               (opts.mlfit): ', opts.mlfit
    print '               preFit      : ', preFit


    Stack.options['pdfName'] = '%s_%s_%s.pdf'  %(var,opts.bin,addName)

    log = eval(config.get('Plot:%s'%region,'log'))

    setup = ['Z_udscg','Zb','Zbb','TT','VVlight','ST','VV2b','qqZHbb','ggZHbb']

    if dataname == 'Zmm' or dataname == 'Zee': 
        try:
            setup.remove('W1b')
            setup.remove('W2b')
            setup.remove('Wlight')
            setup.remove('WH')
        except: print '@INFO: Wb / Wligh / WH not present in the datacard'
    if not dataname == 'Znn' and 'QCD' in setup:
        setup.remove('QCD')
    Stack.setup = setup

    Dict = eval(config.get('LimitGeneral','Dict'))
    #Dict = eval(config.get('Plot_general','Group'))
    lumi = eval(config.get('Plot_general','lumi'))
    
    options = copy(opts)
    options.dataname = "data_obs"
    options.mass = 0
    options.format = "%8.3f +/- %6.3f"
    options.channel = opts.bin
    options.excludeSyst = []
    options.norm = False
    options.stat = False
    options.bin = True # fake that is a binary output, so that we parse shape lines
    options.out = "tmp.root"
    options.fileName = args[0]
    options.cexpr = False
    options.fixpars = False
    options.libs = []
    options.verbose = 0
    options.poisson = 0
    options.nuisancesToExclude = []
    options.noJMax = None
    theBinning = ROOT.RooFit.Binning(Stack.nBins,Stack.xMin,Stack.xMax)

    file = open(opts.dc, "r")

    os.chdir(os.path.dirname(opts.dc))

    print '\nDC Path:', os.path.dirname(opts.dc)

    DC = parseCard(file, options)

    if not DC.hasShapes: DC.hasShapes = True

    MB = ShapeBuilder(DC, options)

    theShapes = {}
    theSyst = {}
    nuiVar = {}

    print '\n\n ------> Mlfit File: ', opts.mlfit

    if opts.mlfit:
        nuiVar = readBestFit(opts.mlfit)

    if not opts.bin in DC.bins: raise RuntimeError, "Cannot open find %s in bins %s of %s" % (opts.bin,DC.bins,opts.dc)

    print '\n-----> Looping over bins in datacard...'
    for b in DC.bins:

        print '  bin: ', b

        if options.channel != None and (options.channel != b): continue
        exps = {}
        expNui = {}
        shapeNui = {}
        reducedShapeNui = {}

        for (p,e) in DC.exp[b].items(): # so that we get only self.DC.processes contributing to this bin
            exps[p] = [ e, [] ]
            expNui[p] = [ e, [] ]

        print '\n-----> Datacard systematics: ', DC.systs

        for (lsyst,nofloat,pdf,pdfargs,errline) in DC.systs:

            print '\n-----> Looping over systematics in datacard: ', (lsyst,nofloat,pdf,pdfargs,errline)

            if pdf in ('param', 'flatParam'): continue

            # begin skip systematics
            skipme = False
            for xs in options.excludeSyst:
                if re.search(xs, lsyst): 
                    skipme = True
            if skipme:
                print '\n-----> skipping systematics...'
                continue
            # end skip systematics

            counter = 0
            print '\n\t-----> Looping over keys in datacard: ', DC.exp[b].keys()

            for p in DC.exp[b].keys(): # so that we get only self.DC.processes contributing to this bin

                print '\n\t-----> Looping over process in this bin: ', p

                if errline[b][p] == 0: continue

                if p == 'QCD' and not 'QCD' in setup: continue

                if pdf == 'gmN':
                    exps[p][1].append(1/sqrt(pdfargs[0]+1));
                elif pdf == 'gmM':
                    exps[p][1].append(errline[b][p]);
                elif type(errline[b][p]) == list: 
                    kmax = max(errline[b][p][0], errline[b][p][1], 1.0/errline[b][p][0], 1.0/errline[b][p][1]);
                    exps[p][1].append(kmax-1.);
                elif pdf == 'lnN':
                     lnNVar = max(errline[b][p], 1.0/errline[b][p])-1.
                     if not nuiVar.has_key('%s_%s'%(opts.fit,lsyst)):
                         nui = 0.
                     else:
                        nui= nuiVar['%s_%s'%(opts.fit,lsyst)][0]
                        lnNVar = lnNVar*nuiVar['%s_%s'%(opts.fit,lsyst)][1]
                     exps[p][1].append(lnNVar)
                     expNui[p][1].append(abs(1-errline[b][p])*nui);

                elif 'shape' in pdf:

                    print '\n\t-----> Filling the Shapes for this process...'

                    #print 'shape %s %s: %s'%(pdf,p,lsyst)
                    s0 = MB.getShape(b,p)
                    sUp   = MB.getShape(b,p,lsyst+"Up")
                    sDown = MB.getShape(b,p,lsyst+"Down")
                    if (s0.InheritsFrom("RooDataHist")):
                        s0 = ROOT.RooAbsData.createHistogram(s0,p,ws_var,theBinning)
                        s0.SetName(p)
                        sUp = ROOT.RooAbsData.createHistogram(sUp,p+lsyst+'Up',ws_var,theBinning)
                        sUp.SetName(p+lsyst+'Up')
                        sDown = ROOT.RooAbsData.createHistogram(sDown,p+lsyst+'Down',ws_var,theBinning)
                        sDown.SetName(p+lsyst+'Down')
                    theShapes[p] = s0.Clone()
                    theShapes[p+lsyst+'Up'] = sUp.Clone()
                    theShapes[p+lsyst+'Down'] = sDown.Clone()
                    if not nuiVar.has_key('%s_%s'%(opts.fit,lsyst)):
                        nui = 0.
                        reducedNui = 1.
                    else:
                        nui= nuiVar['%s_%s'%(opts.fit,lsyst)][0]
                        reducedNui= nuiVar['%s_%s'%(opts.fit,lsyst)][1]
                    shapeNui[p+lsyst] = nui
                    reducedShapeNui[lsyst] = reducedNui
                    if not 'CMS_vhbb_stat' in lsyst:
                        if counter == 0:
                            theSyst[lsyst] = s0.Clone() 
                            theSyst[lsyst+'Up'] = sUp.Clone() 
                            theSyst[lsyst+'Down'] = sDown.Clone() 
                        else:
                            theSyst[lsyst].Add(s0)
                            theSyst[lsyst+'Up'].Add(sUp.Clone())
                            theSyst[lsyst+'Down'].Add(sDown.Clone()) 
                        counter += 1

    procs = DC.exp[b].keys(); procs.sort()

    if not 'QCD' in setup and 'QCD' in procs:
        procs.remove('QCD')
    if not 'W2b' in setup and 'WjHF' in procs:
        procs.remove('WjHF')
    if not 'Wlight' in setup and 'WjLF' in procs:
        procs.remove('WjLF')

    fmt = ("%%-%ds " % max([len(p) for p in procs]))+"  "+options.format;


    #Compute norm uncertainty and best fit
    theNormUncert = {}
    theBestFit = {}
    print '\n-----> Computing norm uncertaint and best fit...'
    for p in procs:
        relunc = sqrt(sum([x*x for x in exps[p][1]]))
        print fmt % (p, exps[p][0], exps[p][0]*relunc)
        theNormUncert[p] = relunc
        absBestFit = sum([x for x in expNui[p][1]])
        theBestFit[p] = 1.+absBestFit

    
    histos = []
    typs = []

    setup2=copy(setup)

    shapesUp = [[] for _ in range(0,len(setup2))]
    shapesDown = [[] for _ in range(0,len(setup2))]
    
    sigCount = 0
    #signalList = ['Zbb','WH']
    #signalList = ['Zbb']
    signalList = ['ZH']
    #signalList = ['ggZHbb','qqZHbb']
    Overlay ={}

    # for shape analysis?
    for p in procs:

        b = opts.bin

        print 'process: ', p
        print 'setup:',setup
        print 'Dict:', Dict
        #print 'theShapes:', theShapes


        for s in setup:
            print '-----> Fillings the shapes for: ', s
            #print Dict[s], p
            if Dict[s] != p:
                print 'not equal', p
                print 'not equal', Dict[s]
                continue
            if s in signalList:
                if sigCount ==0:
                    Overlay=copy(theShapes[Dict[s]])
                else:
                    Overlay.Add(theShapes[Dict[s]])
                sigCount += 1
            else:
                histos.append(theShapes[Dict[s]])
                typs.append(s)
            for (lsyst,nofloat,pdf,pdfargs,errline) in DC.systs:
                if errline[b][p] == 0: continue
                if ("shape" in pdf) and not 'CMS_vhbb_stat' in lsyst:
                    print 'syst %s'%lsyst
                    shapesUp[setup2.index(s)].append(theShapes[Dict[s]+lsyst+'Up'])
                    shapesDown[setup2.index(s)].append(theShapes[Dict[s]+lsyst+'Down'])

    #-------------
    #Compute absolute uncertainty from shapes
    counter = 0
    for (lsyst,nofloat,pdf,pdfargs,errline) in DC.systs:
        sumErr = 0

        for p in procs:
            sumErr += errline[b][p]

            print '---> PDF:',pdf, lsyst

        if ("shape" in pdf) and not 'CMS_vhbb_stat' in lsyst and not sumErr == 0:
            theSystUp = theSyst[lsyst+'Up'].Clone()
            theSystUp.Add(theSyst[lsyst].Clone(),-1.)
            theSystUp.Multiply(theSystUp)
            theSystDown = theSyst[lsyst+'Down'].Clone()
            theSystDown.Add(theSyst[lsyst].Clone(),-1.)
            theSystDown.Multiply(theSystDown)
            theSystUp.Scale(reducedShapeNui[lsyst])
            theSystDown.Scale(reducedShapeNui[lsyst])
            if counter == 0:
                theAbsSystUp = theSystUp.Clone()
                theAbsSystDown = theSystDown.Clone()
            else:
                theAbsSystUp.Add(theSystUp.Clone())
                theAbsSystDown.Add(theSystDown.Clone())
            counter +=1
    
    #-------------
    #Best fit for shapes
    if not preFit:

        # Set the preFit as an overlay
        print '\n Making prefit overlay...'
        print procs

        i = 0
        for hist in theShapes:
            if hist not in procs: continue
            print 'Process:', hist
            print 'Shape:', theShapes[hist]
            print 'i:', i
            if i == 0:
                prefit_overlay=copy(theShapes[hist])
                #prefit_overlay=theShapes[hist]
                print 'First Integral:', theShapes[hist].Integral()
                i+=1
            else:
                #prefit_overlay.Add(theShapes[hist], 1.0)
                prefit_overlay.Add(theShapes[hist])
                print 'Integral:', theShapes[hist].Integral()

        print  'prefit_overlay:', prefit_overlay
        print 'Integral:', prefit_overlay.Integral()

        print '\n-----> Getting best fit shapes(for postFit)...'
        histos, Overlay, typs = getBestFitShapes(procs,theShapes,shapeNui,theBestFit,DC,setup,opts,Dict)


    

    counter = 0
    errUp=[]
    total=[]
    errDown=[]
    nBins = histos[0].GetNbinsX()

    #print histos
    # temp hack to get histo names right
    #names = ['ggZH','DY2B', 'DY1B', 'DYlight', 'TT', 'VV']
    #for name,i in enumerate(histos):
    #    i.SetName(names[name])
    #Overlay.SetName('ZH')
    # end hack

    print '\n total bins %s'%nBins
    print '\n histos: ',histos
    print '\n theNormUncert: ',theNormUncert
    print '\n Overlay: ', Overlay

    Error = ROOT.TGraphAsymmErrors(histos[0])
    theTotalMC = histos[0].Clone()

    for h in range(1,len(histos)):
        theTotalMC.Add(histos[h])
    
    total = [[]]*nBins
    errUp = [[]]*nBins
    errDown = [[]]*nBins

    print '\n\n\t\t -----> The Histos: ', histos

    for bin in range(1,nBins+1):
        binError = theTotalMC.GetBinError(bin)
        if math.isnan(binError):
            binError = 0.
        total[bin-1]=theTotalMC.GetBinContent(bin)

        #Stat uncertainty of the MC outline
        errUp[bin-1] = [binError]
        errDown[bin-1] = [binError]

        # Temp hack to fix theNormUncert naming
        temp_theNormUncert = {}
        for i,hist in enumerate(histos):
            for x in theNormUncert:
                #print '\nx: ', x
                if x in histos[i].GetName():
                    temp_theNormUncert[histos[i].GetName()] = theNormUncert[x]
        #print  temp_theNormUncert

        #Relative norm uncertainty of the individual MC
        for h in range(0,len(histos)):
            #errUp[bin-1].append(histos[h].GetBinContent(bin)*theNormUncert[histos[h].GetName()])
            #errDown[bin-1].append(histos[h].GetBinContent(bin)*theNormUncert[histos[h].GetName()])
            errUp[bin-1].append(histos[h].GetBinContent(bin)*temp_theNormUncert[histos[h].GetName()])
            errDown[bin-1].append(histos[h].GetBinContent(bin)*temp_theNormUncert[histos[h].GetName()])


    #Shape uncertainty of the MC
    for bin in range(1,nBins+1):
        #print sqrt(theSystUp.GetBinContent(bin))
        errUp[bin-1].append(sqrt(theAbsSystUp.GetBinContent(bin)))
        errDown[bin-1].append(sqrt(theAbsSystDown.GetBinContent(bin)))
    

    #Add all in quadrature
    totErrUp=[sqrt(sum([x**2 for x in bin])) for bin in errUp]
    totErrDown=[sqrt(sum([x**2 for x in bin])) for bin in errDown]

    #Make TGraph with errors
    for bin in range(1,nBins+1):
        if not total[bin-1] == 0:
            point=histos[0].GetXaxis().GetBinCenter(bin)
            Error.SetPoint(bin-1,point,1)
            Error.SetPointEYlow(bin-1,totErrDown[bin-1]/total[bin-1])
            #print 'down %s'%(totErrDown[bin-1]/total[bin-1])
            Error.SetPointEYhigh(bin-1,totErrUp[bin-1]/total[bin-1])
            #print 'up   %s'%(totErrUp[bin-1]/total[bin-1])

    #-----------------------
    #Read data
    data0 = MB.getShape(opts.bin,'data_obs')
    if (data0.InheritsFrom("RooDataHist")):
        data0 = ROOT.RooAbsData.createHistogram(data0,'data_obs',ws_var,theBinning)
        data0.SetName('data_obs')
    datas=[data0]
    datatyps = [None]
    #datanames=[dataname]
    datanames= dataname

    print '\nDATA HIST:', data0
    print 'Data name:', dataname

    if blind:
        for bin in range(12,datas[0].GetNbinsX()+1):
            datas[0].SetBinContent(bin,0)

    #for bin in range(0,datas[0].GetNbinsX()+1):
    #    print 'Data in bin x:', datas[0].GetBinContent(bin)


    if 'VV' in opts.bin:
        signalList = ['VVb',' VVlight']

    print 'Signal List:', signalList

    histos.append(copy(Overlay))
    if 'Zbb' in signalList and 'WH' in signalList:
        typs.append('Zbb')
        if 'Zbb' in Stack.setup: Stack.setup.remove('Zbb')
        if 'WH' in Stack.setup: Stack.setup.remove('WH')
        Stack.setup.insert(0,'Zbb')
    elif 'Zbb' in signalList:
        typs.append('Zbb')
    elif 'WH' in signalList:
        typs.append('WH')
    elif 'ZH' in signalList:
        typs.append('ZH')
    if 'VVb' in signalList:
        typs.append('VVb')
        #typs.append('VVlight')


    print '\n-----> Stack.setup(double check)...'
    print 'Histos:', histos
    print 'typs:', typs

    Stack.histos = histos
    Stack.typs = typs
    Stack.datas = datas
    Stack.datatyps = datatyps
    Stack.datanames= datanames

    #Stack.prefit_overlay = [prefit_overlay]

    if '13TeV' in region:
        Stack.overlay = [Overlay]
    print '\n\n\t\t Overlay: ',Stack.overlay

    Stack.AddErrors=Error
    if dataname == 'Wtn': 
        lumi = 18300.
    Stack.lumi = lumi
    Stack.doPlot()

    print 'i am done!\n'
#-------------------------------------------------


if __name__ == "__main__":
    drawFromDC()
    sys.exit(0)
