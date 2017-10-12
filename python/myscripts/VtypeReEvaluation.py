#!/usr/bin/env python
import ROOT
import sys
import numpy as np

#!/usr/bin/env python
import ROOT
import sys
import numpy as np
from array import array

# RUN:
#
from array import array
#

# **********************************************************************************************************************
#

class CorrectionType:
    KINEMATIC, MC_AVERAGE_BORN, MC_ERROR_BORN, MC_AVERAGE_COMPLETE, MC_ERROR_COMPLETE,MC_AVERAGE_EW, MC_ERROR_EW, \
    MC_AVERAGE_QCD, MC_ERROR_QCD, MC_AVERAGE_INC_PHOTON, MC_ERROR_INC_PHOTON, MC_AVERAGE_INC_GLU, MC_ERROR_INC_GLU = range(13)

# **********************************************************************************************************************
#  Class to apply corrections text file
# **********************************************************************************************************************
class TreeCopierWithCorrectionFromFile:
    def __init__(self):
        self.corrections = {}
        self.delimiter = '  '
        self.commentsMarker = '#'

    def loadCorrections(self, corrections):
        for correction in corrections:
            with open(correction['file'], 'rb') as correctionFile:
                self.corrections[correction['name']] = np.genfromtxt(correctionFile, delimiter=self.delimiter, comments=self.commentsMarker)

    def getCorrection(self, name, v):
        index = self.corrections[name][:, CorrectionType.KINEMATIC].searchsorted(v)
        if index > len(self.corrections[name]) - 1:
            index = len(self.corrections[name]) - 1

        try:
            corr = self.corrections[name][index, CorrectionType.MC_AVERAGE_COMPLETE] / self.corrections[name][index, CorrectionType.MC_AVERAGE_BORN]
        except Exception as e:
            print "ERROR:", e, "=> set weight to 1"
            corr = 1

        return corr

    # ----------------------------------------------------------------------------------------------------------------------
    # copy the tree and add new branch with weight from text file
    # ----------------------------------------------------------------------------------------------------------------------
    def copy(self, inputFileName, outputFileName):

        ifile = ROOT.TFile.Open(inputFileName, "READ")
        ofile = ROOT.TFile.Open(outputFileName, "RECREATE")

        # copy other file objects
        ifile.cd()
        obj = ROOT.TObject
        for key in ROOT.gDirectory.GetListOfKeys():
            ifile.cd()
            obj = key.ReadObj()
            if obj.GetName() == 'tree':
                continue
            ofile.cd()
            obj.Write(key.GetName())

        ifile.cd()
        tree = ifile.Get('tree')
        ofile.cd()

        # clone TTree
        otree = tree.CloneTree(0)

        # ----------------------------------------------------------------------------------------------------------------------
        # set branches
        # ----------------------------------------------------------------------------------------------------------------------



        Vtype_new = array('f',[0])
        otree.Branch('Vtype_new',Vtype_new,'Vtype_new/F')

        vLeptonsBranches={}
        VBranches={}
        ##define Vleptons branch
        vLeptonsvar = ['pt', 'eta', 'phi', 'mass', 'relIso03', 'relIso04']
        for var in vLeptonsvar:
            #vLeptonsBranches[var] = np.array([0]*2, dtype=float)
            vLeptonsBranches[var] = np.zeros(21, dtype=np.float32)
            obranch = otree.Branch('vLeptons_new_%s'%var, vLeptonsBranches[var], 'vLeptons_new_%s[2]/F'%var)

        ##define Vleptons branch
        Vvar = ['pt', 'eta', 'phi', 'mass']
        LorentzDic = {'pt':'Pt','eta':'Eta','phi':'Phi','mass':'M'}
        for var in Vvar:
            #vLeptonsBranches[var] = np.array([0]*2, dtype=float)
            VBranches[var] = np.zeros(21, dtype=np.float32)
            obranch = otree.Branch('V_new_%s'%var, VBranches[var], 'V_new_%s/F'%var)

        # ----------------------------------------------------------------------------------------------------------------------
        # define all the lambda function
        # ----------------------------------------------------------------------------------------------------------------------

        #include the Vytpe reco here
        zEleSelection = lambda x : tree.selLeptons_pt[x] > 15 and tree.selLeptons_eleMVAIdSppring16GenPurp[x] >= 1
        zMuSelection = lambda x : tree.selLeptons_pt[x] > 15 and  tree.selLeptons_looseIdPOG[x] and tree.selLeptons_relIso04[x] < 0.25

        # ----------------------------------------------------------------------------------------------------------------------
        # apply corrections
        # ----------------------------------------------------------------------------------------------------------------------
        nEntries = tree.GetEntries()
        print "nEntries = ", nEntries
        for entry in range(nEntries):
            #if entry > 100:
            #    break
            #if entry % 10000 == 0:
            #    print "processing entry: %d"%entry

            tree.GetEntry(entry)

            #Variable to store Vtype and leptons info
            Vtype_new_ = -1
            V_mass_new = -1

            vLeptons_new = []
            #get all the lepton index
            lep_index = range(len(tree.selLeptons_pt))
            selectedElectrons = [i for i in  lep_index if abs(tree.selLeptons_pdgId[i]) == 11]
            selectedMuons =  [i for i in lep_index if abs(tree.selLeptons_pdgId[i]) == 13]

            zElectrons=[x for x in selectedElectrons if zEleSelection(x) ]
            zMuons=[x for x in selectedMuons if zMuSelection(x) ]

            zMuons.sort(key=lambda x:tree.selLeptons_pt[x],reverse=True)
            zElectrons.sort(key=lambda x:tree.selLeptons_pt[x],reverse=True)

            if len(zMuons) >=  2 :
                if tree.selLeptons_pt[zMuons[0]] > 20:
                    for i in zMuons[1:]:
                        if  tree.selLeptons_charge[zMuons[0]]*tree.selLeptons_charge[i] < 0:
                            #if tree.Vtype == 1:
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
                            #if tree.Vtype == 0:
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
                #to handle missasigned Vtype 4 or -1 because of addtional electron cut
                elif (tree.Vtype == 4 or tree.Vtype == -1) and len(zElectrons) + len(zMuons) > 0:
                    Vtype_new_ = 5
                #to handle missasigned Vtype 5 because of addtional electron cut
                elif tree.Vtype == 5 and len(zElectrons) + len(zMuons) == 0:
                    if tree.met_pt < 80:
                        Vtype_new_ = -1
                    else:
                        Vtype_new_ = 4
                #if none of the exception above happen, it is save to copy the Vtype
                else:
                    Vtype_new_ = tree.Vtype



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

            otree.Fill()

        # ----------------------------------------------------------------------------------------------------------------------
        # write and close files
        # ----------------------------------------------------------------------------------------------------------------------
        print "writing to file..."
        ofile.cd()
        otree.Write()

        ofile.Close()
        ifile.Close()

        print "done."

# **********************************************************************************************************************
#  main
# **********************************************************************************************************************
theTreeCopier = TreeCopierWithCorrectionFromFile()

#theTreeCopier.loadCorrections(corrections)

#if len(sys.argv) == 4:
#    theTreeCopier.copy(sys.argv[1], sys.argv[2], sys.argv[3])#sys.argv[3] should be the string "True" or "False"

theTreeCopier.copy(sys.argv[1], sys.argv[2])

#else:
#    print "syntax: {file} input.root output.root useNNLO".format(file=sys.argv[0] if len(sys.argv) > 0 else './file.py')
