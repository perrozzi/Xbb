#!/usr/bin/env python
import pickle
import ROOT 
from array import array
import sys, os
from optparse import OptionParser
from copy import copy,deepcopy
from math import sqrt
import zlib
import base64
import time
ROOT.gROOT.SetBatch(True)

argv = sys.argv

#Read the arguments. --region corresponds to the region to plot --configs to the lists of the config files for a given energy.
#i.e. opts.config = ['8TeVconfig/paths', '8TeVconfig/general', '8TeVconfig/cuts', '8TeVconfig/training', '8TeVconfig/datacards', '8TeVconfig/plots', '8TeVconfig/lhe_weights'] when --config is 8TeV in runAll

print ""
print "=================="
print "Start Ploting Step"
print "==================\n"

begin_time  = time.time()

print "Read Parameters"
print "===================\n"
parser = OptionParser()
parser.add_option("-R", "--region", dest="region", default="",
                      help="region to plot")
parser.add_option("-C", "--config", dest="config", default=[], action="append",
                      help="configuration file")
parser.add_option("-f", "--filelist", dest="filelist", default="",
                              help="list of files you want to run on")
parser.add_option("-m", "--mergeplot", dest="mergeplot", default=False,
                              help="option to merge")
parser.add_option("-M", "--mergecachingplot", dest="mergecachingplot", default=False, action='store_true', help="use files from mergecaching")
parser.add_option("-s", "--settings", dest="settings", default=False,
                              help="co ntains sample you want to merge, as well as the subcut bin")
(opts, args) = parser.parse_args(argv)
if opts.config =="":
        opts.config = "config"

# to avoid argument size limits, filelist can be encoded with 'base64:' + base64(zlib(.)), decode it first in this case
if opts.filelist.startswith('base64:'):
    opts.filelist = zlib.decompress(base64.b64decode(opts.filelist[7:]))
    #print 'zlib decoded file list:', opts.filelist

from myutils import BetterConfigParser, printc, ParseInfo, mvainfo, StackMaker, HistoMaker

print 'opts.settings is', opts.settings
print 'mergeplot is', opts.mergeplot
print 'mergecachingplot is', opts.mergecachingplot

sample_to_merge_ = None
subcut_ =  None
var_to_plot_ = None
#This will go in the name of the pdf, png etc file
subcut_plotname = ''

# reads n files, writes single file. disabled if set to -1
mergeCachingPart = -1

if opts.settings:
    print 'settings is', opts.settings
    if 'CUTBIN' in opts.settings:
        print '@INFO: The PLOT regions contains subcuts'
        subcut = opts.settings[opts.settings.find('CUTBIN')+7:].split('__')
        subcut_ = '(' + str(subcut[1]) + ' < '+ subcut[0] + ' ) & ( ' + subcut[0] + ' < '+ str(subcut[2]) + ' )'
        subcut_plotname = '%s_%s_%s'%(subcut[0],subcut[1],subcut[2])
        print 'subcut_ is', subcut_
    if 'CACHING' in opts.settings:
        sample_to_merge_ = '__'.join(opts.settings[opts.settings.find('CACHING')+7:].split('__')[1:])
        print '@INFO: Only caching will be performed. The sample to be cached is', sample_to_merge_
    if 'MERGECACHING' in opts.settings:
        mergeCachingPart = int(opts.settings[opts.settings.find('CACHING')+7:].split('__')[0].split('_')[-1])
        print '@INFO: Partially merged caching: this is part', mergeCachingPart
    if 'VAR' in opts.settings:
        var_to_plot_ = opts.settings[opts.settings.find('VAR')+4:]
        print '@INFO: Only the %s parameter will be ploted' %var_to_plot_

#adds the file vhbbPlotDef.ini to the config list
#print 'opts.config',opts.config
# print 'opts.filelist="'+opts.filelist+'"'
filelist=filter(None,opts.filelist.replace(' ', '').split(';'))
# print filelist
print "len(filelist)",len(filelist),
if len(filelist)>0:
    print "filelist[0]:",filelist[0];
else:
    print ''

vhbbPlotDef=opts.config[0].split('/')[0]+'/vhbbPlotDef.ini'
opts.config.append(vhbbPlotDef)#adds it to the config list

config = BetterConfigParser()
config.read(opts.config)

#path = opts.path
region = opts.region

# additional blinding cut:
addBlindingCut = None
if config.has_option('Plot_general','addBlindingCut'):#contained in plots, cut on the event number
    addBlindingCut = config.get('Plot_general','addBlindingCut')
    print 'adding add. blinding cut'

print "Compile external macros"
print "=======================\n"

#get locations:
Wdir=config.get('Directories','Wdir')# working direcoty containing the ouput
samplesinfo=config.get('Directories','samplesinfo')# samples_nosplit.cfg

path = config.get('Directories','plottingSamples')# from which samples to plot

section='Plot:%s'%region

info = ParseInfo(samplesinfo,path) #creates a list of Samples by reading the info in samples_nosplit.cfg and the conentent of the path.

import os
if os.path.exists("../interface/DrawFunctions_C.so"):
    print 'ROOT.gROOT.LoadMacro("../interface/DrawFunctions_C.so")'
    ROOT.gROOT.LoadMacro("../interface/DrawFunctions_C.so")
if os.path.exists("../interface/VHbbNameSpace_h.so"):
    print 'ROOT.gROOT.LoadMacro("../interface/VHbbNameSpace_h.so")'
    ROOT.gROOT.LoadMacro("../interface/VHbbNameSpace_h.so")


#----------Histo from trees------------
#Get the selections and the samples
def doPlot():
    #print "Read Ploting Region information"
    #print "===============================\n"

    if var_to_plot_:
        vars = [var_to_plot_]
    else:
        vars = (config.get(section, 'vars')).split(',')#get the variables to be ploted in each region
    print "The variables are", vars, "\n"
    data = eval(config.get(section,'Datas'))# read the data corresponding to each CR (section)
    mc = eval(config.get('Plot_general','samples'))# read the list of mc samples
    total_lumi = eval(config.get('Plot_general','lumi'))
    #print 'total lumi is', total_lumi
    print "The list of mc samples is", mc

    remove_sys_ = eval(config.get('Plot_general','remove_sys'))
    #print "Check if is Signal Region"
    #print "=========================\n"
    SignalRegion = False
    if config.has_option(section,'Signal'):
        mc.append(config.get(section,'Signal'))
        SignalRegion = True
    #print "After addind the signal, the mc is", mc

    #print "Getting information on data and mc samples"
    #print "==========================================\n"
           
    #print "Getting data sample"
    datasamples = info.get_samples(data)
    #print "datasamples is\n", datasamples
    #print "Getting mc sample"
    mcsamples = info.get_samples(mc)
    #print "mc sample is\n"
    #for sample in mcsamples:
      #print "sample name", sample.name

    GroupDict = eval(config.get('Plot_general','Group'))#Contained in plots. Listed in general, under Group [Samples] group. This is a dictionnary that descriebes what samples should share the same color under the stack plot.


    #GETALL AT ONCE
    options = []
    Stacks = []
    #print "Start Loop over the list of variables(to fill the StackMaker )" print "==============================================================\n"
    for i in range(len(vars)):# loop over the list of variables to be ploted in each reagion
        #print "The variable is ", vars[i], "\n"
        Stacks.append(StackMaker(config,vars[i],region,SignalRegion, None, '_'+subcut_plotname))# defined in myutils DoubleStackMaker. The StackMaker merge together all the informations necessary to perform the plot (plot region, variables, samples and signal region ). "options" contains the variables information, including the cuts.
        options.append(Stacks[i].options)
    #print "Finished Loop over the list of variables(to fill the StackMaker )"
    #print "================================================================\n"

    #Prepare cached files in the temporary (tmpSamples) folder.
    #def __init__(self, samples, path, config, optionsList, GroupDict=None, filelist=None, mergeplot=False, sample_to_merge=None, mergecaching=False):

    Plotter=HistoMaker(samples=mcsamples+datasamples, path=path, config=config, optionsList=options, GroupDict=GroupDict, filelist=filelist, mergeplot=opts.mergeplot, sample_to_merge=sample_to_merge_, mergeCachingPart=mergeCachingPart, plotMergeCached = opts.mergecachingplot, branch_to_keep=None, dccut=None,remove_sys=remove_sys_)
    if len(filelist)>0 or opts.mergeplot:
        print('ONLY CACHING PERFORMED, EXITING');
        sys.exit(1)

    #print '\nProducing Plot of %s\n'%vars[v]
    Lhistos = [[] for _ in range(0,len(vars))]
    Ltyps = [[] for _ in range(0,len(vars))]
    Ldatas = [[] for _ in range(0,len(vars))]
    Ldatatyps = [[] for _ in range(0,len(vars))]
    Ldatanames = [[] for _ in range(0,len(vars))]
    Ljobnames = [[] for _ in range(0,len(vars))]

    #print "Summing up the Luminosity"
    #print "=========================\n"

    #! Sums up the luminosity of the data:
    lumicounter=0.
    lumi=0.
    if datasamples == []:
        lumi = total_lumi
    else:
        print "Will run over datasamples to sum up the lumi"
        for job in datasamples:
            print "Datasample is", job
            lumi+=float(job.lumi)
            lumicounter+=1.
        if lumicounter > 0:
            lumi=lumi/lumicounter
    
    print "The lumi is", lumi, "\n"

    Plotter.lumi=lumi
    mass = Stacks[0].mass

    #print 'mcsamples',mcsamples
    inputs=[]
    for job in mcsamples:
#        print 'job.name'
#        cutOverWrite = None
#        if addBlindingCut:
#            cutOverWrite = config.get('Cuts',region)+' & ' + addBlindingCut
        inputs.append((Plotter,"get_histos_from_tree",(job,True, subcut_, '1')))

    #print 'inputs are', inputs
    
    # if('pisa' in config.get('Configuration','whereToLaunch')):
    multiprocess=int(config.get('Configuration','nprocesses'))
#    multiprocess=0

    start_time = time.time()
    outputs = []
    if multiprocess>1:
        from multiprocessing import Pool
        from myutils import GlobalFunction
        p = Pool(multiprocess)
        #print 'launching get_histos_from_tree with ',multiprocess,' processes'
        outputs = p.map(GlobalFunction, inputs)
    else:
        #print 'launching get_histos_from_tree with ',multiprocess,' processes'
        for input_ in  inputs:
            outputs.append(getattr(input_[0],input_[1])(*input_[2])) #ie. Plotter.get_histos_from_tree(job)
    #print 'get_histos_from_tree DONE'
    Overlaylist = []

    print "All histograms retrived. DONE in ", str(time.time() - start_time)," s."

    start_time = time.time()

    for i,job in enumerate(mcsamples):
        hDictList = outputs[i]
        if job.name in mass:
            histoList = []
            for v in range(0,len(vars)):
                histoCopy = deepcopy(hDictList[v].values()[0])
                histoCopy.SetTitle(job.name)
                histoList.append(histoCopy)
            Overlaylist.append(histoList)
        for v in range(0,len(vars)):
            Lhistos[v].append(hDictList[v].values()[0])
            Ltyps[v].append(hDictList[v].keys()[0])
            Ljobnames[v].append(job.name)
    
    #print "len(vars)=",len(vars)
    #print "Ltyps is", Ltyps
    ##invert Overlaylist[variable][job] -> Overlaylist[job][variable]
    #print "len(Overlaylist) before: ",len(Overlaylist)
    #print "Overlaylist",Overlaylist
#    newOverlaylist = [[None]*len(Overlaylist)]*len(vars)
#    for i,OverlaySameSample in enumerate(Overlaylist):
#            for j,Overlay in enumerate(OverlaySameSample):
#                newOverlaylist[j][i] = Overlay    
#    Overlaylist = newOverlaylist
    Overlaylist = [list(a) for a in zip(*Overlaylist)]
    #print "len(Overlaylist) after: ",len(Overlaylist)
    #print "Overlaylist",Overlaylist
    
    ##merge overlays in groups 
    for i in range(len(Overlaylist)):
        newhistos = {}
        #print "len(Overlaylist[i]):",Overlaylist[i]
        for histo in Overlaylist[i]:
            #print "histo.GetName()",histo.GetName(),
            #print "histo.GetTitle()",histo.GetTitle(),
            group = GroupDict[histo.GetTitle()]
            if not group in newhistos.keys():
                histo.SetTitle(group)
                newhistos[group]=histo
            else:
                #print "Before newhistos[group].Integral()",newhistos[group].Integral(),
                newhistos[group].Add(histo)
                #print "After newhistos[group].Integral()",newhistos[group].Integral()
        Overlaylist[i] = newhistos.values()
        


#   ### ORIGINAL ###
#    print 'mcsamples',mcsamples
#    for job in mcsamples:
#        print 'job.name',job.name
#        #hTempList, typList = Plotter.get_histos_from_tree(job)
#        if addBlindingCut:
#            hDictList = Plotter.get_histos_from_tree(job,config.get('Cuts',region)+' & ' + addBlindingCut)
#        else:
#            print 'going to get_histos_from_tree'
#            hDictList = Plotter.get_histos_from_tree(job)
#        if job.name == mass:
#            print 'job.name', job.name
#            Overlaylist= deepcopy([hDictList[v].values()[0] for v in range(0,len(vars))])
#        for v in range(0,len(vars)):
#            Lhistos[v].append(hDictList[v].values()[0])
#            Ltyps[v].append(hDictList[v].keys()[0])
#            Ljobnames[v].append(job.name)


    #print "DATA samples\n"
    #! Get the data histograms
    for job in datasamples:
        if addBlindingCut:
            if subcut_: dDictList = Plotter.get_histos_from_tree(job,True, config.get('Cuts',region)+' & ' + addBlindingCut +' & ' + subcut_)
            else: dDictList = Plotter.get_histos_from_tree(job, True, config.get('Cuts',region)+' & ' + addBlindingCut, '1')
        else:
            if subcut_: dDictList = Plotter.get_histos_from_tree(job, True, config.get('Cuts',region)+' & ' + subcut_)
            else: dDictList = Plotter.get_histos_from_tree(job, True, None, '1')
        #! add the variables list for each job (Samples)
        for v in range(0,len(vars)):
            Ldatas[v].append(dDictList[v].values()[0])
            Ldatatyps[v].append(dDictList[v].keys()[0])
            Ldatanames[v].append(job.name)

    for v in range(0,len(vars)):

        #print "Ltyps[v]:",Ltyps[v]
        #print "Lhistos[v]:",Lhistos[v]
        #print "Ldatas[v]:",Ldatas[v]
        #print "Ldatatyps[v]:",Ldatatyps[v]
        #print "Ldatanames[v]:",Ldatanames[v]
        #print "lumi:",lumi

        histos = Lhistos[v]
        typs = Ltyps[v]
        Stacks[v].histos = Lhistos[v]
        Stacks[v].typs = Ltyps[v]
        Stacks[v].datas = Ldatas[v]
        Stacks[v].datatyps = Ldatatyps[v]
        Stacks[v].datanames= Ldatanames[v]
        try:
          if SignalRegion:
            Stacks[v].overlay = Overlaylist[v] ## from
        except Exception as e:
            print "NO OVERLAY LIST:", e

        Stacks[v].lumi = lumi
        Stacks[v].jobnames= Ljobnames[v]
        Stacks[v].normalize = eval(config.get(section,'Normalize'))
        #print 'Stack[v].subcut is', Stacks[v].subcut
        #if subcut_plotname: Stacks[v].subcut = '_'+subcut_plotname
        #print 'again, Stack[v].subcut is', Stacks[v].subcut
        Stacks[v].doPlot()
        ##FIXME##
#        Stacks[v].histos = Lhistos[v]
#        Stacks[v].typs = Ltyps[v]
#        Stacks[v].datas = Ldatas[v]
#        Stacks[v].datatyps = Ldatatyps[v]
#        Stacks[v].datanames= Ldatanames[v]
#        Stacks[v].normalize = True
#        Stacks[v].options['pdfName'] = Stacks[v].options['pdfName'].replace('.pdf','_norm.pdf')
#        Stacks[v].doPlot()
        print 'i am done!\n'

    print "Last part DONE in ", str(time.time() - start_time)," s."
    print "tree_stack done in ", str(time.time() - begin_time)," s."
    print 'DOPLOT END'
#----------------------------------------------------
doPlot()
sys.exit(0)
