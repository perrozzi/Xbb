#!/usr/bin/env python
from optparse import OptionParser
import sys
import pickle
import ROOT 
import zlib
import base64
ROOT.gROOT.SetBatch(True)
from array import array
#warnings.filterwarnings( action='ignore', category=RuntimeWarning, message='creating converter.*' )
#usage: ./train run gui

# in case of a list of files, read them as a TChain
def getTree(rootFileNames):
    if type(rootFileNames) is list:
        CuttedTree = ROOT.TChain(job.tree)
        for rootFileName in rootFileNames:
            status = CuttedTree.Add(rootFileName + '/' + job.tree, 0)
            if status != 1:
                print ('ERROR: in HistoMaker.py, cannot add file to chain:'+rootFileName)
        input = None
    # otherwise as a TFile for backwards compatibility
    else:
        CuttedTree = ROOT.TChain(job.tree)
        CuttedTree.Add(rootFileNames, 0)
        CuttedTree.SetCacheSize(0)
        #input = ROOT.TFile.Open(rootFileNames,'read')
        ##Not: no subcut is needed since  done in caching
        ##if job.subsample:
        ##    addCut += '& (%s)' %(job.subcut)
        #CuttedTree = input.Get(job.tree)
        #CuttedTree.SetCacheSize(0)
    #print 'CuttedTree.GetEntries()',CuttedTree.GetEntries()

    found = False
    try:
        for branch in CuttedTree.GetListOfBranches():
              if( branch.GetName() == "DY_specialWeight" ):
                  found = True
                  break
        if not found:
            print "Warning 21347120983: Tree doesn't contrain DY_specialWeight"
    except TypeError:
        print 'TypeError: iteration over non-sequence'

    return CuttedTree

#CONFIGURE
argv = sys.argv
parser = OptionParser()
parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                          help="Verbose mode.")
parser.add_option("-T", "--training", dest="training", default="",
                      help="Training")
parser.add_option("-C", "--config", dest="config", default=[], action="append",
                      help="configuration file")
parser.add_option("-S","--setting", dest="MVAsettings", default='',
                      help="Parameter setting string")
parser.add_option("-N","--name", dest="set_name", default='',
                      help="Parameter setting name. Output files will have this name")
parser.add_option("-L","--local",dest="local", default='True',
                      help="True to run it locally. False to run on batch system using config")
parser.add_option("-m", "--mergeplot", dest="mergeplot", default=False,
                              help="option to merge")
parser.add_option("-M", "--mergecachingplot", dest="mergecachingplot", default=False, action='store_true', help="use files from mergecaching")
parser.add_option("-f", "--filelist", dest="filelist", default="",
                              help="list of files you want to run on")

(opts, args) = parser.parse_args(argv)
if opts.config =="":
        opts.config = "config"

print 'mergeplot is', opts.mergeplot
print 'mergecachingplot is', opts.mergecachingplot

#Import after configure to get help message
from myutils import BetterConfigParser, mvainfo, ParseInfo, TreeCache

import os
if os.path.exists("../interface/DrawFunctions_C.so"):
    print 'ROOT.gROOT.LoadMacro("../interface/DrawFunctions_C.so")'
    ROOT.gROOT.LoadMacro("../interface/DrawFunctions_C.so")

#load config
config = BetterConfigParser()
config.read(opts.config)
run=opts.training
gui=opts.verbose

anaTag = config.get("Analysis","tag")


#print "Compile external macros"
#print "=======================\n"

## compile external macros to compute variables on the fly
#ROOT.gSystem.CompileMacro("../plugins/PU.C")

#GLOABAL rescale from Train/Test Spliiting:
global_rescale=2.

#get locations:
MVAdir=config.get('Directories','vhbbpath')+'/python/weights/'
samplesinfo=config.get('Directories','samplesinfo')

#systematics
systematics=config.get('systematics','systematics')
systematics=systematics.split(' ')

weightF=config.get('Weights','weightF')

VHbbNameSpace=config.get('VHbbNameSpace','library')
ROOT.gSystem.Load(VHbbNameSpace)

#CONFIG
#factory
factoryname=config.get('factory','factoryname')
factorysettings=config.get('factory','factorysettings')
#MVA
MVAtype=config.get(run,'MVAtype')
#MVA name and settings. From local running or batch running different option
print 'opts.local is', opts.local
optimisation_training = False
sample_to_cache_ = None
subcut_ = None
par_optimisation = None
mergeCachingPart = None

data_as_signal = eval(config.get("Analysis","Data_as_signal"))
if data_as_signal:
    global_rescale=1.
    print '@INFO: Signal is data. Will change the weights accordingly (this should be used for correlation plots only)'

if not  opts.MVAsettings == '':
    print 'MVAsettins are', opts.MVAsettings
    if 'CUTBIN' in opts.MVAsettings:
        print '@INFO: The MVA regions contains subcuts'
        subcut = opts.MVAsettings[opts.MVAsettings.find('CUTBIN')+7:].split('__')
        subcut_ = '(' + str(subcut[1]) + ' < '+ subcut[0] + ' ) & ( ' + subcut[0] + ' < '+ str(subcut[2]) + ' )'
        print 'subcut_ is', subcut_
    if 'CACHING' in opts.MVAsettings:
        sample_to_cache_ = opts.MVAsettings[opts.MVAsettings.find('CACHING')+7:].split('__')[1]
        print '@INFO: Only caching will be performed. The sample to be cached is', sample_to_cache_
    if 'MERGECACHING' in opts.MVAsettings:
        mergeCachingPart = int(opts.MVAsettings[opts.MVAsettings.find('CACHING')+7:].split('__')[0].split('_')[-1])
        print '@INFO: Partially merged caching: this is part', mergeCachingPart
    if 'OPT' in opts.MVAsettings:
        par_optimisation = opts.MVAsettings[opts.MVAsettings.find('OPT')+3:].split('__')[1]
        if par_optimisation == 'mainpar':
            print 'using main BDT parameters'
        else:
            value_optimisation =opts.MVAsettings[opts.MVAsettings.find('OPT')+3:].split('__')[2]
            print '@INFO: Optimisation will be performed. The optimisation parameter is',par_optimisation,'with a value of',value_optimisation
        #opt_MVAsettings = opts.MVAsettings
        optimisation_training = True

# to avoid argument size limits, filelist can be encoded with 'base64:' + base64(zlib(.)), decode it first in this case
if opts.filelist.startswith('base64:'):
    opts.filelist = zlib.decompress(base64.b64decode(opts.filelist[7:]))
    #print 'zlib decoded file list:', opts.filelist

filelist=filter(None,opts.filelist.replace(' ', '').split(';'))
# print filelist
print "len(filelist)",len(filelist),
if len(filelist)>0:
    print "filelist[0]:",filelist[0];
else:
    print ''

remove_sys_ = eval(config.get('Plot_general','remove_sys'))


#setupt MVAsettings
MVAsettings=config.get(run,'MVAsettings')
#print 'MVAsettings are',MVAsettings


#if(eval(opts.local)):
#  print 'Local run'
MVAname=run
#print 'MVAname before opt is', MVAname
#MVAsettings=config.get(run,'MVAsettings')
#MVAname=opts.set_name
if par_optimisation:
    if not par_optimisation == 'mainpar':
        #opt_Dict = dict(item.split("=") for item in opt_MVAsettings.split(","))
        #for key in opt_Dict:
        for par in MVAsettings.split(':'):
            #if not key in par: continue
            if not par_optimisation in par: continue
            par_old= par.split('=')[1]
            #par_new += opt_Dict[key]
            print 'goona replace','%s=%s'%(par_optimisation,par_old),'by','%s=%s'%(par_optimisation,value_optimisation)
            MVAsettings = MVAsettings.replace('%s=%s'%(par_optimisation,par_old),'%s=%s'%(par_optimisation,value_optimisation))
            MVAname += '_OPT_%s_%s'%(par_optimisation,value_optimisation)

#print 'MVAsettings after replacements are',MVAsettings
#print 'MVAname after replacement is', MVAname


#elif(opts.set_name!='' and opts.MVAsettings!=''):
#  print 'Batch run'
#  MVAname=opts.set_name
#  MVAsettings=opts.MVAsettings
#else :
#  print 'Problem in configuration. Missing or inconsitent information Check input options'
#  sys.exit()  
print '@DEBUG: MVAname'
print 'input : ' + opts.set_name
print 'used : ' + MVAname

fnameOutput = MVAdir+factoryname+'_'+MVAname+'.root'
#fnameOutput = MVAdir+factoryname+'_'+MVAname+'_'+opts.MVAsettings+'.root'
print '@DEBUG: output file name : ' + fnameOutput

#locations
path=config.get('Directories','MVAin')

TCutname=config.get(run, 'treeCut')
TCut=config.get('Cuts',TCutname)
print 'TCut is', TCut
#adding the subcut
#IMPORTANT: since subcuts is also present in the other steps (plot, dc), be sure the additional cut is performed the same way, so the caching would need to be performed only once.
if subcut_: TCut += '&' + subcut_


#signals
signals=config.get(run,'signals')
signals=eval(signals)
#backgrounds
backgrounds=config.get(run,'backgrounds')
backgrounds=eval(backgrounds)
treeVarSet=config.get(run,'treeVarSet')
print 'signals are', signals
print 'backgrounds are', backgrounds
        
#variables
#TreeVar Array
MVA_Vars={}
MVA_Vars['Nominal']=config.get(treeVarSet,'Nominal')
MVA_Vars['Nominal']=MVA_Vars['Nominal'].split(' ')    

#Infofile
info = ParseInfo(samplesinfo,path)

#Workdir
workdir=ROOT.gDirectory.GetPath()


#Remove EventForTraining in order to run the MVA directly from the PREP step
#TrainCut='%s & !((evt%s)==0 || isData)'%(TCut,'%2')
#EvalCut= '%s & ((evt%s)==0 || isData)'%(TCut,'%2')
TrainCut='!((evt%2)==0 || isData)'
EvalCut= '((evt%2)==0 || isData)'
#TrainCut='%s & EventForTraining==1'%TCut
#EvalCut='%s & EventForTraining==0'%TCut

if data_as_signal:
    TrainCut = '1'
    EvalCut = '1'

print "TrainCut:",TrainCut
print "EvalCut:",EvalCut
#cuts = [TrainCut,EvalCut]
cuts = [TCut]

if sample_to_cache_:
    #Doing splitsubcaching: only one sample should remain
    if sample_to_cache_ in signals:
        signals = []
        backgrounds = []
        signals.append(sample_to_cache_)
    elif sample_to_cache_ in backgrounds:
        signals = []
        backgrounds = []
        backgrounds.append(sample_to_cache_)
    else:
        print "@ERROR: The target sample in splitsubcaching is not used in the bdt. Aborting."
        sys.exit()

print 'after the selections, backgrounds are', backgrounds
print 'after the selections, signals are', signals
samples = []
samples = info.get_samples(signals+backgrounds)

print "XXXXXXXXXXXXXXXX"
print 'filelist is', filelist

#tc = TreeCache(cuts,samples,path,config, [])
#to be compatible with mergecaching
tc = TreeCache(cuts, samples, path, config, filelist=filelist, mergeplot=opts.mergeplot, sample_to_merge=sample_to_cache_, mergeCachingPart=mergeCachingPart, plotMergeCached = opts.mergecachingplot, remove_sys=remove_sys_)  # created cached tree i.e. create new skimmed trees using the list of cuts

#for mergesubcaching step, need to continue even if some root files are missing to perform the caching in parallel
if sample_to_cache_ or mergeCachingPart:
    tc = TreeCache(cuts, samples, path, config, filelist=filelist, mergeplot=opts.mergeplot, sample_to_merge=None, mergeCachingPart=mergeCachingPart, plotMergeCached = opts.mergecachingplot, branch_to_keep=None, do_onlypart_n=True,   dccut=None, remove_sys=remove_sys_)
else:
    tc = TreeCache(cuts, samples, path, config, filelist=filelist, mergeplot=opts.mergeplot, sample_to_merge=None, mergeCachingPart=mergeCachingPart, plotMergeCached = opts.mergecachingplot, branch_to_keep=None, do_onlypart_n=False, dccut=None, remove_sys=remove_sys_)

##   .tc = TreeCache(self.cuts, samples, path, config, filelist, mergeplot, sample_to_merge, mergeCachingPart,                                         plotMergeCached,                         branch_to_keep,        False,                dccut,        remove_sys)  # created cached tree i.e. create new skimmed trees using the list of cuts
#
#    def __init__(self, cutList, sampleList, path, config,filelist=None,mergeplot=False,sample_to_merge=None,mergeCachingPart=-1,                      plotMergeCached=False,                   branch_to_keep=None,   do_onlypart_n= False, dccut = None, remove_sys=None):

#if sample_to_cache_:
#    print "@INFO: performed caching only. bye"
#    sys.exit(1)

output = ROOT.TFile.Open(fnameOutput, "RECREATE")

print '\n\t>>> READING EVENTS <<<\n'

signal_samples = info.get_samples(signals)
background_samples = info.get_samples(backgrounds)

#TRAIN trees
Tbackgrounds = []
TbScales = []
Tsignals = []
TsScales = []
#EVAL trees
Ebackgrounds = []
EbScales = []
Esignals = []
EsScales = []

INPUT_SIG = []
INPUT_ESIG = []
INPUT_BKG = []
INPUT_EBKG = []

#load trees
for job in signal_samples:
    print 'job.name is', job.name
    if  sample_to_cache_ and sample_to_cache_!= job.name: continue
    print '\tREADING IN %s AS SIG'%job.name
    #INPUT_SIG.append(ROOT.TFile.Open(tc.get_tree(job,TrainCut),'read'))
    INPUT_SIG.append(getTree(tc.get_tree(job,TrainCut)))
    #Tsignal = INPUT_SIG[-1].Get(job.tree)
    Tsignal = INPUT_SIG[-1]

    ROOT.gDirectory.Cd(workdir)
    if not data_as_signal:
        TsScale = tc.get_scale(job,config)*global_rescale
    else:
        TsScale = 1
    Tsignals.append(Tsignal)
    TsScales.append(TsScale)
    #INPUT_ESIG.append(ROOT.TFile.Open(tc.get_tree(job,EvalCut),'read'))
    INPUT_ESIG.append(getTree(tc.get_tree(job,EvalCut)))
    #Esignal = INPUT_ESIG[-1].Get(job.tree)
    Esignal = INPUT_ESIG[-1]

    #Esignal = tc.get_tree(job,EvalCut)
    Esignals.append(Esignal)
    EsScales.append(TsScale)
    print '\t\t\tTraining %s events'%Tsignal.GetEntries()
    print '\t\t\tEval %s events'%Esignal.GetEntries()
for job in background_samples:
    print '\tREADING IN %s AS BKG'%job.name
    #INPUT_BKG.append(ROOT.TFile.Open(tc.get_tree(job,TrainCut),'read'))
    INPUT_BKG.append(getTree(tc.get_tree(job,TrainCut)))
    #Tbackground = INPUT_BKG[-1].Get(job.tree)
    Tbackground = INPUT_BKG[-1]

    ROOT.gDirectory.Cd(workdir)
    TbScale = tc.get_scale(job,config)*global_rescale
    Tbackgrounds.append(Tbackground)
    TbScales.append(TbScale)
    #INPUT_EBKG.append(ROOT.TFile.Open(tc.get_tree(job,),'read'))
    INPUT_EBKG.append(getTree(tc.get_tree(job,EvalCut)))
    #Ebackground = INPUT_EBKG[-1].Get(job.tree)
    Ebackground = INPUT_EBKG[-1]

    #Ebackground = tc.get_tree(job,EvalCut)
    ROOT.gDirectory.Cd(workdir)
    Ebackgrounds.append(Ebackground)
    EbScales.append(TbScale)
    print '\t\t\tTraining %s events'%Tbackground.GetEntries()
    print '\t\t\tEval %s events'%Ebackground.GetEntries()


if sample_to_cache_ or mergeCachingPart:
    print '@INFO:',sample_to_cache_,'has beeen cached and subcached. Exiting.'
    sys.exit(1)

# print 'creating TMVA.Factory object'
factory = ROOT.TMVA.Factory(factoryname, output, factorysettings)

#set input trees
# print 'set signal input trees'
for i in range(len(Tsignals)):
    factory.AddSignalTree(Tsignals[i], TsScales[i], ROOT.TMVA.Types.kTraining)
    factory.AddSignalTree(Esignals[i], EsScales[i], ROOT.TMVA.Types.kTesting)

# print 'set background input trees'
for i in range(len(Tbackgrounds)):
    if (Tbackgrounds[i].GetEntries()>0):
        factory.AddBackgroundTree(Tbackgrounds[i], TbScales[i], ROOT.TMVA.Types.kTraining)

    if (Ebackgrounds[i].GetEntries()>0):
        factory.AddBackgroundTree(Ebackgrounds[i], EbScales[i], ROOT.TMVA.Types.kTesting)
        
# print 'add the variables'
for var in MVA_Vars['Nominal']:
    factory.AddVariable(var,'D') # add the variables

#Execute TMVA
print 'Execute TMVA: SetSignalWeightExpression'
if data_as_signal:
    factory.SetSignalWeightExpression('1')
else:
    factory.SetSignalWeightExpression(weightF)
print 'Execute TMVA: SetBackgroundWeightExpression'
factory.SetBackgroundWeightExpression(weightF)
factory.Verbose()
print 'Execute TMVA: factory.BookMethod'
#my_methodBase_bdt = factory.BookMethod(MVAtype,MVAname,MVAsettings)
factory.BookMethod(MVAtype,MVAname,MVAsettings)
print 'Execute TMVA: TrainMethod'
#my_methodBase_bdt.TrainAllMethod()
factory.TrainAllMethods()
#factory.TrainAllMethods()
print 'Execute TMVA: TestAllMethods'
factory.TestAllMethods()
print 'Execute TMVA: EvaluateAllMethods'
factory.EvaluateAllMethods()
print 'Execute TMVA: output.Write'
output.Close()


#training performance parameters

#output.ls()
#output.cd('Method_%s'%MVAtype)
#ROOT.gDirectory.ls()
#ROOT.gDirectory.cd(MVAname)

## print 'Get ROCs'
#rocIntegral_default=my_methodBase_bdt.GetROCIntegral()
#roc_integral_test = my_methodBase_bdt.GetROCIntegral(ROOT.gDirectory.Get(factoryname+'_'+MVAname+'_S'),ROOT.gDirectory.Get(factoryname+'_'+MVAname+'_B'))
#roc_integral_train = my_methodBase_bdt.GetROCIntegral(ROOT.gDirectory.Get(factoryname+'_'+MVAname+'_Train_S'),ROOT.gDirectory.Get(factoryname+'_'+MVAname+'_Train_B'))
## print 'Get significances'
#significance = my_methodBase_bdt.GetSignificance()
#separation_test = my_methodBase_bdt.GetSeparation(ROOT.gDirectory.Get(factoryname+'_'+MVAname+'_S'),ROOT.gDirectory.Get(factoryname+'_'+MVAname+'_B'))
#separation_train = my_methodBase_bdt.GetSeparation(ROOT.gDirectory.Get(factoryname+'_'+MVAname+'_Train_S'),ROOT.gDirectory.Get(factoryname+'_'+MVAname+'_Train_B'))
#ks_signal = (ROOT.gDirectory.Get(factoryname+'_'+MVAname+'_S')).KolmogorovTest(ROOT.gDirectory.Get(factoryname+'_'+MVAname+'_Train_S'))
#ks_bkg= (ROOT.gDirectory.Get(factoryname+'_'+MVAname+'_B')).KolmogorovTest(ROOT.gDirectory.Get(factoryname+'_'+MVAname+'_Train_B'))
#
#
#print '@DEBUG: Test Integral'
#print ROOT.gDirectory.Get(factoryname+'_'+MVAname+'_S').Integral()
#print '@LOG: ROC integral (default)'
#print rocIntegral_default
#print '@LOG: ROC integral using signal and background'
#print roc_integral_test
#print '@LOG: ROC integral using train signal and background'
#print roc_integral_train
#print '@LOG: ROC integral ratio (Test/Train)'
#print roc_integral_test/roc_integral_train
#print '@LOG: Significance'
#print significance
#print '@LOG: Separation for test sample'
#print separation_test
#print '@LOG: Separation for test train'
#print separation_train
#print '@LOG: Kolmogorov test on signal'
#print ks_signal
#print '@LOG: Kolmogorov test on background'
#print ks_bkg
#
##!! update the database
#import sqlite3 as lite
#con = lite.connect(MVAdir+'Trainings.db',timeout=10000) #timeout in milliseconds. default 5 sec
#with con: # here DB is locked
#    cur = con.cursor()
#    cur.execute("create table if not exists trainings (Roc_integral real, Separation real, Significance real, Ks_signal real, Ks_background real, Roc_integral_train real, Separation_train real, MVASettings text)");
#    cur.execute("insert into trainings values(?,?,?,?,?,?,?,?)",(roc_integral_test,separation_test,significance,ks_signal,ks_bkg,roc_integral_train,separation_train,MVAsettings));
##!! here is unlocked
#
##!! Close the output file to avoid memory leak
#output.Close()


#WRITE INFOFILE
infofile = open(MVAdir+factoryname+'_'+MVAname+'.info','w')
print '@DEBUG: output infofile name'
print infofile

info=mvainfo(MVAname)
info.factoryname=factoryname
info.factorysettings=factorysettings
info.MVAtype=MVAtype
info.MVAsettings=MVAsettings
info.weightfilepath=MVAdir
info.path=path
info.varset=treeVarSet
info.vars=MVA_Vars['Nominal']
pickle.dump(info,infofile)
infofile.close()

# open the TMVA Gui 
#if gui == True:
#    ROOT.gROOT.ProcessLine( ".L myutils/TMVAGui.C")
#    ROOT.gROOT.ProcessLine( "TMVAGui(\"%s\")" % fnameOutput )
#    ROOT.gApplication.Run()


