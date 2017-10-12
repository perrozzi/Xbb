from optparse import OptionParser
import os
import sys
import subprocess
import ROOT

parser = OptionParser()

parser.add_option("-T", "--tag", dest="tag", default="8TeV",
                      help="Tag to run the analysis with, example '8TeV' uses config8TeV and pathConfig8TeV to run the analysis")
parser.add_option("-D", "--datacard", dest="dc_folder", default="",
                      help="Path to the datacards to be ploted")
parser.add_option("-P", "--postfit", dest="postfit", default=True,
                  help="bool. Do you want to plot postfit or not (prefit) ?")
parser.add_option("-L", "--log", dest="log", default=True,
                  help="bool. Do you want to plot in log scale ?")

(opts, args) = parser.parse_args(sys.argv)

print 'Config suffix is', opts.tag
print 'Datacards folder is', opts.dc_folder
opts.tag = opts.tag+'config'

DC = os.listdir(opts.dc_folder)

#List of strings needed to launch the various pre/postfit

#mlfit_ = None
#mlfit_ = True
command_dics = []
mlfit_= None

for file in DC:
    if 'mlfit.root' in file:
        mlfit_ = opts.dc_folder+'/'+file
    if 'mlfit_from_w.root' in file:
        mlfit_ = opts.dc_folder+'/'+file

for file in DC:
    #if '.root' in file: continue
    #if 'M125' in file: continue
    #if '.swp' in file: continue
    #if not 'vhbb_DC_TH_ZuuBDT_highpt' in file and not 'vhbb_DC_TH_BDT_Zuu_HighPt' in file: continue
    #if not 'Mass' in file: continue
    #if not 'ZuuMass_Vptbin2' in file: continue
    #if not 'ZeeMass_Vptbin0' in file:continue
    #if not '.txt' in file and not '.root' in file: continue
    #if not 'vhbb_DC_TH_BDT_Zee_LowPt' in file: continue
    if not '.txt' in file: continue
    if '.swp' in file: continue
    if 'M125' in file: continue
    if not 'vhbb_DC_TH_BDT_Zuu_HighPt' in file: continue
    print '============'
    print 'The file name is', file
    print '============'
    command_dic = {}

    dc_file_ = opts.dc_folder+'/'+file
    #mlfit_= opts.dc_folder+'/'+'mlfit.root'
    dc_bin_ = file.replace('vhbb_DC_TH_','').replace('.txt','')
    dc_bin_ = file.replace('vhbb_dc_TH_','').replace('.txt','')

    #for VV prefit using dc from David
    if 'vhbb_DC_TH_BDT_Zee_LowPt' in file:  dc_bin_ = 'ZeeLowPt_13TeV'
    if 'vhbb_DC_TH_BDT_Zee_HighPt' in file: dc_bin_ = 'ZeeHighPt_13TeV'
    if 'vhbb_DC_TH_BDT_Zuu_LowPt' in file:  dc_bin_ = 'ZuuLowPt_13TeV'
    if 'vhbb_DC_TH_BDT_Zuu_HighPt' in file: dc_bin_ = 'ZuuHighPt_13TeV'

    if 'BDT' in dc_bin_ or 'BDT' in file:
        var_ = 'HCMVAV2_reg_mass'
        #var_ = 'BDTCMVA'
        #var_ = 'BDT'
    elif 'CR' in dc_bin_:
        #var_ = 'HjCSV1_CSV'
        var_ = 'HjMVA1_MVA'
    elif 'Mass' in dc_bin_ and not 'VV' in dc_bin_:
        var_ = 'DijetVHMass'
    elif 'Mass' in dc_bin_ and 'VV' in dc_bin_:
        var_ = 'DijetVVMass'
    else:
        print '@ERROR: neither CR not SR. Aborting'
        sys.exit()

    #dc_bin_ = 'ZuuHighPt_13TeV'

    #blind = 'False'
    blind = 'True'
    if 'BDT' in file:
        blind = 'True'


    command_dic['blind'] = blind
    command_dic['dc_file'] = dc_file_
    command_dic['dc_bin'] =  dc_bin_
    command_dic['var'] =  var_
    command_dic['mlfit'] =  mlfit_
    if eval(opts.postfit):
        command_dic['postfit'] = 'True'
    else:
        command_dic['postfit'] = 'False'
    command_dics.append(command_dic)

#if not mlfit_:
#    print '@ERROR: mlfit.root not found. Aborting'
#    sys.exit()

#Launching all the commands
for command_dic in command_dics:
    suffix = ' -C %s/general.ini -C %s/samples_nosplit.ini -C %s/configPlot_vars  -C %s/datacard.ini -C %s/plots.ini -C %s/paths.ini -C %s/datacards.ini  -C %s/vhbbPlotDef.ini' %(opts.tag, opts.tag, opts.tag,opts.tag,opts.tag,opts.tag,opts.tag,opts.tag)


    ####
    #
    #Prefit from dc (no mlfit)
    command = 'python stack_from_dc_no_mlfit.py -D %s -B %s -F b' %( command_dic['dc_file'], command_dic['dc_bin'])
    command += suffix
    print 'command is', command
    subprocess.call([command], shell=True)
    print 'Postfit command is', command

    ####
    ##Postfit after PostFitShapesFromWorkspace
    #command = 'python stack_from_dc_improved.py -D %s -B %s -M %s -F b -V %s -A False -P True' %( command_dic['dc_file'], command_dic['dc_bin'], command_dic['mlfit'], command_dic['var'])
    #command += suffix
    #print 'command is', command
    #subprocess.call([command], shell=True)
    #print 'Postfit command is', command


    #####
    ##old
    ###########################
    ###prefit
    ##command = 'python stack_from_dcv2.py -D %s -B %s -F b -V %s' %( command_dic['dc_file'], command_dic['dc_bin'], command_dic['var'])
    ##command += suffix
    ###print 'Prefit command is', command
    ##subprocess.call([command], shell=True)

    ###new
    ##command = 'python stack_from_dc_improved.py -D %s -B %s -M %s -F b -V %s -A %s -P %s' %( command_dic['dc_file'], command_dic['dc_bin'], command_dic['mlfit'], command_dic['var'], command_dic['blind'], command_dic['postfit'])
    ##command += suffix
    ####print 'Prefit command is', command
    ##subprocess.call([command], shell=True)
    ###########################

    #command = 'python stack_from_dc_improved.py -D %s -B %s -M %s -F b -V %s -A %s -P %s' %( command_dic['dc_file'], command_dic['dc_bin'], command_dic['mlfit'], command_dic['var'], command_dic['blind'], command_dic['postfit'])
    #command += suffix
    #print 'command is', command
    #subprocess.call([command], shell=True)
    #print 'Postfit command is', command

    ####Using macro from David
    ##if eval(opts.postfit):
    ##    command = 'python stack_from_dc_David.py -D %s -B %s -M %s -F b -V %s -A %s' %( command_dic['dc_file'], command_dic['dc_bin'], command_dic['mlfit'], command_dic['var'], command_dic['blind'])
    ##    print 'ERROR'
    ##    sys.exit()
    ##else:
    ##    #Gael
    ##    #command = 'python stack_from_dc_David.py -D %s -B %s -F b -V %s -A %s' %( command_dic['dc_file'], command_dic['dc_bin'], command_dic['var'], command_dic['blind'])
    ##    #David
    ##    command = 'python stack_from_dc_David.py -D %s -B %s -F b -V %s -A %s' %( command_dic['dc_file'], 'ZuuHighPt_13TeV', command_dic['var'], command_dic['blind'])

    ##command += suffix
    ##print 'command is', command
    ##subprocess.call([command], shell=True)
    ###print 'Postfit command is', command




