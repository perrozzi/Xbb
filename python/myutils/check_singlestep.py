#! /usr/bin/env python
import ROOT,sys,os,subprocess,random,string,hashlib
ROOT.gROOT.SetBatch(True)
from printcolor import printc
import pickle
import sys
from optparse import OptionParser
from BetterConfigParser import BetterConfigParser
from sample_parser import ParseInfo
import StackMaker, HistoMaker

if __name__ == "__main__":

    print 'start check_singlestep.py'

    argv = sys.argv

    #get files info from config
    parser = OptionParser()
    parser.add_option("-C", "--config", dest="config", default=[], action="append",
                          help="directory config")
    parser.add_option("-S", "--samples", dest="names", default="",
                                  help="samples you want to run on")
    parser.add_option("-R", "--region", dest="region", default="",
                                  help="region to plot")

    parser.add_option("-t", "--task", dest="task", default="",
                                  help="task (prep, sys, eval, plot) to be checked")
    parser.add_option("-f", "--filelist", dest="filelist", default="",
                                  help="list of files you want to run on")

    (opts, args) = parser.parse_args(argv)

    vhbbPlotDef=opts.config[0].split('/')[0]+'/vhbbPlotDef.ini'
    opts.config.append(vhbbPlotDef)#adds it to the config list

    config = BetterConfigParser()
    config.read(opts.config)

    samplesinfo=config.get('Directories','samplesinfo')
    sampleconf = BetterConfigParser()
    sampleconf.read(samplesinfo)

    # if opts.filelist != '': print 'filelist NOT NULL!'

    if opts.task == 'checksingleprep':
        pathOUT_orig = config.get('Directories','PREPout')
        pathIN_orig = 'DAS'
    elif opts.task == 'checksinglesys':
        pathOUT_orig = config.get('Directories','SYSout')
        pathIN_orig = config.get('Directories','SYSin')
    elif opts.task == 'checksingleeval':
        pathOUT_orig = config.get('Directories','MVAout')
        pathIN_orig = config.get('Directories','MVAin')
    elif opts.task == 'checksingleplot':
        pathOUT_orig = config.get('Directories','tmpSamples')
        pathIN_orig = config.get('Directories','plottingSamples')

    pathOUT_orig = pathOUT_orig.replace('gsidcap://t3se01.psi.ch:22128/','').replace('dcap://t3se01.psi.ch:22125/','').replace('root://t3dcachedb03.psi.ch:1094/','')
    pathIN_orig = pathIN_orig.replace('gsidcap://t3se01.psi.ch:22128/','').replace('dcap://t3se01.psi.ch:22125/','').replace('root://t3dcachedb03.psi.ch:1094/','')
    # print "opts.task",opts.task
    samplefiles = config.get('Directories','samplefiles')
    print 'pathIN_orig',pathIN_orig
    print 'pathOUT_orig',pathOUT_orig

    hash = ''
    if opts.region:
        # print 'opts.region',opts.region
        region = opts.region
        print 'evaluating cuts for region',region
        section='Plot:%s'%region
        vars = (config.get(section, 'vars')).split(',')#get the variables to be ploted in each region
        # print 'vars',vars
        SignalRegion = False
        if config.has_option(section,'Signal'):
            # mc.append(config.get(section,'Signal'))
            SignalRegion = True
        # # #GETALL AT ONCE
        options = []
        Stacks = []
        #print "Start Loop over the list of variables(to fill the StackMaker )" print "==============================================================\n"
        for i in range(len(vars)):# loop over the list of variables to be ploted in each reagion
            # print "The variable is ", vars[i], "\n"
            Stacks.append(StackMaker.StackMaker(config,vars[i],region,SignalRegion))# defined in myutils DoubleStackMaker. The StackMaker merge together all the informations necessary to perform the plot (plot region, variables, samples and signal region ). "options" contains the variables information, including the cuts.
            options.append(Stacks[i].options)
        cuts = []
        for option in options:
            cuts.append(option['cut'])
        _cutList = []
        #! Make the cut lists from inputs
        for cut in cuts:
            _cutList.append('(%s)'%cut.replace(' ',''))
        effective_cuts = []
        for cut in _cutList:
            if not cut in effective_cuts:
                effective_cuts.append(cut)
        _cutList = effective_cuts
        minCut = '||'.join(_cutList)

        hash = hashlib.sha224(minCut).hexdigest()
        print 'pathOUT_orig', pathOUT_orig
        print hash

    grep_hash = ''
    if hash != '':
        grep_hash = ' |grep '+hash

    mc_dataset_missing_files = []
    data_dataset_missing_files = []
    dataset_identifiers = []

    if opts.filelist == "" or opts.names == 'nosample':
        # print "info:",info
        info = ParseInfo(samplesinfo,pathOUT_orig)
        # if opts.names == ""
        for job in info:
            dataset_identifiers.append(job.identifier)
        dataset_identifiers = set(dataset_identifiers)
        for identifier in dataset_identifiers:
            sampleType = config.get(identifier,'sampleType')
            print 'sampleType',sampleType

            # print identifier
            # identifier=opts.names.split(',')[0]
            print "identifier:",identifier
            pathOUT = pathOUT_orig+'/'+identifier
            filenames = open(samplefiles+'/'+identifier+'.txt').readlines()
            print 'number of files on DAS:',len(filenames),#filenames[0]

            if pathIN_orig != 'DAS':
                pathIN = pathIN_orig+'/'+identifier
                nFilesInPathIn = int(os.popen('ls '+pathIN+'/*.root |wc -l').read())
                print '    --->>    number of input files for '+opts.task+':',nFilesInPathIn,#,firstfileInPathOut[0]
            else:
                nFilesInPathIn = len(filenames)

            # print 'pathOUT', pathOUT
            # print('ls '+pathOUT+'/*.root |wc -l')
            nFilesInPathOut = int(os.popen('ls '+pathOUT+'/*.root '+grep_hash+'|wc -l').read())
            firstfileInPathOut = os.popen('ls '+pathOUT+'/*.root '+grep_hash+'|head -n 1').read()
            print '    --->>    number of output files:',nFilesInPathOut#,firstfileInPathOut[0]
            if int(nFilesInPathIn) == int(nFilesInPathOut):
                print 'ALL FILES CORRECTLY PROCESSED BY '+opts.task+'\n'
                # sys.exit(0)
            else:
                print '-------->>>>>> MISSING '+str(nFilesInPathIn-int(nFilesInPathOut))+'/'+str(nFilesInPathIn)+' OUTPUT FILES IN THE '+opts.task+' TASK FOR THE SAMPLE '+identifier
                # sys.exit(1)
                if sampleType == 'DATA':
                    data_dataset_missing_files.append(identifier)
                else:
                    mc_dataset_missing_files.append(identifier)
            if len(filenames) != int(nFilesInPathIn):
                print '-------->>>>>> MISSING '+str(len(filenames)-int(nFilesInPathIn))+'/'+str(len(filenames))+' INPUT FILES FOR THE '+opts.task+' TASK WITH RESPECT TO DAS\n'

        print '\n\nFINAL RECAP: \n\nmissing files for the following MC datasets:'
        print mc_dataset_missing_files
        for file in mc_dataset_missing_files:
            print file
        print '\nmissing files for the following DATA datasets (VERY IMPORTANT!!!):'
        print data_dataset_missing_files
        for file in data_dataset_missing_files:
            print file
    else:
        pathOUT = pathOUT_orig+'/'+opts.names
        filenames = open(samplefiles+'/'+opts.names+'.txt').readlines()
        nFilesInPathOut = int(os.popen('ls '+pathOUT+'/*.root '+grep_hash+'|wc -l').read())
        if pathIN_orig != 'DAS':
            pathIN = pathIN_orig+'/'+opts.names
            nFilesInPathIn = int(os.popen('ls '+pathIN+'/*.root |wc -l').read())
        else:
            nFilesInPathIn = len(filenames)
        if int(nFilesInPathIn) == int(nFilesInPathOut): print 'all files available'; sys.exit(10)

        filelist=filter(None,opts.filelist.replace(' ', '').split(';'))
        for inputfile in filelist:

            inputtree = inputfile.rsplit('/',1)[len(inputfile.rsplit('/',1))-1]
            inputfolder = inputfile.replace('/'+inputtree,'')
            # print 'inputfile',inputfile,'inputtree',inputtree,'inputfolder',inputfolder
            # inputfileexists = int(os.popen('xrdfs t3se01.psi.ch ls -l -u '+inputfolder+'|grep '+inputtree+'|wc -l').read())
            # print 'inputfileexists PSI',inputfileexists
            # if int(inputfileexists) == 0:
                # inputfileexists = int(os.popen('xrdfs stormgf1.pi.infn.it ls -l -u '+inputfolder+'|grep '+inputtree+'|wc -l').read())
                # print 'inputfileexists PISA',inputfileexists
            # if inputfileexists == 0: continue

            inputtreenumber = inputtree.replace('tree','').replace('.root','')+'_'
            # print 'opts.names',opts.names
            # print 'pathOUT',pathOUT,'inputtreenumber',inputtreenumber
            isFileInPathOut = int(os.popen('ls '+pathOUT+'/*.root '+grep_hash+'|grep '+inputtreenumber+'|wc -l').read())
            # print 'isFileInPathOut',isFileInPathOut
            if isFileInPathOut == 0:
                print'FILE MISSING, RESUBMITTING TRANCHE FROM SAMPLE',opts.names
                sys.exit(1)

        sys.exit(0)

