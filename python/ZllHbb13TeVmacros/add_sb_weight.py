#!/usr/bin/env python
import logging
import sys

import ROOT
import numpy


#TEST1
## The path to the signal region shapes file.
##SIGNAL_SHAPES_PATH = 'vhbb_TH_Znn_13TeV_Signal.root'
#SIGNAL_SHAPES_PATH = '/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_7/src/HiggsAnalysis/CombinedLimit/V24/DC_VH_26_06_2017_newMVAid_BDTmin_0p2_split_copy/remove1/vhbb_TH_ZeeBDT_highpt.root'
## The name of the signal region bin in the signal region shapes file.
#SIGNAL_SHAPES_BIN = 'ZeeBDT_highpt'
## The path to the mlfit.root file.
#MLFIT_PATH = '/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_7/src/HiggsAnalysis/CombinedLimit/V24/DC_VH_26_06_2017_newMVAid_BDTmin_0p2_split_copy/remove1/mlfit.root'
## The name of the signal region bin in the mlfit.root file.
#MLFIT_BIN = 'Zee_BDT_highpt'
## The name of the branch containing the nominal BDT score.
#BDT_BRANCH = 'ZllBDT_highptCMVA.Nominal'

#TEST2
# The path to the signal region shapes file.
#SIGNAL_SHAPES_PATH = 'vhbb_TH_Znn_13TeV_Signal.root'
SIGNAL_SHAPES_PATH = '/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_7/src/HiggsAnalysis/CombinedLimit/V24/DC_VH_26_06_2017_newMVAid_BDTmin_0p2_split_copy/remove1/vhbb_TH_ZuuBDT_lowpt.root'
# The name of the signal region bin in the signal region shapes file.
SIGNAL_SHAPES_BIN = 'ZuuBDT_lowpt'
# The path to the mlfit.root file.
MLFIT_PATH = '/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_7/src/HiggsAnalysis/CombinedLimit/V24/DC_VH_26_06_2017_newMVAid_BDTmin_0p2_split_copy/remove1/mlfit.root'
# The name of the signal region bin in the mlfit.root file.
MLFIT_BIN = 'Zuu_BDT_lowpt'
# The name of the branch containing the nominal BDT score.
BDT_BRANCH = 'ZllBDT_lowptCMVA.Nominal'


PATH_ALL_DC = '/mnt/t3nfs01/data01/shome/gaperrin/VHbb/CMSSW_7_4_7/src/HiggsAnalysis/CombinedLimit/V24/DC_VH_26_06_2017_newMVAid_BDTmin_0p2_split_copy/remove1/'


# Adding all the bin, dc and branch information in a dictionnary. Allows to fill multiple branches in one single loop. Keys of the histo are dc/mlfit_BIN (they are identical for Zll).
#Order to fill the dic: [BDT_BRANCH, SIGNAL_SHAPES_PATH, SIGNAL_SHAPES_BIN, MLFIT_BIN]
DC_INFO_DIC = {
        'ZeeBDT_highpt':['ZllBDT_highptCMVA.Nominal',PATH_ALL_DC+'vhbb_TH_ZeeBDT_highpt.root','ZeeBDT_highpt','Zee_BDT_highpt'],
        'ZuuBDT_highpt':['ZllBDT_highptCMVA.Nominal',PATH_ALL_DC+'vhbb_TH_ZuuBDT_highpt.root','ZuuBDT_highpt','Zuu_BDT_highpt'],
        'ZeeBDT_lowpt': ['ZllBDT_lowptCMVA.Nominal', PATH_ALL_DC+'vhbb_TH_ZeeBDT_lowpt.root', 'ZeeBDT_lowpt', 'Zee_BDT_lowpt'],
        'ZuuBDT_lowpt': ['ZllBDT_lowptCMVA.Nominal', PATH_ALL_DC+'vhbb_TH_ZuuBDT_lowpt.root', 'ZuuBDT_lowpt', 'Zuu_BDT_lowpt']
        }

#
DC_INFO_DIC['MLFIT_PATH'] = PATH_ALL_DC+'/mlfit.root'


def get_shape_bin_edges_dic(dc_info_dic):
    bin_edges_dic = {}
    for key in dc_info_dic:
        if key == 'MLFIT_PATH': continue
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
        DC_INFO_DIC[key].append(signal_postfit_dic[key])
        DC_INFO_DIC[key].append(background_postfit_dic[key])


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
    print 'list of keys'
    ROOT.gDirectory.GetListOfKeys().ls()
    shapes_file.cd(datacard_bin)
    shapes = ROOT.gDirectory.GetListOfKeys()
    #print 'list of Keys is', ROOT.gDirectory.GetListOfKeys().ls()
    # Since the nominal and varied shapes share the same binning,
    # take any of the histograms found in the shapes file.
    shape = ROOT.gDirectory.Get(shapes[0].GetName())
    bin_edges = numpy.array(
        [shape.GetXaxis().GetBinLowEdge(i) for i in xrange(1, shape.GetNbinsX() + 1)],
        dtype=numpy.float64,
    )
    shapes_file.Close()
    #print 'bin_edges is', bin_edges
    #sys.exit()
    return bin_edges


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
    mlfit_file.cd('shapes_fit_s/{}'.format(datacard_bin))
    total_signal = ROOT.gDirectory.Get('total_signal')
    total_background = ROOT.gDirectory.Get('total_background')
    total_signal.SetDirectory(0)
    total_background.SetDirectory(0)
    mlfit_file.Close()
    signal_postfit = ROOT.TH1F('signal_postfit', '', len(bin_edges) - 1, bin_edges)
    background_postfit = signal_postfit.Clone('background_postfit')
    for i in xrange(1, signal_postfit.GetNbinsX() + 1):
        signal_postfit.SetBinContent(i, total_signal.GetBinContent(i))
        background_postfit.SetBinContent(i, total_background.GetBinContent(i))
    for s in signal_postfit:
        print 's is', s
    for b in background_postfit:
        print 'b is', b
    #print 'signal_postfit', signal_postfit
    #print 'background_postfit', background_postfit
    return signal_postfit, background_postfit


#def add_sb_weight(src, dst, bdt_branch, signal_postfit, background_postfit):
def add_sb_weight_dic(src, dst, dc_info_dic):
    """Add a branch named "sb_weight" which contains the per-event S/(S+B) weight
    for the events' corresponding bin in the signal region BDT score distribution.
    This is to be applied to all MC and data.

    Parameters
    ----------
    src : path
        The path to the input ntuple.
    dst : path
        The path to the output ntuple.
    bdt_branch : string
        The name of the branch containing the nominal BDT score.
    signal_postfit : ROOT.TH1F
        The postfit total signal shape.
    background_postfit : ROOT.TH1F
        The postfit total background shape.
    """
    logger = logging.getLogger('add_sb_weight')
    # Copy any count and weight histograms.
    # Get input and output tree
    infile = ROOT.TFile.Open(src)
    outfile = ROOT.TFile.Open(dst, 'recreate')
    for key in infile.GetListOfKeys():
        if key.GetName() == 'tree':
            continue
        obj = key.ReadObj()
        obj.Write()
    tree = infile.Get('tree')
    # Reset the branch in case it already exists.
    tree.SetBranchStatus('sb_weight*', 0)
    # Set the BDT branch address for faster reading, making
    # sure that Xbb-style leaflists are handled properly.
    bdt_buffer = {}
    leaf_index = {}
    for key in dc_info_dic:
        if key == 'MLFIT_PATH': continue
        bdt_branch = dc_info_dic[key][0]
        if '.' in bdt_branch:
            branch_name, leaf_name = bdt_branch.split('.')
            branch = tree.GetBranch(branch_name)
            n_leaves = branch.GetNleaves()
            leaf_index[bdt_branch] = [leaf.GetName() for leaf in branch.GetListOfLeaves()].index(leaf_name)
            bdt_buffer[bdt_branch] = numpy.zeros(n_leaves, dtype=numpy.float32)
        else:
            branch_name = bdt_branch
            leaf_index[bdt_branch] = None
            bdt_buffer[bdt_branch] = numpy.zeros(1, dtype=numpy.float32)
            print 'problem'
            sys.exit()
        tree.SetBranchAddress(branch_name, bdt_buffer[bdt_branch])
    # Clone the original tree and add the new branch.
    tree_new = tree.CloneTree(0)
    sb_weight_dic = {}
    for key in dc_info_dic:
        if key == 'MLFIT_PATH': continue
        sb_weight_dic[key] = numpy.zeros(1, dtype=numpy.float64)
        #sb_weight = numpy.zeros(1, dtype=numpy.float64)
        tree_new.Branch('sb_weight_%s'%key, sb_weight_dic[key], 'sb_weight_%s/D'%key)
        #tree_new.Branch('sb_weight', sb_weight, 'sb_weight/D')
    # Cache the Fill method for faster filling.
    fill_tree_new = tree_new.Fill
    for i, event in enumerate(tree, start=1):
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
            s = dc_info_dic[key][5].GetBinContent(bin_index)
            b = dc_info_dic[key][6].GetBinContent(bin_index)
            #s = signal_postfit.GetBinContent(bin_index)
            #b = background_postfit.GetBinContent(bin_index)
            sb_weight_dic[key][0] = s / (s + b) if b > 0 else 0
        fill_tree_new()
        if i % 1000 == 0 or sb_weight_dic[key][0] > 10:
            print 'i is', i
            logger.info('Processing Entry #%s: BDT Score = %s, S/(S+B) = %s', i, bdt_score, sb_weight_dic[key])
    tree_new.Write()
    outfile.Close()
    infile.Close()

def add_sb_weight(src, dst, bdt_branch, signal_postfit, background_postfit):
    """Add a branch named "sb_weight" which contains the per-event S/(S+B) weight
    for the events' corresponding bin in the signal region BDT score distribution.
    This is to be applied to all MC and data.

    Parameters
    ----------
    src : path
        The path to the input ntuple.
    dst : path
        The path to the output ntuple.
    bdt_branch : string
        The name of the branch containing the nominal BDT score.
    signal_postfit : ROOT.TH1F
        The postfit total signal shape.
    background_postfit : ROOT.TH1F
        The postfit total background shape.
    """
    logger = logging.getLogger('add_sb_weight')
    # Copy any count and weight histograms.
    infile = ROOT.TFile.Open(src)
    outfile = ROOT.TFile.Open(dst, 'recreate')
    for key in infile.GetListOfKeys():
        if key.GetName() == 'tree':
            continue
        obj = key.ReadObj()
        obj.Write()
    tree = infile.Get('tree')
    # Reset the branch in case it already exists.
    tree.SetBranchStatus('sb_weight', 0)
    # Set the BDT branch address for faster reading, making
    # sure that Xbb-style leaflists are handled properly.
    if '.' in bdt_branch:
        branch_name, leaf_name = bdt_branch.split('.')
        branch = tree.GetBranch(branch_name)
        n_leaves = branch.GetNleaves()
        leaf_index = [leaf.GetName() for leaf in branch.GetListOfLeaves()].index(leaf_name)
        bdt_buffer = numpy.zeros(n_leaves, dtype=numpy.float32)
    else:
        branch_name = bdt_branch
        leaf_index = None
        bdt_buffer = numpy.zeros(1, dtype=numpy.float32)
    tree.SetBranchAddress(branch_name, bdt_buffer)
    # Clone the original tree and add the new branch.
    tree_new = tree.CloneTree(0)
    sb_weight = numpy.zeros(1, dtype=numpy.float64)
    tree_new.Branch('sb_weight', sb_weight, 'sb_weight/D')
    # Cache the Fill method for faster filling.
    fill_tree_new = tree_new.Fill
    for i, event in enumerate(tree, start=1):
        # Find the BDT bin containing the event. If the event is
        # found in the underflow bin, use the first bin instead.
        bdt_score = bdt_buffer[0] if leaf_index is None else bdt_buffer[leaf_index]
        bin_index = signal_postfit.FindBin(bdt_score) or 1
        # Calculate the S/(S+B) weight for the event.
        s = signal_postfit.GetBinContent(bin_index)
        b = background_postfit.GetBinContent(bin_index)
        sb_weight[0] = s / (s + b) if b > 0 else 0
        fill_tree_new()
        if i % 1000 == 0 or sb_weight[0] > 10:
            logger.info('Processing Entry #%s: BDT Score = %s, S/(S+B) = %s', i, bdt_score, sb_weight)
    tree_new.Write()
    outfile.Close()
    infile.Close()


def main():
    #print 'DC_INFO_DIC before function is', DC_INFO_DIC
    #get_shape_bin_edges_dic(DC_INFO_DIC)
    #print 'DC_INFO_DIC after bin edge function is', DC_INFO_DIC
    #get_total_postfit_shapes_dic(DC_INFO_DIC)
    #print 'DC_INFO_DIC after postfit shape funciton is', DC_INFO_DIC
    #add_sb_weight_dic(sys.argv[1], sys.argv[2], DC_INFO_DIC)
    """Example usage:
    python add_sb_weight.py ZH_HToBB_ZToNuNu_M125_13TeV_powheg_pythia8.root ZH_HToBB_ZToNuNu_M125_13TeV_powheg_pythia8_new.root
    """
    logging.basicConfig(format='[%(name)s] %(levelname)s - %(message)s', level=logging.INFO)
    bin_edges = get_shape_bin_edges(SIGNAL_SHAPES_PATH, SIGNAL_SHAPES_BIN)
    signal_postfit, background_postfit = get_total_postfit_shapes(MLFIT_PATH, MLFIT_BIN, bin_edges)
    add_sb_weight(sys.argv[1], sys.argv[2], BDT_BRANCH, signal_postfit, background_postfit)


if __name__ == '__main__':

    status = main()
    sys.exit(status)

