#!/usr/bin/env python

import sys,hashlib
import os,subprocess
import ROOT 
import math
import itertools
import shutil
import numpy as np
from array import array
import warnings
warnings.filterwarnings( action='ignore', category=RuntimeWarning, message='creating converter.*' )
ROOT.gROOT.SetBatch(True)
from optparse import OptionParser
from btag_reweight import *
from time import gmtime, strftime
#import pdb

argv = sys.argv
parser = OptionParser()
parser.add_option("-S", "--samples", dest="names", default="", 
                      help="samples you want to run on")
parser.add_option("-C", "--config", dest="config", default=[], action="append",
                      help="configuration defining the plots to make")
parser.add_option("-f", "--filelist", dest="filelist", default="",
                              help="list of files you want to run on")
parser.add_option("-F", "--force", dest="force", action="store_true", help="overwrite existing files")

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

from myutils import BetterConfigParser, ParseInfo, TreeCache, LeptonSF, bTagSF
#from btagSF import BtagSF
#import BtagSF
#from bTagSF import *

print opts.config
config = BetterConfigParser()
config.read(opts.config)
anaTag = config.get("Analysis","tag")
TrainFlag = eval(config.get('Analysis','TrainFlag'))
btagLibrary = config.get('BTagReshaping','library')
samplesinfo=config.get('Directories','samplesinfo')
channel=config.get('Configuration','channel')
print 'channel is', channel

VHbbNameSpace=config.get('VHbbNameSpace','library')
ROOT.gSystem.Load(VHbbNameSpace)
AngLikeBkgs=eval(config.get('AngularLike','backgrounds'))
ang_yield=eval(config.get('AngularLike','yields'))

pathIN = config.get('Directories','SYSin')
pathOUT = config.get('Directories','SYSout')
tmpDir = os.environ["TMPDIR"]

print 'INput samples:\t%s'%pathIN
print 'OUTput samples:\t%s'%pathOUT

applyBTagweights=eval(config.get('Analysis','applyBTagweights'))
print 'applyBTagweights is', applyBTagweights
csv_rwt_hf=config.get('BTagHFweights','file')
csv_rwt_lf=config.get('BTagLFweights','file')
applyRegression=eval(config.get('Regression','applyRegression'))
print 'applyRegression is', applyRegression
#print "csv_rwt_hf",csv_rwt_hf,"csv_rwt_lf",csv_rwt_lf
bweightcalc = BTagWeightCalculator(
    csv_rwt_hf,
    csv_rwt_lf
)
bweightcalc.btag = "btag"

try:
    recomputeVtype = config.get('Analysis', 'Recompute_Vtype').lower().strip() == 'true'
except:
    recomputeVtype = False
print "Recompute Vtype:", recomputeVtype

try:
    stopAfterVtypeCorrection = config.get('Analysis', 'Stop_after_Vtype_correction').lower().strip() == 'true'
except:
    stopAfterVtypeCorrection = False
print "Recompute Vtype only:", stopAfterVtypeCorrection
try:
    Stop_after_BTagweights = config.get('Analysis', 'Stop_after_BTagweights').lower().strip() == 'true'
except:
    Stop_after_BTagweights = False
print "Recompute bTag only:",Stop_after_BTagweights

try:
    applyLepSF = config.get('Analysis', 'applyLepSF').lower().strip() == 'true'
except:
    applyLepSF = False
print "evaluate lepton SF:", applyLepSF
try:
    Stop_after_LepSF = config.get('Analysis', 'Stop_after_LepSF').lower().strip() == 'true'
except:
    Stop_after_LepSF = False
print "Recompute LepSF only:", Stop_after_LepSF
#
try:
    addBranches = config.get('Analysis', 'addBranches').lower().strip() == 'true'
except:
    addBranches = False
print "Adding new variables/branches:", applyLepSF
try:
    Stop_after_addBranches = config.get('Analysis', 'Stop_after_addBranches').lower().strip() == 'true'
except:
    Stop_after_addBranches = False
print "Stop after adding new variables/branches:", Stop_after_LepSF
try:
    AddSpecialWeight = config.get('Analysis', 'AddSpecialWeight').lower().strip() == 'true'
except:
    AddSpecialWeight = False
print "I shall add the specialweight, my Lord !", AddSpecialWeight

try:
    applyJESsystematics= config.get('Analysis', 'applyJESsystematics').lower().strip() == 'true'
except:
    applyJESsystematics = False
print "I shall add the JESsystematics, milord !", applyJESsystematics
try:
    applyJESsystematicsMinMax = config.get('Analysis', 'applyJESsystematicsMinMax').lower().strip() == 'true'
except:
    applyJESsystematicsMinMax = False
print "I shall add the JESsystematics, milord !", applyJESsystematicsMinMax
try:
   addEWK = config.get('Analysis', 'addEWK').lower().strip() == 'true'
except:
   addEWK = False
print "I shall add the EWK weigght, milord !", addEWK
try:
   remove_useless_branch = config.get('Analysis', 'remove_useless_branch').lower().strip() == 'true'
except:
   remove_useless_branch = False
print "I shall remove the useless branches, milord !", remove_useless_branch
try:
   remove_useless_after_sys = config.get('Analysis', 'remove_useless_after_sys').lower().strip() == 'true'
except:
   remove_useless_after_sys = False
print "I shall remove the useless branches after sys, milord !", remove_useless_after_sys
try:
   addTTW= config.get('Analysis', 'addTTW').lower().strip() == 'true'
except:
   addTTW= False
print "I shall add the TT weight, milord !",addTTW
#
try:
   addSBweight= config.get('Analysis', 'addSBweight').lower().strip() == 'true'
except:
   addSBweight= False
print "I shall add the s/(s+b) weight, milord !"


namelist=opts.names.split(',')

#load info
info = ParseInfo(samplesinfo,pathIN)

if addSBweight:
    # Adding all the bin, dc and branch information in a dictionnary. Allows to fill multiple branches in one single loop. Keys of the histo are dc/mlfit_BIN (they are identical for Zll).
    #Order to fill the dic: [BDT_BRANCH, SIGNAL_SHAPES_PATH, SIGNAL_SHAPES_BIN, MLFIT_BIN]

    #For VH
    #PATH_ALL_DC = '/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_7/src/HiggsAnalysis/CombinedLimit/V24/VH_Datacards_02to1_oldJEC/'
    PATH_ALL_DC = '/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_7/src/HiggsAnalysis/CombinedLimit/V24/VH_combo_7_12/ZllHbb_Datacards_Minus08to1_JECfix_7_3/'

    DC_INFO_DIC = {
            'ZeeBDTVH_highpt':['ZllBDT_highptCMVA.Nominal',PATH_ALL_DC+'vhbb_TH_BDT_Zee_HighPt.root', 'ZeeHighPt_13TeV','ZllHbb_ch4_Zee_SIG_high'],
            'ZuuBDTVH_highpt':['ZllBDT_highptCMVA.Nominal',PATH_ALL_DC+'vhbb_TH_BDT_Zuu_HighPt.root','ZuuHighPt_13TeV','ZllHbb_ch3_Zmm_SIG_high'],
            'ZeeBDTVH_lowpt': ['ZllBDT_lowptCMVA.Nominal', PATH_ALL_DC+'vhbb_TH_BDT_Zee_LowPt.root', 'ZeeLowPt_13TeV', 'ZllHbb_ch2_Zee_SIG_low'],
            'ZuuBDTVH_lowpt': ['ZllBDT_lowptCMVA.Nominal', PATH_ALL_DC+'vhbb_TH_BDT_Zuu_LowPt.root', 'ZuuLowPt_13TeV', 'ZllHbb_ch1_Zmm_SIG_low']
            }

    ###
    #DC_INFO_DIC['MLFIT_PATH'] = '/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_7/src/HiggsAnalysis/CombinedLimit/V24/combo200617/VH/mlfitmlfitunblindrUltraSimple.root'
    #DC_INFO_DIC['MLFIT_PATH'] = '/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_7/src/HiggsAnalysis/CombinedLimit/V24/VH_combo_7_12/ZllHbb_Datacards_Minus08to1_JECfix_7_3/'
    DC_INFO_DIC['MLFIT_PATH'] = '/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_7/src/HiggsAnalysis/CombinedLimit/V24/VH_combo_7_12/mlfit.root'

    ##For VV
    #PATH_ALL_DC = '/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_7/src/HiggsAnalysis/CombinedLimit/V24/ZllZbb_Datacards_Minus08to1_JECfix_7_3/'

    #DC_INFO_DIC = {
    #        'ZeeBDT_highpt':['ZllBDTVV_highpt.Nominal',PATH_ALL_DC+'vhbb_TH_BDT_Zee_HighPt.root', 'ZeeHighPt_13TeV','ZllHbb_ch4_Zee_SIG_high'],
    #        'ZuuBDT_highpt':['ZllBDTVV_highpt.Nominal',PATH_ALL_DC+'vhbb_TH_BDT_Zuu_HighPt.root','ZuuHighPt_13TeV','ZllHbb_ch3_Zmm_SIG_high'],
    #        'ZeeBDT_lowpt': ['ZllBDTVV_lowpt.Nominal', PATH_ALL_DC+'vhbb_TH_BDT_Zee_LowPt.root', 'ZeeLowPt_13TeV', 'ZllHbb_ch2_Zee_SIG_low'],
    #        'ZuuBDT_lowpt': ['ZllBDTVV_lowpt.Nominal', PATH_ALL_DC+'vhbb_TH_BDT_Zuu_LowPt.root', 'ZuuLowPt_13TeV', 'ZllHbb_ch1_Zmm_SIG_low']
    #        }

    ###
    #DC_INFO_DIC['MLFIT_PATH'] = '/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_7/src/HiggsAnalysis/CombinedLimit/V24/combo200617/VZ/mlfitmlfitunblindrUltraSimple.root'

    #dc_info_dic = DC_INFO_DIC
    
    def get_shape_bin_edges_dic(dc_info_dic):
        bin_edges_dic = {}
        for key in dc_info_dic:
            if key == 'MLFIT_PATH': continue
            #bin_edges_dic[key] = get_shape_bin_edges(dc_info_dic['MLFIT_PATH'], dc_info_dic[key][3])
            #bin_edges_dic[key] = get_shape_bin_edges(dc_info_dic['MLFIT_PATH'], dc_info_dic[key][3])
            bin_edges_dic[key] = get_shape_bin_edges(dc_info_dic[key][1], dc_info_dic[key][2])
    
        for key in dc_info_dic:
            if key == 'MLFIT_PATH': continue
            dc_info_dic[key].append(bin_edges_dic[key])
    
    def get_total_postfit_shapes_dic(dc_info_dic):
        signal_postfit_dic = {}
        background_postfit_dic = {}
    
        for key in dc_info_dic:
            if key == 'MLFIT_PATH': continue
            signal_postfit_dic[key], background_postfit_dic[key] = get_total_postfit_shapes(dc_info_dic['MLFIT_PATH'],dc_info_dic[key][3], dc_info_dic[key][4])
    
        for key in dc_info_dic:
            if key == 'MLFIT_PATH': continue
            dc_info_dic[key].append(signal_postfit_dic[key])
            dc_info_dic[key].append(background_postfit_dic[key])
    
    def get_shape_bin_edges(shapes_path, datacard_bin):
        """Return an array of the bin edges used by the input shapes.
    
        Parameters
        ----------
        shapes_path : path
            The path to the shapes file.
        datacard_bin : string
            The name of the datacard bin containing the shapes.
    
        Returns
        -------
        bin_edges : numpy.array
            The array of bin edges.
        """
        shapes_file = ROOT.TFile.Open(shapes_path)
        print 'tfile path is', shapes_path
        print 'list of keys'
        #ROOT.gDirectory.GetListOfKeys().ls()
        print 'gonnad cd', datacard_bin
        print shapes_file.cd(datacard_bin)
        shapes = ROOT.gDirectory.GetListOfKeys()
        #print 'list of Keys is', ROOT.gDirectory.GetListOfKeys().ls()
        # Since the nominal and varied shapes share the same binning,
        # take any of the histograms found in the shapes file.
        print 'debug0'
        shape = ROOT.gDirectory.Get(shapes[0].GetName())
        print 'debug'
        bin_edges = np.array(
            [shape.GetXaxis().GetBinLowEdge(i) for i in xrange(1, shape.GetNbinsX() + 1)],
            dtype=np.float64,
        )
        shapes_file.Close()
        print 'bin_edges for datacard_bin is', bin_edges
        #sys.exit()
        return bin_edges
    
    #def get_shape_bin_edges(mlfit_path, datacard_bin):
    #    """Return an array of the bin edges used by the input shapes.
    #
    #    Parameters
    #    ----------
    #    shapes_path : path
    #        The path to the shapes file.
    #    datacard_bin : string
    #        The name of the datacard bin containing the shapes.
    #
    #    Returns
    #    -------
    #    bin_edges : numpy.array
    #        The array of bin edges.
    #    """
    #    #mlfit_file = ROOT.TFile.Open(mlfit_path)
    #    #mlfit_file.cd('shapes_fit_s/{}'.format(datacard_bin))
    #    #shape = ROOT.gDirectory.Get('total_background')
    #    ##total_signal = ROOT.gDirectory.Get('total_background')

    #    #shapes_file = ROOT.TFile.Open(shapes_path)
    #    #print 'list of keys'
    #    #ROOT.gDirectory.GetListOfKeys().ls()
    #    #shapes_file.cd(datacard_bin)
    #    #shapes = ROOT.gDirectory.GetListOfKeys()
    #    #print 'list of Keys is', ROOT.gDirectory.GetListOfKeys().ls()
    #    ## Since the nominal and varied shapes share the same binning,
    #    ## take any of the histograms found in the shapes file.
    #    #shape = ROOT.gDirectory.Get(shapes[0].GetName())
    #    bin_edges = np.array(
    #        [shape.GetXaxis().GetBinLowEdge(i) for i in xrange(1, shape.GetNbinsX() + 1)],
    #        dtype=np.float64,
    #    )
    #    mlfit_file.Close()
    #    print 'bin_edges is', bin_edges
    #    return bin_edges

    
    def get_total_postfit_shapes(mlfit_path, datacard_bin, bin_edges):
        """Retrun the rebinned the postfit shapes for the total
        signal and total background from an mlfit.root file.
    
        Parameters
        ----------
        mlfit_path : path
            The path to the mlfit.root file.
        datacard_bin : string
            The name of the datacard bin containing the shapes.
        bin_edges : numpy.array of float
            An array of bin low edge values used to rebin the postfit shapes.
    
        Returns
        -------
        signal_postfit, background_postfit : tuple of ROOT.TH1F
            The rebinned signal and background postfit shapes.
        """
        print 'mlfit_path is', mlfit_path
        print 'datacard_bin is', datacard_bin
        mlfit_file = ROOT.TFile.Open(mlfit_path)
        mlfit_file.cd('shapes_prefit/{}'.format(datacard_bin))
        total_signal = ROOT.gDirectory.Get('total_signal')
        total_signal.SetDirectory(0)
        mlfit_file.cd('../..')
        #
        mlfit_file.cd('shapes_fit_s/{}'.format(datacard_bin))
        #total_signal = ROOT.gDirectory.Get('total_signal')
        total_background = ROOT.gDirectory.Get('total_background')
        #total_signal.SetDirectory(0)
        total_background.SetDirectory(0)
        mlfit_file.Close()
        signal_postfit = ROOT.TH1F('signal_postfit', '', len(bin_edges) - 1, bin_edges)
        background_postfit = signal_postfit.Clone('background_postfit')
        for i in xrange(1, signal_postfit.GetNbinsX() + 2):
            signal_postfit.SetBinContent(i, total_signal.GetBinContent(i))
            background_postfit.SetBinContent(i, total_background.GetBinContent(i))
        for s in signal_postfit:
            print 's is', s
        for b in background_postfit:
            print 'b is', b

        first_iter = True
        for s, b in zip(signal_postfit,background_postfit):
            if first_iter:
                first_iter = False
                continue
            print 'S/(S+B) weight is', s/(s+b)


        #print 'signal_postfit', signal_postfit
        #print 'background_postfit', background_postfit
        return signal_postfit, background_postfit

    get_shape_bin_edges_dic(DC_INFO_DIC)
    get_total_postfit_shapes_dic(DC_INFO_DIC)
    dc_info_dic = DC_INFO_DIC


def isInside(map_,eta,phi):
    bin_ = map_.FindBin(phi,eta)
    bit = map_.GetBinContent(bin_)
    if bit>0:
        return True
    else:
        return False

def deltaPhi(phi1, phi2): 
    result = phi1 - phi2
    while (result > math.pi): result -= 2*math.pi
    while (result <= -math.pi): result += 2*math.pi
    return result

def deltaR(phi1, eta1, phi2, eta2):
    deta = eta1-eta2
    dphi = deltaPhi(phi1, phi2)
    result = math.sqrt(deta*deta + dphi*dphi)
    return result

def projectionMETOntoJet(met, metphi, jet, jetphi, onlyPositive=True, threshold = math.pi/4.0):

  deltaphi = deltaPhi(metphi, jetphi)
  met_dot_jet = met * jet * math.cos(deltaphi)
  jetsq = jet * jet
  projection = met_dot_jet / jetsq * jet

  if onlyPositive and abs(deltaphi) >= threshold:
      return 0.0
  else:
      return projection

def signal_ewk(GenVbosons_pt):

	SF = 1.
	#print 'Vpt:', GenVbosons_pt
	EWK = [0.932072955817,
	       0.924376254386,
	       0.916552449249,
	       0.909654343838,
	       0.90479110736,
	       0.902244634267,
	       0.89957486928,
	       0.902899199569,
	       0.899314861082,
	       0.89204902646,
	       0.886663993587,
	       0.878915415638,
	       0.870241565009,
	       0.863239359219,
	       0.85727925851,
	       0.849770804948,
	       0.83762562793,
	       0.829982098864,
	       0.81108451152,
	       0.821942287438,
	       0.79,
	       0.79,
	       0.79,
	       0.79,
	       0.79]

	#print EWK[0]
	#print EWK[1]

	if GenVbosons_pt > 0. and GenVbosons_pt < 3000:

		if GenVbosons_pt > 0 and GenVbosons_pt <= 20:
			SF = EWK[0]
		if GenVbosons_pt > 20 and GenVbosons_pt <= 40:
			SF = EWK[1]
		if GenVbosons_pt > 40 and GenVbosons_pt <= 60:
			SF = EWK[2]
		if GenVbosons_pt > 60 and GenVbosons_pt <= 80:
			SF = EWK[3]
		if GenVbosons_pt > 80 and GenVbosons_pt <= 100:
			SF = EWK[4]
		if GenVbosons_pt > 100 and GenVbosons_pt <= 120:
			SF = EWK[5]
		if GenVbosons_pt > 120 and GenVbosons_pt <= 140:
			SF = EWK[6]
		if GenVbosons_pt > 140 and GenVbosons_pt <= 160:
			SF = EWK[7]
		if GenVbosons_pt > 160 and GenVbosons_pt <= 180:
			SF = EWK[8]
		if GenVbosons_pt > 180 and GenVbosons_pt <= 200:
			SF = EWK[9]
		if GenVbosons_pt > 200 and GenVbosons_pt <= 220:
			SF = EWK[10]
		if GenVbosons_pt > 220 and GenVbosons_pt <= 240:
			SF = EWK[11]
		if GenVbosons_pt > 240 and GenVbosons_pt <= 260:
			SF = EWK[12]
		if GenVbosons_pt > 260 and GenVbosons_pt <= 280:
			SF = EWK[13]
		if GenVbosons_pt > 280 and GenVbosons_pt <= 300:
			SF = EWK[14]
		if GenVbosons_pt > 300 and GenVbosons_pt <= 320:
			SF = EWK[15]
		if GenVbosons_pt > 320 and GenVbosons_pt <= 340:
			SF = EWK[16]
		if GenVbosons_pt > 340 and GenVbosons_pt <= 360:
			SF = EWK[17]
		if GenVbosons_pt > 360 and GenVbosons_pt <= 380:
			SF = EWK[18]
		if GenVbosons_pt > 380 and GenVbosons_pt <= 400:
			SF = EWK[19]
		if GenVbosons_pt > 400 and GenVbosons_pt <= 420:
			SF = EWK[20]
		if GenVbosons_pt > 420 and GenVbosons_pt <= 440:
			SF = EWK[21]
		if GenVbosons_pt > 440 and GenVbosons_pt <= 460:
			SF = EWK[22]
		if GenVbosons_pt > 460 and GenVbosons_pt <= 480:
			SF = EWK[23]
		if GenVbosons_pt > 480:
			SF = EWK[24]
		if GenVbosons_pt <= 0:
			SF = 1


	return SF

def signal_ewk_up(GenVbosons_pt):

	SF = 1.
	#print 'Vpt:', GenVbosons_pt
	EWK = [0.933479852292,
	       0.925298220882,
	       0.917622981133,
	       0.91102286158,
	       0.90718076681,
	       0.905350232844,
	       0.90336604675,
	       0.903947932682,
	       0.903377015003,
	       0.897282669087,
	       0.892978480734,
	       0.885729935121,
	       0.878913596976,
	       0.872505666469,
	       0.866859512888,
	       0.860942354659,
	       0.850346790893,
	       0.844431351897,
	       0.829520542725,
	       0.837419206895,
	       0.81,
	       0.81,
	       0.81,
	       0.81,
	       0.81
	       ]

	if GenVbosons_pt > 0. and GenVbosons_pt < 3000:

		if GenVbosons_pt > 0 and GenVbosons_pt <= 20:
			SF = EWK[0]
		if GenVbosons_pt > 20 and GenVbosons_pt <= 40:
			SF = EWK[1]
		if GenVbosons_pt > 40 and GenVbosons_pt <= 60:
			SF = EWK[2]
		if GenVbosons_pt > 60 and GenVbosons_pt <= 80:
			SF = EWK[3]
		if GenVbosons_pt > 80 and GenVbosons_pt <= 100:
			SF = EWK[4]
		if GenVbosons_pt > 100 and GenVbosons_pt <= 120:
			SF = EWK[5]
		if GenVbosons_pt > 120 and GenVbosons_pt <= 140:
			SF = EWK[6]
		if GenVbosons_pt > 140 and GenVbosons_pt <= 160:
			SF = EWK[7]
		if GenVbosons_pt > 160 and GenVbosons_pt <= 180:
			SF = EWK[8]
		if GenVbosons_pt > 180 and GenVbosons_pt <= 200:
			SF = EWK[9]
		if GenVbosons_pt > 200 and GenVbosons_pt <= 220:
			SF = EWK[10]
		if GenVbosons_pt > 220 and GenVbosons_pt <= 240:
			SF = EWK[11]
		if GenVbosons_pt > 240 and GenVbosons_pt <= 260:
			SF = EWK[12]
		if GenVbosons_pt > 260 and GenVbosons_pt <= 280:
			SF = EWK[13]
		if GenVbosons_pt > 280 and GenVbosons_pt <= 300:
			SF = EWK[14]
		if GenVbosons_pt > 300 and GenVbosons_pt <= 320:
			SF = EWK[15]
		if GenVbosons_pt > 320 and GenVbosons_pt <= 340:
			SF = EWK[16]
		if GenVbosons_pt > 340 and GenVbosons_pt <= 360:
			SF = EWK[17]
		if GenVbosons_pt > 360 and GenVbosons_pt <= 380:
			SF = EWK[18]
		if GenVbosons_pt > 380 and GenVbosons_pt <= 400:
			SF = EWK[19]
		if GenVbosons_pt > 400 and GenVbosons_pt <= 420:
			SF = EWK[20]
		if GenVbosons_pt > 420 and GenVbosons_pt <= 440:
			SF = EWK[21]
		if GenVbosons_pt > 440 and GenVbosons_pt <= 460:
			SF = EWK[22]
		if GenVbosons_pt > 460 and GenVbosons_pt <= 480:
			SF = EWK[23]
		if GenVbosons_pt > 480:
			SF = EWK[24]
		if GenVbosons_pt <= 0:
			SF = 1


	return SF

def signal_ewk_down(GenVbosons_pt):

	SF = 1.
	#print 'Vpt:', GenVbosons_pt
	EWK = [0.930666059342,
	       0.923454287889,
	       0.915481917365,
	       0.908285826095,
	       0.90240144791,
	       0.89913903569,
	       0.895783691809,
	       0.895150466456,
	       0.895252707162,
	       0.886815383834,
	       0.88034950644,
	       0.872100896154,
	       0.861569533042,
	       0.853973051969,
	       0.847699004132,
	       0.838599255237,
	       0.824904464966,
	       0.815532845831,
	       0.792648480316,
	       0.806465367982,
	       0.79,
	       0.79,
	       0.79,
	       0.79,
	       0.79
	       ]

	if GenVbosons_pt > 0. and GenVbosons_pt < 3000:

		if GenVbosons_pt > 0 and GenVbosons_pt <= 20:
			SF = EWK[0]
		if GenVbosons_pt > 20 and GenVbosons_pt <= 40:
			SF = EWK[1]
		if GenVbosons_pt > 40 and GenVbosons_pt <= 60:
			SF = EWK[2]
		if GenVbosons_pt > 60 and GenVbosons_pt <= 80:
			SF = EWK[3]
		if GenVbosons_pt > 80 and GenVbosons_pt <= 100:
			SF = EWK[4]
		if GenVbosons_pt > 100 and GenVbosons_pt <= 120:
			SF = EWK[5]
		if GenVbosons_pt > 120 and GenVbosons_pt <= 140:
			SF = EWK[6]
		if GenVbosons_pt > 140 and GenVbosons_pt <= 160:
			SF = EWK[7]
		if GenVbosons_pt > 160 and GenVbosons_pt <= 180:
			SF = EWK[8]
		if GenVbosons_pt > 180 and GenVbosons_pt <= 200:
			SF = EWK[9]
		if GenVbosons_pt > 200 and GenVbosons_pt <= 220:
			SF = EWK[10]
		if GenVbosons_pt > 220 and GenVbosons_pt <= 240:
			SF = EWK[11]
		if GenVbosons_pt > 240 and GenVbosons_pt <= 260:
			SF = EWK[12]
		if GenVbosons_pt > 260 and GenVbosons_pt <= 280:
			SF = EWK[13]
		if GenVbosons_pt > 280 and GenVbosons_pt <= 300:
			SF = EWK[14]
		if GenVbosons_pt > 300 and GenVbosons_pt <= 320:
			SF = EWK[15]
		if GenVbosons_pt > 320 and GenVbosons_pt <= 340:
			SF = EWK[16]
		if GenVbosons_pt > 340 and GenVbosons_pt <= 360:
			SF = EWK[17]
		if GenVbosons_pt > 360 and GenVbosons_pt <= 380:
			SF = EWK[18]
		if GenVbosons_pt > 380 and GenVbosons_pt <= 400:
			SF = EWK[19]
		if GenVbosons_pt > 400 and GenVbosons_pt <= 420:
			SF = EWK[20]
		if GenVbosons_pt > 420 and GenVbosons_pt <= 440:
			SF = EWK[21]
		if GenVbosons_pt > 440 and GenVbosons_pt <= 460:
			SF = EWK[22]
		if GenVbosons_pt > 460 and GenVbosons_pt <= 480:
			SF = EWK[23]
		if GenVbosons_pt > 480:
			SF = EWK[24]
		if GenVbosons_pt <= 0:
			SF = 1

	return SF


def addAdditionalJets(H, tree):
    for i in range(tree.nhjidxaddJetsdR08):
        idx = tree.hjidxaddJetsdR08[i]
        if (idx == tree.hJCidx[0]) or (idx == tree.hJCidx[1]): continue
        addjet = ROOT.TLorentzVector()
        if idx<tree.nJet:
            addjet.SetPtEtaPhiM(tree.Jet_pt[idx],tree.Jet_eta[idx],tree.Jet_phi[idx],tree.Jet_mass[idx])
        H = H + addjet
    return H

def resolutionBias(eta):
    if(eta< 0.5): return 0.052
    if(eta< 1.1): return 0.057
    if(eta< 1.7): return 0.096
    if(eta< 2.3): return 0.134
    if(eta< 5): return 0.28
    return 0

def corrPt(pt,eta,mcPt):
    return 1 ##FIXME
    # return (pt+resolutionBias(math.fabs(eta))*(pt-mcPt))/pt

def corrCSV(btag,  csv, flav):
    if(csv < 0.): return csv
    if(csv > 1.): return csv;
    if(flav == 0): return csv;
    if(math.fabs(flav) == 5): return  btag.ib.Eval(csv)
    if(math.fabs(flav) == 4): return  btag.ic.Eval(csv)
    if(math.fabs(flav) != 4  and math.fabs(flav) != 5): return  btag.il.Eval(csv)
    return -10000


def csvReshape(sh, pt, eta, csv, flav):
    return sh.reshape(float(eta), float(pt), float(csv), int(flav))

def computeSF(weight_SF):
    '''Combines SF of each leg to compute final event SF'''
    weight_SF[0] = (weight[0][0]*weight[1][0])
    weight_SF[1] = ( (weight[0][0]-weight[0][1])*(weight[1][0]-weight[1][1]) )
    weight_SF[2] = ( (weight[0][0]+weight[0][1])*(weight[1][0]+weight[1][1]) )

def computeSF_region(weight_SF_LowEta, weight_SF_HighEta, lep1_eta, lep2_eta, etacut):
    '''Extact the systematics corresponding to computeSF function in different region of eta'''
    if abs(lep1_eta) < etacut and abs(lep2_eta) < etacut:
        #assign sys
        weight_SF_LowEta[0] = ((weight[0][0]-weight[0][1])*(weight[1][0]-weight[1][1]))
        weight_SF_LowEta[1] = ((weight[0][0]+weight[0][1])*(weight[1][0]+weight[1][1]))
        #sys are nom value
        weight_SF_HighEta[0] = (weight[0][0]*weight[1][0])
        weight_SF_HighEta[1] = (weight[0][0]*weight[1][0])

    elif abs(lep1_eta) > etacut and abs(lep2_eta) > etacut:
        #sys are nom value
        weight_SF_LowEta[0] =  (weight[0][0]*weight[1][0])
        weight_SF_LowEta[1] =  (weight[0][0]*weight[1][0])
        #assign sys
        weight_SF_HighEta[0] = ((weight[0][0]-weight[0][1])*(weight[1][0]-weight[1][1])) 
        weight_SF_HighEta[1] = ((weight[0][0]+weight[0][1])*(weight[1][0]+weight[1][1])) 

    elif abs(lep1_eta) < etacut and abs(lep2_eta) > etacut:
        weight_SF_LowEta[0] =  ((weight[0][0]-weight[0][1])*weight[1][0])
        weight_SF_LowEta[1] =  ((weight[0][0]+weight[0][1])*weight[1][0])
        weight_SF_HighEta[0] = ((weight[0][0])*(weight[1][0]-weight[1][1])) 
        weight_SF_HighEta[1] = ((weight[0][0])*(weight[1][0]+weight[1][1])) 

    elif abs(lep1_eta) > etacut and abs(lep2_eta) < etacut:
        weight_SF_LowEta[0] =  ((weight[0][0])*(weight[1][0]-weight[1][1])) 
        weight_SF_LowEta[1] =  ((weight[0][0])*(weight[1][0]+weight[1][1])) 
        weight_SF_HighEta[0] = ((weight[0][0]-weight[0][1])*weight[1][0])
        weight_SF_HighEta[1] = ((weight[0][0]+weight[0][1])*weight[1][0])

def computeSF_leg(leg):
    #leg is the leg index, can be 0 or 1
    eff_leg = [1.,0.,0.]
    eff_leg[0] = (weight[leg][0])
    eff_leg[1] = weight[leg][0]-weight[leg][1]
    eff_leg[2] = weight[leg][0]+weight[leg][1]
    return eff_leg

def computeEventSF_fromleg(effleg1, effleg2):
    #returns event efficiency and relative uncertainty
    eff_event = [1.,0.]
    eff_event[0] = ((effleg1[0][0]**2*effleg2[1][0] + effleg1[1][0]**2*effleg2[0][0])/(effleg1[0][0] + effleg1[1][0]))
    #relative uncertainty down
    uncert_down = (abs(((effleg1[0][1]**2*effleg2[1][1] + effleg1[1][1]**2*effleg2[0][1])/(effleg1[0][1] + effleg1[1][1])) - eff_event[0])/eff_event[0])
    #relative uncertainty up
    uncert_up = (abs(((effleg1[0][2]**2*effleg2[1][2] + effleg1[1][2]**2*effleg2[0][2])/(effleg1[0][2] + effleg1[1][2])) - eff_event[0])/eff_event[0])
    eff_event[1]  = (uncert_down+uncert_up)/2.
    return eff_event

def computeEvenSF_DZ(eff):
    eff_event = [1.,0.]
    eff_event[0] = ((eff[0][0]**2 + eff[1][0]**2)/(eff[0][0] + eff[1][0]))
    #relative uncertainty down
    uncert_down = (((eff[0][1]**2 + eff[1][1]**2)/(eff[0][1] + eff[1][1])) - eff_event[0])/eff_event[0]
    #relative uncertainty up
    uncert_up = (((eff[0][2]**2 + eff[1][2]**2)/(eff[0][2] + eff[1][2])) - eff_event[0])/eff_event[0]
    eff_event[1]  = (uncert_down+uncert_up)/2.
    return eff_event

def getLumiAvrgSF(weightLum1, lum1, weightLum2, lum2, weight_SF):
    ##Take SF for two different run categorie and makes lumi average'''
    #print 'weightLum1[0] is', weightLum1[0]
    #print 'weightLum1[1] is', weightLum1[1]
    #print 'weightLum1[2] is', weightLum1[2]
    #print 'weightLum2[0] is', weightLum2[0]
    #print 'weightLum2[1] is', weightLum2[1]
    #print 'weightLum2[2] is', weightLum2[2]

    weight_SF[0] = weightLum1[0]*lum1+weightLum2[0]*lum2
    weight_SF[1] = weightLum1[1]*lum1+weightLum2[1]*lum2
    weight_SF[2] = weightLum1[2]*lum1+weightLum2[2]*lum2

def computeEff(weight_Eff):
    eff1 = []
    eff2 = []
    eff1.append(weight[0][0])
    eff1.append(weight[0][0]-weight[0][1])
    eff1.append(weight[0][0]+weight[0][1])
    eff2.append(weight[1][0])
    eff2.append(weight[1][0]-weight[1][1])
    eff2.append(weight[1][0]+weight[1][1])
    weight_Eff[0] = (eff1[0]*(1-eff2[0])*eff1[0] + eff2[0]*(1-eff1[0])*eff2[0] + eff1[0]*eff1[0]*eff2[0]*eff2[0])
    weight_Eff[1] = (eff1[1]*(1-eff2[1])*eff1[1] + eff2[1]*(1-eff1[1])*eff2[1] + eff1[1]*eff1[1]*eff2[1]*eff2[1])
    weight_Eff[2] = (eff1[2]*(1-eff2[2])*eff1[2] + eff2[2]*(1-eff1[2])*eff2[2] + eff1[2]*eff1[2]*eff2[2]*eff2[2])
    return weight_Eff

def computeWeight(a, b):
    weight = []
    weight.append([])
    weight.append([])
    for i in range(2):
        weight[i].append(a*muTrigEffBfr[i][0] + b*muTrigEffAftr[i][0])
        weight[i].append(math.sqrt((a*muTrigEffBfr[i][1])**2 + (b*muTrigEffAftr[i][1])**2))
    return weight

#    muTrigEffBfr
#    muTrigEffAftr



if channel == "Znn":
    filt = ROOT.TFile("plot.root")
    NewUnder    = filt.Get("NewUnder")
    NewOver     = filt.Get("NewOver")
    NewUnderQCD = filt.Get("NewUnderQCD")
    NewOverQCD  = filt.Get("NewOverQCD")

for job in info:
    if not job.name in namelist and len([x for x in namelist if x==job.identifier])==0:
        #print 'job.name',job.name,'and job.identifier',job.identifier,'not in namelist',namelist
        continue
    ROOT.gROOT.ProcessLine(
        "struct H {\
        int         HiggsFlag;\
        float         mass;\
        float         pt;\
        float         eta;\
        float         phi;\
        float         dR;\
        float         dPhi;\
        float         dEta;\
        } ;"
    )
    #ROOT.gROOT.ProcessLine(
    #    "struct JET{\
    #    float         pt;\
    #    float         eta;\
    #    int         hadronFlavour;\
    #    float         btag;\
    #    } ;"
    #)
    class Jet :
        def __init__(self, pt, eta, fl, csv) :
            self.pt = pt
            self.eta = eta
            self.hadronFlavour = fl
            self.csv = csv

    
    lhe_weight_map = False if not config.has_option('LHEWeights', 'weights_per_bin') else eval(config.get('LHEWeights', 'weights_per_bin'))
    
    
    print '\t match - %s' %(job.name)
    inputfiles = []
    outputfiles = []
    tmpfiles = []
    if len(filelist) == 0:
        inputfiles.append(pathIN+'/'+job.prefix+job.identifier+'.root')
        print('opening '+pathIN+'/'+job.prefix+job.identifier+'.root')
        tmpfiles.append(tmpDir+'/'+job.prefix+job.identifier+'.root')
        outputfiles.append("%s/%s%s" %(pathOUT,job.prefix,job.identifier+'.root'))
    else:
        for inputFile in filelist:
            subfolder = inputFile.split('/')[-4]
            filename = inputFile.split('/')[-1]
            filename = filename.split('_')[0]+'_'+subfolder+'_'+filename.split('_')[1]
            hash = hashlib.sha224(filename).hexdigest()
            inputFile = "%s/%s/%s" %(pathIN,job.identifier,filename.replace('.root','')+'_'+str(hash)+'.root')
            #if not os.path.isfile(inputFile): continue
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
    
    for inputfile,tmpfile,outputFile in zip(inputfiles,tmpfiles,outputfiles):
        input = ROOT.TFile.Open(inputfile,'read')
        output = ROOT.TFile.Open(tmpfile,'recreate')
        print 'tmp is', tmpfile
        print ''
        print 'inputfile',inputfile
        print "Writing: ",tmpfile
        print 'outputFile',outputFile
        print ''

        # continue if some of the files are not there
        if not input or input.IsZombie():
            print 'file does not exist ==> SKIPPED!'
            continue

        try:
            input.cd()
        except Exception as e:
            print '-'*40
            print 'INPUT:',inputfile
            print 'OUTPUT:',outputFile
            print 'TMP:',tmpfile
            print 'EXCEPTION:',e
            print '-'*40
            continue
        obj = ROOT.TObject
        for key in ROOT.gDirectory.GetListOfKeys():
            input.cd()
            obj = key.ReadObj()
            if obj.GetName() == job.tree:
                continue
            output.cd()
            obj.Write(key.GetName())

        input.cd()
        tree = input.Get(job.tree)
        nEntries = tree.GetEntries()

        H = ROOT.H()
        HNoReg = ROOT.H()
        HaddJetsdR08 = ROOT.H()
        HaddJetsdR08NoReg = ROOT.H()

        if applyLepSF and job.type != 'DATA':
            tree.SetBranchStatus('weight_SF_LooseID',0)
            tree.SetBranchStatus('weight_SF_LooseISO',0)
            tree.SetBranchStatus('weight_SF_LooseIDnISO',0)
            tree.SetBranchStatus('weight_SF_LooseIDnISO_B',0)
            tree.SetBranchStatus('weight_SF_LooseIDnISO_E',0)
            tree.SetBranchStatus('weight_SF_TRK',0)
            tree.SetBranchStatus('weight_SF_Lepton',0)
            tree.SetBranchStatus('eTrigSFWeight_doubleEle80x',0)
            tree.SetBranchStatus('muTrigSFWeight_doublemu',0)

        #Jet structure (to apply CSV weight)
        # For new regresssion zerop the branches out before cloning new tree
        if applyJESsystematics:
            tree.SetBranchStatus('HCMVAV2_reg_mass',0)
            tree.SetBranchStatus('HCMVAV2_reg_pt',0)
            tree.SetBranchStatus('HCMVAV2_reg_eta',0)
            tree.SetBranchStatus('HCMVAV2_reg_phi',0)

            tree.SetBranchStatus('HCMVAV2_reg_mass*',0)
            tree.SetBranchStatus('HCMVAV2_reg_pt*',0)
            tree.SetBranchStatus('HCMVAV2_reg_eta*',0)
            tree.SetBranchStatus('HCMVAV2_reg_phi*',0)
            tree.SetBranchStatus('hJetCMVAV2_pt_reg_0*',0)
            tree.SetBranchStatus('hJetCMVAV2_pt_reg_1*',0)
            tree.SetBranchStatus('hJetCMVAV2_pt_reg*',0)

            tree.SetBranchStatus('HCMVAV2_reg_mass',0)
            tree.SetBranchStatus('HCMVAV2_reg_pt',0)
            tree.SetBranchStatus('HCMVAV2_reg_eta',0)
            tree.SetBranchStatus('HCMVAV2_reg_phi',0)
            tree.SetBranchStatus('hJetCMVAV2_pt_reg_0',0)
            tree.SetBranchStatus('hJetCMVAV2_pt_reg_1',0)
            tree.SetBranchStatus('hJetCMVAV2_pt_reg',0)

        #remove branches
        nBranchesRemoved = 0
        branchList = tree.GetListOfBranches()
        if remove_useless_branch:
            bl_branch = eval(config.get('Branches', 'useless_branch'))
            for br in bl_branch:
                if branchList.FindObject(br):
                    tree.SetBranchStatus(br,0)
                    nBranchesRemoved += 1
        if remove_useless_after_sys:
            bl_branch = eval(config.get('Branches', 'useless_after_sys'))
            for br in bl_branch:
                if branchList.FindObject(br):
                    tree.SetBranchStatus(br,0)
                    nBranchesRemoved += 1
        print "# of branches removed:", nBranchesRemoved

        if addEWK:
            if job.type != 'DATA':
                #In case of redoing, make sure to disable the branches
                tree.SetBranchStatus('EWKw',0)
                tree.SetBranchStatus('NLOw',0)
                tree.SetBranchStatus('DYw',0)
                tree.SetBranchStatus('isDY',0)

        if applyBTagweights:
            tree.SetBranchStatus("bTagWeightCMVAV2_Moriond*",0)

        if addSBweight:
            #tree.SetBranchStatus('sb_weight*', 0)
            bdt_buffer = {}
            leaf_index = {}
            #dc_info_dic = DC_INFO_DIC
            for key in dc_info_dic:
                if key == 'MLFIT_PATH': continue
                bdt_branch = dc_info_dic[key][0]
                if '.' in bdt_branch:
                    branch_name, leaf_name = bdt_branch.split('.')
                    branch = tree.GetBranch(branch_name)
                    n_leaves = branch.GetNleaves()
                    leaf_index[bdt_branch] = [leaf.GetName() for leaf in branch.GetListOfLeaves()].index(leaf_name)
                    bdt_buffer[bdt_branch] = np.zeros(n_leaves, dtype=np.float32)
                else:
                    branch_name = bdt_branch
                    leaf_index[bdt_branch] = None
                    bdt_buffer[bdt_branch] = np.zeros(1, dtype=np.float32)
                    print 'problem'
                    sys.exit()
                tree.SetBranchAddress(branch_name, bdt_buffer[bdt_branch])
        
       # tree.SetBranchStatus('H',0)
        output.cd()
        newtree = tree.CloneTree(0)

        if addSBweight:
            sb_weight_dic = {} 
            for key in dc_info_dic:
                if key == 'MLFIT_PATH': continue
                sb_weight_dic[key] = np.zeros(1, dtype=np.float64)
                #sb_weight = numpy.zeros(1, dtype=numpy.float64)
                newtree.Branch('sb_weight_%s'%key, sb_weight_dic[key], 'sb_weight_%s/D'%key)
                #newtree.Branch('sb_weight', sb_weight, 'sb_weight/D')
            # Cache the Fill method for faster filling.
            #fill_newtree = tree_new.Fill




        if applyBTagweights:
            ROOT.gSystem.Load("./BTagCalibrationStandalone.so")
            #ROOT.gROOT.ProcessLine('.L ../interface/BTagCalibrationStandalone.cpp+')

            # from within CMSSW:
            #ROOT.gSystem.Load('libCondFormatsBTauObjects')

            print '\nCompilation done...\n'

            # CSVv2
            #calib_csv = ROOT.BTagCalibration("csvv2", "./ttH_BTV_CSVv2_13TeV_2016All_36p5_2017_1_10.csv")
            calib_csv = ROOT.BTagCalibration("csvv2", "/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_3/src/Xbb/python/csv/CSVv2_Moriond17_B_H.csv")

            # cMVAv2
            #calib_cmva = ROOT.BTagCalibration("cmvav2", "./ttH_BTV_cMVAv2_13TeV_2016All_36p5_2017_1_26.csv")
            calib_cmva = ROOT.BTagCalibration("cmvav2", "/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_3/src/Xbb/python/csv/cMVAv2_Moriond17_B_H.csv")

            print "\nCalibration Init...\n"

            # map between algo/flavour and measurement type
            sf_type_map = {
                "CSV" : {
                    "file" : calib_csv,
                    "bc" : "comb",
                    "l" : "incl",
                    },
                "CMVAV2" : {
                    "file" : calib_cmva,
                    "bc" : "ttbar",
                    "l" : "incl",
                    }
                }

            # map of calibrators. E.g. btag_calibrators["CSVM_nominal_bc"], btag_calibrators["CSVM_up_l"], ...
            btag_calibrators = {}
            #for algo in ["CSV", "CMVAV2"]:
            #    for wp in [ [0, "L"],[1, "M"], [2,"T"] ]:
            #        for syst in ["central", "up", "down"]:
            #            for fl in ["bc", "l"]:
            #                print "[btagSF]: Loading calibrator for algo:", algo, ", WP:", wp[1], ", systematic:", syst, ", flavour:", fl
            #                btag_calibrators[algo+wp[1]+"_"+syst+"_"+fl] = ROOT.BTagCalibrationReader(sf_type_map[algo]["file"], wp[0], sf_type_map[algo][fl], syst)

            for algo in ["CSV", "CMVAV2"]:
                for syst in ["central", "up_jes", "down_jes", "up_lf", "down_lf", "up_hf", "down_hf", "up_hfstats1", "down_hfstats1", "up_hfstats2", "down_hfstats2", "up_lfstats1", "down_lfstats1", "up_lfstats2", "down_lfstats2", "up_cferr1", "down_cferr1", "up_cferr2", "down_cferr2"]:
                    print "[btagSF]: Loading calibrator for algo:", algo, "systematic:", syst
                    btag_calibrators[algo+"_iterative_"+syst] = ROOT.BTagCalibrationReader(sf_type_map[algo]["file"], 3 , "iterativefit", syst)
            sysRefMap = {}
            sysMap = {}
            sysMap["JESUp"] = "up_jes"
            sysMap["JESDown"] = "down_jes"
            sysMap["LFUp"] = "up_lf"
            sysMap["LFDown"] = "down_lf"
            sysMap["HFUp"] = "up_hf"
            sysMap["HFDown"] = "down_hf"
            sysMap["HFStats1Up"] = "up_hfstats1"
            sysMap["HFStats1Down"] = "down_hfstats1"
            sysMap["HFStats2Up"] = "up_hfstats2"
            sysMap["HFStats2Down"] = "down_hfstats2"
            sysMap["LFStats1Up"] = "up_lfstats1"
            sysMap["LFStats1Down"] = "down_lfstats1"
            sysMap["LFStats2Up"] = "up_lfstats2"
            sysMap["LFStats2Down"] = "down_lfstats2"
            sysMap["cErr1Up"] = "up_cferr1"
            sysMap["cErr1Down"] = "down_cferr1"
            sysMap["cErr2Up"] = "up_cferr2"
            sysMap["cErr2Down"] = "down_cferr2"


            print "\nCalibration Done...\n"


            # depending on flavour, only a sample of systematics matter
            def applies( flavour, syst ):
                if flavour==5 and syst not in ["central", "up_jes", "down_jes",  "up_lf", "down_lf",  "up_hfstats1", "down_hfstats1", "up_hfstats2", "down_hfstats2"]:
                    return False
                elif flavour==4 and syst not in ["central", "up_cferr1", "down_cferr1", "up_cferr2", "down_cferr2" ]:
                    return False
                elif flavour==0 and syst not in ["central", "up_jes", "down_jes", "up_hf", "down_hf",  "up_lfstats1", "down_lfstats1", "up_lfstats2", "down_lfstats2" ]:
                    return False

                return True


            # function that reads the SF
            def get_SF(pt=30., eta=0.0, fl=5, val=0.0, syst="central", algo="CSV", wp="M", shape_corr=False, btag_calibrators=btag_calibrators):

                # no SF for pT<20 GeV or pt>1000 or abs(eta)>2.4
                if abs(eta)>2.4 or pt>1000. or pt<20.:
                    return 1.0

                # the .csv files use the convention: b=0, c=1, l=2. Convert into hadronFlavour convention: b=5, c=4, f=0
                fl_index = min(-fl+5,2)
                # no fl=1 in .csv for CMVAv2 (a bug???)
                #if not shape_corr and "CMVAV2" in algo and fl==4:
                #    fl_index = 0

                if shape_corr:
                    if applies(fl,syst):
                        sf = btag_calibrators[algo+"_iterative_"+syst].eval(fl_index ,eta, pt, val)
                        #print 'shape_corr SF:', sf
                        return sf
                    else:
                        sf = btag_calibrators[algo+"_iterative_central"].eval(fl_index ,eta, pt, val)
                        #print 'shape_corr for central SF:', sf
                        return sf


                # pt ranges for bc SF: needed to avoid out_of_range exceptions
                pt_range_high_bc = 670.-1e-02 if "CSV" in algo else 320.-1e-02
                pt_range_low_bc = 30.+1e-02

                # b or c jets
                if fl>=4:
                    # use end_of_range values for pt in [20,30] or pt in [670,1000], with double error
                    out_of_range = False
                    if pt>pt_range_high_bc or pt<pt_range_low_bc:
                        out_of_range = True
                    pt = min(pt, pt_range_high_bc)
                    pt = max(pt, pt_range_low_bc)
                    sf = btag_calibrators[algo+wp+"_"+syst+"_bc"].eval(fl_index ,eta, pt)
                    # double the error for pt out-of-range
                    if out_of_range and syst in ["up","down"]:
                        sf = max(2*sf - btag_calibrators[algo+wp+"_central_bc"].eval(fl_index ,eta, pt), 0.)
                    #print sf
                    return sf
                # light jets
                else:
                    sf = btag_calibrators[algo+wp+"_"+syst+"_l"].eval( fl_index ,eta, pt)
                    #print sf
                    return  sf

            def get_event_SF(ptmin, ptmax, etamin, etamax, jets=[], syst="central", algo="CSV", btag_calibrators=btag_calibrators):
                weight = 1.0

                #print 'gonna add the jet SF'
                for jet in jets:
                    #print 'ptmin', ptmin, 'ptmax', ptmax, 'etamin', etamin, 'etamax', etamax
                    #print 'jet: pt', jet.pt, 'eta', jet.eta
                    if (jet.pt > ptmin and jet.pt < ptmax and abs(jet.eta) > etamin and abs(jet.eta) < etamax):
                        #print syst, '!'
                        weight *= get_SF(pt=jet.pt, eta=jet.eta, fl=jet.hadronFlavour, val=jet.csv, syst=syst, algo=algo, wp="", shape_corr=True, btag_calibrators=btag_calibrators)
                    else:
                        #print 'central !'
                        weight *= get_SF(pt=jet.pt, eta=jet.eta, fl=jet.hadronFlavour, val=jet.csv, syst="central", algo=algo, wp="", shape_corr=True, btag_calibrators=btag_calibrators)
                    #print 'weight is', weight
                return weight
            #class Jet :
            #    def __init__(self, pt, eta, fl, csv) :
            #        self.pt = pt
            #        self.eta = eta
            #        self.hadronFlavour = fl
            #        self.csv = csv
            def MakeSysRefMap():
                sysRefMap["JESUp"] = tree.btagWeightCSV_up_jes
                sysRefMap["JESDown"] = tree.btagWeightCSV_down_jes
                sysRefMap["LFUp"] = tree.btagWeightCSV_up_lf
                sysRefMap["LFDown"] = tree.btagWeightCSV_down_lf
                sysRefMap["HFUp"] = tree.btagWeightCSV_up_hf
                sysRefMap["HFDown"] = tree.btagWeightCSV_down_hf
                sysRefMap["HFStats1Up"] = tree.btagWeightCSV_up_hfstats1
                sysRefMap["HFStats1Down"] = tree.btagWeightCSV_down_hfstats1
                sysRefMap["HFStats2Up"] = tree.btagWeightCSV_up_hfstats2
                sysRefMap["HFStats2Down"] = tree.btagWeightCSV_down_hfstats2
                sysRefMap["LFStats1Up"] = tree.btagWeightCSV_up_lfstats1
                sysRefMap["LFStats1Down"] = tree.btagWeightCSV_down_lfstats1
                sysRefMap["LFStats2Up"] = tree.btagWeightCSV_up_lfstats2
                sysRefMap["LFStats2Down"] = tree.btagWeightCSV_down_lfstats2
                sysRefMap["cErr1Up"] = tree.btagWeightCSV_up_cferr1
                sysRefMap["cErr1Down"] = tree.btagWeightCSV_down_cferr1
                sysRefMap["cErr2Up"] = tree.btagWeightCSV_up_cferr2
                sysRefMap["cErr2Down"] = tree.btagWeightCSV_down_cferr2
            # Add bTag weights. Stole code from David
            # https://github.com/dcurry09/v25Heppy/blob/master/python/bTagSF.py
            # see "VHbb btagWeight Macro" mail from 13/02/2017
            if job.type != 'DATA':
                bTagWeights = {}
                bTagWeights["bTagWeightCMVAV2_Moriond"] = np.zeros(1, dtype=float)
                newtree.Branch("bTagWeightCMVAV2_Moriond", bTagWeights["bTagWeightCMVAV2_Moriond"], "bTagWeightCMVAV2_Moriond/D")
                for syst in ["JES", "LF", "HF", "LFStats1", "LFStats2", "HFStats1", "HFStats2", "cErr1", "cErr2"]:
                    for sdir in ["Up", "Down"]:

                        bTagWeights["bTagWeightCMVAV2_Moriond_"+syst+sdir] = np.zeros(1, dtype=float)
                        newtree.Branch("bTagWeightCMVAV2_Moriond_"+syst+sdir, bTagWeights["bTagWeightCMVAV2_Moriond_"+syst+sdir], "bTagWeightCMVAV2_Moriond_"+syst+sdir+"/D")

                        #bTagWeights["bTagWeightCSV_Moriond_"+syst+sdir] = np.zeros(1, dtype=float)
                        #newtree.Branch("bTagWeightCSV_Moriond_"+syst+sdir, bTagWeights["bTagWeightCSV_Moriond_"+syst+sdir], "bTagWeightCSV_Moriond_"+syst+sdir+"/D")

                        for ipt in range(0,5):
                            for ieta in range(1,4):
                                bTagWeights["bTagWeightCMVAV2_Moriond_"+syst+"_pt"+str(ipt)+"_eta"+str(ieta)+sdir] = np.zeros(1, dtype=float)
                                newtree.Branch("bTagWeightCMVAV2_Moriond_"+syst+"_pt"+str(ipt)+"_eta"+str(ieta)+sdir, bTagWeights["bTagWeightCMVAV2_Moriond_"+syst+"_pt"+str(ipt)+"_eta"+str(ieta)+sdir], "bTagWeightCMVAV2_Moriond_"+syst+"_pt"+str(ipt)+"_eta"+str(ieta)+sdir+"/D")

                        ##remove old branches
                        #for systcat in ["HighCentral","LowCentral","HighForward","LowForward"]:
                        #    tree.SetBranchStatus("bTagWeightCMVAV2_Moriond_"+syst+systcat+sdir,0)
                        #OLD
                        #for systcat in ["HighCentral","LowCentral","HighForward","LowForward"]:

                        #    bTagWeights["bTagWeightCMVAV2_Moriond_"+syst+systcat+sdir] = np.zeros(1, dtype=float)
                        #    newtree.Branch("bTagWeightCMVAV2_Moriond_"+syst+systcat+sdir, bTagWeights["bTagWeightCMVAV2_Moriond_"+syst+systcat+sdir], "bTagWeightCMVAV2_Moriond_"+syst+systcat+sdir+"/D")

                        #    #bTagWeights["bTagWeightCSV_Moriond_"+syst+systcat+sdir] = np.zeros(1, dtype=float)
                        #    #newtree.Branch("bTagWeightCSV_Moriond_"+syst+systcat+sdir, bTagWeights["bTagWeightCSV_Moriond_"+syst+systcat+sdir], "bTagWeightCSV_Moriond_"+syst+systcat+sdir+"/D")


    ######################
    #Include JES spliting#

        if applyJESsystematics:
            doGroup = False
            isVerbose = False
            #isVerbose = True

            #regWeight = './reg/ttbar-G25-500k-13d-300t.weights.xml'
            regWeight = './reg/gravall-v25.weights.xml'
            #regWeight = './reg/TMVARegression_BDTG.weights.xml'
            regVars = ["Jet_pt",
                       "nPVs",
                       "Jet_eta",
                       "Jet_mt",
                       "Jet_leadTrackPt",
                       "Jet_leptonPtRel",
                       "Jet_leptonPt",
                       "Jet_leptonDeltaR",
                       "Jet_neHEF",
                       "Jet_neEmEF",
                       "Jet_vtxPt",
                       "Jet_vtxMass",
                       "Jet_vtx3dL",
                       "Jet_vtxNtrk",
                       "Jet_vtx3deL"
                       #"met_pt",
                       #"Jet_met_proj"
                       ]
            regDict = {"Jet_pt":"Jet_pt[hJCMVAV2idx[0]]",
                       #"Jet_corr":"Jet_corr[hJCMVAV2idx[0]]"
                       "nPVs":"nPVs",
                       "Jet_eta":"Jet_eta[hJCMVAV2idx[0]]",
                       "Jet_mt":"Jet_mt[hJCMVAV2idx[0]]",
                       "Jet_leadTrackPt": "Jet_leadTrackPt[hJCMVAV2idx[0]]",
                       "Jet_leptonPtRel":"Jet_leptonPtRel[hJCMVAV2idx[0]]",
                       "Jet_leptonPt":"Jet_leptonPt[hJCMVAV2idx[0]]",
                       "Jet_leptonDeltaR":"Jet_leptonDeltaR[hJCMVAV2idx[0]]",
                       "Jet_neHEF":"Jet_neHEF[hJCMVAV2idx[0]]",
                       "Jet_neEmEF":"Jet_neEmEF[hJCMVAV2idx[0]]",
                       "Jet_vtxPt":"Jet_vtxPt[hJCMVAV2idx[0]]",
                       "Jet_vtxMass":"Jet_vtxMass[hJCMVAV2idx[0]]",
                       "Jet_vtx3dL":"Jet_vtx3dl[hJCMVAV2idx[0]]",
                       "Jet_vtxNtrk":"Jet_vtxNtrk[hJCMVAV2idx[0]]",
                       "Jet_vtx3deL":"Jet_vtx3deL[hJCMVAV2idx[0]]"
                       #"met_pt":"met_pt[hJCMVAV2idx[0]]",
                       #"Jet_met_proj":"Jet_met_proj[hJCMVAV2idx[0]]"
                       }
            if doGroup:
                JECsys = [
                    "JER",
                    "PileUp",
                    "Relative",
                    "AbsoluteMisc"
                    ]
                JECsysGroupDict = {
                    "PileUp": ["PileUpDataMC",
                               "PileUpPtRef",
                               "PileUpPtBB",
                               "PileUpPtEC1",
                               "PileUpPtEC2",
                               "PileUpPtHF"],
                    "Relative": ["RelativeJEREC1",
                                 "RelativeJEREC2",
                                 "RelativeJERHF",
                                 "RelativeFSR",
                                 "RelativeStatFSR",
                                 "RelativeStatEC",
                                 "RelativeStatHF",
                                 "RelativePtBB",
                                 "RelativePtEC1",
                                 "RelativePtEC2",
                                 "RelativePtHF"],
                    "AbsoluteMisc": [ "AbsoluteScale",
                                      "AbsoluteMPFBias",
                                      "AbsoluteStat",
                                      "SinglePionECAL",
                                      "SinglePionHCAL",
                                      "Fragmentation",
                                      "TimePtEta",
                                      "FlavorQCD"]
                    }
            else:
                JECsys = [
                    "JER",
                    "PileUpDataMC",
                    "PileUpPtRef",
                    "PileUpPtBB",
                    "PileUpPtEC1",
                    #"PileUpPtEC2",
                    #"PileUpPtHF",
                    "RelativeJEREC1",
                    #"RelativeJEREC2",
                    #"RelativeJERHF",
                    "RelativeFSR",
                    "RelativeStatFSR",
                    "RelativeStatEC",
                    #"RelativeStatHF",
                    "RelativePtBB",
                    "RelativePtEC1",
                    #"RelativePtEC2",
                    #"RelativePtHF",
                    "AbsoluteScale",
                    "AbsoluteMPFBias",
                    "AbsoluteStat",
                    "SinglePionECAL",
                    "SinglePionHCAL",
                    "Fragmentation",
                    "TimePtEta",
                    "FlavorQCD"
                    ]


            JEC_systematics = {}

            hJ = ROOT.TLorentzVector()
            hJ0 = ROOT.TLorentzVector()
            hJ1 = ROOT.TLorentzVector()



            VarList = ['HCMVAV2_reg_mass','HCMVAV2_reg_pt','HCMVAV2_reg_eta','HCMVAV2_reg_phi','hJetCMVAV2_pt_reg_0','hJetCMVAV2_pt_reg_1','hJetCMVAV2_pt_reg']

            for var in VarList:
                if not var == 'hJetCMVAV2_pt_reg':
                    JEC_systematics[var] = np.zeros(1, dtype=float)
                    newtree.Branch(var, JEC_systematics[var], var+'/D')
                    #disable old branch in case of rerunning
                    tree.SetBranchStatus(var,0)
                else:
                    #disable old branch in case of rerunning
                    JEC_systematics[var] = np.zeros(21, dtype=float)
                    newtree.Branch(var, JEC_systematics[var], var+'[21]/D')
                    tree.SetBranchStatus(var,0)

            if job.type != 'DATA':
                for syst in JECsys:
                    for sdir in ["Up", "Down"]:
                        for var in VarList:
                            #if not 'hJet' in var:
                            if not var == 'hJetCMVAV2_pt_reg':
                                JEC_systematics[var+"_corr"+syst+sdir] = np.zeros(1, dtype=float)
                                newtree.Branch(var+"_corr"+syst+sdir, JEC_systematics[var+"_corr"+syst+sdir], var+"_corr"+syst+sdir+"/D")
                                #disable old branch in case of rerunning
                                tree.SetBranchStatus(var+"_corr"+syst+sdir,0)
                            else:
                                JEC_systematics[var+"_corr"+syst+sdir] = np.zeros(21, dtype=float)
                                newtree.Branch(var+"_corr"+syst+sdir, JEC_systematics[var+"_corr"+syst+sdir], var+"_corr"+syst+sdir+"[21]/D")
                                #disable old branch in case of rerunning
                                tree.SetBranchStatus(var+"_corr"+syst+sdir,0)
            ##Compute MinMax
            ###Those branches will Max/Minimise the systematic values. Used to speed-up th dc step
            JEC_systematicsMinMax = {}
            VarList = ['HCMVAV2_reg_mass','HCMVAV2_reg_pt','HCMVAV2_reg_eta','HCMVAV2_reg_phi','hJetCMVAV2_pt_reg_0','hJetCMVAV2_pt_reg_1']
            if job.type != 'DATA':
                for bound in ["Min", "Max"]:
                    for var in VarList:
                        JEC_systematicsMinMax[var+"_corr_"+bound] = np.zeros(1, dtype=float)
                        newtree.Branch(var+"_corr_"+bound, JEC_systematicsMinMax[var+"_corr_"+bound], var+"_corr_"+bound+"/D")

            # define all the readers
            TMVA_reader = {}
            theVars = {}

            TMVA_reader['readerJet'] = ROOT.TMVA.Reader("!Color:!Silent" )

            #add a dictionary of containing array of the vars in the TMVAreader
            def addVarsToReader(reader,theVars):
                    for key in regVars:
                        #print key
                        #var = regDict[key]
                        theVars[key] = array( 'f', [ 0 ] )
                        reader.AddVariable(key,theVars[key])
                    return

            # Init the TMVA readers
            addVarsToReader(TMVA_reader['readerJet'],theVars)
            TMVA_reader['readerJet'].BookMVA("readerJet", regWeight)

            print '\n\t ----> Evaluating Regression on sample....'

            #print tree

        #if applyJESsystematicsMinMax:
        #    JEC_systematicsMinMax = {}
        #    VarList = ['HCMVAV2_reg_mass','HCMVAV2_reg_pt','HCMVAV2_reg_eta','HCMVAV2_reg_phi','hJetCMVAV2_pt_reg_0','hJetCMVAV2_pt_reg_1']
        #    if job.type != 'DATA':
        #        for bound in ["Min", "Max"]:
        #            for var in VarList:
        #                JEC_systematicsMinMax[var+"_corr_"+bound] = np.zeros(1, dtype=float)
        #                newtree.Branch(var+"_corr_"+bound, JEC_systematicsMinMax[var+"_corr_"+bound], var+"_corr_"+bound+"/D")

        if applyLepSF and job.type != 'DATA':

            #
            #end to include bTag weights
            #

            ########################################
            # Add  Lepton SF
            ########################################

            #ID(will be 1 for electron)
            weight_SF_LooseID= array('f',[0]*3)
            weight_SF_LooseID[0], weight_SF_LooseID[1], weight_SF_LooseID[2] = 1,0,0
            newtree.Branch('weight_SF_LooseID',weight_SF_LooseID,'weight_SF_LooseID[3]/F')
            #ISO (will be 1 for electron)
            weight_SF_LooseISO = array('f',[0]*3)
            weight_SF_LooseISO[0], weight_SF_LooseISO[1], weight_SF_LooseISO[2] = 1,0,0
            newtree.Branch('weight_SF_LooseISO',weight_SF_LooseISO,'weight_SF_LooseISO[3]/F')
            #ID and ISO
            weight_SF_LooseIDnISO = array('f',[0]*3)
            weight_SF_LooseIDnISO[0], weight_SF_LooseIDnISO[1], weight_SF_LooseIDnISO[2] = 1,0,0
            newtree.Branch('weight_SF_LooseIDnISO',weight_SF_LooseIDnISO,'weight_SF_LooseIDnISO[3]/F')
            #Split MVAID sys in barrel or endcap
            #Barrel
            weight_SF_LooseIDnISO_B = array('f',[0]*2)
            weight_SF_LooseIDnISO_B[0], weight_SF_LooseIDnISO_B[1] = 0,0
            newtree.Branch('weight_SF_LooseIDnISO_B',weight_SF_LooseIDnISO_B,'weight_SF_LooseIDnISO_B[2]/F')
            #Endcap
            weight_SF_LooseIDnISO_E = array('f',[0]*2)
            weight_SF_LooseIDnISO_E[0], weight_SF_LooseIDnISO_E[1] = 0,0
            newtree.Branch('weight_SF_LooseIDnISO_E',weight_SF_LooseIDnISO_E,'weight_SF_LooseIDnISO_E[2]/F')

            #Tracker
            weight_SF_TRK= array('f',[0]*3)
            weight_SF_TRK[0], weight_SF_TRK[1], weight_SF_TRK[2] = 1,0,0
            newtree.Branch('weight_SF_TRK',weight_SF_TRK,'weight_SF_TRK[3]/F')
            #Lepton (contains all the SF)
            weight_SF_Lepton = array('f',[0]*3)
            weight_SF_Lepton[0],  weight_SF_Lepton[1],  weight_SF_Lepton[2] = 1,0,0
            newtree.Branch('weight_SF_Lepton',weight_SF_Lepton,'weight_SF_Lepton[3]/F')
            #double electron Trig
            eTrigSFWeight_doubleEle80x = array('f',[0]*3)
            eTrigSFWeight_doubleEle80x[0], eTrigSFWeight_doubleEle80x[1], eTrigSFWeight_doubleEle80x[2] = 1,0,0
            newtree.Branch('eTrigSFWeight_doubleEle80x', eTrigSFWeight_doubleEle80x, 'eTrigSFWeight_doubleEle80x[3]/F')
            #double muon Trig
            muTrigSFWeight_doublemu= array('f',[0]*3)
            muTrigSFWeight_doublemu[0], muTrigSFWeight_doublemu[1], muTrigSFWeight_doublemu[2] = 1,0,0
            newtree.Branch('muTrigSFWeight_doublemu', muTrigSFWeight_doublemu, 'muTrigSFWeight_doublemu[3]/F')

            #V24
            ##Loose ISO+ID SF
            ##muon iso (wrong in the nutples)
            #weight_SF_LooseISO = array('f',[0]*3)
            #weight_SF_LooseISO[0], weight_SF_LooseISO[1], weight_SF_LooseISO[2] = 1,1,1
            #newtree.Branch('weight_SF_LooseISO',weight_SF_LooseISO,'weight_SF_LooseISO[3]/F')
            #   #electron MVAID (wrong in the ntuples)
            #weight_SF_LooseMVAID_BCD = array('f',[0]*3)
            #weight_SF_LooseMVAID_BCD[0], weight_SF_LooseMVAID_BCD[1], weight_SF_LooseMVAID_BCD[2] = 1,1,1
            #newtree.Branch('weight_SF_LooseMVAID_BCD',weight_SF_LooseMVAID_BCD,'weight_SF_LooseMVAID_BCD[3]/F')
            #   #
            #weight_SF_LooseMVAID_BCDEF = array('f',[0]*3)
            #weight_SF_LooseMVAID_BCDEF[0], weight_SF_LooseMVAID_BCDEF[1], weight_SF_LooseMVAID_BCDEF[2] = 1,1,1
            #newtree.Branch('weight_SF_LooseMVAID_BCDEF',weight_SF_LooseMVAID_BCDEF,'weight_SF_LooseMVAID_BCDEF[3]/F')
            ##Lepton trigger
            #   #electron
            #weight_Eff_eletriglooseBCD = array('f',[0]*3)
            #weight_Eff_eletriglooseBCD[0], weight_Eff_eletriglooseBCD[1], weight_Eff_eletriglooseBCD[2] = 1,1,1
            #newtree.Branch('weight_Eff_eletriglooseBCD',weight_Eff_eletriglooseBCD,'weight_Eff_eletriglooseBCD[3]/F')
            #weight_Eff_eletriglooseBCDEF = array('f',[0]*3)
            #weight_Eff_eletriglooseBCDEF[0], weight_Eff_eletriglooseBCDEF[1], weight_Eff_eletriglooseBCDEF[2] = 1,1,1
            #newtree.Branch('weight_Eff_eletriglooseBCDEF',weight_Eff_eletriglooseBCDEF,'weight_Eff_eletriglooseBCDEF[3]/F')
            #   #pt23
            #weight_Eff_eletrigloosept23 = array('f',[0]*3)
            #weight_Eff_eletrigloosept23[0], weight_Eff_eletrigloosept23[1], weight_Eff_eletrigloosept23[2] = 1,1,1
            #newtree.Branch('weight_Eff_eletrigloosept23',weight_Eff_eletrigloosept23,'weight_Eff_eletrigloosept23[3]/F')
            #   #muon
            #   #for ICHEP dataset
            #weight_Eff_mutriglooseICHEP = array('f',[0]*3)
            #weight_Eff_mutriglooseICHEP[0], weight_Eff_mutriglooseICHEP[1], weight_Eff_mutriglooseICHEP[2]= 1,1,1
            #newtree.Branch('weight_Eff_mutriglooseICHEP',weight_Eff_mutriglooseICHEP,'weight_Eff_mutriglooseICHEP[3]/F')
            #   #for full 22/fb dataset
            #weight_Eff_mutrigloose = array('f',[0]*3)
            #weight_Eff_mutrigloose[0], weight_Eff_mutrigloose[1], weight_Eff_mutrigloose[2] = 1,1,1
            #newtree.Branch('weight_Eff_mutrigloose',weight_Eff_mutrigloose,'weight_Eff_mutrigloose[3]/F')
            #   #Trk:
            #      #electron
            #weight_trk_electron = array('f',[0]*3)
            #weight_trk_electron[0], weight_trk_electron[1], weight_trk_electron[2] = 1,1,1
            #newtree.Branch('weight_trk_electron',weight_trk_electron,'weight_trk_electron[3]/F')
            #   #final weight (without triggers):
            #muweight = array('f',[0]*3)
            #muweight[0], muweight[1], muweight[2] = 1,1,1
            #newtree.Branch('muweight',muweight,'muweight[3]/F')
            #eleweight= array('f',[0]*3)
            #eleweight[0], eleweight[1], eleweight[2] = 1,1,1
            #newtree.Branch('eleweight',eleweight,'eleweight[3]/F')

        if addEWK:
            if job.type != 'DATA':
                #tree.SetBranchStatus('EWKw',0)
                #tree.SetBranchStatus('NLOw',0)
                #tree.SetBranchStatus('DYw',0)
                #tree.SetBranchStatus('isDY',0)

                #EWK weights
                EWKw = array('f',[0]*3)
                EWKw[0], EWKw[1], EWKw[2]= 1,1,1
                newtree.Branch('EWKw',EWKw,'EWKw[3]/F')

                #NLO weights
                NLOw = array('f',[0])
                NLOw[0] = 1
                newtree.Branch('NLOw',NLOw,'NLOw/F')

                #DY_weight. Are the product of the three weights declared above
                DYw= array('f',[0])
                DYw[0] = 1
                newtree.Branch('DYw',DYw,'DYw/F')

                #isDY: to identify what kind of DY sample it is
                isDY = array('i',[-1])
                DYw[0] = -1
                newtree.Branch('isDY', isDY, 'isDY/I')

        if addTTW:
            if job.type != 'DATA':
                #TT  weights
                TTW = array('f',[0])
                TTW[0] = 1
                newtree.Branch('TTW',TTW,'TTW/F')


        if addBranches:

            ### Adding new variable from configuration ###
            newVariableNames = []

            writeNewVariables = eval(config.get("Regression","writeNewVariables"))

            newVariableDefs = writeNewVariables.keys()
            newVariableNames = []
            newVariables = {}
            newVariableFormulas = {}
            newVariableLengths = {}
            for variable in newVariableDefs:
                # parse definition
                variableName = variable
                variableType = 'F'
                if '/' in variable:
                    variableName = variable.split('/')[0]
                    variableType = variable.split('/')[-1]
                variableLength = 1
                if '[' in variableName:
                    variableLength = int(variableName.split('[')[1].strip(']'))
                    variableName = variableName.split('[')[0].strip()

                formula = writeNewVariables[variable]
                print "adding variable ",variableName,", length", variableLength, " type",variableType," using formula",formula," .",
                newVariables[variableName] = array(variableType.lower(),[0]*variableLength)  #type: f

                # build variable definition for tree
                variableDef = variableName
                if variableLength > 1:
                    variableDef += '[%d]'%variableLength
                variableDef += '/' + variableType

                # add variable to tree
                newtree.Branch(variableName,newVariables[variableName],variableDef)
                newVariableFormulas[variableName] =ROOT.TTreeFormula(variableName,formula,tree)
                print "done."
                newVariableNames.append(variableName)
                newVariableLengths[variableName] = variableLength

        if AddSpecialWeight and job.type != 'DATA':
            DY_specialWeight= array('f',[0])
            DY_specialWeight[0] = 1
            newtree.Branch('DY_specialWeight',DY_specialWeight,'DY_specialWeight/F')


        if recomputeVtype:
            ### new branches for Vtype correction ###
            Vtype_new = array('f', [0])
            newtree.Branch('Vtype_new', Vtype_new, 'Vtype_new/F')

            vLeptonsBranches = {}
            VBranches = {}
            ##define Vleptons branch
            vLeptonsvar = ['pt', 'eta', 'phi', 'mass', 'relIso03', 'relIso04']
            for var in vLeptonsvar:
                vLeptonsBranches[var] = np.zeros(21, dtype=np.float32)
                obranch = newtree.Branch('vLeptons_new_%s'%var, vLeptonsBranches[var], 'vLeptons_new_%s[2]/F'%var)

            ##define Vleptons branch
            Vvar = ['pt', 'eta', 'phi', 'mass']
            LorentzDic = {'pt':'Pt', 'eta':'Eta', 'phi':'Phi', 'mass':'M'}
            for var in Vvar:
                #vLeptonsBranches[var] = np.array([0]*2, dtype=float)
                VBranches[var] = np.zeros(21, dtype=np.float32)
                obranch = newtree.Branch('V_new_%s'%var, VBranches[var], 'V_new_%s/F'%var)

            #include the Vytpe reco here
            zEleSelection = lambda x : tree.selLeptons_pt[x] > 15 and tree.selLeptons_eleMVAIdSppring16GenPurp[x] >= 1
            zMuSelection = lambda x : tree.selLeptons_pt[x] > 15 and  tree.selLeptons_looseIdPOG[x] and tree.selLeptons_relIso04[x] < 0.25

        #count number of corrected events
        n_vtype_changed = 0
        n_vtype_unchanged = 0
        n_vtype_events_skipped = 0

        print 'starting event loop, processing',str(nEntries),'events'
        j_out=1;

        #########################
        #Start event loop
        #########################

        for entry in range(0,nEntries):
                if ((entry%j_out)==0):
                    if ((entry/j_out)==9 and j_out < 1e4): j_out*=10;
                    print strftime("%Y-%m-%d %H:%M:%S", gmtime()),' - processing event',str(entry)+'/'+str(nEntries), '(cout every',j_out,'events)'
                    #sys.stdout.flush()

                #if entry > 10000: break
                #if entry > 100: break
                #if entry > 1000: break
                tree.GetEntry(entry)


                ### Vtype correction for V25 samples
                if channel == "Zmm" and recomputeVtype:

                    #Variable to store Vtype and leptons info
                    Vtype_new_ = -1
                    V_mass_new = -1

                    vLeptons_new = []
                    #get all the lepton index
                    lep_index = range(len(tree.selLeptons_pt))
                    selectedElectrons = [i for i in  lep_index if abs(tree.selLeptons_pdgId[i]) == 11]
                    selectedMuons = [i for i in lep_index if abs(tree.selLeptons_pdgId[i]) == 13]

                    zElectrons = [x for x in selectedElectrons if zEleSelection(x)]
                    zMuons = [x for x in selectedMuons if zMuSelection(x)]

                    zMuons.sort(key=lambda x:tree.selLeptons_pt[x], reverse=True)
                    zElectrons.sort(key=lambda x:tree.selLeptons_pt[x], reverse=True)

                    if len(zMuons) >=  2 :
                        if tree.selLeptons_pt[zMuons[0]] > 20:
                            for i in zMuons[1:]:
                                if  tree.selLeptons_charge[zMuons[0]]*tree.selLeptons_charge[i] < 0:
                                    Vtype_new_ = 0
                                    for var in vLeptonsvar:
                                        vLeptonsBranches[var][0] = getattr(tree,'selLeptons_%s'%var)[0]
                                        vLeptonsBranches[var][1] = getattr(tree,'selLeptons_%s'%var)[i]
                                    break
                    elif len(zElectrons) >=  2 :
                        if tree.selLeptons_pt[zElectrons[0]] > 20:
                            for i in zElectrons[1:]:
                                if  tree.selLeptons_charge[zElectrons[0]]*tree.selLeptons_charge[i] < 0:
                                    Vtype_new_ = 1
                                    for var in vLeptonsvar:
                                        vLeptonsBranches[var][0] = getattr(tree,'selLeptons_%s'%var)[0]
                                        vLeptonsBranches[var][1] = getattr(tree,'selLeptons_%s'%var)[i]
                                    break
                    else:
                        if tree.Vtype == 0 or tree.Vtype == 1:
                            print '@ERROR: This is impossible, the new ele cut should be losser...'
                            sys.exit(1)
                        #add lepton if Vtype 2 or 3
                        if tree.Vtype == 2 or tree.Vtype == 3:
                            Vtype_new_ = tree.Vtype
                            for var in vLeptonsvar:
                                vLeptonsBranches[var][0] = getattr(tree,'vLeptons_%s'%var)[0]
                        #to handle misassigned Vtype 4 or -1 because of additional electron cut
                        elif (tree.Vtype == 4 or tree.Vtype == -1) and len(zElectrons) + len(zMuons) > 0:
                            Vtype_new_ = 5
                        #to handle misassigned Vtype 5 because of additional electron cut
                        elif tree.Vtype == 5 and len(zElectrons) + len(zMuons) == 0:
                            if tree.met_pt < 80:
                                Vtype_new_ = -1
                            else:
                                Vtype_new_ = 4
                        #if none of the exception above happen, it is save to copy the Vtype
                        else:
                            Vtype_new_ = tree.Vtype

                    # skip event, if vtype neither 0 or 1
                    if Vtype_new_ != 0 and Vtype_new_ != 1:
                        n_vtype_events_skipped += 1
                        continue

                    if Vtype_new_ == tree.Vtype:
                        n_vtype_unchanged += 1
                    else:
                        n_vtype_changed += 1

                    V = ROOT.TLorentzVector()

                    if Vtype_new_ == 0 or Vtype_new_ == 1:
                        lep1 = ROOT.TLorentzVector()
                        lep2 = ROOT.TLorentzVector()
                        lep1.SetPtEtaPhiM(vLeptonsBranches['pt'][0], vLeptonsBranches['eta'][0], vLeptonsBranches['phi'][0], vLeptonsBranches['mass'][0])
                        lep2.SetPtEtaPhiM(vLeptonsBranches['pt'][1], vLeptonsBranches['eta'][1], vLeptonsBranches['phi'][1], vLeptonsBranches['mass'][1])
                        V = lep1+lep2
                        for var in Vvar:
                            VBranches[var][0] = getattr(V,LorentzDic[var])()
                    else:
                        for var in Vvar:
                            VBranches[var][0] = getattr(tree,'V_%s'%var)

                    Vtype_new[0] = Vtype_new_

                    #skip event not satisfying kinematic lepton cut
                    if  vLeptonsBranches['pt'][0] < 20 or vLeptonsBranches['pt'][1] < 20 or VBranches['pt'][0] < 50:
                        continue
                    if job.type == 'DATA' and 'DoubleMuon' in job.name and  Vtype_new_ != 0:
                        continue
                    if job.type == 'DATA' and 'DoubleEG' in job.name and  Vtype_new_ != 1:
                        continue

                    if stopAfterVtypeCorrection:
                        newtree.Fill()
                        continue

                if channel == "Zmm" and applyBTagweights and job.type != 'DATA':
                    MakeSysRefMap()

                    jets_csv = []
                    jets_cmva = []

                    for i in range(tree.nJet):
                        if (tree.Jet_pt_reg[i] > 20 and abs(tree.Jet_eta[i]) < 2.4):
                            jet_cmva = Jet(tree.Jet_pt_reg[i], tree.Jet_eta[i], tree.Jet_hadronFlavour[i], tree.Jet_btagCMVAV2[i])
                            jets_cmva.append(jet_cmva)

                    ptmin = 20.
                    ptmax = 1000.
                    etamin = 0.
                    etamax = 2.4

                    central_SF = get_event_SF(ptmin, ptmax, etamin, etamax, jets_cmva, "central", "CMVAV2", btag_calibrators)
                    bTagWeights["bTagWeightCMVAV2_Moriond"][0] = central_SF
                    #print "central bTagWeightCMVAV2_Moriond_v2  is ", central_SF
                    #print ""


                    for syst in ["JES", "LF", "HF", "LFStats1", "LFStats2", "HFStats1", "HFStats2", "cErr1", "cErr2"]:
                        for sdir in ["Up", "Down"]:

                            bTagWeights["bTagWeightCMVAV2_Moriond_"+syst+sdir][0] = get_event_SF( ptmin, ptmax, etamin, etamax, jets_cmva, sysMap[syst+sdir], "CMVAV2", btag_calibrators)

                            for ipt in range(0,5):

                                ptmin = 20.
                                ptmax = 1000.
                                etamin = 0.
                                etamax = 2.4

                                if ipt == 0:
                                    ptmin = 20.
                                    ptmax = 30.
                                elif ipt == 1:
                                    ptmin = 30.
                                    ptmax = 40.
                                elif ipt ==2:
                                    ptmin = 40.
                                    ptmax = 60.
                                elif ipt ==3:
                                    ptmin = 60.
                                    ptmax = 100.
                                elif ipt ==4:
                                    ptmin = 100.
                                    ptmax = 1000.

                                for ieta in range(1,4):

                                    #print '\n Btag for SYS:', syst+"_pt"+str(ipt)+"_eta"+str(ieta)+sdir
                                    if ieta ==1:
                                        etamin = 0.
                                        etamax = 0.8
                                    elif ieta ==2:
                                        etamin = 0.8
                                        etamax = 1.6
                                    elif ieta ==3:
                                        etamin = 1.6
                                        etamax = 2.4

                                        #bTagWeights["bTagWeightCMVAV2_Moriond_"+syst+systcat+sdir][0] = get_event_SF(ptmin, ptmax, etamin, etamax, jets_cmva, sysMap[syst+sdir], "CMVAV2", btag_calibrators)
                                    bTagWeights["bTagWeightCMVAV2_Moriond_"+syst+"_pt"+str(ipt)+"_eta"+str(ieta)+sdir][0] = get_event_SF(ptmin, ptmax, etamin, etamax, jets_cmva, sysMap[syst+sdir], "CMVAV2", btag_calibrators)


                            #OLD
                            #for systcat in ["HighCentral","LowCentral","HighForward","LowForward"]:

                            #    ptmin = 20.
                            #    ptmax = 1000.
                            #    etamin = 0.
                            #    etamax = 2.4
                            #    if (systcat.find("High")!=-1):
                            #        ptmin = 100.
                            #    if (systcat.find("Low")!=-1):
                            #        ptmax = 100.
                            #    if (systcat.find("Central")!=-1):
                            #        etamax = 1.4
                            #    if (systcat.find("Forward")!=-1):
                            #        etamin = 1.4

                            #    event_SF_ = get_event_SF(ptmin, ptmax, etamin, etamax, jets_cmva, sysMap[syst+sdir], "CMVAV2", btag_calibrators)
                            #    bTagWeights["bTagWeightCMVAV2_Moriond_"+syst+systcat+sdir][0] = event_SF_
                            #    #print "bTagWeightCMVAV2_Moriond_v2_"+syst+systcat+sdir, ' is', event_SF_#get_event_SF(ptmin, ptmax, etamin, etamax, jets_cmva, sysMap[syst+sdir], "CMVAV2", btag_calibrators)
                            #    #print ""

                if channel == "Zmm" and applyBTagweights and Stop_after_BTagweights:
                    newtree.Fill()
                    continue

                #Get regression variable
                if applyJESsystematics:
                    Reg_var_list = []
                    for j in xrange(min(tree.nJet,21)):
                        reg_var_dic = {}
                        reg_var_dic['Jet_pt']= tree.Jet_pt[j]
                        #print 'when filling list, pt is', reg_var_dic['Jet_pt']
                        reg_var_dic['Jet_ptRaw']= tree.Jet_rawPt[j]
                        reg_var_dic['Jet_eta'] = tree.Jet_eta[j]
                        reg_var_dic['Jet_m']= tree.Jet_mass[j]
                        reg_var_dic['Jet_phi']= tree.Jet_phi[j]
                        reg_var_dic['hJ'] = hJ.SetPtEtaPhiM(reg_var_dic['Jet_pt'], reg_var_dic['Jet_eta'], reg_var_dic['Jet_phi'], reg_var_dic['Jet_m'])
                        reg_var_dic['Jet_e']= hJ.E()
                        reg_var_dic['Jet_chEmEF']=tree.Jet_chEmEF[j]
                        reg_var_dic['Jet_chHEF']=tree.Jet_chHEF[j]
                        reg_var_dic['Jet_rawPt']= tree.Jet_rawPt[j]
                        reg_var_dic['Jet_chMult']= tree.Jet_chMult[j]

                        #regVars are here
                        reg_var_dic['Jet_vtx3deL']= max(0.,tree.Jet_vtx3DSig[j])
                        reg_var_dic['Jet_vtxNtrk']= max(0.,tree.Jet_vtxNtracks[j])
                        reg_var_dic['Jet_vtx3dL']= max(0.,tree.Jet_vtx3DVal[j])
                        reg_var_dic['Jet_vtxMass']= max(0.,tree.Jet_vtxMass[j])
                        reg_var_dic['Jet_vtxPt']= max(0.,tree.Jet_vtxPt[j])
                        reg_var_dic['Jet_neEmEF']=tree.Jet_neEmEF[j]
                        reg_var_dic['Jet_neHEF']=tree.Jet_neHEF[j]
                        reg_var_dic['Jet_leptonDeltaR']= max(0.,tree.Jet_leptonDeltaR[j])
                        reg_var_dic['Jet_leptonPt']= max(0.,tree.Jet_leptonPt[j])
                        reg_var_dic['Jet_leptonPtRel']= max(0.,tree.Jet_leptonPtRel[j])
                        reg_var_dic['Jet_leadTrackPt']= max(0.,tree.Jet_leadTrackPt[j])
                        reg_var_dic['Jet_mt']= hJ.Mt()
                        reg_var_dic['Jet_eta']= tree.Jet_eta[j]
                        reg_var_dic['nPVs']=tree.nPVs
                        #reg_var_dic['met_pt']=tree.met_pt
                        #reg_var_dic['Jet_met_proj']=projectionMETOntoJet(tree.met_pt, tree.met_phi, reg_var_dic['Jet_pt'], reg_var_dic['Jet_phi'])

                        Reg_var_list.append(reg_var_dic)


                    # JEC factorized branches
                    Jec_sys_list = []
                    if job.type != 'DATA':
                        for j in xrange(min(tree.nJet,21)):
                            jec_sys_dic = {}
                            jec_sys_dic['Jet_corr'] =  getattr(tree,'Jet_corr')[j]
                            jec_sys_dic['Jet_corr_JER'] =  getattr(tree,'Jet_corr_JER')[j]
                            for jecsys in JECsys:
                                for ud in ['Up', 'Down']:
                                    jec_sys_dic[jecsys+ud] =  getattr(tree,'Jet_corr_'+jecsys+ud)[j]
                            Jec_sys_list.append(jec_sys_dic)



                        #Fill regression vars used in TMVA
                            #now loop over all the jets
                    for j in xrange(min(tree.nJet,21)):
                        for key in regVars:
                            theVars[key][0] = Reg_var_list[j][key]

                        Pt = max(0.0001, TMVA_reader['readerJet'].EvaluateRegression("readerJet")[0])
                        rPt = Reg_var_list[j]['Jet_pt']*Pt
                        JEC_systematics["hJetCMVAV2_pt_reg"][j] = Pt
                        JetCMVAV2_regWeight = Pt/Reg_var_list[j]['Jet_pt']
                        #print 'pt is', Reg_var_list[j]['Jet_pt']
                        #print 'reg pt is', Pt

                        #Fill the Higgs jet
                        if j == tree.hJCMVAV2idx[0]:
                            hJ0.SetPtEtaPhiM(Pt, Reg_var_list[j]['Jet_eta'], Reg_var_list[j]['Jet_phi'], Reg_var_list[j]['Jet_m']*JetCMVAV2_regWeight)
                        elif j == tree.hJCMVAV2idx[1]:
                            hJ1.SetPtEtaPhiM(Pt, Reg_var_list[j]['Jet_eta'], Reg_var_list[j]['Jet_phi'], Reg_var_list[j]['Jet_m']*JetCMVAV2_regWeight)

                    #print 'mass is', (hJ0+hJ1).M()
                    JEC_systematics["HCMVAV2_reg_mass"][0] = (hJ0+hJ1).M()
                    JEC_systematics["HCMVAV2_reg_pt"][0]   = (hJ0+hJ1).Pt()
                    JEC_systematics["HCMVAV2_reg_eta"][0]  = (hJ0+hJ1).Eta()
                    JEC_systematics["HCMVAV2_reg_phi"][0]  = (hJ0+hJ1).Phi()
                    JEC_systematics["hJetCMVAV2_pt_reg_0"][0]  = hJ0.Pt()
                    JEC_systematics["hJetCMVAV2_pt_reg_1"][0]  = hJ1.Pt()

                    if job.type != 'DATA':
                        #now loop over all the jets
                        for syst in JECsys:
                            for sdir in ["Up", "Down"]:
                                for j in xrange(min(tree.nJet,21)):
                                    for key in regVars:
                                        theVars[key][0] = Reg_var_list[j][key]
                                    theVars['Jet_pt'][0] = 0

                                    if syst == "JER":
                                        theVars['Jet_pt'][0] = Reg_var_list[j]['Jet_rawPt']*Jec_sys_list[j]['Jet_corr']*Jec_sys_list[j]['JER'+sdir]
                                    else:
                                        #theVars['Jet_pt'][0] = Reg_var_list[j]['Jet_rawPt']*Jec_sys_list[j][syst+sdir]*Jec_sys_list[j]['Jet_corr_JER']
                                        theVars['Jet_pt'][0] = (Reg_var_list[j]['Jet_pt']/Jec_sys_list[j]['Jet_corr'])*Jec_sys_list[j][syst+sdir]

                                    pt = max(0.0001, TMVA_reader['readerJet'].EvaluateRegression("readerJet")[0])

                                    rPt = Reg_var_list[j]['Jet_pt']*pt
                                    JEC_systematics["hJetCMVAV2_pt_reg_corr"+syst+sdir][j] = pt
                                    Jet_regWeight= pt/Reg_var_list[j]['Jet_pt']

                                    if j == tree.hJCMVAV2idx[0]:
                                        hJ0.SetPtEtaPhiM(pt, Reg_var_list[j]['Jet_eta'], Reg_var_list[j]['Jet_phi'], Reg_var_list[j]['Jet_m']*Jet_regWeight)
                                    elif j == tree.hJCMVAV2idx[1]:
                                        hJ1.SetPtEtaPhiM(pt, Reg_var_list[j]['Jet_eta'], Reg_var_list[j]['Jet_phi'], Reg_var_list[j]['Jet_m']*Jet_regWeight)

                                JEC_systematics["HCMVAV2_reg_mass_corr"+syst+sdir][0] = (hJ0+hJ1).M()
                                JEC_systematics["HCMVAV2_reg_pt_corr"+syst+sdir][0] = (hJ0+hJ1).Pt()
                                JEC_systematics["HCMVAV2_reg_eta_corr"+syst+sdir][0] = (hJ0+hJ1).Eta()
                                JEC_systematics["HCMVAV2_reg_phi_corr"+syst+sdir][0] = (hJ0+hJ1).Phi()
                                JEC_systematics["hJetCMVAV2_pt_reg_0_corr"+syst+sdir][0] = hJ0.Pt()
                                JEC_systematics["hJetCMVAV2_pt_reg_1_corr"+syst+sdir][0] = hJ1.Pt()

                        #Compute Min/Max
                        VarList = ['HCMVAV2_reg_mass','HCMVAV2_reg_pt','HCMVAV2_reg_eta','HCMVAV2_reg_phi','hJetCMVAV2_pt_reg_0','hJetCMVAV2_pt_reg_1']
                        for var in VarList:
                            for bound in ['Min','Max']:
                                #intialise by using central value (no sys)
                                #new
                                val = JEC_systematics[var][0]
                                #old
                                #val =  getattr(tree,var)
                                for syst in JECsys:
                                    for sdir in ["Up", "Down"]:
                                        #new
                                        if bound == 'Min': val = min(val, JEC_systematics[var+"_corr"+syst+sdir])
                                        if bound == 'Max': val = max(val, JEC_systematics[var+"_corr"+syst+sdir])
                                        #old
                                        #if bound == 'Min': val = min(val, getattr(tree,var+"_corr"+syst+sdir))
                                        #if bound == 'Max': val = max(val, getattr(tree,var+"_corr"+syst+sdir))
                                JEC_systematicsMinMax[var+"_corr_"+bound][0] = val
                                #print 'val is', val

                #if applyJESsystematicsMinMax:
                #    if job.type != 'DATA':
                #        VarList = ['HCMVAV2_reg_mass','HCMVAV2_reg_pt','HCMVAV2_reg_eta','HCMVAV2_reg_phi','hJetCMVAV2_pt_reg_0','hJetCMVAV2_pt_reg_1']
                #        JECsys = [
                #            "JER",
                #            "PileUpDataMC",
                #            "PileUpPtRef",
                #            "PileUpPtBB",
                #            "PileUpPtEC1",
                #            #"PileUpPtEC2",
                #            #"PileUpPtHF",
                #            "RelativeJEREC1",
                #            #"RelativeJEREC2",
                #            #"RelativeJERHF",
                #            "RelativeFSR",
                #            "RelativeStatFSR",
                #            "RelativeStatEC",
                #            #"RelativeStatHF",
                #            "RelativePtBB",
                #            "RelativePtEC1",
                #            #"RelativePtEC2",
                #            #"RelativePtHF",
                #            "AbsoluteScale",
                #            "AbsoluteMPFBias",
                #            "AbsoluteStat",
                #            "SinglePionECAL",
                #            "SinglePionHCAL",
                #            "Fragmentation"
                #            "TimePtEta",
                #            "FlavorQCD"
                #            ]
                #        for var in VarList:
                #            for bound in ['Min','Max']:
                #                #val = -42.
                #                #intialise by using central value (no sys)
                #                val =  getattr(tree,var)
                #                #first = True
                #                for syst in JECsys:
                #                    for sdir in ["Up", "Down"]:
                #                        #if first: val = getattr(tree,var+"_corr"+syst+sdir)
                #                        if bound == 'Min': val = min(val, getattr(tree,var+"_corr"+syst+sdir))
                #                        if bound == 'Max': val = max(val, getattr(tree,var+"_corr"+syst+sdir))
                #                        #first = False
                #                JEC_systematicsMinMax[var+"_corr_"+bound][0] = val
                #                #print 'val is', val

                if applyLepSF and job.type != 'DATA':
            # ================ Lepton Scale Factors =================
                # For custom made form own JSON files

                    #Reinitialize all the variables

                    weight_SF_LooseID[0], weight_SF_LooseID[1],  weight_SF_LooseID[2] = 1.,0.,0.
                    weight_SF_LooseISO[0], weight_SF_LooseISO[1],  weight_SF_LooseISO[2] = 1.,0.,0.
                    weight_SF_LooseIDnISO[0], weight_SF_LooseIDnISO[1],  weight_SF_LooseIDnISO[2] = 1.,0.,0.
                    weight_SF_LooseIDnISO_B[0], weight_SF_LooseIDnISO_B[1] = 0.,0.
                    weight_SF_LooseIDnISO_E[0], weight_SF_LooseIDnISO_E[1] = 0.,0.
                    weight_SF_TRK[0], weight_SF_TRK[1],  weight_SF_TRK[2] = 1.,0.,0.
                    weight_SF_Lepton[0], weight_SF_Lepton[1], weight_SF_Lepton[2] = 1.,0.,0.
                    eTrigSFWeight_doubleEle80x[0], eTrigSFWeight_doubleEle80x[1], eTrigSFWeight_doubleEle80x[2] = 1.,0.,0.
                    muTrigSFWeight_doublemu[0], muTrigSFWeight_doublemu[1], muTrigSFWeight_doublemu[2] = 1.,0.,0.


                    #V24
                    #DY_specialWeight[0] = 1.
                    #weight_SF_LooseID[0], weight_SF_LooseID[1],  weight_SF_LooseID[2] = 1.,1.,1.
                    #weight_SF_LooseISO[0], weight_SF_LooseISO[1],  weight_SF_LooseISO[2] = 1.,1.,1.
                    #weight_SF_LooseMVAID_BCD[0], weight_SF_LooseMVAID_BCD[1], weight_SF_LooseMVAID_BCD[2]  = 1.,1.,1.
                    #weight_SF_LooseMVAID_BCDEF[0], weight_SF_LooseMVAID_BCDEF[1], weight_SF_LooseMVAID_BCDEF[2] = 1.,1.,1.
                    #weight_Eff_eletriglooseBCD[0], weight_Eff_eletriglooseBCD[1], weight_Eff_eletriglooseBCD[2] = 1.,1.,1.
                    #weight_Eff_eletriglooseBCDEF[0], weight_Eff_eletriglooseBCDEF[1], weight_Eff_eletriglooseBCDEF[2] = 1.,1.,1.
                    #weight_Eff_eletrigloosept23[0], weight_Eff_eletrigloosept23[1], weight_Eff_eletrigloosept23[2]= 1.,1.,1.
                    #weight_Eff_mutriglooseICHEP[0], weight_Eff_mutriglooseICHEP[1], weight_Eff_mutriglooseICHEP[2] = 1.,1.,1.
                    #weight_Eff_mutrigloose[0], weight_Eff_mutrigloose[1], weight_Eff_mutrigloose[2] = 1.,1.,1.
                    #weight_trk_electron[0], weight_trk_electron[1], weight_trk_electron[2] = 1.,1.,1.
                    #eleweight[0], eleweight[1], eleweight[2] = 1.,1.,1.
                    #muweight[0], muweight[1], muweight[2] = 1.,1.,1.

                    muID_BCDEF = [1.,0.,0.]
                    muID_GH = [1.,0.,0.]
                    muISO_BCDEF = [1.,0.,0.]
                    muISO_GH = [1.,0.,0.]
                    muTRK_BCDEF= [1.0,0.,0.]
                    muTRK_GH = [1.0,0.,0.]
                    btagSF = [1.,0.,0.]
                    #for muon trigger
                     #Run BCDEFG
                    effDataBCDEFG_leg8 = []
                    effDataBCDEFG_leg17= []
                    effMCBCDEFG_leg8= []
                    effMCBCDEFG_leg17 = []
                     #Run H
                    effDataH_leg8 = []
                    effDataH_leg17 = []
                    effMCH_leg8 = []
                    effMCH_leg17 = []
                     #Run H dZ
                    effDataH_DZ= []
                    effMCH_DZ= []

                    wdir = config.get('Directories','vhbbpath')

                    jsons = {
                        #
                        #Muon
                        #
                        #ID and ISO
                        wdir+'/python/json/V25/muon_ID_BCDEFv2.json' : ['MC_NUM_LooseID_DEN_genTracks_PAR_pt_eta', 'abseta_pt_ratio'],
                        wdir+'/python/json/V25/muon_ID_GHv2.json' : ['MC_NUM_LooseID_DEN_genTracks_PAR_pt_eta', 'abseta_pt_ratio'],
                        wdir+'/python/json/V25/muon_ISO_BCDEFv2.json' : ['LooseISO_LooseID_pt_eta', 'abseta_pt_ratio'],
                        wdir+'/python/json/V25/muon_ISO_GHv2.json' : ['LooseISO_LooseID_pt_eta', 'abseta_pt_ratio'],
                        #Tracker
                        wdir+'/python/json/V25/trk_SF_RunBCDEF.json' : ['Graph', 'ratio_eff_eta3_dr030e030_corr'],
                        wdir+'/python/json/V25/trk_SF_RunGH.json' : ['Graph', 'ratio_eff_eta3_dr030e030_corr'],
                        #Trigg
                            #BCDEFG
                        wdir+'/python/json/V25/Data_EfficienciesAndSF_doublehlt_perleg_RunBCDEFG_leg8.json' : ['MC_NUM_hlt_Mu17_Mu8_OR_TkMu8_leg8_DEN_LooseIDnISO_PAR_pt_eta', 'abseta_pt_DATA'],
                        wdir+'/python/json/V25/Data_EfficienciesAndSF_doublehlt_perleg_RunBCDEFG_leg17.json' : ['MC_NUM_hlt_Mu17Mu8_leg17_DEN_LooseIDnISO_PAR_pt_eta', 'abseta_pt_DATA'],
                        wdir+'/python/json/V25/MC_EfficienciesAndSF_doublehlt_perleg_RunBCDEFG_leg8.json' : ['MC_NUM_hlt_Mu17_Mu8_OR_TkMu8_leg8_DEN_LooseIDnISO_PAR_pt_eta', 'abseta_pt_MC'],
                        wdir+'/python/json/V25/MC_EfficienciesAndSF_doublehlt_perleg_RunBCDEFG_leg17.json' : ['MC_NUM_hlt_Mu17Mu8_leg17_DEN_LooseIDnISO_PAR_pt_eta', 'abseta_pt_MC'],
                            #H
                                #no DZ
                        wdir+'/python/json/V25/Data_EfficienciesAndSF_doublehlt_perleg_RunH_leg8.json' : ['MC_NUM_hlt_Mu17_Mu8_OR_TkMu8_leg8_DEN_LooseIDnISO_PAR_pt_eta', 'abseta_pt_DATA'],
                        wdir+'/python/json/V25/Data_EfficienciesAndSF_doublehlt_perleg_RunH_leg17.json' : ['MC_NUM_hlt_Mu17Mu8_leg17_DEN_LooseIDnISO_PAR_pt_eta', 'abseta_pt_DATA'],
                        wdir+'/python/json/V25/MC_EfficienciesAndSF_doublehlt_perleg_RunH_leg8.json' : ['MC_NUM_hlt_Mu17_Mu8_OR_TkMu8_leg8_DEN_LooseIDnISO_PAR_pt_eta', 'abseta_pt_MC'],
                        wdir+'/python/json/V25/MC_EfficienciesAndSF_doublehlt_perleg_RunH_leg17.json' : ['MC_NUM_hlt_Mu17Mu8_leg17_DEN_LooseIDnISO_PAR_pt_eta', 'abseta_pt_MC'],
                                #with DZ
                        wdir+'/python/json/V25/DATA_EfficienciesAndSF_dZ_numH.json' : ['MC_NUM_dZ_DEN_hlt_Mu17_Mu8_OR_TkMu8_loose_PAR_eta1_eta2', 'tag_abseta_abseta_DATA'],
                        wdir+'/python/json/V25/MC_EfficienciesAndSF_dZ_numH.json' : ['MC_NUM_dZ_DEN_hlt_Mu17_Mu8_OR_TkMu8_loose_PAR_eta1_eta2', 'tag_abseta_abseta_MC'],
                        #
                        #Electron
                        #
                        #ID and ISO
                        wdir+'/python/json/V25/EIDISO_ZH_out.json' : ['EIDISO_ZH', 'eta_pt_ratio'],
                        #Tracker
                        wdir+'/python/json/V25/ScaleFactor_etracker_80x.json' : ['ScaleFactor_tracker_80x', 'eta_pt_ratio'],
                        #Trigg
                        wdir+'/python/json/V25/DiEleLeg1AfterIDISO_out.json' : ['DiEleLeg1AfterIDISO', 'eta_pt_ratio'],
                        wdir+'/python/json/V25/DiEleLeg2AfterIDISO_out.json' : ['DiEleLeg2AfterIDISO', 'eta_pt_ratio']
                        }

                    for j, name in jsons.iteritems():

                        weight = []
                        lepCorr = LeptonSF(j , name[0], name[1])

                        #2-D binned SF
                        if not j.find('trk_SF_Run') != -1 and not j.find('EfficienciesAndSF_dZ_numH') != -1:
                            weight.append(lepCorr.get_2D(tree.vLeptons_new_pt[0], tree.vLeptons_new_eta[0]))
                            weight.append(lepCorr.get_2D(tree.vLeptons_new_pt[1], tree.vLeptons_new_eta[1]))
                        elif not j.find('trk_SF_Run') != -1 and j.find('EfficienciesAndSF_dZ_numH') != -1:
                            weight.append(lepCorr.get_2D(tree.vLeptons_new_eta[0], tree.vLeptons_new_eta[1]))
                            weight.append(lepCorr.get_2D(tree.vLeptons_new_eta[1], tree.vLeptons_new_eta[0]))
                        #1-D binned SF
                        else:
                            weight.append(lepCorr.get_1D(tree.vLeptons_new_eta[0]))
                            weight.append(lepCorr.get_1D(tree.vLeptons_new_eta[1]))

                        if tree.Vtype_new == 0:
                            #IDISO
                            if j.find('muon_ID_BCDEF') != -1:
                                computeSF(muID_BCDEF)
                            elif j.find('muon_ID_GH') != -1:
                                computeSF(muID_GH)
                            elif j.find('muon_ISO_BCDEF') != -1:
                                computeSF(muISO_BCDEF)
                            elif j.find('muon_ISO_GH') != -1:
                                computeSF(muISO_GH)
                            #TRK
                            elif j.find('trk_SF_RunBCDEF') != -1:
                                computeSF(muTRK_BCDEF)
                            elif j.find('trk_SF_RunGH') != -1:
                                computeSF(muTRK_GH)
                            #TRIG
                            elif j.find('EfficienciesAndSF_doublehlt_perleg') != -1:
                                    #BCDEFG
                                if   j.find('Data_EfficienciesAndSF_doublehlt_perleg_RunBCDEFG_leg8') != -1:
                                    #compute the efficiency for both legs
                                    effDataBCDEFG_leg8.append(computeSF_leg(0))
                                    effDataBCDEFG_leg8.append(computeSF_leg(1))
                                elif j.find('Data_EfficienciesAndSF_doublehlt_perleg_RunBCDEFG_leg17') != -1:
                                    effDataBCDEFG_leg17.append(computeSF_leg(0))
                                    effDataBCDEFG_leg17.append(computeSF_leg(1))
                                elif j.find('MC_EfficienciesAndSF_doublehlt_perleg_RunBCDEFG_leg8') != -1:
                                    effMCBCDEFG_leg8.append(computeSF_leg(0))
                                    effMCBCDEFG_leg8.append(computeSF_leg(1))
                                elif j.find('MC_EfficienciesAndSF_doublehlt_perleg_RunBCDEFG_leg17') != -1:
                                    effMCBCDEFG_leg17.append(computeSF_leg(0))
                                    effMCBCDEFG_leg17.append(computeSF_leg(1))
                                    #H
                                elif j.find('Data_EfficienciesAndSF_doublehlt_perleg_RunH_leg8') != -1:
                                    effDataH_leg8.append(computeSF_leg(0))
                                    effDataH_leg8.append(computeSF_leg(1))
                                elif j.find('Data_EfficienciesAndSF_doublehlt_perleg_RunH_leg17') != -1:
                                    effDataH_leg17.append(computeSF_leg(0))
                                    effDataH_leg17.append(computeSF_leg(1))
                                elif j.find('MC_EfficienciesAndSF_doublehlt_perleg_RunH_leg8') != -1:
                                    effMCH_leg8.append(computeSF_leg(0))
                                    effMCH_leg8.append(computeSF_leg(1))
                                elif j.find('MC_EfficienciesAndSF_doublehlt_perleg_RunH_leg17') != -1:
                                    effMCH_leg17.append(computeSF_leg(0))
                                    effMCH_leg17.append(computeSF_leg(1))
                                    #H dZ only
                            elif j.find('DATA_EfficienciesAndSF_dZ_numH') != -1:
                                effDataH_DZ.append(computeSF_leg(0))
                                effDataH_DZ.append(computeSF_leg(1))
                            elif j.find('MC_EfficienciesAndSF_dZ_numH') != -1:
                                effMCH_DZ.append(computeSF_leg(0))
                                effMCH_DZ.append(computeSF_leg(1))

                        elif tree.Vtype_new == 1:
                            #IDISO
                            if j.find('EIDISO_ZH_out') != -1:
                                computeSF(weight_SF_LooseIDnISO)
                                computeSF_region(weight_SF_LooseIDnISO_B, weight_SF_LooseIDnISO_E, tree.vLeptons_new_eta[0], tree.vLeptons_new_eta[1], 1.566)
                            #TRK
                            elif j.find('ScaleFactor_etracker_80x') != -1:
                                computeSF(weight_SF_TRK)
                            #TRIG
                            elif j.find('DiEleLeg1AfterIDISO_out') != -1:
                                eff1 = weight[0][0]
                                eff1Up = (weight[0][0]+weight[0][1])
                                eff1Down = (weight[0][0]-weight[0][1])
                            elif j.find('DiEleLeg2AfterIDISO_out') != -1:
                                eff2 = weight[1][0]
                                eff2Up = (weight[1][0]+weight[1][1])
                                eff2Down = (weight[1][0]-weight[1][1])

                        #else:
                        #    print 'json is', j
                        #    sys.exit('@ERROR: SF list doesn\'t match json files. Abort')

                    # End JSON loop ====================================

                    #Fill muon triggers

                    if tree.Vtype_new == 0:
                        #print 'muTRK_BCDEF is', muTRK_BCDEF
                        #print 'muTRK_GH is', muTRK_GH
                        #print 'muID_BCDEF is', muID_BCDEF
                        #print 'muID_GH is', muID_GH
                        #print 'muISO_BCDEF is', muISO_BCDEF
                        #print 'muISO_GH is', muISO_GH

                        #Tracker
                        getLumiAvrgSF(muTRK_BCDEF,(20.1/36.4),muTRK_GH,(16.3/36.4),weight_SF_TRK)
                        #ID and ISO
                        getLumiAvrgSF(muID_BCDEF,(20.1/36.4),muID_GH,(16.3/36.4),weight_SF_LooseID)
                        getLumiAvrgSF(muISO_BCDEF,(20.1/36.4),muISO_GH,(16.3/36.4),weight_SF_LooseISO)

                        weight_SF_LooseIDnISO[0] = weight_SF_LooseID[0]*weight_SF_LooseISO[0]
                        weight_SF_LooseIDnISO[1] = weight_SF_LooseID[1]*weight_SF_LooseISO[1]
                        weight_SF_LooseIDnISO[2] = weight_SF_LooseID[2]*weight_SF_LooseISO[2]
                        #Trigger
                            #BCDEFG no DZ
                        EffData_BCDEFG = [1.0,0.]
                        EffMC_BCDEFG = [1.0,0.]
                        SF_BCDEFG = [1.0,0.,0.]
                        EffData_BCDEFG = computeEventSF_fromleg(effDataBCDEFG_leg8,effDataBCDEFG_leg17)
                        EffMC_BCDEFG = computeEventSF_fromleg(effMCBCDEFG_leg8,effMCBCDEFG_leg17)
                        SF_BCDEFG[0] =  (EffData_BCDEFG[0]/EffMC_BCDEFG[0])
                        SF_BCDEFG[1] = (1-math.sqrt(EffData_BCDEFG[1]**2+ EffMC_BCDEFG[1]**2))*SF_BCDEFG[0]
                        SF_BCDEFG[2] = (1+math.sqrt(EffData_BCDEFG[1]**2+ EffMC_BCDEFG[1]**2))*SF_BCDEFG[0]
                            #H no DZ
                        EffData_H = [1.0,0.]
                        EffMC_H = [1.0,0.]
                        SF_H = [1.0,0.,0.]
                        EffData_H = computeEventSF_fromleg(effDataH_leg8,effDataH_leg17)
                        EffMC_H = computeEventSF_fromleg(effMCH_leg8,effMCH_leg17)
                        SF_H[0] =  (EffData_H[0]/EffMC_H[0])
                        SF_H[1] = (1-math.sqrt(EffData_H[1]**2+ EffMC_H[1]**2))*SF_H[0]
                        SF_H[2] = (1+math.sqrt(EffData_H[1]**2+ EffMC_H[1]**2))*SF_H[0]
                            #H DZ SF
                        EffData_DZ = [1.0,0.]
                        EffMC_DZ = [1.0,0.]
                        SF_DZ = [1.0,0.,0.]
                        EffData_DZ = computeEvenSF_DZ(effDataH_DZ)
                        EffMC_DZ = computeEvenSF_DZ(effMCH_DZ)
                        SF_DZ[0] = (EffData_DZ[0]/EffMC_DZ[0])
                        SF_DZ[1] = (1-math.sqrt(EffData_DZ[1]**2+ EffMC_DZ[1]**2))*SF_DZ[0]
                        SF_DZ[2] = (1+math.sqrt(EffData_DZ[1]**2+ EffMC_DZ[1]**2))*SF_DZ[0]

                        #print 'List of all the double trigger SF + uncert'
                        #print 'SF_BCDEFG:', SF_BCDEFG[0], '+', SF_BCDEFG[1], '-', SF_BCDEFG[2]
                        #print 'SF_H:', SF_H[0], '+', SF_H[1], '-', SF_H[2]
                        #print 'SF_DZ:', SF_DZ[0], '+', SF_DZ[1], '-', SF_DZ[2]
                        #Final weight
                        muTrigSFWeight_doublemu[0] = (27.221/35.827)*SF_BCDEFG[0] + (8.606/35.827)*SF_H[0]*SF_DZ[0]
                        muTrigSFWeight_doublemu[1] = (27.221/35.827)*SF_BCDEFG[1] + (8.606/35.827)*SF_H[1]*SF_DZ[1]
                        muTrigSFWeight_doublemu[2] = (27.221/35.827)*SF_BCDEFG[2] + (8.606/35.827)*SF_H[2]*SF_DZ[2]


                        #Final weight

                        #OLD
                        #Trigger
                        #    #BCDEFG no DZ
                        #EffData_BCDEFG = ((effDataBCDEFG_leg8[0]**2*effDataBCDEFG_leg17[1] + effDataBCDEFG_leg8[1]**2*effDataBCDEFG_leg17[0])/(effDataBCDEFG_leg8[0] + effDataBCDEFG_leg8[1]))
                        #EffMC_BCDEFG = ((effMCBCDEFG_leg8[0]**2*effMCBCDEFG_leg17[1] + effMCBCDEFG_leg8[1]**2*effMCBCDEFG_leg17[0])/(effMCBCDEFG_leg8[0] + effMCBCDEFG_leg8[1]))
                        #SF_BCDEFG = EffData_BCDEFG/EffMC_BCDEFG
                        #    #H no DZ
                        #EffData_H = ((effDataH_leg8[0]**2*effDataH_leg17[1] + effDataH_leg8[1]**2*effDataH_leg17[0])/(effDataH_leg8[0] + effDataH_leg8[1]))
                        #EffMC_H = ((effMCH_leg8[0]**2*effMCH_leg17[1] + effMCH_leg8[1]**2*effMCH_leg17[0])/(effMCH_leg8[0] + effMCH_leg8[1]))
                        #SF_H = EffData_H/EffMC_H
                        #    #H DZ SF
                        #EffData_DZ = ((effDataH_DZ[0]**2 + effDataH_DZ[1]**2)/(effDataH_DZ[0] + effDataH_DZ[1]))
                        #EffMC_DZ = ((effMCH_DZ[0]**2 + effMCH_DZ[1]**2)/(effMCH_DZ[0] + effMCH_DZ[1]))
                        #EffMC_SF = EffData_DZ/EffMC_DZ
                        ##Final weight


                    if tree.Vtype_new == 1:
			            eTrigSFWeight_doubleEle80x[0]     = eff1*(1-eff2)*eff1 + eff2*(1-eff1)*eff2 + eff1*eff1*eff2*eff2
			            eTrigSFWeight_doubleEle80x[1] = eff1Down*(1-eff2Down)*eff1Down + eff2Down*(1-eff1Down)*eff2Down + eff1Down*eff1Down*eff2Down*eff2Down
			            eTrigSFWeight_doubleEle80x[2]   = eff1Up*(1-eff2Up)*eff1Up + eff2Up*(1-eff1Up)*eff2Up + eff1Up*eff1Up*eff2Up*eff2Up
                    #
                    #comput total weight
                    #
                    weight_SF_Lepton[0] = weight_SF_TRK[0]*weight_SF_LooseIDnISO[0]
                    weight_SF_Lepton[1] = weight_SF_TRK[1]*weight_SF_LooseIDnISO[1]
                    weight_SF_Lepton[2] = weight_SF_TRK[2]*weight_SF_LooseIDnISO[2]


                if applyLepSF and Stop_after_LepSF:
                    newtree.Fill()
                    continue

                if addBranches:

                    ### Fill new variable from configuration ###
                    for variableName in newVariableNames:
                        nData = newVariableFormulas[variableName].GetNdata()
                        if nData > 1:
                            for element in range(nData):
                                newVariables[variableName][element] = newVariableFormulas[variableName].EvalInstance(element)
                        else:
                            newVariables[variableName][0] = newVariableFormulas[variableName].EvalInstance()

                if addBranches and Stop_after_addBranches:
                    newtree.Fill()
                    continue

                if addEWK:
                    if job.type != 'DATA':
                        ### todo: job.FullName is not defined!
                        jobName = str(job.FullName)

                        if 'DY' in jobName:
                            if '10to50' in jobName:
                                isDY[0] = 3
                            elif 'amcatnloFXFX' in jobName:
                                isDY[0] = 2
                            else:
                                isDY[0] = 1
                        else:
                            isDY[0] = 0

                        EWKw[0] = 1
                        EWKw[1] = 1
                        EWKw[2] = 1

                        if isDY[0] == 1 or isDY[0] == 2: #apply only on m50 DY samples
                            #print 'GebVboson is', tree.GenVbosons_pt[0]
                            if len(tree.GenVbosons_pt) > 0 and tree.GenVbosons_pt[0] > 100. and  tree.GenVbosons_pt[0] < 3000:
                                EWKw[0]= -0.1808051+6.04146*(pow((tree.GenVbosons_pt[0]+759.098),-0.242556))
                                EWKw[1]= EWKw[0]
                                EWKw[2]= EWKw[0]
                        NLOw[0] = 1
                        if isDY[0] == 1:
                            etabb = abs(tree.Jet_eta[tree.hJCidx[0]] - tree.Jet_eta[tree.hJCidx[1]])
                            if etabb < 5: NLOw[0] = 1.153*(0.940679 + 0.0306119*etabb -0.0134403*etabb*etabb + 0.0132179*etabb*etabb*etabb -0.00143832*etabb*etabb*etabb*etabb)

                        elif 'ZH_HToBB' in job.name and not 'ggZH' in job.name:
                            if tree.nGenVbosons > 0:
                                EWKw[0] = signal_ewk(tree.GenVbosons_pt[0])
                                EWKw[1] = signal_ewk_down(tree.GenVbosons_pt[0])
                                EWKw[2] = signal_ewk_up(tree.GenVbosons_pt[0])

                        #print 'EWKw is ', EWKw[0]

                        DYw[0] = EWKw[0]*NLOw[0]

                if addTTW:
                    if job.type != 'DATA':
                        TTW[0] = 1
                        if (tree.nGenTop == 2):
                            sf_top1 = math.exp(0.0615 - 0.0005*tree.GenTop_pt[0])
                            sf_top2 = math.exp(0.0615 - 0.0005*tree.GenTop_pt[1])
                            TTW[0] = math.sqrt(sf_top1*sf_top2)

                if addSBweight:

                    """Add a branch named "sb_weight" which contains the per-event S/(S+B) weight
                    for the events' corresponding bin in the signal region BDT score distribution.
                    This is to be applied to all MC and data.
                    """

                    
                    ##logger = logging.getLogger('add_sb_weight')
                    # Copy any count and weight histograms.
                    # Get input and output tree
                    ##infile = ROOT.TFile.Open(src)
                    ##outfile = ROOT.TFile.Open(dst, 'recreate')
                    ##for key in infile.GetListOfKeys():
                    ##    if key.GetName() == 'tree':
                    ##        continue
                    ##    obj = key.ReadObj()
                    ##    obj.Write()
                    ##tree = infile.Get('tree')
                    # Reset the branch in case it already exists.
                    ##tree.SetBranchStatus('sb_weight*', 0)
                    # Set the BDT branch address for faster reading, making
                    # sure that Xbb-style leaflists are handled properly.
                    ##bdt_buffer = {}
                    ##leaf_index = {}
                    ##for key in dc_info_dic:
                    ##    if key == 'MLFIT_PATH': continue
                    ##    bdt_branch = dc_info_dic[key][0]
                    ##    if '.' in bdt_branch:
                    ##        branch_name, leaf_name = bdt_branch.split('.')
                    ##        branch = tree.GetBranch(branch_name)
                    ##        n_leaves = branch.GetNleaves()
                    ##        leaf_index[bdt_branch] = [leaf.GetName() for leaf in branch.GetListOfLeaves()].index(leaf_name)
                    ##        bdt_buffer[bdt_branch] = numpy.zeros(n_leaves, dtype=numpy.float32)
                    ##    else:
                    ##        branch_name = bdt_branch
                    ##        leaf_index[bdt_branch] = None
                    ##        bdt_buffer[bdt_branch] = numpy.zeros(1, dtype=numpy.float32)
                    ##        print 'problem'
                    ##        sys.exit()
                    ##    tree.SetBranchAddress(branch_name, bdt_buffer[bdt_branch])
                    ### Clone the original tree and add the new branch.
                    #tree_new = tree.CloneTree(0)
                    ##sb_weight_dic = {} 
                    ##for key in dc_info_dic:
                    ##    if key == 'MLFIT_PATH': continue
                    ##    sb_weight_dic[key] = numpy.zeros(1, dtype=numpy.float64)
                    ##    #sb_weight = numpy.zeros(1, dtype=numpy.float64)
                    ##    newtree.Branch('sb_weight_%s'%key, sb_weight_dic[key], 'sb_weight_%s/D'%key)
                    ##    #newtree.Branch('sb_weight', sb_weight, 'sb_weight/D')
                    ### Cache the Fill method for faster filling.
                    ##fill_newtree = tree_new.Fill
                    ##for i, event in enumerate(tree, start=1):
                    for key in dc_info_dic:
                        if key == 'MLFIT_PATH': continue
                        bdt_branch = dc_info_dic[key][0]
                        # Find the BDT bin containing the event. If the event is
                        # found in the underflow bin, use the first bin instead.
                        bdt_score = bdt_buffer[bdt_branch][0] if leaf_index[bdt_branch] is None else bdt_buffer[bdt_branch][leaf_index[bdt_branch]]
                        #print 'bdt buffer', bdt_buffer[bdt_branch]
                        bin_index = dc_info_dic[key][5].FindBin(bdt_score) or 1
                        #bin_index = signal_postfit.FindBin(bdt_score) or 1
                        # Calculate the S/(S+B) weight for the event.
                        #dc_info_dic[key][5].SaveAs('/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_3/src/Xbb/python/checkhisto.root')
                        #sys.exit()
                        s = dc_info_dic[key][5].GetBinContent(bin_index)
                        b = dc_info_dic[key][6].GetBinContent(bin_index)
                        #if 'ZeeBDT_highpt' in key:
                        #    print 'bdt_score is', bdt_score
                        #    print 'bin index is', bin_index
                        #    print 's is', s
                        #    print 'b is', b
                        #s = signal_postfit.GetBinContent(bin_index)
                        #b = background_postfit.GetBinContent(bin_index)
                        sb_weight_dic[key][0] = s / (s + b) if b > 0 else 0
                        #fill_newtree()
                        #if i % 1000 == 0 or sb_weight_dic[key][0] > 10:
                        #    print 'i is', i
                        #    logger.info('Processing Entry #%s: BDT Score = %s, S/(S+B) = %s', i, bdt_score, sb_weight_dic[key])
                    #newtree.Write()
                    #outfile.Close()
                    #infile.Close()

                if AddSpecialWeight and job.type != 'DATA':
                    DY_specialWeight[0] = 1
                    if not job.specialweight:
                        pass
                    else :
                        specialWeight = ROOT.TTreeFormula('specialWeight',job.specialweight, tree)
                        specialWeight_ = specialWeight.EvalInstance()
                        DY_specialWeight[0] = specialWeight_

                newtree.Fill()

        print 'Exit loop'
        newtree.AutoSave()
        print 'Save'
        output.Close()
        print 'Close'

        if recomputeVtype:
            print 'Vtype correction statistics:' 
            print ' #skipped:',n_vtype_events_skipped
            print ' #unchanged:',n_vtype_unchanged
            print ' #changed:',n_vtype_changed
     
        targetStorage = pathOUT.replace('gsidcap://t3se01.psi.ch:22128/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')+'/'+job.prefix+job.identifier+'.root'
        if('pisa' in config.get('Configuration','whereToLaunch')):
            command = 'cp %s %s' %(tmpDir+'/'+job.prefix+job.identifier+'.root',targetStorage)
            print(command)
            subprocess.call([command], shell=True)
        else:
            command = "uberftp t3se01 'mkdir %s ' " %(pathOUT.replace('gsidcap://t3se01.psi.ch:22128/','')+'/'+job.identifier).replace('root://t3dcachedb03.psi.ch:1094/','')
            print(command)
            subprocess.call([command], shell=True)
            if len(filelist) == 0:
                command = 'srmrm %s' %(targetStorage.replace('root://t3dcachedb03.psi.ch:1094/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=/'))
                print(command)
                os.system(command)
                #command = 'env -i X509_USER_PROXY=/shome/$USER/.x509up_u`id -u` gfal-copy file:////%s %s' %(tmpDir.replace('/mnt/t3nfs01/data01','')+'/'+job.prefix+job.identifier+'.root',targetStorage.replace('root://t3dcachedb03.psi.ch:1094/','srm://t3se01.psi.ch/'))
                command = 'xrdcp -d 1 '+tmpfile+' '+outputFile
                print(command)
                os.system(command)
            else:
                # srmpathOUT = pathOUT.replace('gsidcap://t3se01.psi.ch:22128/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=').replace('dcap://t3se01.psi.ch:22125/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=').replace('root://t3dcachedb03.psi.ch:1094/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
                # command = 'srmcp -2 -globus_tcp_port_range 20000,25000 file:///'+tmpfile+' '+outputFile.replace('root://t3dcachedb03.psi.ch:1094/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')
                command = 'xrdcp -d 1 '+tmpfile+' '+outputFile
                print command
                subprocess.call([command], shell=True)

                print 'checking output file',outputFile
                #f = ROOT.TFile.Open(outputFile,'read')
                f = ROOT.TFile.Open(outputFile,'read')
                if not f or f.GetNkeys() == 0 or f.TestBit(ROOT.TFile.kRecovered) or f.IsZombie():
                    print 'TERREMOTO AND TRAGEDIA: THE MERGED FILE IS CORRUPTED!!! ERROR: exiting'
                    print outputFile
                    print f, f.IsZombie(), f.TestBit(ROOT.TFile.kRecovered), f.GetNkeys()

                    sys.exit(1)

                command = 'rm '+tmpfile
                print command
                subprocess.call([command], shell=True)
