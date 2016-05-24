#!/usr/bin/env python
from __future__ import print_function
import sys,hashlib
import os,subprocess
import ROOT 
from array import array
from math import sqrt
from copy import copy
#suppres the EvalInstace conversion warning bug
import warnings
warnings.filterwarnings( action='ignore', category=RuntimeWarning, message='creating converter.*' )
from optparse import OptionParser
import pickle


#CONFIGURE
ROOT.gROOT.SetBatch(True)
#load config
argv = sys.argv
parser = OptionParser()
parser.add_option("-D", "--discr", dest="discr", default="",
                      help="discriminators to be added")
parser.add_option("-S", "--samples", dest="names", default="",
                      help="samples you want to run on")
parser.add_option("-C", "--config", dest="config", default=[], action="append",
                      help="configuration file")
parser.add_option("-W", "--weight", dest="weight", default='',
                      help="list of weights, used when performing the optimisation")
parser.add_option("-f", "--filelist", dest="filelist", default="",
                              help="list of files you want to run on")
(opts, args) = parser.parse_args(argv)

if opts.config =="":
        opts.config = "config"

weight = opts.weight
evaluate_optimisation = False
if weight != '': evaluate_optimisation = True

print ('opts.filelist="'+opts.filelist+'"')
filelist=filter(None,opts.filelist.replace(' ', '').split(';'))
print (filelist)
print ("len(filelist)",len(filelist),)
if len(filelist)>0:
    print ("filelist[0]:",filelist[0])
else:
    print ('')

#Import after configure to get help message
from myutils import BetterConfigParser, progbar, printc, ParseInfo, MvaEvaluator

config = BetterConfigParser()
config.read(opts.config)
anaTag = config.get("Analysis","tag")

#get locations:
Wdir=config.get('Directories','Wdir')
samplesinfo=config.get('Directories','samplesinfo')

#read shape systematics
systematics=config.get('systematics','systematics')

#systematics
INpath = config.get('Directories','MVAin')
OUTpath = config.get('Directories','MVAout')

info = ParseInfo(samplesinfo,INpath)

arglist = ''

if not evaluate_optimisation:
    arglist=opts.discr #RTight_blavla,bsbsb
else:
#    print '@INFO: Evaluating bdt for optimisation'
    arglist=weight

namelistIN=opts.names
namelist=namelistIN.split(',')

print ('namelist',namelist)
# sys.exit(1)

#doinfo=bool(int(opts.update))

MVAlist=arglist.split(',')

#CONFIG
#factory
factoryname=config.get('factory','factoryname')

#load the namespace
VHbbNameSpace=config.get('VHbbNameSpace','library')
ROOT.gSystem.Load(VHbbNameSpace)

#MVA
MVAinfos=[]
MVAdir=config.get('Directories','vhbbpath')
for MVAname in MVAlist:
    MVAinfofile = open(MVAdir+'/python/weights/'+factoryname+'_'+MVAname+'.info','r')
    MVAinfos.append(pickle.load(MVAinfofile))
    MVAinfofile.close()
    
longe=40
#Workdir
workdir=ROOT.gDirectory.GetPath()



theMVAs = []
for mva in MVAinfos:
    theMVAs.append(MvaEvaluator(config,mva))


#eval

# samples = info.get_samples(namelist)
# print('info',info)
tmpDir = os.environ["TMPDIR"]
for job in info:
    print ('job.name',job.name,'job.identifier',job.identifier,'namelist',namelist)
    if not job.name in namelist and len([x for x in namelist if x==job.identifier])==0:
        print ('job.name',job.name,'and job.identifier',job.identifier,'not in namelist',namelist)
        continue
    print ('\t match - %s' %(job.name))
    inputfiles = []
    outputfiles = []
    tmpfiles = []
    if len(filelist) == 0:
        #get trees:
        # print(INpath+'/'+job.prefix+job.identifier+'.root')
        # input = ROOT.TFile.Open(INpath+'/'+job.prefix+job.identifier+'.root','read')
        # print(OUTpath+'/'+job.prefix+job.identifier+'.root')
        # outfile = ROOT.TFile.Open(tmpDir+'/'+job.prefix+job.identifier+'.root','recreate')

        inputfiles.append(INpath+'/'+job.prefix+job.identifier+'.root')
        print('opening '+INpath+'/'+job.prefix+job.identifier+'.root')
        tmpfiles.append(tmpDir+'/'+job.prefix+job.identifier+'.root')
        try:
            os.mkdir(OUTpath)
        except:
            pass
        outputfiles.append("%s/%s/%s" %(OUTpath,job.prefix,job.identifier+'.root'))
    else:
        for inputFile in filelist:
            subfolder = inputFile.split('/')[-4]
            filename = inputFile.split('/')[-1]
            filename = filename.split('_')[0]+'_'+subfolder+'_'+filename.split('_')[1]
            hash = hashlib.sha224(filename).hexdigest()
            inputFile = "%s/%s/%s" %(INpath,job.identifier,filename.replace('.root','')+'_'+str(hash)+'.root')
            if not os.path.isfile(inputFile): continue
            outputFile = "%s/%s/%s" %(OUTpath,job.identifier,filename.replace('.root','')+'_'+str(hash)+'.root')
            tmpfile = "%s/%s" %(tmpDir,filename.replace('.root','')+'_'+str(hash)+'.root')
            if inputFile in inputfiles: continue
            del_protocol = outputFile
            del_protocol = del_protocol.replace('gsidcap://t3se01.psi.ch:22128/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
            del_protocol = del_protocol.replace('dcap://t3se01.psi.ch:22125/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
            del_protocol = del_protocol.replace('root://t3dcachedb03.psi.ch:1094/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
            if os.path.isfile(del_protocol.replace('srm://t3se01.psi.ch:8443/srm/managerv2?SFN=','')):
                f = ROOT.TFile.Open(outputFile,'read')
                if not f:
                  print ('file is null, adding to input')
                  inputfiles.append(inputFile)
                  outputfiles.append(outputFile)
                  tmpfiles.append(tmpfile)
                  continue
                # f.Print()
                if f.GetNkeys() == 0 or f.TestBit(ROOT.TFile.kRecovered) or f.IsZombie():
                    print ('f.GetNkeys()',f.GetNkeys(),'f.TestBit(ROOT.TFile.kRecovered)',f.TestBit(ROOT.TFile.kRecovered),'f.IsZombie()',f.IsZombie())
                    print ('File', del_protocol.replace('srm://t3se01.psi.ch:8443/srm/managerv2?SFN=',''), 'already exists but is buggy, gonna delete and rewrite it.')
                    #command = 'rm %s' %(outputFile)
                    command = 'srmrm %s' %(del_protocol)
                    subprocess.call([command], shell=True)
                    print(command)
                else: continue
            inputfiles.append(inputFile)
            outputfiles.append(outputFile)
            tmpfiles.append(tmpfile)
        print ('inputfiles',inputfiles,'tmpfiles',tmpfiles)

    for inputfile,tmpfile,outputFile in zip(inputfiles,tmpfiles,outputfiles):
        input = ROOT.TFile.Open(inputfile,'read')
        output = ROOT.TFile.Open(tmpfile,'recreate')
        print ('')
        print ('inputfile',inputfile)
        print ("Writing: ",tmpfile)
        print ('outputFile',outputFile)
        print ('')
        input.cd()
        obj = ROOT.TObject
        for key in ROOT.gDirectory.GetListOfKeys():
            input.cd()
            obj = key.ReadObj()
            #print obj.GetName()
            if obj.GetName() == job.tree:
                continue
            output.cd()
            #print key.GetName()
            obj.Write(key.GetName())
        tree = input.Get(job.tree)
        nEntries = tree.GetEntries()
        output.cd()
        newtree = tree.CloneTree(0)

        #Set branch adress for all vars
        for i in range(0,len(theMVAs)):
            theMVAs[i].setVariables(tree,job)
        output.cd()
        #Setup Branches
        mvaVals=[]
        for i in range(0,len(theMVAs)):
            if job.type == 'Data':
                mvaVals.append(array('f',[0]))
                newtree.Branch(MVAinfos[i].MVAname,mvaVals[i],'nominal/F')
            else:
                mvaVals.append(array('f',[0]*len(systematics.split())))
                newtree.Branch(theMVAs[i].MVAname,mvaVals[i],':'.join(systematics.split())+'/F')
                #newtree.Branch(theMVAs[i].MVAname,mvaVals[i],'nominal:JER_up:JER_down:JES_up:JES_down:beff_up:beff_down:bmis_up:bmis_down:beff1_up:beff1_down/F')
            MVA_formulas_Nominal = []
            print('\n--> ' + job.name +':')
        #Fill event by event:
        for entry in range(0,nEntries):
            tree.GetEntry(entry)

            for i in range(0,len(theMVAs)):
                theMVAs[i].evaluate(mvaVals[i],job)
            #Fill:
            newtree.Fill()
        newtree.AutoSave()
        output.Close()

        # targetStorage = OUTpath.replace('gsidcap://t3se01.psi.ch:22128/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')+'/'+job.prefix+job.identifier+'.root'
        targetStorage = outputFile.replace('gsidcap://t3se01.psi.ch:22128/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
        if('pisa' in config.get('Configuration','whereToLaunch')):
          command = 'rm %s' %(targetStorage)
          print(command)
          subprocess.call([command], shell=True)
          # command = 'cp %s %s' %(tmpDir+'/'+job.prefix+job.identifier+'.root',targetStorage)
          command = 'cp %s %s' %(tmpfile,targetStorage)
          print(command)
          subprocess.call([command], shell=True)
        else:
            command = 'srmrm %s' %(targetStorage.replace('root://t3dcachedb03.psi.ch:1094/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=/'))
            print(command)
            subprocess.call([command], shell=True)
            command = 'srmcp -2 -globus_tcp_port_range 20000,25000 file:///%s %s' %(tmpfile,targetStorage.replace('root://t3dcachedb03.psi.ch:1094/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=/'))
            print(command)
            os.system(command)
            command = 'rm %s' %(tmpfile)


    
print('\n')
