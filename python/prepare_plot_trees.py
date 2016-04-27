#!/usr/bin/env python
import pickle
import ROOT
from array import array
import sys, os
from optparse import OptionParser
from copy import copy,deepcopy
from math import sqrt
ROOT.gROOT.SetBatch(True)

argv = sys.argv

#Read the arguments. --region corresponds to the region to plot --configs to the lists of the config files for a given energy.
#i.e. opts.config = ['8TeVconfig/paths', '8TeVconfig/general', '8TeVconfig/cuts', '8TeVconfig/training', '8TeVconfig/datacards', '8TeVconfig/plots', '8TeVconfig/lhe_weights'] when --config is 8TeV in runAll

print ""
print "=================="
print "Start Ploting Step"
print "==================\n"

print "Read Parameters"
print "===================\n"
parser = OptionParser()
parser.add_option("-S", "--samples", dest="names", default="",
                      help="samples you want to run on")
parser.add_option("-C", "--config", dest="config", default=[], action="append",
                      help="configuration file")
parser.add_option("-f", "--filelist", dest="filelist", default="",
                              help="list of files you want to run on")
(opts, args) = parser.parse_args(argv)
if opts.config =="":
        opts.config = "config"

print 'opts.filelist="'+opts.filelist+'"'
filelist=filter(None,opts.filelist.replace(' ', '').split(';'))
print filelist
print "len(filelist)",len(filelist),
if len(filelist)>0:
    print "filelist[0]:",filelist[0];
else:
    print ''

from myutils import BetterConfigParser, printc, ParseInfo, mvainfo, StackMaker, HistoMaker

#adds the file vhbbPlotDef.ini to the config list
print 'opts.config',opts.config

vhbbPlotDef=opts.config[0].split('/')[0]+'/vhbbPlotDef.ini'
opts.config.append(vhbbPlotDef)#adds it to the config list

config = BetterConfigParser()
config.read(opts.config)

#path = opts.path
namelist=opts.names.split(',')

# additional blinding cut:
addBlindingCut = None
if config.has_option('Plot_general','addBlindingCut'):#contained in plots, cut on the event number
    addBlindingCut = config.get('Plot_general','addBlindingCut')
    print 'adding add. blinding cut'

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
def preparePlotTrees():

    print "Read Plotting Region information"
    print "===============================\n"

    vars = (config.get(section, 'vars')).split(',')#get the variables to be ploted in each region
    print "The variables are", vars, "\n"
    data = eval(config.get(section,'Datas'))# read the data corresponding to each CR (section)
    mc = eval(config.get('Plot_general','samples'))# read the list of mc samples
    total_lumi = eval(config.get('Plot_general','lumi'))
    print 'total lumi is', total_lumi

    print "The list of mc samples is", mc

    print "Check if is Signal Region"
    print "=========================\n"

    SignalRegion = False
    if config.has_option(section,'Signal'):
        mc.append(config.get(section,'Signal'))
        SignalRegion = True

    print "After adding the signal, the mc is", mc

    print "Getting information on data and mc samples"
    print "==========================================\n"

    print "Getting data sample"
    datasamples = info.get_samples(data)
    print "datasamples is\n", datasamples
    print "Getting mc sample"
    print mc
    mcsamples = info.get_samples(mc)
    print "mc sample is\n"
    for sample in mcsamples:
      print "sample name", sample.name

    GroupDict = eval(config.get('Plot_general','Group'))#Contained in plots. Listed in general, under Group [Samples] group. This is a dictionnary that descriebes what samples should share the same color under the stack plot.

    for job in info:
        if not job.name in namelist and len([x for x in namelist if x==job.identifier])==0:
            print 'job.name',job.name,'and job.identifier',job.identifier,'not in namelist',namelist
            continue

        print '\t match - %s' %(job.name)
        inputfiles = []
        outputfiles = []
        tmpfiles = []
        if len(filelist) == 0:
            inputfiles.append(pathIN+'/'+job.prefix+job.identifier+'.root')
            print('opening '+pathIN+'/'+job.prefix+job.identifier+'.root')
            tmpfiles.append(tmpDir+'/'+job.prefix+job.identifier+'.root')
            outputfiles.append("%s/%s/%s" %(pathOUT,job.prefix,job.identifier+'.root'))
        else:
            for inputFile in filelist:
                subfolder = inputFile.split('/')[-4]
                filename = inputFile.split('/')[-1]
                filename = filename.split('_')[0]+'_'+subfolder+'_'+filename.split('_')[1]
                hash = hashlib.sha224(filename).hexdigest()
                inputFile = "%s/%s/%s" %(pathIN,job.identifier,filename.replace('.root','')+'_'+str(hash)+'.root')
                outputFile = "%s/%s/%s" %(pathOUT,job.identifier,filename.replace('.root','')+'_'+str(hash)+'.root')
                tmpfile = "%s/%s" %(tmpDir,filename.replace('.root','')+'_'+str(hash)+'.root')
                if inputFile in inputfiles: continue
                del_protocol = outputFile
                del_protocol = del_protocol.replace('gsidcap://t3se01.psi.ch:22128/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
                del_protocol = del_protocol.replace('dcap://t3se01.psi.ch:22125/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
                del_protocol = del_protocol.replace('root://t3dcachedb03.psi.ch:1094/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
                if os.path.isfile(del_protocol.replace('srm://t3se01.psi.ch:8443/srm/managerv2?SFN=','')):
                    f = ROOT.TFile.Open(outputFile,'read')
                    if not f:
                      print 'file is null, adding to input'
                      inputfiles.append(inputFile)
                      outputfiles.append(outputFile)
                      tmpfiles.append(tmpfile)
                      continue
                    # f.Print()
                    if f.GetNkeys() == 0 or f.TestBit(ROOT.TFile.kRecovered) or f.IsZombie():
                        print 'f.GetNkeys()',f.GetNkeys(),'f.TestBit(ROOT.TFile.kRecovered)',f.TestBit(ROOT.TFile.kRecovered),'f.IsZombie()',f.IsZombie()
                        print 'File', del_protocol.replace('srm://t3se01.psi.ch:8443/srm/managerv2?SFN=',''), 'already exists but is buggy, gonna delete and rewrite it.'
                        #command = 'rm %s' %(outputFile)
                        command = 'srmrm %s' %(del_protocol)
                        subprocess.call([command], shell=True)
                        print(command)
                    else: continue
                inputfiles.append(inputFile)
                outputfiles.append(outputFile)
                tmpfiles.append(tmpfile)
            print 'inputfiles',inputfiles,'tmpfiles',tmpfiles


preparePlotTrees()
sys.exit(0)
