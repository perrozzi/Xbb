#!/usr/bin/env python
import sys
import os,subprocess
import ROOT 
import math
import shutil
from array import array
import warnings
warnings.filterwarnings( action='ignore', category=RuntimeWarning, message='creating converter.*' )
ROOT.gROOT.SetBatch(True)
from optparse import OptionParser

#usage: ./write_regression_systematic.py path

#os.mkdir(path+'/sys')
argv = sys.argv
parser = OptionParser()
#parser.add_option("-P", "--path", dest="path", default="", 
#                      help="path to samples")
parser.add_option("-S", "--samples", dest="names", default="", 
                      help="samples you want to run on")
parser.add_option("-C", "--config", dest="config", default=[], action="append",
                      help="configuration defining the plots to make")
(opts, args) = parser.parse_args(argv)
if opts.config =="":
        opts.config = "config"

from myutils import BetterConfigParser, ParseInfo, TreeCache

print opts.config
config = BetterConfigParser()
config.read(opts.config)
anaTag = config.get("Analysis","tag")
TrainFlag = eval(config.get('Analysis','TrainFlag'))
btagLibrary = config.get('BTagReshaping','library')
samplesinfo=config.get('Directories','samplesinfo')

VHbbNameSpace=config.get('VHbbNameSpace','library')
ROOT.gSystem.Load(VHbbNameSpace)
AngLikeBkgs=eval(config.get('AngularLike','backgrounds'))
ang_yield=eval(config.get('AngularLike','yields'))

#path=opts.path
pathIN = config.get('Directories','SYSin')
pathOUT = config.get('Directories','SYSout')
tmpDir = os.environ["TMPDIR"]

print 'INput samples:\t%s'%pathIN
print 'OUTput samples:\t%s'%pathOUT


#storagesamples = config.get('Directories','storagesamples')


namelist=opts.names.split(',')

#load info
info = ParseInfo(samplesinfo,pathIN)

def deltaPhi(phi1, phi2): 
    result = phi1 - phi2
    while (result > math.pi): result -= 2*math.pi
    while (result <= -math.pi): result += 2*math.pi
    return result

def addAdditionalJets(H, tree):
    for i in range(tree.nhjidxaddJetsdR08):
        idx = tree.hjidxaddJetsdR08[i]
        if (idx == tree.hJCidx[0]) or (idx == tree.hJCidx[1]): continue
        addjet = ROOT.TLorentzVector()
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
#    return (pt+resolutionBias(math.fabs(eta))*(pt-mcPt))/pt

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


for job in info:
    if not job.name in namelist: continue
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
    if anaTag == '7TeV':
        ROOT.gSystem.Load(btagLibrary)
        from ROOT import BTagShape
        btagNom = BTagShape("../data/csvdiscr.root")
        btagNom.computeFunctions()
        btagUp = BTagShape("../data/csvdiscr.root")
        btagUp.computeFunctions(+1.,0.)
        btagDown = BTagShape("../data/csvdiscr.root")
        btagDown.computeFunctions(-1.,0.)
        btagFUp = BTagShape("../data/csvdiscr.root")
        btagFUp.computeFunctions(0.,+1.)
        btagFDown = BTagShape("../data/csvdiscr.root")
        btagFDown.computeFunctions(0.,-1.)
    else:
        ROOT.gSystem.Load(btagLibrary)
        from ROOT import BTagShapeInterface
        btagNom = BTagShapeInterface("../data/csvdiscr.root",0,0)
        btagUp = BTagShapeInterface("../data/csvdiscr.root",+1,0)
        btagDown = BTagShapeInterface("../data/csvdiscr.root",-1,0)
        btagFUp = BTagShapeInterface("../data/csvdiscr.root",0,+1.)
        btagFDown = BTagShapeInterface("../data/csvdiscr.root",0,-1.)
    
    lhe_weight_map = False if not config.has_option('LHEWeights', 'weights_per_bin') else eval(config.get('LHEWeights', 'weights_per_bin'))
    
    
    print '\t - %s' %(job.name)
    print('opening '+pathIN+'/'+job.prefix+job.identifier+'.root')
    input = ROOT.TFile.Open(pathIN+'/'+job.prefix+job.identifier+'.root','read')
    output = ROOT.TFile.Open(tmpDir+'/'+job.prefix+job.identifier+'.root','recreate')
    print
    print "Writing: ",tmpDir+'/'+job.prefix+job.identifier+'.root'
    print

    input.cd()
    if lhe_weight_map and 'DY' in job.name:
        inclusiveJob = info.get_sample('DY')
        print inclusiveJob.name
        inclusive = ROOT.TFile.Open(pathIN+inclusiveJob.get_path,'read')
        inclusive.cd()
        obj = ROOT.TObject
        for key in ROOT.gDirectory.GetListOfKeys():
            input.cd()
            obj = key.ReadObj()
            if obj.GetName() == job.tree:
                continue
            output.cd()
            obj.Write(key.GetName())
        inclusive.Close()
    else:
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
    
#    tree.SetBranchStatus('H',0)
    output.cd()
    newtree = tree.CloneTree(0)
        
    hJ0 = ROOT.TLorentzVector()
    hJ1 = ROOT.TLorentzVector()
    vect = ROOT.TLorentzVector()
    #hFJ0 = ROOT.TLorentzVector()
    #hFJ1 = ROOT.TLorentzVector()
        
    writeNewVariables = eval(config.get("Regression","writeNewVariables"))
    regWeight = config.get("Regression","regWeight")
    regDict = eval(config.get("Regression","regDict"))
    regVars = eval(config.get("Regression","regVars"))
    #regWeightFilterJets = config.get("Regression","regWeightFilterJets")
    #regDictFilterJets = eval(config.get("Regression","regDictFilterJets"))
    #regVarsFilterJets = eval(config.get("Regression","regVarsFilterJets"))

    #Regression branches
    applyRegression = True
#    hJet_pt = array('f',[0]*2)
#    hJet_mass = array('f',[0]*2)
    newtree.Branch( 'H', H , 'HiggsFlag/I:mass/F:pt/F:eta/F:phi/F:dR/F:dPhi/F:dEta/F' )
    newtree.Branch( 'HNoReg', HNoReg , 'HiggsFlag/I:mass/F:pt/F:eta/F:phi/F:dR/F:dPhi/F:dEta/F' )
    newtree.Branch( 'HaddJetsdR08', HaddJetsdR08 , 'HiggsFlag/I:mass/F:pt/F:eta/F:phi/F:dR/F:dPhi/F:dEta/F' )
    newtree.Branch( 'HaddJetsdR08NoReg', HaddJetsdR08NoReg , 'HiggsFlag/I:mass/F:pt/F:eta/F:phi/F:dR/F:dPhi/F:dEta/F' )
    #FatHReg = array('f',[0]*2) 
    #newtree.Branch('FatHReg',FatHReg,'filteredmass:filteredpt/F')
    Event = array('f',[0])
    METet = array('f',[0])
    rho = array('f',[0])
    METphi = array('f',[0])
    frho = ROOT.TTreeFormula("rho",'rho',tree)
    fEvent = ROOT.TTreeFormula("Event",'evt',tree)
    fFatHFlag = ROOT.TTreeFormula("FatHFlag",'nFatjetCA15trimmed>0',tree)
    fFatHnFilterJets = ROOT.TTreeFormula("FatHnFilterJets",'nFatjetCA15ungroomed',tree)
    fMETet = ROOT.TTreeFormula("METet",'met_pt',tree)
    fMETphi = ROOT.TTreeFormula("METphi",'met_phi',tree)
    fHVMass = ROOT.TTreeFormula("HVMass",'VHbb::HV_mass(H_pt,H_eta,H_phi,H_mass,V_pt,V_eta,V_phi,V_mass)',tree)
    hJet_MtArray = [array('f',[0]),array('f',[0])]
    hJet_etarray = [array('f',[0]),array('f',[0])]
    hJet_MET_dPhi = array('f',[0]*2)
    hJet_regWeight = array('f',[0]*2)
    fathFilterJets_regWeight = array('f',[0]*2)
    hJet_MET_dPhiArray = [array('f',[0]),array('f',[0])]
    hJet_rawPtArray = [array('f',[0]),array('f',[0])]
    newtree.Branch('hJet_MET_dPhi',hJet_MET_dPhi,'hJet_MET_dPhi[2]/F')
    newtree.Branch('hJet_regWeight',hJet_regWeight,'hJet_regWeight[2]/F')
    readerJet0 = ROOT.TMVA.Reader("!Color:!Silent" )
    readerJet1 = ROOT.TMVA.Reader("!Color:!Silent" )

    readerJet0_JER_up = ROOT.TMVA.Reader("!Color:!Silent" )
    readerJet1_JER_up = ROOT.TMVA.Reader("!Color:!Silent" )
    readerJet0_JER_down = ROOT.TMVA.Reader("!Color:!Silent" )
    readerJet1_JER_down = ROOT.TMVA.Reader("!Color:!Silent" )
    readerJet0_JEC_up = ROOT.TMVA.Reader("!Color:!Silent" )
    readerJet1_JEC_up = ROOT.TMVA.Reader("!Color:!Silent" )
    readerJet0_JEC_down = ROOT.TMVA.Reader("!Color:!Silent" )
    readerJet1_JEC_down = ROOT.TMVA.Reader("!Color:!Silent" )

    theForms = {}
    theVars0 = {}
    theVars1 = {}
    theVars0_JER_up = {}
    theVars1_JER_up = {}
    theVars0_JER_down = {}
    theVars1_JER_down = {}
    theVars0_JEC_up = {}
    theVars1_JEC_up = {}
    theVars0_JEC_down = {}
    theVars1_JEC_down = {}

    def addVarsToReader(reader,regDict,regVars,theVars,theForms,i,hJet_MET_dPhiArray,METet,rho,hJet_MtArray,hJet_etarray,hJet_rawPtArray,syst=""):
#        print "regDict: ",regDict
#        print "regVars: ",regVars
        for key in regVars:
            var = regDict[key]
            theVars[key+syst] = array( 'f', [ 0 ] )
            reader.AddVariable(key,theVars[key+syst])
            formulaX = var
            brakets = ""
            if formulaX.find("[hJCidx[0]]"): brakets = "[hJCidx[0]]"
            elif formulaX.find("[hJCidx[1]]"): brakets = "[hJCidx[1]]"
            elif formulaX.find("[0]"): brakets = "[0]"
            elif formulaX.find("[1]"): brakets = "[1]"
            else: pass

            formulaX = formulaX.replace(brakets,"[X]")

            if syst == "":
                pass
#                formulaX = formulaX.replace("Jet_pt[X]","Jet_rawPt[X]*Jet_corr[X]*Jet_corr_JER[X]")
            elif syst == "JER_up":
                formulaX = formulaX.replace("Jet_pt[X]","Jet_rawPt[X]*Jet_corr[X]*Jet_corr_JERUp[X]")
            elif syst == "JER_down":
                formulaX = formulaX.replace("Jet_pt[X]","Jet_rawPt[X]*Jet_corr[X]*Jet_corr_JERDown[X]")
            elif syst == "JEC_up":
                formulaX = formulaX.replace("Jet_pt[X]","Jet_rawPt[X]*Jet_corr_JECUp[X]*Jet_corr_JER[X]")
            elif syst == "JEC_down":
                formulaX = formulaX.replace("Jet_pt[X]","Jet_rawPt[X]*Jet_corr_JECDown[X]*Jet_corr_JER[X]")
            else:
                raise Exception(syst," is unknown!")

            formula = formulaX.replace("[X]",brakets)
            formula = formula.replace("[0]","[%.0f]" %i)
            theForms['form_reg_%s_%.0f'%(key+syst,i)] = ROOT.TTreeFormula("form_reg_%s_%.0f"%(key+syst,i),'%s' %(formula),tree)
        return 

    addVarsToReader(readerJet0,regDict,regVars,theVars0,theForms,0,hJet_MET_dPhiArray,METet,rho,hJet_MtArray,hJet_etarray,hJet_rawPtArray)    
    addVarsToReader(readerJet1,regDict,regVars,theVars1,theForms,1,hJet_MET_dPhiArray,METet,rho,hJet_MtArray,hJet_etarray,hJet_rawPtArray)    
    if job.type != 'DATA':
        addVarsToReader(readerJet0_JER_up,regDict,regVars,theVars0,theForms,0,hJet_MET_dPhiArray,METet,rho,hJet_MtArray,hJet_etarray,hJet_rawPtArray,"JER_up")
        addVarsToReader(readerJet1_JER_up,regDict,regVars,theVars1,theForms,1,hJet_MET_dPhiArray,METet,rho,hJet_MtArray,hJet_etarray,hJet_rawPtArray,"JER_up")
        addVarsToReader(readerJet0_JER_down,regDict,regVars,theVars0,theForms,0,hJet_MET_dPhiArray,METet,rho,hJet_MtArray,hJet_etarray,hJet_rawPtArray,"JER_down")
        addVarsToReader(readerJet1_JER_down,regDict,regVars,theVars1,theForms,1,hJet_MET_dPhiArray,METet,rho,hJet_MtArray,hJet_etarray,hJet_rawPtArray,"JER_down")
        addVarsToReader(readerJet0_JEC_up,regDict,regVars,theVars0,theForms,0,hJet_MET_dPhiArray,METet,rho,hJet_MtArray,hJet_etarray,hJet_rawPtArray,"JEC_up")
        addVarsToReader(readerJet1_JEC_up,regDict,regVars,theVars1,theForms,1,hJet_MET_dPhiArray,METet,rho,hJet_MtArray,hJet_etarray,hJet_rawPtArray,"JEC_up")
        addVarsToReader(readerJet0_JEC_down,regDict,regVars,theVars0,theForms,0,hJet_MET_dPhiArray,METet,rho,hJet_MtArray,hJet_etarray,hJet_rawPtArray,"JEC_down")
        addVarsToReader(readerJet1_JEC_down,regDict,regVars,theVars1,theForms,1,hJet_MET_dPhiArray,METet,rho,hJet_MtArray,hJet_etarray,hJet_rawPtArray,"JEC_down")

    readerJet0.BookMVA( "jet0Regression", regWeight )
    readerJet1.BookMVA( "jet1Regression", regWeight )
    
    if job.type != 'DATA':
        readerJet0_JER_up.BookMVA( "jet0Regression", regWeight )
        readerJet1_JER_up.BookMVA( "jet1Regression", regWeight )
        readerJet0_JER_down.BookMVA( "jet0Regression", regWeight )
        readerJet1_JER_down.BookMVA( "jet1Regression", regWeight )

        readerJet0_JEC_up.BookMVA( "jet0Regression", regWeight )
        readerJet1_JEC_up.BookMVA( "jet1Regression", regWeight )
        readerJet0_JEC_down.BookMVA( "jet0Regression", regWeight )
        readerJet1_JEC_down.BookMVA( "jet1Regression", regWeight )

        
    #Add training Flag
    EventForTraining = array('i',[0])
    newtree.Branch('EventForTraining',EventForTraining,'EventForTraining/I')
    EventForTraining[0]=0

    TFlag=ROOT.TTreeFormula("EventForTraining","evt%2",tree)

    #Angular Likelihood
    angleHB = array('f',[0])
    newtree.Branch('angleHB',angleHB,'angleHB/F')
    angleLZ = array('f',[0])
    newtree.Branch('angleLZ',angleLZ,'angleLZ/F')
    angleZZS = array('f',[0])
    newtree.Branch('angleZZS',angleZZS,'angleZZS/F')
    kinLikeRatio = array('f',[0]*len(AngLikeBkgs))
    newtree.Branch('kinLikeRatio',kinLikeRatio,'%s/F' %(':'.join(AngLikeBkgs)))
    fAngleHB = ROOT.TTreeFormula("fAngleHB",'abs(VHbb::ANGLEHB(Jet_pt[hJCidx[0]],Jet_eta[hJCidx[0]],Jet_phi[hJCidx[0]],Jet_mass[hJCidx[0]],Jet_pt[hJCidx[1]],Jet_eta[hJCidx[1]],Jet_phi[hJCidx[1]],Jet_mass[hJCidx[1]]))',newtree)
    fAngleLZ = ROOT.TTreeFormula("fAngleLZ",'abs(VHbb::ANGLELZ(vLeptons_pt[hJCidx[0]],vLeptons_eta[hJCidx[0]],vLeptons_phi[hJCidx[0]],vLeptons_mass[hJCidx[0]],vLeptons_pt[hJCidx[1]],vLeptons_eta[hJCidx[1]],vLeptons_phi[hJCidx[1]],vLeptons_mass[hJCidx[1]]))',newtree)
    fAngleZZS = ROOT.TTreeFormula("fAngleZZS",'abs(VHbb::ANGLELZ(H_pt,H_eta,H_phi,H_pt,V_pt,V_eta,V_phi,V_mass))',newtree)
    fVpt = ROOT.TTreeFormula("fVpt",'V_pt',tree)
    fVeta = ROOT.TTreeFormula("fVeta",'V_eta',tree)
    fVphi = ROOT.TTreeFormula("fVphi",'V_phi',tree)
    fVmass = ROOT.TTreeFormula("fVmass",'V_mass',tree)
    likeSBH = array('f',[0]*len(AngLikeBkgs))
    likeBBH = array('f',[0]*len(AngLikeBkgs))
    likeSLZ = array('f',[0]*len(AngLikeBkgs))
    likeBLZ = array('f',[0]*len(AngLikeBkgs))
    likeSZZS = array('f',[0]*len(AngLikeBkgs))
    likeBZZS = array('f',[0]*len(AngLikeBkgs))
    likeSMassZS = array('f',[0]*len(AngLikeBkgs))
    likeBMassZS = array('f',[0]*len(AngLikeBkgs))
    HVMass_Reg = array('f',[0])
    newtree.Branch('HVMass_Reg',HVMass_Reg,'HVMass_Reg/F')

    SigBH = []; BkgBH = []; SigLZ = []; BkgLZ = []; SigZZS = []; BkgZZS = []; SigMassZS = []; BkgMassZS = [];
#    for angLikeBkg in AngLikeBkgs:
#        f = ROOT.TFile("../data/angleFitFunctions-%s.root"%(angLikeBkg),"READ")
#        SigBH.append(f.Get("sigFuncBH"))
#        BkgBH.append(f.Get("bkgFuncBH"))
#        SigLZ.append(f.Get("sigFuncLZ"))
#        BkgLZ.append(f.Get("bkgFuncLZ"))
#        SigZZS.append(f.Get("sigFuncZZS"))
#        BkgZZS.append(f.Get("bkgFuncZZS"))
#        SigMassZS.append(f.Get("sigFuncMassZS"))
#        BkgMassZS.append(f.Get("bkgFuncMassZS"))
#        f.Close()

        
#    if job.type != 'DATA': ##FIXME###
    if True:
        #CSV branches
        hJet_hadronFlavour = array('f',[0]*2)
        hJet_btagCSV = array('f',[0]*2)
        hJet_btagCSVOld = array('f',[0]*2)
        hJet_btagCSVUp = array('f',[0]*2)
        hJet_btagCSVDown = array('f',[0]*2)
        hJet_btagCSVFUp = array('f',[0]*2)
        hJet_btagCSVFDown = array('f',[0]*2)
        newtree.Branch('hJet_btagCSV',hJet_btagCSV,'hJet_btagCSV[2]/F')
        newtree.Branch('hJet_btagCSVOld',hJet_btagCSVOld,'hJet_btagCSVOld[2]/F')
        newtree.Branch('hJet_btagCSVUp',hJet_btagCSVUp,'hJet_btagCSVUp[2]/F')
        newtree.Branch('hJet_btagCSVDown',hJet_btagCSVDown,'hJet_btagCSVDown[2]/F')
        newtree.Branch('hJet_btagCSVFUp',hJet_btagCSVFUp,'hJet_btagCSVFUp[2]/F')
        newtree.Branch('hJet_btagCSVFDown',hJet_btagCSVFDown,'hJet_btagCSVFDown[2]/F')
        
        #JER branches
        hJet_pt_JER_up = array('f',[0]*2)
        newtree.Branch('hJet_pt_JER_up',hJet_pt_JER_up,'hJet_pt_JER_up[2]/F')
        hJet_pt_JER_down = array('f',[0]*2)
        newtree.Branch('hJet_pt_JER_down',hJet_pt_JER_down,'hJet_pt_JER_down[2]/F')
        hJet_mass_JER_up = array('f',[0]*2)
        newtree.Branch('hJet_mass_JER_up',hJet_mass_JER_up,'hJet_mass_JER_up[2]/F')
        hJet_mass_JER_down = array('f',[0]*2)
        newtree.Branch('hJet_mass_JER_down',hJet_mass_JER_down,'hJet_mass_JER_down[2]/F')
        H_JER = array('f',[0]*4)
        newtree.Branch('H_JER',H_JER,'mass_up:mass_down:pt_up:pt_down/F')
        HVMass_JER_up = array('f',[0])
        HVMass_JER_down = array('f',[0])
        newtree.Branch('HVMass_JER_up',HVMass_JER_up,'HVMass_JER_up/F')
        newtree.Branch('HVMass_JER_down',HVMass_JER_down,'HVMass_JER_down/F')
        angleHB_JER_up = array('f',[0])
        angleHB_JER_down = array('f',[0])
        angleZZS_JER_up = array('f',[0])
        angleZZS_JER_down = array('f',[0])
        newtree.Branch('angleHB_JER_up',angleHB_JER_up,'angleHB_JER_up/F')
        newtree.Branch('angleHB_JER_down',angleHB_JER_down,'angleHB_JER_down/F')
        newtree.Branch('angleZZS_JER_up',angleZZS_JER_up,'angleZZS_JER_up/F')
        newtree.Branch('angleZZS_JER_down',angleZZS_JER_down,'angleZZS_JER_down/F')
        
        hJet_ptOld = array('f',[0]*2)
        newtree.Branch('hJet_ptOld',hJet_ptOld,'hJet_ptOld[2]/F')

        hJet_pt = array('f',[0]*2)
        newtree.Branch('hJet_pt',hJet_pt,'hJet_pt[2]/F')

        hJet_ptMc = array('f',[0]*2)
        newtree.Branch('hJet_ptMc',hJet_ptMc,'hJet_ptMc[2]/F')

        hJet_mass = array('f',[0]*2)
        newtree.Branch('hJet_mass',hJet_mass,'hJet_mass[2]/F')

        hJet_eta = array('f',[0]*2)
        newtree.Branch('hJet_eta',hJet_eta,'hJet_eta[2]/F')

        hJet_phi = array('f',[0]*2)
        newtree.Branch('hJet_phi',hJet_phi,'hJet_phi[2]/F')


        #JES branches
        hJet_pt_JES_up = array('f',[0]*2)
        newtree.Branch('hJet_pt_JES_up',hJet_pt_JES_up,'hJet_pt_JES_up[2]/F')
        hJet_pt_JES_down = array('f',[0]*2)
        newtree.Branch('hJet_pt_JES_down',hJet_pt_JES_down,'hJet_pt_JES_down[2]/F')
        hJet_mass_JES_up = array('f',[0]*2)
        newtree.Branch('hJet_mass_JES_up',hJet_mass_JES_up,'hJet_mass_JES_up[2]/F')
        hJet_mass_JES_down = array('f',[0]*2)
        newtree.Branch('hJet_mass_JES_down',hJet_mass_JES_down,'hJet_mass_JES_down[2]/F')
        H_JES = array('f',[0]*4)
        newtree.Branch('H_JES',H_JES,'mass_up:mass_down:pt_up:pt_down/F')
        HVMass_JES_up = array('f',[0])
        HVMass_JES_down = array('f',[0])
        newtree.Branch('HVMass_JES_up',HVMass_JES_up,'HVMass_JES_up/F')
        newtree.Branch('HVMass_JES_down',HVMass_JES_down,'HVMass_JES_down/F')
        angleHB_JES_up = array('f',[0])
        angleHB_JES_down = array('f',[0])
        angleZZS_JES_up = array('f',[0])
        angleZZS_JES_down = array('f',[0])
        newtree.Branch('angleHB_JES_up',angleHB_JES_up,'angleHB_JES_up/F')
        newtree.Branch('angleHB_JES_down',angleHB_JES_down,'angleHB_JES_down/F')
        newtree.Branch('angleZZS_JES_up',angleZZS_JES_up,'angleZZS_JES_up/F')
        newtree.Branch('angleZZS_JES_down',angleZZS_JES_down,'angleZZS_JES_down/F')
    
        #Formulas for syst in angular
        fAngleHB_JER_up = ROOT.TTreeFormula("fAngleHB_JER_up",'abs(VHbb::ANGLEHBWithM(hJet_pt_JER_up[0],Jet_eta[hJCidx[0]],Jet_phi[hJCidx[0]],hJet_mass_JER_up[0],hJet_pt_JER_up[1],Jet_eta[hJCidx[1]],Jet_phi[hJCidx[1]],hJet_mass_JER_up[1]))',newtree)
        fAngleHB_JER_down = ROOT.TTreeFormula("fAngleHB_JER_down",'abs(VHbb::ANGLEHBWithM(hJet_pt_JER_down[0],Jet_eta[hJCidx[0]],Jet_phi[hJCidx[0]],hJet_mass_JER_down[0],hJet_pt_JER_down[1],Jet_eta[hJCidx[1]],Jet_phi[hJCidx[1]],hJet_mass_JER_down[1]))',newtree)
        fAngleHB_JES_up = ROOT.TTreeFormula("fAngleHB_JES_up",'abs(VHbb::ANGLEHBWithM(hJet_pt_JES_up[0],Jet_eta[hJCidx[0]],Jet_phi[hJCidx[0]],hJet_mass_JES_up[0],hJet_pt_JES_up[1],Jet_eta[hJCidx[1]],Jet_phi[hJCidx[1]],hJet_mass_JES_up[1]))',newtree)
        fAngleHB_JES_down = ROOT.TTreeFormula("fAngleHB_JES_down",'abs(VHbb::ANGLEHBWithM(hJet_pt_JES_down[0],Jet_eta[hJCidx[0]],Jet_phi[hJCidx[0]],hJet_mass_JES_down[0],hJet_pt_JES_down[1],Jet_eta[hJCidx[1]],Jet_phi[hJCidx[1]],hJet_mass_JES_down[1]))',newtree)
        fAngleZZS_JER_up = ROOT.TTreeFormula("fAngleZZS_JER_Up",'abs(VHbb::ANGLELZ(H_JER.pt_up,H_eta,H_phi,H_JER.pt_up,V_pt,V_eta,V_phi,V_mass))',newtree)
        fAngleZZS_JER_down = ROOT.TTreeFormula("fAngleZZS_JER_Down",'abs(VHbb::ANGLELZ(H_JER.pt_down,H_eta,H_phi,H_JER.pt_down,V_pt,V_eta,V_phi,V_mass))',newtree)
        fAngleZZS_JES_up = ROOT.TTreeFormula("fAngleZZS_JES_Up",'abs(VHbb::ANGLELZ(H_JER.pt_up,H_eta,H_phi,H_JER.pt_up,V_pt,V_eta,V_phi,V_mass))',newtree)
        fAngleZZS_JES_down = ROOT.TTreeFormula("fAngleZZS_JES_Down",'abs(VHbb::ANGLELZ(H_JER.pt_down,H_eta,H_phi,H_JER.pt_down,V_pt,V_eta,V_phi,V_mass))',newtree)
        lheWeight = array('f',[0])
        newtree.Branch('lheWeight',lheWeight,'lheWeight/F')
        theBinForms = {}
        if lhe_weight_map and 'DY' in job.name:
            for bin in lhe_weight_map:
                theBinForms[bin] = ROOT.TTreeFormula("Bin_formula_%s"%(bin),bin,tree)
        else:
            lheWeight[0] = 1.
        
    ### Adding new variable from configuration ###
    newVariableNames = []
    try:
        writeNewVariables = eval(config.get("Regression","writeNewVariables"))
        newVariableNames = writeNewVariables.keys()
        newVariables = {}
        newVariableFormulas = {}
        for variableName in newVariableNames:
            newVariables[variableName] = array('f',[0])
            newtree.Branch(variableName,newVariables[variableName],variableName+'/F')
            newVariableFormulas[variableName] =ROOT.TTreeFormula(variableName,writeNewVariables[variableName],tree)
            print "adding variable ",variableName,", using formula",writeNewVariables[variableName]," ."
    except:
        pass

    for entry in range(0,nEntries):
            tree.GetEntry(entry)
            
            ### Fill new variable from configuration ###
            for variableName in newVariableNames:
                newVariableFormulas[variableName].GetNdata()
                newVariables[variableName][0] = newVariableFormulas[variableName].EvalInstance()

            if tree.nJet<=tree.hJCidx[0] or tree.nJet<=tree.hJCidx[1]:
                print('tree.nJet<=tree.hJCidx[0] or tree.nJet<=tree.hJCidx[1]',tree.nJet,tree.hJCidx[0],tree.hJCidx[1])
                print('skip event')
                newtree.Fill()
                continue
            if job.type != 'DATA':
                EventForTraining[0]=int(not TFlag.EvalInstance())
            if lhe_weight_map and 'DY' in job.name:
                match_bin = None
                for bin in lhe_weight_map:
                    if theBinForms[bin].EvalInstance() > 0.:
                        match_bin = bin
                if match_bin:
                    lheWeight[0] = lhe_weight_map[match_bin]
                else:
                    lheWeight[0] = 1.

            #Has fat higgs
            #fatHiggsFlag=fFatHFlag.EvalInstance()*fFatHnFilterJets.EvalInstance()

            # get
            vect.SetPtEtaPhiM(fVpt.EvalInstance(),fVeta.EvalInstance(),fVphi.EvalInstance(),fVmass.EvalInstance())
            # print tree.Jet_pt
            # print tree.hJCidx
            # hJet_pt = tree.Jet_pt[tree.hJCidx]
            # hJet_mass = tree.Jet_mass[tree.hJCidx]

            ##FIXME##
            try:
                hJet_pt0 = tree.Jet_pt[tree.hJCidx[0]]
                hJet_pt1 = tree.Jet_pt[tree.hJCidx[1]]
            except:
                print "tree.nhJCidx",tree.nhJCidx
                print "tree.nJet",tree.nJet
                print "tree.hJCidx[0]",tree.hJCidx[0]
                print "tree.hJCidx[1]",tree.hJCidx[1]
                if tree.hJCidx[1] >=tree.nJet : tree.hJCidx[1] =1
                if tree.hJCidx[0] >=tree.nJet : tree.hJCidx[0] =0
                

            hJet_pt[0] = hJet_pt0
            hJet_pt[1] = hJet_pt1
            hJet_mass0 = tree.Jet_mass[tree.hJCidx[0]]
            hJet_mass1 = tree.Jet_mass[tree.hJCidx[1]]
            if job.type != 'DATA': hJet_mcPt0 = tree.Jet_mcPt[tree.hJCidx[0]]
            if job.type != 'DATA': hJet_mcPt1 = tree.Jet_mcPt[tree.hJCidx[1]]
            hJet_rawPt0 = tree.Jet_rawPt[tree.hJCidx[0]]
            hJet_rawPt1 = tree.Jet_rawPt[tree.hJCidx[1]]
            hJet_phi0 = tree.Jet_phi[tree.hJCidx[0]]
            hJet_phi1 = tree.Jet_phi[tree.hJCidx[1]]
            hJet_eta0 = tree.Jet_eta[tree.hJCidx[0]]
            hJet_eta1 = tree.Jet_eta[tree.hJCidx[1]]

#            ## NB. Jet_corr_JECUp - Jet_corr = Jet_corr - Jet_corr_JECDown
#            hJet_JECUnc0 = tree.Jet_corr_JECUp[tree.hJCidx[0]] - tree.Jet_corr[tree.hJCidx[0]]
#            hJet_JECUnc1 = tree.Jet_corr_JECUp[tree.hJCidx[1]] - tree.Jet_corr[tree.hJCidx[1]]

            hJet_ptOld[0] = tree.Jet_pt[tree.hJCidx[0]]
            hJet_ptOld[1] = tree.Jet_pt[tree.hJCidx[1]]
            if job.type != 'DATA': hJet_ptMc[0] = tree.Jet_mcPt[tree.hJCidx[0]]
            if job.type != 'DATA': hJet_ptMc[1] = tree.Jet_mcPt[tree.hJCidx[1]]
            hJet_phi[0] = tree.Jet_phi[tree.hJCidx[0]]
            hJet_phi[1] = tree.Jet_phi[tree.hJCidx[1]]
            hJet_eta[0] = tree.Jet_eta[tree.hJCidx[0]]
            hJet_eta[1] = tree.Jet_eta[tree.hJCidx[1]]
            hJet_mass[0] = tree.Jet_mass[tree.hJCidx[0]]
            hJet_mass[1] = tree.Jet_mass[tree.hJCidx[1]]


            # Filterjets
            # if fatHiggsFlag:
               # fathFilterJets_pt0 = tree.fathFilterJets_pt[tree.hJCidx[0]]
               # fathFilterJets_pt1 = tree.fathFilterJets_pt[tree.hJCidx[1]]
               # fathFilterJets_eta0 = tree.fathFilterJets_eta[tree.hJCidx[0]]
               # fathFilterJets_eta1 = tree.fathFilterJets_eta[tree.hJCidx[1]]
               # fathFilterJets_phi0 = tree.fathFilterJets_phi[tree.hJCidx[0]]
               # fathFilterJets_phi1 = tree.fathFilterJets_phi[tree.hJCidx[1]]
               # fathFilterJets_e0 = tree.fathFilterJets_e[tree.hJCidx[0]]
               # fathFilterJets_e1 = tree.fathFilterJets_e[tree.hJCidx[1]]
            Event[0]=fEvent.EvalInstance()
            METet[0]=fMETet.EvalInstance()
            rho[0]=frho.EvalInstance()
            METphi[0]=fMETphi.EvalInstance()
            for key, value in regDict.items():
#                if not (value == 'hJet_MET_dPhi' or value == 'METet' or value == "rho" or value == "hJet_et" or value == 'hJet_mt' or value == 'hJet_rawPt'):
                for syst in ["","JER_up","JER_down","JEC_up","JEC_down"]:
                    if job.type == 'DATA' and not syst is "": continue
                    theForms["form_reg_%s_0" %(key+syst)].GetNdata();
                    theForms["form_reg_%s_1" %(key+syst)].GetNdata();
                    theVars0[key+syst][0] = theForms["form_reg_%s_0" %(key+syst)].EvalInstance()
                    theVars1[key+syst][0] = theForms["form_reg_%s_1" %(key+syst)].EvalInstance()
            #for key, value in regDictFilterJets.items():
            #    if not (value == 'hJet_MET_dPhi' or value == 'METet' or value == "rho" or value == "hJet_et" or value == 'hJet_mt' or value == 'hJet_rawPt'):
            #        theVars0FJ[key][0] = theFormsFJ["form_reg_%s_0" %(key)].EvalInstance()
            #        theVars1FJ[key][0] = theFormsFJ["form_reg_%s_1" %(key)].EvalInstance()
            hJet_MET_dPhi[0] = deltaPhi(METphi[0],hJet_phi0)
            hJet_MET_dPhi[1] = deltaPhi(METphi[0],hJet_phi1)
            hJet_MET_dPhiArray[0][0] = deltaPhi(METphi[0],hJet_phi0)
            hJet_MET_dPhiArray[1][0] = deltaPhi(METphi[0],hJet_phi1)
            if not job.type == 'DATA':
                corrRes0 = corrPt(hJet_pt0,hJet_eta0,hJet_mcPt0)
                corrRes1 = corrPt(hJet_pt1,hJet_eta1,hJet_mcPt1)
                hJet_rawPt0 *= corrRes0
                hJet_rawPt1 *= corrRes1
            hJet_rawPtArray[0][0] = hJet_rawPt0
            hJet_rawPtArray[1][0] = hJet_rawPt1
            hJ0.SetPtEtaPhiM(hJet_pt0,hJet_eta0,hJet_phi0,hJet_mass0)
            hJ1.SetPtEtaPhiM(hJet_pt1,hJet_eta1,hJet_phi1,hJet_mass1)
            jetEt0 = hJ0.Et()
            jetEt1 = hJ1.Et()
            hJet_mt0 = hJ0.Mt()
            hJet_mt1 = hJ1.Mt()
            
            
            if applyRegression:
                HNoReg.HiggsFlag = 1
                HNoReg.mass = (hJ0+hJ1).M()
                HNoReg.pt = (hJ0+hJ1).Pt()
                HNoReg.eta = (hJ0+hJ1).Eta()
                HNoReg.phi = (hJ0+hJ1).Phi()
                HNoReg.dR = hJ0.DeltaR(hJ1)
                HNoReg.dPhi = hJ0.DeltaPhi(hJ1)
                HNoReg.dEta = abs(hJ0.Eta()-hJ1.Eta())

                HNoRegwithFSR = ROOT.TLorentzVector()
                HNoRegwithFSR.SetPtEtaPhiM(HNoReg.pt,HNoReg.eta,HNoReg.phi,HNoReg.mass)
                
                HNoRegwithFSR = addAdditionalJets(HNoRegwithFSR,tree)
                
                HaddJetsdR08NoReg.HiggsFlag = 1
                HaddJetsdR08NoReg.mass = HNoRegwithFSR.M()
                HaddJetsdR08NoReg.pt = HNoRegwithFSR.Pt()
                HaddJetsdR08NoReg.eta = HNoRegwithFSR.Eta()
                HaddJetsdR08NoReg.phi = HNoRegwithFSR.Phi()
                HaddJetsdR08NoReg.dR = 0
                HaddJetsdR08NoReg.dPhi = 0
                HaddJetsdR08NoReg.dEta = 0                
                
                hJet_MtArray[0][0] = hJ0.Mt()
                hJet_MtArray[1][0] = hJ1.Mt()
                hJet_etarray[0][0] = hJ0.Et()
                hJet_etarray[1][0] = hJ1.Et()

                rPt0 = max(0.0001,readerJet0.EvaluateRegression( "jet0Regression" )[0])
                rPt1 = max(0.0001,readerJet1.EvaluateRegression( "jet1Regression" )[0])

                hJet_pt[0] = rPt0
                hJet_pt[1] = rPt1

                hJet_regWeight[0] = rPt0/hJet_pt0
                hJet_regWeight[1] = rPt1/hJet_pt1

                hJ0.SetPtEtaPhiM(rPt0,hJ0.Eta(),hJ0.Phi(),hJ0.M())
                hJ1.SetPtEtaPhiM(rPt1,hJ1.Eta(),hJ1.Phi(),hJ1.M())
                rMass0 = hJ0.M()
                rMass1 = hJ1.M()

                H.HiggsFlag = 1
                H.mass = (hJ0+hJ1).M()
                H.pt = (hJ0+hJ1).Pt()
                H.eta = (hJ0+hJ1).Eta()
                H.phi = (hJ0+hJ1).Phi()
                H.dR = hJ0.DeltaR(hJ1)
                H.dPhi = hJ0.DeltaPhi(hJ1)
                H.dEta = abs(hJ0.Eta()-hJ1.Eta())
                HVMass_Reg[0] = (hJ0+hJ1+vect).M()
                
                HwithFSR = ROOT.TLorentzVector()
                HwithFSR.SetPtEtaPhiM(H.pt,H.eta,H.phi,H.mass)
                
                HwithFSR = addAdditionalJets(HwithFSR,tree)
                
                HaddJetsdR08.HiggsFlag = 1
                HaddJetsdR08.mass = HwithFSR.M()
                HaddJetsdR08.pt = HwithFSR.Pt()
                HaddJetsdR08.eta = HwithFSR.Eta()
                HaddJetsdR08.phi = HwithFSR.Phi()
                HaddJetsdR08.dR = 0
                HaddJetsdR08.dPhi = 0
                HaddJetsdR08.dEta = 0                
                
                if hJet_regWeight[0] > 3. or hJet_regWeight[1] > 3. or hJet_regWeight[0] < 0.3 or hJet_regWeight[1] < 0.3:
                    print '### Debug event with ptReg/ptNoReg>0.3 or ptReg/ptNoReg<3 ###'
                    print 'Event %.0f' %(Event[0])
                    print 'MET %.2f' %(METet[0])
                    print 'rho %.2f' %(rho[0])
                    for key, value in regDict.items():
                        if not (value == 'hJet_MET_dPhi' or value == 'METet' or value == "rho" or value == "hJet_et" or value == 'hJet_mt' or value == 'hJet_rawPt'):
                            print '%s 0: %.2f'%(key, theVars0[key][0])
                            print '%s 1: %.2f'%(key, theVars1[key][0])
                    for i in range(2):
                        print 'dPhi %.0f %.2f' %(i,hJet_MET_dPhiArray[i][0])
                    for i in range(2):
                        print 'ptRaw %.0f %.2f' %(i,hJet_rawPtArray[i][0])
                    for i in range(2):
                        print 'Mt %.0f %.2f' %(i,hJet_MtArray[i][0])
                    for i in range(2):
                        print 'Et %.0f %.2f' %(i,hJet_etarray[i][0])
                    print 'corr 0 %.2f' %(hJet_regWeight[0])
                    print 'corr 1 %.2f' %(hJet_regWeight[1])
                    print 'rPt0 %.2f' %(rPt0)
                    print 'rPt1 %.2f' %(rPt1)
                    print 'rMass0 %.2f' %(rMass0)
                    print 'rMass1 %.2f' %(rMass1)
                    print 'Mass %.2f' %(H.mass)
                    
                    print 'hJet_pt0: ',hJet_pt0
                    print 'hJet_pt1: ',hJet_pt1
                # if fatHiggsFlag:
                    # hFJ0.SetPtEtaPhiE(fathFilterJets_pt0,fathFilterJets_eta0,fathFilterJets_phi0,fathFilterJets_e0)
                    # hFJ1.SetPtEtaPhiE(fathFilterJets_pt1,fathFilterJets_eta1,fathFilterJets_phi1,fathFilterJets_e1)
                    # rFJPt0 = max(0.0001,readerFJ0.EvaluateRegression( "jet0RegressionFJ" )[0])
                    # rFJPt1 = max(0.0001,readerFJ1.EvaluateRegression( "jet1RegressionFJ" )[0])
                    # fathFilterJets_regWeight[0] = rPt0/fathFilterJets_pt0
                    # fathFilterJets_regWeight[1] = rPt1/fathFilterJets_pt1
                    # rFJE0 = fathFilterJets_e0*fathFilterJets_regWeight[0]
                    # rFJE1 = fathFilterJets_e1*fathFilterJets_regWeight[1]
                    # hFJ0.SetPtEtaPhiE(rFJPt0,fathFilterJets_eta0,fathFilterJets_phi0,rFJE0)
                    # hFJ1.SetPtEtaPhiE(rFJPt1,fathFilterJets_eta1,fathFilterJets_phi1,rFJE1)
                    # FatHReg[0] = (hFJ0+hFJ1).M()
                    # FatHReg[1] = (hFJ0+hFJ1).Pt()
                # else:
                    # FatHReg[0] = 0.
                    # FatHReg[1] = 0.

                    # print rFJPt0
                    # print rFJPt1
            
            angleHB[0]=fAngleHB.EvalInstance()
            angleLZ[0]=fAngleLZ.EvalInstance()
            angleZZS[0]=fAngleZZS.EvalInstance()

           # for i, angLikeBkg in enumerate(AngLikeBkgs):
               # likeSBH[i] = math.fabs(SigBH[i].Eval(angleHB[0]))
               # likeBBH[i] = math.fabs(BkgBH[i].Eval(angleHB[0]))

               # likeSZZS[i] = math.fabs(SigZZS[i].Eval(angleZZS[0]))
               # likeBZZS[i] = math.fabs(BkgZZS[i].Eval(angleZZS[0]))

               # likeSLZ[i] = math.fabs(SigLZ[i].Eval(angleLZ[0]))
               # likeBLZ[i] = math.fabs(BkgLZ[i].Eval(angleLZ[0]))

               # likeSMassZS[i] = math.fabs(SigMassZS[i].Eval(fHVMass.EvalInstance()))
               # likeBMassZS[i] = math.fabs(BkgMassZS[i].Eval(fHVMass.EvalInstance()))

               # scaleSig  = float( ang_yield['Sig'] / (ang_yield['Sig'] + ang_yield[angLikeBkg]))
               # scaleBkg  = float( ang_yield[angLikeBkg] / (ang_yield['Sig'] + ang_yield[angLikeBkg]) )

               # numerator = (likeSBH[i]*likeSZZS[i]*likeSLZ[i]*likeSMassZS[i]);
               # denominator = ((scaleBkg*likeBLZ[i]*likeBZZS[i]*likeBBH[i]*likeBMassZS[i])+(scaleSig*likeSBH[i]*likeSZZS[i]*likeSLZ[i]*likeSMassZS[i]))

               # if denominator > 0:
                   # kinLikeRatio[i] = numerator/denominator;
               # else:
                   # kinLikeRatio[i] = 0;

            if job.type == 'DATA':
                for i in range(2):
                    csv = float(tree.Jet_btagCSV[tree.hJCidx[i]])
                    hJet_btagCSVOld[i] = csv 
                    hJet_btagCSV[i] = csv 
                newtree.Fill()
                continue

            for i in range(2):
                flavour = int(tree.Jet_hadronFlavour[tree.hJCidx[i]])
                pt = float(tree.Jet_pt[tree.hJCidx[i]])
                eta = float(tree.Jet_eta[tree.hJCidx[i]])
                csv = float(tree.Jet_btagCSV[tree.hJCidx[i]])
                hJet_btagCSVOld[i] = csv 
                ##FIXME## we have to add the CSV reshaping
                hJet_btagCSV[i] = csv 
                if anaTag == '7TeV':
                    tree.Jet_btagCSV[tree.hJCidx[i]] = corrCSV(btagNom,csv,flavour)
                    hJet_btagCSVDown[i] = corrCSV(btagDown,csv,flavour)
                    hJet_btagCSVUp[i] = corrCSV(btagUp,csv,flavour) 
                    hJet_btagCSVFDown[i] = corrCSV(btagFDown,csv,flavour)
                    hJet_btagCSVFUp[i] = corrCSV(btagFUp,csv,flavour)
                else:
                    # tree.Jet_btagCSV[i] = btagNom.reshape(eta,pt,csv,flavour)
                    # hJet_btagCSVDown[i] = btagDown.reshape(eta,pt,csv,flavour)
                    # hJet_btagCSVUp[i] = btagUp.reshape(eta,pt,csv,flavour)
                    # hJet_btagCSVFDown[i] = btagFDown.reshape(eta,pt,csv,flavour)
                    # hJet_btagCSVFUp[i] = btagFUp.reshape(eta,pt,csv,flavour)
                    # tree.Jet_btagCSV[i] = tree.Jet_btagCSV[i]
                    hJet_btagCSVDown[i] = tree.Jet_btagCSV[tree.hJCidx[i]]
                    hJet_btagCSVUp[i] = tree.Jet_btagCSV[tree.hJCidx[i]]
                    hJet_btagCSVFDown[i] = tree.Jet_btagCSV[tree.hJCidx[i]]
                    hJet_btagCSVFUp[i] = tree.Jet_btagCSV[tree.hJCidx[i]]

############################################
            if job.type != 'DATA':
                ## JER_up
                rPt0 = max(0.0001,readerJet0_JER_up.EvaluateRegression( "jet0Regression" )[0])
                rPt1 = max(0.0001,readerJet1_JER_up.EvaluateRegression( "jet1Regression" )[0])
                hJ0.SetPtEtaPhiM(rPt0,hJet_eta0,hJet_phi0,hJet_mass0)
                hJ1.SetPtEtaPhiM(rPt1,hJet_eta1,hJet_phi1,hJet_mass1)
                rMass0=hJ0.M()
                rMass1=hJ1.M()
                hJet_pt_JER_up[0]=rPt0
                hJet_pt_JER_up[1]=rPt1
                hJet_mass_JER_up[0]=rMass0
                hJet_mass_JER_up[1]=rMass1
                H_JER[0]=(hJ0+hJ1).M()
                H_JER[2]=(hJ0+hJ1).Pt()
                HVMass_JER_up[0] = (hJ0+hJ1+vect).M()

                ## JER_down
                rPt0 = max(0.0001,readerJet0_JER_down.EvaluateRegression( "jet0Regression" )[0])
                rPt1 = max(0.0001,readerJet1_JER_down.EvaluateRegression( "jet1Regression" )[0])
                hJ0.SetPtEtaPhiM(rPt0,hJet_eta0,hJet_phi0,hJet_mass0)
                hJ1.SetPtEtaPhiM(rPt1,hJet_eta1,hJet_phi1,hJet_mass1)
                rMass0=hJ0.M()
                rMass1=hJ1.M()
                hJet_pt_JER_down[0]=rPt0
                hJet_pt_JER_down[1]=rPt1
                hJet_mass_JER_down[0]=rMass0
                hJet_mass_JER_down[1]=rMass1
                H_JER[1]=(hJ0+hJ1).M()
                H_JER[3]=(hJ0+hJ1).Pt()
                HVMass_JER_down[0] = (hJ0+hJ1+vect).M()

                ## JEC_up
                rPt0 = max(0.0001,readerJet0_JEC_up.EvaluateRegression( "jet0Regression" )[0])
                rPt1 = max(0.0001,readerJet1_JEC_up.EvaluateRegression( "jet1Regression" )[0])
                hJ0.SetPtEtaPhiM(rPt0,hJet_eta0,hJet_phi0,hJet_mass0)
                hJ1.SetPtEtaPhiM(rPt1,hJet_eta1,hJet_phi1,hJet_mass1)
                rMass0=hJ0.M()
                rMass1=hJ1.M()
                hJet_pt_JES_up[0]=rPt0
                hJet_pt_JES_up[1]=rPt1
                hJet_mass_JES_up[0]=rMass0
                hJet_mass_JES_up[1]=rMass1
                H_JES[0]=(hJ0+hJ1).M()
                H_JES[2]=(hJ0+hJ1).Pt()
                HVMass_JES_up[0] = (hJ0+hJ1+vect).M()

                ## JEC_down
                rPt0 = max(0.0001,readerJet0_JEC_down.EvaluateRegression( "jet0Regression" )[0])
                rPt1 = max(0.0001,readerJet1_JEC_down.EvaluateRegression( "jet1Regression" )[0])
                hJ0.SetPtEtaPhiM(rPt0,hJet_eta0,hJet_phi0,hJet_mass0)
                hJ1.SetPtEtaPhiM(rPt1,hJet_eta1,hJet_phi1,hJet_mass1)
                rMass0=hJ0.M()
                rMass1=hJ1.M()
                hJet_pt_JES_down[0]=rPt0
                hJet_pt_JES_down[1]=rPt1
                hJet_mass_JES_down[0]=rMass0
                hJet_mass_JES_down[1]=rMass1
                H_JES[1]=(hJ0+hJ1).M()
                H_JES[3]=(hJ0+hJ1).Pt()
                HVMass_JES_down[0] = (hJ0+hJ1+vect).M()

            angleHB_JER_up[0]=fAngleHB_JER_up.EvalInstance()
            angleHB_JER_down[0]=fAngleHB_JER_down.EvalInstance()
            angleHB_JES_up[0]=fAngleHB_JES_up.EvalInstance()
            angleHB_JES_down[0]=fAngleHB_JES_down.EvalInstance()
            angleZZS[0]=fAngleZZS.EvalInstance()
            angleZZS_JER_up[0]=fAngleZZS_JER_up.EvalInstance()
            angleZZS_JER_down[0]=fAngleZZS_JER_down.EvalInstance()
            angleZZS_JES_up[0]=fAngleZZS_JES_up.EvalInstance()
            angleZZS_JES_down[0]=fAngleZZS_JES_down.EvalInstance()

            # print "hJet_eta[0]",hJet_eta[0]
            # print "hJet_eta[1]",hJet_eta[1]
            # print "hJet_phi[0]",hJet_phi[0]
            # print "hJet_phi[1]",hJet_phi[1]
            # print "hJet_mass[0]",hJet_mass[0]
            # print "hJet_mass[1]",hJet_mass[1]

            newtree.Fill()
                   
    print 'Exit loop'
    newtree.AutoSave()
    print 'Save'
    output.Close()
    print 'Close'
    targetStorage = pathOUT.replace('gsidcap://t3se01.psi.ch:22128/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=')+'/'+job.prefix+job.identifier+'.root'
    if('pisa' in config.get('Configuration','whereToLaunch')):
       # command = 'lcg-del -b -D srmv2 -l %s' %(targetStorage)
       # print(command)
       # subprocess.call([command], shell=True)
        command = 'cp %s %s' %(tmpDir+'/'+job.prefix+job.identifier+'.root',targetStorage)
        print(command)
        subprocess.call([command], shell=True)
    # elif TreeCache.get_slc_version() == '111SLC5': # NOT WORKING !!! ALWAYS USE SRM
        # command = 'lcg-del -b -D srmv2 -l %s' %(targetStorage)
        # print(command)
        # subprocess.call([command], shell=True)
        # command = 'lcg-cp -b -D srmv2 file:///%s %s' %(tmpDir+'/'+job.prefix+job.identifier+'.root',targetStorage)
        # print(command)
        # subprocess.call([command], shell=True)
    else:
        command = 'srmrm %s' %(targetStorage.replace('root://t3dcachedb03.psi.ch:1094/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=/'))
        print(command)
        subprocess.call([command], shell=True)
        # command = 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib64/dcap'
        # print(command)
        # subprocess.call([command], shell=True)
        command = 'srmcp -2 -globus_tcp_port_range 20000,25000 file:///%s %s' %(tmpDir+'/'+job.prefix+job.identifier+'.root',targetStorage.replace('root://t3dcachedb03.psi.ch:1094/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN=/'))
        print(command)
        os.system(command)
        # command = 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib64/dcap; gfal-copy file:///%s %s' %(tmpDir+'/'+job.prefix+job.identifier+'.root',targetStorage.replace('root://t3dcachedb03.psi.ch:1094/','srm://t3se01.psi.ch/'))
        # print(command)
        # os.system(command)
        # command = 'lcg-cp -b -D srmv2  %s %s' %(tmpDir+'/'+job.prefix+job.identifier+'.root',targetStorage.replace('root://t3dcachedb03.psi.ch:1094/','srm://t3se01.psi.ch:8443/srm/managerv2?SFN='))
        # print(command)
        # os.system(command)
        # # subprocess.call([command], shell=True)

