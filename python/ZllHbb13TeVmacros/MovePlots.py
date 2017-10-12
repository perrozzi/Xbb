import os
import sys
import shutil
import subprocess

#Read input arguments

args = sys.argv[1:]
if len(args) == 2:
    _input = args[0]
    _output = args[1]
else:
    print 'Error, need two agruments. You have provided', len(args)
    sys.exit(1)

print 'Input folder is', _input
print 'Output folder is', _output

#Move all plots in corresponding subfolders

def MakeSubFolders(_input, RegioList):

    #I am in macro location
    current_ = os.getcwd()
    os.chdir(_input)
    #I am in Plots
    _plotfolder = _input.split('/')[-2]

    if not os.path.isdir(_plotfolder):
        os.mkdir(_plotfolder)

    print 'command is','cp -r '+current_+'/.htaccess ' + _plotfolder + '/'
    subprocess.call('cp -r ../config ' + _plotfolder + '/', shell = True)
    subprocess.call('cp -r '+current_+'/.htaccess ' + _plotfolder + '/', shell = True)
    subprocess.call('cp -r '+current_+'/index.php ' + _plotfolder + '/', shell = True)

    FILE = os.listdir('.')

    #subprocess.call('cp -r ../config .', shell = True)

    for file in FILE:
        #if not 'comp' in file: continue #Skip shape plots
        print 'file is', file
        for name, folder in RegionList:
            if not name in file: continue
            folder2 = os.path.join(_plotfolder,folder)
            if not os.path.isdir(folder2):
                os.mkdir(folder2)
                #subprocess.call('cp -r ../config '+ folder2 + '/', shell = True)
                subprocess.call('cp -r '+current_+'/.htaccess ' + folder2 + '/', shell = True)
                subprocess.call('cp -r '+current_+'/index.php ' + folder2 + '/', shell = True)
            shutil.copy(file,folder2)
            if os.path.isfile('pdf/'+file.replace('png','pdf')):
                shutil.copy('pdf/'+file.replace('png','pdf'), folder2)
            else:
                print 'pdf/'+file.replace('png','pdf'), 'doesn\'t exist'
            if os.path.isfile('root/'+file.replace('png','C')) :
                shutil.copy('root/'+file.replace('png','C'), folder2)
                print 'root is here'
            else:
                print 'root/'+file.replace('png','C'), 'doesn\'t exist'

def MoveSubFolders(_input, _output):
    _plotfolder = _input.split('/')[-2]
    print 'gonna lunch the command'
    #copyCommand = 'scp -r ' + _plotfolder + ' piberger@lxplus.cern.ch:' + _output
    copyCommand = 'scp -r ' + _plotfolder + ' gaperrin@lxplus.cern.ch:' + _output
    print copyCommand
    subprocess.call(copyCommand, shell = True)
    print 'that was delicious!'

RegionList = [('Zll_CRZb_incl__','Zhf_Zll'),('Zll_CRZb_incl_lowpt__','Zhf_Zll_lowpt'),('Zll_CRZb_incl_highpt__','Zhf_Zll_highpt'),\
              ('Zll_CRZlight__','Zlf_Zll'),('Zll_CRZlight_lowpt__','Zlf_Zll_lowpt'),('Zll_CRZlight_highpt__','Zlf_Zll_highpt'),\
              ('Zll_CRttbar__','ttbar_Zll'),('Zll_CRttbar_lowpt__','ttbar_Zll_lowpt'),('Zll_CRttbar_highpt__','ttbar_Zll_highpt'),\
              ('Zee_SR','SR_Zee'),('Zuu_SR','SR_Zuu'),\
              ('Zee_CRZb_incl__','Zhf_Zee'),('Zee_CRZb_incl_lowpt__','Zhf_Zee_lowpt'),('Zee_CRZb_incl_highpt__','Zhf_Zee_highpt'),\
              ('Zee_CRZlight__','Zlf_Zee'),('Zee_CRZlight_lowpt__','Zlf_Zee_incl_lowpt'),('Zee_CRZlight_highpt__','Zlf_Zee_incl_highpt'),\
              ('Zee_CRttbar__','ttbar_Zee'),('Zee_CRttbar_lowpt__','ttbar_Zee_lowpt'),('Zee_CRttbar_highpt__','ttbar_Zee_highpt'),\
              ('Zuu_CRZb_incl__','Zhf_Zuu'),('Zuu_CRZb_incl_lowpt__','Zhf_Zuu_lowpt'),('Zuu_CRZb_incl_highpt__','Zhf_Zuu_highpt'),\
              ('Zuu_CRZlight__','Zlf_Zuu'),('Zuu_CRZlight_lowpt__','Zlf_Zuu_lowpt'),('Zuu_CRZlight_highpt__','Zlf_Zuu_highpt'),\
              ('Zuu_CRttbar__','ttbar_Zuu'),('Zuu_CRttbar_lowpt__','ttbar_Zuu_lowpt'),('Zuu_CRttbar_highpt__','ttbar_Zuu_highpt'),\
              ('Zee_CRZb_incl_new','Zhf_Zee_new'),('Zuu_CRZb_incl_new','Zhf_Zuu_new'),('Zll_CRZb_inclPhi2p3','Zhf_Zll_Phi2p3'),('Zll_CRZb_inclPhi2p5','Zhf_Zll_Phi2p5'),('Zll_CRZb_inclPhi2p5','Zhf_Zll_Phi2p5'),('Zll_CRZlightPhi2p3','Zlf_Zll_Phi2p3'),('Zll_CRZlightPhi2p5','Zlf_Zll_Phi2p5'),('BasicCuts_low','BasicCuts_low'),('BasicCuts_high','BasicCuts_high'),
              ('Zll_BasicCuts','ZBasicCuts_Zll'),\
              ('ZeeBDT_lowpt','ZSR_Zee_lowpt'),('ZeeBDT_highpt','ZSR_Zee_highpt'),('ZuuBDT_lowpt','ZSR_Zuu_lowpt'),('ZuuBDT_highpt','ZSR_Zuu_highpt'),\
              ('ZllBDT__','ZSR_Zll'),('ZllBDT_lowpt__','ZSR_Zll_lowpt'),('ZllBDT_highpt__','ZSR_Zll_highpt')
              ]

MakeSubFolders(_input, RegionList)
MoveSubFolders(_input, _output)

