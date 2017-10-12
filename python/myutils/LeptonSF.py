import os
import json

# A class to apply SF's tabulated in json files
class LeptonSF:
    def __init__(self, lep_json, lep_name, lep_binning, extrapolateFromClosestBin=True) :
        if not os.path.isfile(lep_json):
            self.valid = False
            if lep_json!="":
                pass
                #print "[LeptonSF]: Warning: ", lep_json, " is not a valid file. Return."
            else:
                pass
                #print "[LeptonSF]: No file has been specified. Return."
        else:
            self.init(lep_json, lep_name, lep_binning, extrapolateFromClosestBin)

    def init(self, lep_json, lep_name, lep_binning, extrapolateFromClosestBin) :
        f = open(lep_json, 'r')             
        #print '[LeptonSF]: Initialize with the following parameters:'
        #print '\tfile:',lep_json
        #print '\titem:', lep_name
        #print '\tbinning:', lep_binning
        results = json.load(f)
        if lep_name not in results.keys():
            self.valid = False
            #print "[LeptonSF]: Warning: ", lep_name , " is not a valid item. Return."
            return False
        self.res = results[lep_name]
        self.lep_name = lep_name
        self.lep_binning = lep_binning
        self.valid = True
        self.extrapolateFromClosestBin = extrapolateFromClosestBin
        f.close()

    def get_1D(self, pt):
        if not self.valid:
            return [1.0, 0.0]

        if self.lep_binning not in self.res.keys():
            return [1.0, 0.0]

        # if no bin is found, search for closest one, and double the uncertainty
        closestPtBin = ""
        closestPt = 9999.

        ptFound = False

        for ptKey, result in sorted(self.res[self.lep_binning].iteritems()) :
            ptL = float(((ptKey[ptKey.find(':')+2:]).rstrip(']').split(',')[0]))
            ptH = float(((ptKey[ptKey.find(':')+2:]).rstrip(']').split(',')[1]))

            #print 'ptL is', ptL
            #print 'ptH is', ptH

            if abs(ptL-pt)<closestPt or abs(ptH-pt)<closestPt and not ptFound:
                closestPt = min(abs(ptL-pt), abs(ptH-pt))
                closestPtBin = ptKey

                if (pt>ptL and pt<ptH):

                    closestPtBin = ptKey
                    ptFound = True

                if ptFound:
                    return [result["value"], result["error"]]

        if self.extrapolateFromClosestBin and not (closestPtBin==""):
            return [self.res[self.lep_binning][closestPtBin]["value"],2*self.res[self.lep_binning][closestPtBin]["error"]]
        else:
            return [1.0, 0.0]
                    

    def get_2D(self, pt, eta):
        if not self.valid:
            return [1.0, 0.0]        

        stripForPt= 4

        stripForEta = 5
        if self.lep_binning not in self.res.keys():
            return [1.0, 0.0]

        if "abseta" in self.lep_binning:
            eta = abs(eta)
            stripForEta = 8

        if "pt_eta_ratio" in self.lep_binning:
            stripForEta = 4
            stripForPt= 5

        #if "abseta_pt_DATA" in self.lep_binning or "abseta_pt_MC" in self.lep_binning:
        #    stripForEta = 8
        #    stripForPt= 4

        # if no bin is found, search for closest one, and double the uncertainty
        closestEtaBin = ""
        closestPtBin = ""
        closestEta = 9999.
        closestPt = 9999.

        etaFound = False
        for etaKey, values in sorted(self.res[self.lep_binning].iteritems()) :
            #print 'etaKey is', etaKey
            #print 'etaKey after strip is', etaKey[stripForEta:]
            #etaL = float(((etaKey[stripForEta:]).rstrip(']').split(',')[0]))
            #etaH = float(((etaKey[stripForEta:]).rstrip(']').split(',')[1]))
            etaL = float(((etaKey[etaKey.find('[')+1:]).rstrip(']').split(',')[0]))
            etaH = float(((etaKey[etaKey.find('[')+1:]).rstrip(']').split(',')[1]))

            ptFound = False

            if abs(etaL-eta)<closestEta or abs(etaH-eta)<closestEta and not etaFound:
                closestEta = min(abs(etaL-eta), abs(etaH-eta))
                closestEtaBin = etaKey

            if (eta>etaL and eta<etaH):
                closestEtaBin = etaKey
                etaFound = True                

            for ptKey, result in sorted(values.iteritems()) :
                #ptL = float(((ptKey[stripForPt:]).rstrip(']').split(',')[0]))
                #ptH = float(((ptKey[stripForPt:]).rstrip(']').split(',')[1]))
                ptL = float(((ptKey[ptKey.find('[')+1:]).rstrip(']').split(',')[0]))
                ptH = float(((ptKey[ptKey.find('[')+1:]).rstrip(']').split(',')[1]))

                if abs(ptL-pt)<closestPt or abs(ptH-pt)<closestPt and not ptFound:
                    closestPt = min(abs(ptL-pt), abs(ptH-pt))
                    closestPtBin = ptKey

                if (pt>ptL and pt<ptH):
                    closestPtBin = ptKey
                    ptFound = True

                if etaFound and ptFound:
                    return [result["value"], result["error"]]

        if self.extrapolateFromClosestBin and not (closestPtBin=="" or closestEtaBin==""):
            return [self.res[self.lep_binning][closestEtaBin][closestPtBin]["value"], 
                    2*self.res[self.lep_binning][closestEtaBin][closestPtBin]["error"]] 
        else:
            return [1.0, 0.0]


##################################################################################################
# EXAMPLE 
#

if __name__ == "__main__":

    wdir = os.environ['CMSSW_BASE']+"/src/Xbb"
    jsons = {
        ##
        ##Muon
        ##
        ##ID and ISO
        #wdir+'/python/json/V25/muon_ID_BCDEFv2.json' : ['MC_NUM_LooseID_DEN_genTracks_PAR_pt_eta', 'abseta_pt_ratio'],
        #wdir+'/python/json/V25/muon_ID_GHv2.json' : ['MC_NUM_LooseID_DEN_genTracks_PAR_pt_eta', 'abseta_pt_ratio'],
        #wdir+'/python/json/V25/muon_ISO_BCDEFv2.json' : ['LooseISO_LooseID_pt_eta', 'abseta_pt_ratio'],
        #wdir+'/python/json/V25/muon_ISO_GHv2.json' : ['LooseISO_LooseID_pt_eta', 'abseta_pt_ratio'],
        ##Tracker
        #wdir+'/python/json/V25/trk_SF_RunBCDEF.json' : ['Graph', 'ratio_eff_eta3_dr030e030_corr'],
        #wdir+'/python/json/V25/trk_SF_RunGH.json' : ['Graph', 'ratio_eff_eta3_dr030e030_corr'],
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
        wdir+'/python/json/V25/MC_EfficienciesAndSF_dZ_numH.json' : ['MC_NUM_dZ_DEN_hlt_Mu17_Mu8_OR_TkMu8_loose_PAR_eta1_eta2', 'tag_abseta_abseta_MC']
        ##
        ##Electron
        ##
        ##ID and ISO
        #wdir+'/python/json/V25/EIDISO_ZH_out.json' : ['EIDISO_ZH', 'eta_pt_ratio'],
        ##Tracker
        #wdir+'/python/json/V25/ScaleFactor_etracker_80x.json' : ['ScaleFactor_tracker_80x', 'eta_pt_ratio']
        ##Trigg
        #wdir+'/python/json/V25/DiEleLeg1AfterIDISO_out.json' : ['DiEleLeg1AfterIDISO', 'eta_pt_ratio'],
        #wdir+'/python/json/V25/DiEleLeg2AfterIDISO_out.json' : ['DiEleLeg2AfterIDISO', 'eta_pt_ratio'],
        }
    #jsons = {
    #    #
    #    #Muon
    #    #
    #    ##ID and ISO
    #    wdir+'/python/json/V25/muon_ID_BCDEFv2.json' : ['MC_NUM_LooseID_DEN_genTracks_PAR_pt_eta', 'abseta_pt_ratio'],
    #    wdir+'/python/json/V25/muon_ID_GHv2.json' : ['MC_NUM_LooseID_DEN_genTracks_PAR_pt_eta', 'abseta_pt_ratio'],
    #    #wdir+'/python/json/V25/muon_ISO_BCDEFv2.json' : ['LooseISO_LooseID_pt_eta', 'abseta_pt_ratio'],
    #    #wdir+'/python/json/V25/muon_ISO_GHv2.json' : ['LooseISO_LooseID_pt_eta', 'abseta_pt_ratio'],
    #    ##Tracker
    #    #wdir+'/python/json/V25/trk_SF_RunBCDEF.json' : ['Graph', 'ratio_eff_eta3_dr030e030_corr'],
    #    #wdir+'/python/json/V25/trk_SF_RunGH.json' : ['Graph', 'ratio_eff_eta3_dr030e030_corr'],
    #    #wdir+'/python/json/V25/trk_SF_RunGH.json' : ['Graph', 'ratio_eff_eta3_dr030e030_corr'],
    #    #Trigg
    #    wdir+'/python/json/V25/DiEleLeg1AfterIDISO_out.json' : ['DiEleLeg1AfterIDISO', 'eta_pt_ratio'],
    #    wdir+'/python/json/V25/DiEleLeg2AfterIDISO_out.json' : ['DiEleLeg2AfterIDISO', 'eta_pt_ratio']
    #    #
    #    #Muon
    #    #
    #    #ID and ISO
    #    #wdir+'/python/json/V25/EIDISO_ZH_out.json' : ['EIDISO_ZH', 'eta_pt_ratio'],
    #    ##Tracker
    #    #wdir+'/python/json/V25/ScaleFactor_etracker_80x.json' : ['ScaleFactor_tracker_80x', 'eta_pt_ratio']
    #    #V24
    #    #jsonpath+'/python/json/ScaleFactor_egammaEff_WP90.json' : ['ScaleFactor_egammaEff_WP90', 'eta_pt_ratio'],
    #    #jsonpath+'/python/json/WP90_BCD.json' : ['HLT_Ele27_WPLoose_eta2p1_WP90_BCD', 'eta_pt_ratio'],
    #    #jsonpath+'/python/json/WP90_BCDEF.json' : ['HLT_Ele27_WPLoose_eta2p1_WP90_BCDEF', 'eta_pt_ratio']
    #    }

    for j, name in jsons.iteritems():
        print 'j is', j
        lepCorr = LeptonSF(j , name[0], name[1])
        if not j.find('trk_SF_Run') != -1 and not j.find('EfficienciesAndSF_dZ_numH') != -1:
            weight = lepCorr.get_2D(65, 1.5)
            #if not j.find('EIDISO_ZH_out') != -1 and not j.find('ScaleFactor_etracker_80x') != -1:
            #    weight = lepCorr.get_2D(65, 1.5)
            #else:
            #    weight = lepCorr.get_2D( 1.5,65)
        #1-D binned SF
        elif j.find('EfficienciesAndSF_dZ_numH') != -1:
            weight = lepCorr.get_2D(1.5, 2.0)
        else:
            weight = lepCorr.get_1D(1.5)
        val = weight[0]
        err = weight[1]
        print 'SF: ',  val, ' +/- ', err

        #print 'j is', j
        #lepCorr = LeptonSF(j , name[0], name[1])
        #if not 'ScaleFactor_egammaEff_WP80' in j:
        #    weight = lepCorr.get_2D( 65 , -1.5)
        #else:
        #    weight = lepCorr.get_2D( -1.5, 65)
        #val = weight[0]
        #err = weight[1]
        #print 'SF: ',  val, ' +/- ', err
    
    
