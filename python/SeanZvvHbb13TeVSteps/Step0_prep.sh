# Signal Samples
python prep.py SeanZvvHbb13TeVconfig ZH   >& ../LOG/prep_ZH.log;
python prep.py SeanZvvHbb13TeVconfig ggZH >& ../LOG/prep_ggZH.log;
python prep.py SeanZvvHbb13TeVconfig WH   >& ../LOG/prep_WH.log;

# W+Jets Samples
python prep.py SeanZvvHbb13TeVconfig WJetsHT0      >& ../LOG/prep_WJetsHT0.log;
python prep.py SeanZvvHbb13TeVconfig WJetsMadHT100 >& ../LOG/prep_WJetsMadHT100.log;
python prep.py SeanZvvHbb13TeVconfig WJetsMadHT200 >& ../LOG/prep_WJetsMadHT200.log;
python prep.py SeanZvvHbb13TeVconfig WJetsMadHT400 >& ../LOG/prep_WJetsMadHT400.log;
python prep.py SeanZvvHbb13TeVconfig WJetsMadHT600 >& ../LOG/prep_WJetsMadHT600.log;

# Z+Jets Samples
python prep.py SeanZvvHbb13TeVconfig ZJetsHT0      >& ../LOG/prep_ZJetsHT0.log;
python prep.py SeanZvvHbb13TeVconfig ZJetsMadHT100 >& ../LOG/prep_ZJetsMadHT100.log;
python prep.py SeanZvvHbb13TeVconfig ZJetsMadHT200 >& ../LOG/prep_ZJetsMadHT200.log;
python prep.py SeanZvvHbb13TeVconfig ZJetsMadHT400 >& ../LOG/prep_ZJetsMadHT400.log;
python prep.py SeanZvvHbb13TeVconfig ZJetsMadHT600 >& ../LOG/prep_ZJetsMadHT600.log;

# TTbar Samples
python prep.py SeanZvvHbb13TeVconfig TT    >& ../LOG/prep_TT.log;
python prep.py SeanZvvHbb13TeVconfig TTPow >& ../LOG/prep_TTPow.log;

# Single Top Samples
python prep.py SeanZvvHbb13TeVconfig ST_s          >& ../LOG/prep_ST_s.log;
python prep.py SeanZvvHbb13TeVconfig ST_t          >& ../LOG/prep_ST_t.log;
python prep.py SeanZvvHbb13TeVconfig ST_tW_antitop >& ../LOG/prep_ST_tW_antitop.log;
python prep.py SeanZvvHbb13TeVconfig ST_tW_top     >& ../LOG/prep_ST_tW_top.log;

# QCD Samples
python prep.py SeanZvvHbb13TeVconfig QCDHT100  >& ../LOG/prep_QCDHT100.log;
python prep.py SeanZvvHbb13TeVconfig QCDHT200  >& ../LOG/prep_QCDHT200.log;
python prep.py SeanZvvHbb13TeVconfig QCDHT300  >& ../LOG/prep_QCDHT300.log;
python prep.py SeanZvvHbb13TeVconfig QCDHT500  >& ../LOG/prep_QCDHT500.log;
python prep.py SeanZvvHbb13TeVconfig QCDHT700  >& ../LOG/prep_QCDHT700.log;
python prep.py SeanZvvHbb13TeVconfig QCDHT1000 >& ../LOG/prep_QCDHT1000.log;
python prep.py SeanZvvHbb13TeVconfig QCDHT1500 >& ../LOG/prep_QCDHT1500.log;
python prep.py SeanZvvHbb13TeVconfig QCDHT2000 >& ../LOG/prep_QCDHT2000.log;

# Diboson Samples
python prep.py SeanZvvHbb13TeVconfig WWpythia  >& ../LOG/prep_WWpythia.log;
python prep.py SeanZvvHbb13TeVconfig WZpythia  >& ../LOG/prep_WZpythia.log;
python prep.py SeanZvvHbb13TeVconfig ZZpythia  >& ../LOG/prep_ZZpythia.log;
python prep.py SeanZvvHbb13TeVconfig ZZTo2Q2Nu >& ../LOG/prep_ZZTo2Q2Nu.log;

python prep.py SeanZvvHbb13TeVconfig MET >& ../LOG/prep_MET.log;

