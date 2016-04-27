#! /usr/bin/env python
from optparse import OptionParser
import sys
import time
import os
import shutil
import subprocess

parser = OptionParser()
parser.add_option("-T", "--tag", dest="tag", default="8TeV",
                      help="Tag to run the analysis with, example '8TeV' uses config8TeV and pathConfig8TeV to run the analysis")
parser.add_option("-J", "--task", dest="task", default="",
                      help="Task to be done, i.e. 'dc' for Datacards, 'prep' for preparation of Trees, 'plot' to produce plots or 'eval' to write the MVA output or 'sys' to write regression and systematics (or 'syseval' for both). ")
parser.add_option("-M", "--mass", dest="mass", default="125",
              help="Mass for DC or Plots, 110...135")
parser.add_option("-S","--samples",dest="samples",default="",
              help="samples you want to run on")
parser.add_option("-F", "--folderTag", dest="ftag", default="",
                      help="Creats a new folder structure for outputs or uses an existing one with the given name")
parser.add_option("-N", "--number-of-events-or-files", dest="nevents_split_nfiles_single", default=-1,
                      help="Number of events per file when splitting or number of files when using single file workflow.")
parser.add_option("-P", "--philipp-love-progress-bars", dest="philipp_love_progress_bars", default=False,
                      help="If you share the love of Philipp...")
parser.add_option("-V", "--verbose", dest="verbose", action="store_true", default=False,
                      help="Activate verbose flag for debug printouts")
parser.add_option("-L", "--local", dest="override_to_run_locally", action="store_true", default=False,
                      help="Override run_locally option to run locally")
parser.add_option("-B", "--batch", dest="override_to_run_in_batch", action="store_true", default=False,
                      help="Override run_locally option to run in batch")

(opts, args) = parser.parse_args(sys.argv)
#print 'opts.mass is', opts.mass

import os,shutil,pickle,subprocess,ROOT,re
ROOT.gROOT.SetBatch(True)
from myutils import BetterConfigParser, Sample, ParseInfo, sample_parser, copytreePSI
from myutils.copytreePSI import filelist
import getpass

debugPrintOUts = opts.verbose

if opts.tag == "":
    print "Please provide tag to run the analysis with, example '-T 8TeV' uses config8TeV and pathConfig8TeV to run the analysis."
    sys.exit(123)

if opts.task == "":
    print "Please provide a task.\n-J prep:\tpreparation of Trees\n-J sys:\t\twrite regression and systematics\n-J eval:\tcreate MVA output\n-J plot:\tproduce Plots\n-J dc:\t\twrite workspaces and datacards"
    sys.exit(123)


en = opts.tag

#create the list with the samples to run over
samplesList=opts.samples.split(",")
timestamp = time.asctime().replace(' ','_').replace(':','-')

if(debugPrintOUts): print 'samplesList',samplesList
if(debugPrintOUts): print 'timestamp',timestamp

# the list of the config is taken from the path config
pathconfig = BetterConfigParser()
pathconfig.read('%sconfig/paths.ini'%(en))
_configs = pathconfig.get('Configuration','List').split(" ")
configs = [ '%sconfig/'%(en) + c for c in _configs  ]

if(debugPrintOUts): print 'configs',configs
if(debugPrintOUts): print 'opts.ftag',opts.ftag

if not opts.ftag == '':
    tagDir = pathconfig.get('Directories','tagDir')
    if(debugPrintOUts): print 'tagDir',tagDir
    DirStruct={'tagDir':tagDir,'ftagdir':'%s/%s/'%(tagDir,opts.ftag),'logpath':'%s/%s/%s/'%(tagDir,opts.ftag,'Logs'),'plotpath':'%s/%s/%s/'%(tagDir,opts.ftag,'Plots'),'limitpath':'%s/%s/%s/'%(tagDir,opts.ftag,'Limits'),'confpath':'%s/%s/%s/'%(tagDir,opts.ftag,'config') }
    
    if(debugPrintOUts): print 'DirStruct',DirStruct

    for keys in ['tagDir','ftagdir','logpath','plotpath','limitpath','confpath']:
        try:
            os.stat(DirStruct[keys])
        except:
            os.mkdir(DirStruct[keys])

    pathfile = open('%sconfig/paths.ini'%(en))
    buffer = pathfile.readlines()
    pathfile.close()
    os.rename('%sconfig/paths.ini'%(en),'%sconfig/paths.ini.bkp'%(en))
    pathfile = open('%sconfig/paths.ini'%(en),'w')
    for line in buffer:
        if line.startswith('plotpath'):
            line = 'plotpath: %s\n'%DirStruct['plotpath']
        elif line.startswith('logpath'):
            line = 'logpath: %s\n'%DirStruct['logpath']
        elif line.startswith('limits'):
            line = 'limits: %s\n'%DirStruct['limitpath']
        pathfile.write(line)
    pathfile.close()

    #copy config files
    for item in configs:
        shutil.copyfile(item,'%s/%s/%s'%(tagDir,opts.ftag,item.strip(en)))

if(debugPrintOUts): print configs
config = BetterConfigParser()
config.read(configs)

# RETRIEVE RELEVANT VARIABLES FROM CONFIG FILES AND FROM COMMAND LINE OPTIONS
logPath = config.get("Directories","logpath")
logo = open('%s/data/submit.txt' %config.get('Directories','vhbbpath')).readlines()
counter = 0
samplesinfo = config.get("Directories","samplesinfo")
whereToLaunch = config.get('Configuration','whereToLaunch')
run_locally = str(config.get("Configuration","run_locally"))
if opts.override_to_run_locally and opts.override_to_run_in_batch:
    print 'both override_to_run_locally and override_to_run_in_batch ativated, using str(config.get("Configuration","run_locally")) instead'
elif opts.override_to_run_locally:
    run_locally = 'True'
    print 'using override_to_run_locally to override str(config.get("Configuration","run_locally"))'
elif opts.override_to_run_in_batch:
    run_locally = 'False'
    print 'using override_to_run_in_batch to override str(config.get("Configuration","run_locally"))'

print 'whereToLaunch',whereToLaunch
print 'run_locally',run_locally

# CREATE DIRECTORIES FOR PSI
if 'PSI' in whereToLaunch:
  print 'Create the ouput folders PREPout, SYSout, MVAout if not existing'
  mkdir_list = [
                config.get('Directories','PREPout').replace('root://t3dcachedb03.psi.ch:1094/',''),
                config.get('Directories','SYSout').replace('root://t3dcachedb03.psi.ch:1094/',''),
                config.get('Directories','MVAout').replace('root://t3dcachedb03.psi.ch:1094/',''),
                config.get('Directories','tmpSamples').replace('root://t3dcachedb03.psi.ch:1094/',''),
                ]
  for mkdir_protocol in mkdir_list:
    if(debugPrintOUts): print 'checking',mkdir_protocol
    _output_folder = ''
    for _folder in mkdir_protocol.split('/'):
        _output_folder += '/'+_folder
        if not os.path.exists(_output_folder):
            command = 'srmmkdir srm://t3se01.psi.ch/' + _output_folder
            subprocess.call([command], shell = True)

def dump_config(configs,output_file):
    """
    Dump all the configs in a output file
    Args:
        output_file: the file where the log will be dumped 
        configs: list of files (string) to be dumped
    Returns:
        nothing
    """
    outf = open(output_file,'w') 
    for i in configs:
        try:
            f=open(i,'r')
            outf.write(f.read())
        except: print '@WARNING: Config' + i + ' not found. It will not be used.'

def compile_macro(config,macro):
    """
    Creates the library from a macro using CINT compiling it in scratch to avoid
    problems with the linking in the working nodes.
    Args:
        config: configuration file where the macro path is specified
        macro: macro name to be compiled
    Returns:
        nothing
    """
    submitDir = os.getcwd()
    _macro=macro+'.h'
    library = config.get(macro,'library')
    libDir=os.path.dirname(library)
    os.chdir(libDir)
    if not os.path.exists(library):
        print '@INFO: Compiling ' + _macro
        scratchDir='/scratch/%s/'%(getpass.getuser())
        # shutil.copyfile(libDir+'/'+_macro,'/scratch/%s/%s'%(getpass.getuser(),_macro))
        os.system("cp "+libDir+'/* /scratch/%s/'%(getpass.getuser())) # OTHERWISE WILL NOT COMPILE SINCE INCLUDES OTHER FILES!!!
        os.chdir(scratchDir)
        print os.listdir(scratchDir)
        ROOT.gROOT.ProcessLine('.L %s+'%(scratchDir+_macro)) # CRASHES WHILE COMPILING THE SECOND ONE...
        shutil.copyfile('/scratch/%s/%s'%(getpass.getuser(),os.path.basename(library)),library)
        print '@INFO: macro',macro,'compiled, exiting to avoid stupid ROOT crash, please resubmit!!!'
        sys.exit(1)
    os.chdir(submitDir)
        
print '===============================\n'
print 'Compiling the macros'
print '===============================\n'
compile_macro(config,'BTagReshaping')
compile_macro(config,'VHbbNameSpace')

#check if the logPath exist. If not exit
if( not os.path.isdir(logPath) ):
    print '@ERROR : ' + logPath + ': dir not found.'
    print '@ERROR : Create it before submitting '
    print 'Exit'
    sys.exit(-1)

# CREATE DICTIONARY TO BE USED AT JOB SUBMISSION TIME
repDict = {'en':en,'logpath':logPath,'job':'','task':opts.task,'queue': 'all.q','timestamp':timestamp,'additional':'','job_id':'noid','nprocesses':str(max(int(pathconfig.get('Configuration','nprocesses')),1))}

# STANDARD WORKFLOW SUBMISSION FUNCTION
def submit(job,repDict,redirect_to_null=False):
    global counter
    repDict['job'] = job
    nJob = counter % len(logo)
    counter += 1
    if opts.philipp_love_progress_bars:
        repDict['name'] = '"%s"' %logo[nJob].strip()
    else:
        repDict['name'] = '%(job)s_%(en)s%(task)s' %repDict
    if run_locally == 'False':
        command = 'qsub -V -cwd -q %(queue)s -l h_vmem=6G -N %(name)s -j y -o %(logpath)s/%(timestamp)s_%(job)s_%(en)s_%(task)s.out -pe smp %(nprocesses)s runAll.sh %(job)s %(en)s ' %(repDict) + opts.task + ' ' + repDict['nprocesses']+ ' ' + repDict['job_id'] + ' ' + repDict['additional']
        print "the command is ", command
        dump_config(configs,"%(logpath)s/%(timestamp)s_%(job)s_%(en)s_%(task)s.config" %(repDict))
        subprocess.call([command], shell=True)
    else:
        waiting_time_before_retry = 60
        number_symultaneous_process = 4
        counter  =  int(subprocess.check_output('ps aux | grep $USER | grep '+opts.task +' | wc -l', shell=True))-1# add 1 to remove submithem count
        print 'counter command is', 'ps aux | grep $USER | grep '+opts.task +' | wc -l'
        while counter > number_symultaneous_process:
            print 'counter is', counter
            print 'waiting',waiting_time_before_retry,'seconds before to retry'
            os.system('sleep '+str(waiting_time_before_retry))
            counter = int(subprocess.check_output('ps aux | grep $USER | grep '+opts.task +' | wc -l', shell=True))

        command = 'sh runAll.sh %(job)s %(en)s ' %(repDict) + opts.task + ' ' + repDict['nprocesses']+ ' ' + repDict['job_id'] + ' ' + repDict['additional']
        if redirect_to_null: command = command + ' 2>&1 > /dev/null &'
        else: command = command + ' 2>&1 > %(logpath)s/%(timestamp)s_%(job)s_%(en)s_%(task)s.out' %(repDict) + ' &'
        print "the command is ", command
        dump_config(configs,"%(logpath)s/%(timestamp)s_%(job)s_%(en)s_%(task)s.config" %(repDict))
        subprocess.call([command], shell=True)

# SINGLE (i.e. FILE BY FILE) AND SPLITTED FILE WORKFLOW SUBMISSION FUNCTION
def submitsinglefile(job,repDict,file,run_locally,counter_local):
    global counter
    repDict['job'] = job
    nJob = counter % len(logo)
    counter += 1
    if opts.philipp_love_progress_bars:
        repDict['name'] = '"%s"' %logo[nJob].strip()
    else:
        repDict['name'] = '%(job)s_%(en)s%(task)s' %repDict
    if run_locally == 'True':
        command = 'sh runAll.sh %(job)s %(en)s ' %(repDict) + opts.task + ' ' + repDict['nprocesses']+ ' ' + repDict['job_id'] + ' ' + ('0' if not repDict['additional'] else repDict['additional'])
    else:
        command = 'qsub -V -cwd -q %(queue)s -l h_vmem=6G -N %(name)s -j y -o %(logpath)s/%(timestamp)s_%(job)s_%(en)s_%(task)s.out -pe smp %(nprocesses)s runAll.sh %(job)s %(en)s ' %(repDict) + opts.task + ' ' + repDict['nprocesses']+ ' ' + repDict['job_id'] + ' ' + ('0' if not repDict['additional'] else repDict['additional'])
        command = command.replace('.out','_'+str(counter_local)+'.out')
    print "the command is ", command
    print "submitting", len(file.split(';')),'files like',file.split(';')[0]
    command = command + ' "' + str(file)+ '"'
    dump_config(configs,"%(logpath)s/%(timestamp)s_%(job)s_%(en)s_%(task)s.config" %(repDict))
    subprocess.call([command], shell=True)

# MERGING FUNCTION FOR SINGLE (i.e. FILE BY FILE) AND SPLITTED FILE WORKFLOW TO BE COMPATIBLE WITH THE OLD WORKFLOW
def mergesubmitsinglefile(job,repDict,run_locally):
    global counter
    repDict['job'] = job
    nJob = counter % len(logo)
    counter += 1
    if opts.philipp_love_progress_bars:
        repDict['name'] = '"%s"' %logo[nJob].strip()
    else:
        repDict['name'] = '%(job)s_%(en)s%(task)s' %repDict
    if run_locally == 'True':
        command = 'sh runAll.sh %(job)s %(en)s ' %(repDict) + opts.task + ' ' + repDict['nprocesses']+ ' ' + repDict['job_id'] + ' ' + ('0' if not repDict['additional'] else repDict['additional'])
    else:
        command = 'qsub -V -cwd -q %(queue)s -l h_vmem=6G -N %(name)s -j y -o %(logpath)s/%(timestamp)s_%(job)s_%(en)s_%(task)s.out -pe smp %(nprocesses)s runAll.sh %(job)s %(en)s ' %(repDict) + opts.task + ' ' + repDict['nprocesses']+ ' ' + repDict['job_id'] + ' ' + ('0' if not repDict['additional'] else repDict['additional'])
    command = command + ' mergeall'
    print "the command is ", command
    dump_config(configs,"%(logpath)s/%(timestamp)s_%(job)s_%(en)s_%(task)s.config" %(repDict))
    subprocess.call([command], shell=True)

# RETRIEVE FILELIST FOR THE TREECOPIER PSI AND SINGLE FILE SYS STEPS
def getfilelist(job):
    samplefiles = config.get('Directories','samplefiles')
    list = filelist(samplefiles,job)
    return list


if opts.task == 'train':
    train_list = (config.get('MVALists','List_for_submitscript')).split(',')
    print train_list
    for item in train_list:
        submit(item,repDict)


if opts.task == 'dc':
    DC_vars= (config.get('LimitGeneral','List')).split(',')
    print DC_vars

if opts.task == 'plot':
    Plot_vars= (config.get('Plot_general','List')).split(',')


if not opts.task == 'prep':
    path = config.get("Directories","samplepath")
    info = ParseInfo(samplesinfo,path)


if opts.task == 'plot': 
    repDict['queue'] = 'all.q'
    for item in Plot_vars:
        submit(item,repDict)


if opts.task == 'trainReg':
    repDict['queue'] = 'all.q'
    submit('trainReg',repDict)


elif opts.task == 'dc':
    repDict['queue'] = 'all.q'
    for item in DC_vars:
        # item here contains the dc name
        submit(item,repDict)


elif opts.task == 'prep':
    if ( opts.samples == ""):
        path = config.get("Directories","PREPin")
        info = ParseInfo(samplesinfo,path)
        for job in info:
            submit(job.name,repDict)
    else:
        for sample in samplesList:
            submit(sample,repDict)


elif opts.task == 'singleprep' or opts.task == 'singlesys' or opts.task == 'singleplot' or opts.task == 'mergesingleprep' or opts.task == 'mergesinglesys':
    if ( opts.samples == ""):
        if opts.task == 'singleprep' or opts.task == 'mergesingleprep':
            path = config.get("Directories","PREPin")
        elif opts.task == 'singlesys' or opts.task == 'mergesinglesys':
            path = config.get("Directories","SYSin")
        elif opts.task == 'singleplot':
            path = config.get("Directories","plottingSamples")
        info = ParseInfo(samplesinfo,path)
        sample_list = []
        for job in info:
            sample_list.append(job.identifier)
        sample_list = set(sample_list)
    else:
        sample_list = set(samplesList)

    for sample in sample_list:
        if sample == '': continue
        if opts.task == 'singleprep' or opts.task == 'singlesys' or opts.task == 'singleplot':
            files = getfilelist(sample)
            files_per_job = int(opts.nevents_split_nfiles_single) if int(opts.nevents_split_nfiles_single) > 0 else int(config.get("Configuration","files_per_job"))
            files_split=[files[x:x+files_per_job] for x in xrange(0, len(files), files_per_job)]
            files_split = [';'.join(sublist) for sublist in files_split]
            counter_local = 0
            for files_sublist in files_split:
                submitsinglefile(sample,repDict,files_sublist,run_locally,counter_local)
                counter_local = counter_local + 1
        elif opts.task == 'mergesingleprep' or opts.task == 'mergesinglesys':
            mergesubmitsinglefile(sample,repDict,run_locally)
            

# ADD SYSTEMATIC UNCERTAINTIES AND ADDITIONAL HIGHER LEVEL VARIABLES TO THE TREES
elif opts.task == 'sys' or opts.task == 'syseval':
    path = config.get("Directories","SYSin")
    info = ParseInfo(samplesinfo,path)
    if opts.samples == "":
        for job in info:
            if (job.subsample): 
                continue # avoid multiple submissions form subsamples
            # TO FIX FOR SPLITTED SAMPLE
            submit(job.name,repDict)
    else:
        for sample in samplesList:
            submit(sample,repDict)


# EVALUATION OF EVENT BY EVENT BDT SCORE
elif opts.task == 'eval':
    repDict['queue'] = 'long.q'
    path = config.get("Directories","MVAin")
    info = ParseInfo(samplesinfo,path)
    if opts.samples == "":
        for job in info:
            if (job.subsample): 
                continue # avoid multiple submissions from subsamples
            if(info.checkSplittedSampleName(job.identifier)): # if multiple entries for one name  (splitted samples) use the identifier to submit
                print '@INFO: Splitted samples: submit through identifier'
                submit(job.identifier,repDict)
            else: submit(job.name,repDict)
    else:
        for sample in samplesList:
            print sample
            submit(sample,repDict)


# POSSIBILITY TO SPLIT SINGLE MERGED FILES IN SUBFILES
# IN PRINCIPLE USEFUL BUT NOT USED ANYMORE AS THE LOGIC CHANGED (I.E. DON'T MERGE FILES)
elif( opts.task == 'split' ):
    path = config.get("Directories","SPLITin")
    repDict['job_id']= int(opts.nevents_split_nfiles_single) if int(opts.nevents_split_nfiles_single) > 0 else 100000
    info = ParseInfo(samplesinfo,path)
    if ( opts.samples == "" ):
        for job in info:
            if (job.subsample): continue # avoid multiple submissions from subsamples
            submit(job.name,repDict)
    else:
        for sample in samplesList:
            submit(sample,repDict)


# BDT optimisation
elif opts.task == 'mva_opt':
    total_number_of_steps=1
    setting = ''
    for par in (config.get('Optimisation','parameters').split(',')):
        scan_par=eval(config.get('Optimisation',par))
        setting+=par+'='+str(scan_par[0])+':'
        if len(scan_par) > 1 and scan_par[2] != 0:
            total_number_of_steps+=scan_par[2]
    #setting=setting[:-1] # eliminate last column at the end of the setting string
    #repDict['additional']=setting
    repDict['additional']='main_par'
    repDict['job_id']=config.get('Optimisation','training')
    submit('OPT_main_set',repDict,False)
    main_setting=setting
    # Scanning all the parameters found in the training config in the Optimisation sector
    for par in (config.get('Optimisation','parameters').split(',')):
        scan_par=eval(config.get('Optimisation',par))
        if len(scan_par) > 1 and scan_par[2] != 0:
            for step in range(scan_par[2]):
                value = (scan_par[0])+((1+step)*(scan_par[1]-scan_par[0])/scan_par[2])
                setting=re.sub(par+'.*?:',par+'='+str(value)+':',main_setting)
                repDict['additional']=setting
                submit('OPT_'+par+str(value),repDict,False)
                # submit(config.get('Optimisation','training'),repDict)

elif opts.task == 'mva_opt_eval':
    #
    #This step evaluate the BDT produced by mva_opt.
    #

    #Read the config
    repDict['queue'] = 'long.q'
    path = config.get("Directories","MVAin")
    repDict['job_id']=config.get('Optimisation','training')
    factoryname=config.get('factory','factoryname')
    MVAdir=config.get('Directories','vhbbpath')+'/python/weights/'
    #Read weights from optimisaiton config, store the in a list (copied from mva_opt)
    total_number_of_steps=1
    setting = ''
    for par in (config.get('Optimisation','parameters').split(',')):
        scan_par=eval(config.get('Optimisation',par))
        setting+=par+'='+str(scan_par[0])+':'
        if len(scan_par) > 1 and scan_par[2] != 0:
            total_number_of_steps+=scan_par[2]
    repDict['additional']=setting
    repDict['job_id']=config.get('Optimisation','training')
    main_setting=setting
    config_weights_list = ['OPT_main_set']
    for par in (config.get('Optimisation','parameters').split(',')):
        scan_par=eval(config.get('Optimisation',par))
        if len(scan_par) > 1 and scan_par[2] != 0:
            for step in range(scan_par[2]):
                value = (scan_par[0])+((1+step)*(scan_par[1]-scan_par[0])/scan_par[2])
                setting=re.sub(par+'.*?:',par+'='+str(value)+':',main_setting)
                config_weights_list.append('OPT_'+par+str(value))
    #List all the weights produced from the optimisation, read from the weight directory. return weights_list
    weights = ''
    for cw in config_weights_list:
        for w in os.listdir(MVAdir):
            w = w.replace(factoryname+'_','')
            w = w.replace('.root','')
            if not w == cw: continue
            weights += w + ','
    if weights[-1] == ',': weights = weights[:-1]#remove , at the end of the list
    #submit the jobs
    info = ParseInfo(samplesinfo,path)
    repDict['additional']=weights
    print 'The optimisation weights are', weights
    if opts.samples == "":
        for job in info:
            if (job.subsample):
                continue # avoid multiple submissions from subsamples
            if(info.checkSplittedSampleName(job.identifier)): # if multiple entries for one name  (splitted samples) use the identifier to submit
                print '@INFO: Splitted samples: submit through identifier'
                submit(job.identifier,repDict)
            else: submit(job.name,repDict)
    else:
        for sample in samplesList:
            print sample
            submit(sample,repDict)

#Work in progress...
elif opts.task == 'mva_opt_dc':
    total_number_of_steps=1
    setting = ''
    for par in (config.get('Optimisation','parameters').split(',')):
        scan_par=eval(config.get('Optimisation',par))
        setting+=par+'='+str(scan_par[0])+':'
        if len(scan_par) > 1 and scan_par[2] != 0:
            total_number_of_steps+=scan_par[2]
    print setting
    repDict['additional']='OPT_main_set'
    dc = config.get('Optimisation','dc')
    #Still need to launch main
    submit(dc,repDict,False)
    main_setting=setting
    # Scanning all the parameters found in the training config in the Optimisation sector
    for par in (config.get('Optimisation','parameters').split(',')):
        scan_par=eval(config.get('Optimisation',par))
        print par
        if len(scan_par) > 1 and scan_par[2] != 0:
            for step in range(scan_par[2]):
                value = (scan_par[0])+((1+step)*(scan_par[1]-scan_par[0])/scan_par[2])
                print value
                repDict['additional']='OPT_'+par+str(value)
                submit(dc,repDict,False)
                print setting


#os.system('qstat')
if (opts.philipp_love_progress_bars):
    os.system('./qstat.py') 
