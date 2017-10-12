###################################
# python AddBranches.py inputfolder outputfolder
###################################

import os
import subprocess
import ROOT

#_path = '/pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V24/mva_v23_final/'
#done_samples = os.listdir('/pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V24/mva_v23_wBtagW')
_path = '/pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V24/mva_v23_wBtagW/'
done_samples = os.listdir('/pnfs/psi.ch/cms/trivcat/store/user/gaperrin/VHbb/ZllHbb13TeV_V24/mva_v23_wBtagW_NNLO/')

n_simul_jobs = 5
counter = 0

FILE = os.listdir(_path)
applyNNLO = "False"

for file in FILE:
    if not '.root' in file: continue
    #if not 'ST_s-channel_4f_leptonDecays_13TeV-amcatnlo-pythia8_TuneCUETP8M1' in file: continue
    if "ZmmH.BestCSV.heppy.ZH_HToBB_ZToLL_M125_13TeV_powheg_pythia8." in file:
        applyNNLO = "True"
    #if not "ZH_HToBB_ZToLL_M125_13TeV_powheg_pythia8" in file:
    #    continue
    print 'file is', file

    ifile_ = 'root://t3dcachedb03.psi.ch:1094/' + _path + file
    #ofile_ = 'BtagWFiles/'+file
    #for BTag
    #ofile_ = '/scratch/gaperrin/BtagWFiles/'+file
    #for NNLO
    ofile_ = '/scratch/gaperrin/NNLOW/'+file

    #for test
    #command = 'python ElectroweakCorrections.py %s %s %s >output.txt &' %(ifile_, ofile_,applyNNLO)
    #for NNLO weights
    command = 'python ElectroweakCorrections.py %s %s %s 2>&1 > /dev/null &' %(ifile_, ofile_,applyNNLO)
    #subprocess.call('python bTagSF.py %s %s 2>&1 > /dev/null &' %(ifile_, ofile_), shell=True)
    #subprocess.call('python ElectroweakCorrections.py %s %s %s 2>&1 > /dev/null &' %(ifile_, ofile_,applyNNLO), shell=True)
    subprocess.call(command, shell=True)
    print 'command is', command

    counter = int(subprocess.check_output('ps aux | grep $USER | grep bTagSF.py | wc -l', shell=True)) -2
    while counter > n_simul_jobs:
        print 'Counter is', counter, '. Gonna sleeZzz...Zzz...'
        os.system('sleep '+str(30))
        counter = int(subprocess.check_output('ps aux | grep $USER | grep bTagSF.py | wc -l', shell=True)) -2

