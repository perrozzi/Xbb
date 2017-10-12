#!/usr/bin/env python
import pickle
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
parser.add_option("-P", "--postfit", dest="postfit", default="",
                  help="if the blind cut need to be applied")

(opts, args) = parser.parse_args(argv)

print opts

def rebinHist(hist,nbin, xmin, xmax, scale=1):
    '''The postfit plots stored in the mlfit.root don't have the proper bin size. A rebinning is therefor necessary.'''
    h_new = ROOT.TH1F(hist.GetName(), hist.GetName(), nbin, xmin, xmax)
    for b in range(0,nbin+2):
        h_new.SetBinContent(b, hist.GetBinContent(b))
        h_new.SetBinError(b, hist.GetBinError(b))
        #print 'bin content is', hist.GetBinContent(b)
    h_new.Scale(scale)
    return h_new



def drawFromDC():

    config = BetterConfigParser()
    config.read(opts.config)

    region = opts.region

    print "\nopts.config:",opts.config
    print "opts:", opts
    print "var:", opts.var
    print "bin:", opts.bin

    #Should Read this from the parser
    datanames = config.get('dc:%s'%opts.bin,'data').split(' ')
    print 'dataname is', datanames

    region = opts.bin

    var = opts.var

    ws_var = config.get('plotDef:%s'%var,'relPath')
    nbin = int(config.get('plotDef:%s'%var,'nBins'))
    xmin = float(config.get('plotDef:%s'%var,'min'))
    xmax = float(config.get('plotDef:%s'%var,'max'))

    blind = eval(opts.blind)
    postfit = eval(opts.postfit)

    print 'config:', config
    print 'var: ', var
    print 'region: ', region
    print 'blind: ', blind
    print 'postfit: ', postfit

    Group_dc =  eval(config.get('Plot_general','Group_dc'))

    Stack=StackMaker(config,var,region,True)

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
    #log = eval(config.get('Plot:%s'%region,'log'))

    if 'Zee' in opts.bin or 'Zuu' in opts.bin:
        #VH
        setup = ['ggZHbb', 'qqZHbb','Zbb','Zb','Z_udscg','TT','VV2b','VVlight','ST']
        #VV
        #setup = ['VV2b','ggZHbb','qqZHbb','Z_udscg','Zb','Zbb','TT','VVlight','ST']
        channel = 'ZllHbb'
        if 'Zee' in opts.bin: lep_channel = 'Zee'
        elif 'Zuu' in opts.bin: lep_channel = 'Zuu'
        #region_dic = {'BDT':'SIG','CRZlight':'Zlf','CRZb':'Zhf','CRttbar':'TT'}
        region_dic = {
                'BDT':'BDT',
                'CRZlight':'CRZlight',
                'CRZb':'CRZb',
                'CRttbar':'CRttbar',
                'ZeeMass_lowpt':'ZeeMass_lowpt',
                'ZeeMass_highpt':'ZeeMass_highpt',
                'ZuuMass_lowpt':'ZuuMass_lowpt',
                'ZuuMass_highpt':'ZuuMass_highpt',
                'ZeeMassVV_lowpt':'ZeeMassVV_lowpt',
                'ZeeMassVV_highpt':'ZeeMassVV_highpt',
                'ZuuMassVV_lowpt':'ZuuMassVV_lowpt',
                'ZuuMassVV_highpt':'ZuuMassVV_highpt',
                'ZuuMass_Vptbin0':'ZuuMass_Vptbin0',
                'ZuuMass_Vptbin1':'ZuuMass_Vptbin1',
                'ZuuMass_Vptbin2':'ZuuMass_Vptbin2',
                'ZeeMass_Vptbin0':'ZeeMass_Vptbin0',
                'ZeeMass_Vptbin1':'ZeeMass_Vptbin1',
                'ZeeMass_Vptbin2':'ZeeMass_Vptbin2',
                }
        print 'opts.bin is', opts.bin
        region_name =  [region_dic[key] for key in region_dic if (key in opts.bin)]
        region_name = region_name[0]
        print 'region_name is', region_name
        pt_region_dic = {'lowpt':'lowpt','highpt':'highpt','bin0':'bin0','bin1':'bin1','bin2':'bin2'}
        pt_region_name =  [pt_region_dic[key] for key in pt_region_dic if (key in opts.bin)]
        pt_region_name = pt_region_name[0]

    else:
        print '@ERROR: This is not a Zll region. Aborting'
        sys.exit()

    Stack.setup = setup

    Dict = eval(config.get('LimitGeneral','Dict'))
    lumi = eval(config.get('General','lumi'))


    Stack.nBins = nbin
    Stack.xMin = xmin
    Stack.xMax = xmax

    print '/n----> The Binning:'
    print 'nBins:', Stack.nBins
    print 'xMin:', Stack.xMin
    print 'xMax:', Stack.xMax

    theBinning = ROOT.RooFit.Binning(Stack.nBins,Stack.xMin,Stack.xMax)


    #################
    #We are now skiping a large part of the orginal code, as everything that remains to be done is to read the postfit plot from the mlfit.root
    #How should the scale sys (lnN be handled) ?
    #

    histos = []
    typs = []
    shapes = {}
    shapesUp = [[] for _ in range(0,len(setup))]
    shapesDown = [[] for _ in range(0,len(setup))]
    #signalList = ['ggZHbb', 'qqZHbb']
    #signalList = []

    sigCount = 0
    #Overlay ={}
    Overlay = []
    prefit_overlay = []

    postfit_from_wc = False
    if opts.mlfit.split('/')[-1] != 'mlfit.root':
        postfit_from_wc = True

    dirname = ''
    ####
    #Open the mlfit.root and retrieve the mc
    print 'opts.mlfit is', opts.mlfit
    file = ROOT.TFile.Open(opts.mlfit)
    #if file == None: raise RuntimeError, "Cannot open file %s" % theFile
    #print '\n\n-----> Fit File: ',file
    print '====================='
    print 'POSTFIT IS', postfit
    print '====================='

    if postfit:
        if not postfit_from_wc:
            if not ROOT.gDirectory.cd('shapes_fit_s'):
                print '@ERROR: didn\'t find the shapes_fit_s directory. Aborting'
                sys.exit()
        else:
            pass
    else:
        if not ROOT.gDirectory.cd('shapes_prefit'):
            print '@ERROR: didn\'t find the shapes_prefit directory. Aborting'
            sys.exit()
    folder_found = False
    for dir in ROOT.gDirectory.GetListOfKeys():
        dirinfo = dir.GetName().split('_')
        print 'dir name is', dir.GetName().split('_')
        ##if not (dirinfo[0] == channel and dirinfo[2] == lep_channel and dirinfo[3] == region_name and dirinfo[4] == pt_region_name):
        print 'dirinfo is', dirinfo
        print 'lep_channel is', lep_channel
        print 'region_name is', region_name
        print 'pt_region_name is', pt_region_name
        if not (dirinfo[0] == lep_channel and dirinfo[1] == region_name and dirinfo[2] ==  pt_region_name):
            #for VV
            if not (dirinfo[2] == region_name.split('_')[0] and dirinfo[3] ==  pt_region_name):
                if not (len(dirinfo) > 3 and dirinfo[3] == region_name.split('_')[0] and dirinfo[4] == 'Vpt'+pt_region_name):
                    continue

        if postfit_from_wc and 'prefit' in dirinfo:
            continue
        folder_found = True
        dirname = dir.GetName()
        #signal, use prefit
        for s in setup:
            if ('ZHbb' in s and postfit) and not postfit_from_wc:
                print 'ERROR'
                sys.exit()
                ROOT.gDirectory.cd('/shapes_prefit')
                ROOT.gDirectory.cd(dirname)
                found = False
                for subdir in ROOT.gDirectory.GetListOfKeys():
                    #print 'subdir name is', subdir.GetName()
                    if subdir.GetName() == Dict[s]:
                        found = True
                        hist = rebinHist(gDirectory.Get(subdir.GetName()).Clone(), nbin, xmin, xmax)
                        histos.append(hist)
                        typs.append(s)
                        #print 's is', s
                        #print 'signalList is', signalList
                        #if s in signalList:
                        #    hist.SetTitle(s)
                        #    Overlay.append(hist)
                        #    print 'the Histogram title is', hist.GetTitle()
            else:
                #SF_ZJets = [0.95188, 0.94404, 1.0463]
                #SF_TTbar = 1.0373
                #;Vpt high
                #SF_ZJets = [1.1235, 0.91368, 1.2435]
                #SF_TTbar = 1.0601
                #Start be getting the SF
                print 'Gonna apply SF'
                scale = 1
                #if 'low' in opts.dc:
                #    if 'TT' in s:       scale =  1.01
                #    if 'Z_udscg' in s:  scale = 0.96
                #    if 'Zb' in s:       scale = 0.99
                #    if 'Zbb' in s  :    scale = 1.04
                #elif 'high' in opts.dc:
                #    if 'TT' in s:       scale = 1.01
                #    if 'Z_udscg' in s:  scale = 1.03
                #    if 'Zb' in s:       scale = 0.96
                #    if 'Zbb' in s:      scale = 1.23
                #else:
                #    pass
                #    #ROOT.gDirectory.cd('/shapes_fit_s')
                #if not postfit_from_wc:
                #    ROOT.gDirectory.cd('/shapes_prefit')
                #    print 'ERROR2'
                #    sys.exit()
                #else:
                #    scale = 1
                ROOT.gDirectory.cd(dirname)
                found = False
                for subdir in ROOT.gDirectory.GetListOfKeys():
                    print 'subdir name is', subdir.GetName()
                    #print 'Dict is ', Dict
                    if subdir.GetName() == Dict[s] or (postfit_from_wc and subdir.GetName() == s):
                        found = True
                        hist = rebinHist(gDirectory.Get(subdir.GetName()).Clone(), nbin, xmin, xmax, scale)
                        histos.append(hist)
                        typs.append(s)
                        print 's is', s
                        #print 'signalList is', signalList
                        #if s in signalList:
                        #    hist.SetTitle(s)
                        #    Overlay.append(hist)
                        #    print 'the Histogram title is', hist.GetTitle()
              #take prefit distr. for signal


            if not found:
                print '@ERROR: didn\'t find  the postfit histogram. Aborting'
                sys.exit()
        if not postfit_from_wc:
            ROOT.gDirectory.cd('/shapes_prefit/'+dirname)
            print 'ERROR3'
            sys.exit()
        if not postfit_from_wc:
            total = rebinHist(gDirectory.Get('total').Clone(), nbin, xmin, xmax)
            total.SetTitle('prefit')
            prefit_overlay.append(total)
            break
    if not folder_found:
        print '@ERROR: Folder was not found.'
        print 'lep_channel', lep_channel
        print 'region_name', region_name
        print 'pt_region_name', pt_region_name
        sys.exit()
    #retrieve the data
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
    #This needs to be done from the "dc" root file
    print 'file is ',opts.dc
    dc_file= open(opts.dc, "r")
    os.chdir(os.path.dirname(opts.dc))
    DC = parseCard(dc_file, options)

    if not DC.hasShapes: DC.hasShapes = True
    MB = ShapeBuilder(DC, options)
    data0 = MB.getShape(opts.bin,'data_obs')
    if (data0.InheritsFrom("RooDataHist")):
        data0 = ROOT.RooAbsData.createHistogram(data0,'data_obs',ws_var,theBinning)
        data0.SetName('data_obs')

    datas=[data0]
    if blind and 'BDT' in var:
        for bin in range(datas[0].GetNbinsX()-3,datas[0].GetNbinsX()+1):
            datas[0].SetBinContent(bin,0)
    if blind and 'Mass' in var:
        for bin in range(datas[0].GetNbinsX()-13,datas[0].GetNbinsX()-7):
            datas[0].SetBinContent(bin,0)
    datatyps = [None]

    #print '\nshapes!!!', shapes
    print '\nOVERLAY!!!', Overlay

    #Add all the histos and overlay to the stackmaker such that they can be ploted
    #print 'before Stack, histos are', histos
    #sys.exit()
    Stack.histos = histos
    Stack.typs = typs
    Stack.overlay = Overlay
    Stack.prefit_overlay = prefit_overlay
    Stack.datas = datas
    Stack.datatyps = datatyps
    Stack.datanames= datanames
    Stack.AddErrors= True

    Stack.lumi = lumi
    if 'BDT' in var:
        Stack.forceLog = True
    Stack.doPlot()

    print 'i am done!\n'

if __name__ == "__main__":
    drawFromDC()
    sys.exit(0)

#  LocalWords:  Zee
