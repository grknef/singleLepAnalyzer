#!/usr/bin/python

import os,sys,time,math,datetime,fnmatch,pickle
from numpy import linspace
from weights import *
from analyze import *
from samples import *
import ROOT as R

R.gROOT.SetBatch(1)
start_time = time.time()

###########################################################
#################### CUTS & OUTPUT ########################
###########################################################

cutList = {'lepPtCut':40, #40, #0, #
		   'leadJetPtCut':150, #300, #0, #
		   'subLeadJetPtCut':75, #150, #0, #
		   'thirdJetPtCut':30, #100, #0, #
		   'metCut':60, #75, #0, #
		   'njetsCut':3, #3, #0, #
		   'nbjetsCut':0, #3, #
		   'drCut':0, #1.0, #
		   }

doAllSys= True
doQ2sys = True
isotrig = 1

cutString = 'lep'+str(int(cutList['lepPtCut']))+'_MET'+str(int(cutList['metCut']))+'_leadJet'+str(int(cutList['leadJetPtCut']))+'_subLeadJet'+str(int(cutList['subLeadJetPtCut']))+'_thirdJet'+str(int(cutList['thirdJetPtCut']))+'_NJets'+str(int(cutList['njetsCut']))+'_NBJets'+str(int(cutList['nbjetsCut']))+'_DR'+str(int(cutList['drCut']))
pfix='kinematics_substructure'
outDir = os.getcwd()+'/'
outDir+=pfix

isEMlist = ['E','M','All']

###########################################################
#################### SAMPLE GROUPS ########################
###########################################################

whichSignal = 'TT' #TT, BB, or T53T53
signalMassRange = [700,1800]
signals = [whichSignal+'M'+str(mass) for mass in range(signalMassRange[0],signalMassRange[1]+100,100)]
if whichSignal=='T53T53': signals = [whichSignal+'M'+str(mass)+chiral for mass in range(signalMassRange[0],signalMassRange[1]+100,100) for chiral in ['left','right']]
if whichSignal=='TT': decays = ['BWBW','THTH','TZTZ','TZBW','THBW','TZTH'] #T' decays
if whichSignal=='BB': decays = ['TWTW','BHBH','BZBZ','BZTW','BHTW','BZBH'] #B' decays
if whichSignal=='T53T53': decays = [''] #decays to tWtW 100% of the time
sigList = {signal+decay:(signal+decay).lower() for signal in signals for decay in decays}

bkgStackList = ['WJets','ZJets','VV','TTV','TTJets','T','QCD']
wjetList  = ['WJetsMG100','WJetsMG200','WJetsMG400','WJetsMG600','WJetsMG800','WJetsMG1200','WJetsMG2500']
zjetList  = ['DY50']
vvList    = ['WW','WZ','ZZ']
ttvList   = ['TTWl','TTWq','TTZl','TTZq']
ttjetList = ['TTJetsPH0to700inc','TTJetsPH700to1000inc','TTJetsPH1000toINFinc','TTJetsPH700mtt','TTJetsPH1000mtt']
#ttjetList = ['TTJetsPH']
tList     = ['Tt','Ts','TtW','TbtW']

dataList = ['DataERRC','DataERRD','DataEPRD','DataMRRC','DataMRRD','DataMPRD']
signalList = [signal+decay for signal in signals for decay in decays]
topList = ['TTJetsPH0to700inc','TTJetsPH700to1000inc','TTJetsPH1000toINFinc','TTJetsPH700mtt','TTJetsPH1000mtt','TTWl','TTZl','TTWq','TTZq','Tt','Ts','TtW','TbtW']
#topList = ['TTJetsPH','TTWl','TTZl','TTWq','TTZq','Tt','Ts','TtW','TbtW']
ewkList = ['DY50','WJetsMG100','WJetsMG200','WJetsMG400','WJetsMG600','WJetsMG800','WJetsMG1200','WJetsMG2500','WW','WZ','ZZ']
qcdList = ['QCDht100','QCDht200','QCDht300','QCDht500','QCDht700','QCDht1000','QCDht1500','QCDht2000']

systematicList = ['pileup','jec','jer','jsf','jmr','jms','btag','tau21','pdf','pdfNew','muR','muF',
				  'muRFcorrd','toppt','muRFenv','muRFcorrdNew','muRFdecorrdNew']

q2UpList   = ['TTWl','TTZl','TTWq','TTZq','TTJetsPHQ2U','Tt','TtW','TtWQ2U','TbtWQ2U']
q2DownList = ['TTWl','TTZl','TTWq','TTZq','TTJetsPHQ2D','Tt','TtW','TtWQ2D','TbtWQ2D']

###########################################################
#################### NORMALIZATIONS #######################
###########################################################

lumiSys = 0.046 #4.6% lumi uncertainty
trigSys = 0.03 #3% trigger uncertainty
lepIdSys = 0.01 #1% lepton id uncertainty
lepIsoSys = 0.01 #1% lepton isolation uncertainty
topXsecSys = 0.0 #55 #5.5% top x-sec uncertainty
ewkXsecSys = 0.0 #5 #5% ewk x-sec uncertainty
qcdXsecSys = 0.0 #50 #50% qcd x-sec uncertainty
corrdSys = math.sqrt(lumiSys**2+trigSys**2+lepIdSys**2+lepIsoSys**2)

CRuncert = {# averaged from CRs, could depend on the selection, but the difference found to be negligible!
			'topE':0.112,
			'topM':0.087,
			'topAll':0.098,
			'ewkE':0.260,
			'ewkM':0.104,
			'ewkAll':0.172,
			}

def negBinCorrection(hist): #set negative bin contents to zero and adjust the normalization
	norm0=hist.Integral()
	for iBin in range(0,hist.GetNbinsX()+2):
		if hist.GetBinContent(iBin)<0: hist.SetBinContent(iBin,0)
		if hist.Integral()!=0 and norm0>0: hist.Scale(norm0/hist.Integral())
		
def overflow(hist):
	nBinsX=hist.GetXaxis().GetNbins()
	content=hist.GetBinContent(nBinsX)+hist.GetBinContent(nBinsX+1)
	error=math.sqrt(hist.GetBinError(nBinsX)**2+hist.GetBinError(nBinsX+1)**2)
	hist.SetBinContent(nBinsX,content)
	hist.SetBinError(nBinsX,error)
	hist.SetBinContent(nBinsX+1,0)
	hist.SetBinError(nBinsX+1,0)

def round_sig(x,sig=2):
	try:
		return round(x, sig-int(math.floor(math.log10(abs(x))))-1)
	except:
		return round(x,5)

###########################################################
######### GROUP SAMPLES AND PRINT YIELDS/UNCERTS ##########
###########################################################
def makeCats(datahists,sighists,bkghists,discriminant):
	## Input  histograms (datahists,sighists,bkghists) must have corresponding histograms returned from analyze.py##
	
	## INITIALIZE DICTIONARIES FOR YIELDS AND STATISTICAL UNCERTAINTIES ##
	yieldTable = {}
	yieldErrTable = {} #what is actually stored here is the square of the yield error
	for isEM in isEMlist:
		histoPrefix=discriminant+'_'+lumiStr+'fb_'+isEM
		yieldTable[histoPrefix]={}
		yieldErrTable[histoPrefix]={}
		if doAllSys:
			for systematic in systematicList:
				for ud in ['Up','Down']:
					yieldTable[histoPrefix+systematic+ud]={}
					
		if doQ2sys:
			yieldTable[histoPrefix+'q2Up']={}
			yieldTable[histoPrefix+'q2Down']={}
	
	## WRITING HISTOGRAMS IN ROOT FILE ##
	outputRfile = R.TFile(outDir+'/templates_'+discriminant+'_'+lumiStr+'fb.root','RECREATE')
	hsig,htop,hewk,hqcd,hdata={},{},{},{},{}
	hwjets,hzjets,httjets,ht,httv,hvv={},{},{},{},{},{}
	for isEM in isEMlist:
		histoPrefix=discriminant+'_'+lumiStr+'fb_'+isEM

		#Group processes
		hwjets[isEM] = bkghists[histoPrefix+'_'+wjetList[0]].Clone(histoPrefix+'_WJets')
		hzjets[isEM] = bkghists[histoPrefix+'_'+zjetList[0]].Clone(histoPrefix+'_ZJets')
		httjets[isEM] = bkghists[histoPrefix+'_'+ttjetList[0]].Clone(histoPrefix+'_TTJets')
		ht[isEM] = bkghists[histoPrefix+'_'+tList[0]].Clone(histoPrefix+'_T')
		httv[isEM] = bkghists[histoPrefix+'_'+ttvList[0]].Clone(histoPrefix+'_TTV')
		hvv[isEM] = bkghists[histoPrefix+'_'+vvList[0]].Clone(histoPrefix+'_VV')
		for bkg in ttjetList:
			if bkg!=ttjetList[0]: httjets[isEM].Add(bkghists[histoPrefix+'_'+bkg])
		for bkg in wjetList:
			if bkg!=wjetList[0]: hwjets[isEM].Add(bkghists[histoPrefix+'_'+bkg])
		for bkg in ttvList:
			if bkg!=ttvList[0]: httv[isEM].Add(bkghists[histoPrefix+'_'+bkg])
		for bkg in tList:
			if bkg!=tList[0]: ht[isEM].Add(bkghists[histoPrefix+'_'+bkg])
		for bkg in zjetList:
			if bkg!=zjetList[0]: hzjets[isEM].Add(bkghists[histoPrefix+'_'+bkg])
		for bkg in vvList:
			if bkg!=vvList[0]: hvv[isEM].Add(bkghists[histoPrefix+'_'+bkg])
		
		#Group QCD processes
		hqcd[isEM] = bkghists[histoPrefix+'_'+qcdList[0]].Clone(histoPrefix+'__qcd')
		for bkg in qcdList: 
			if bkg!=qcdList[0]: hqcd[isEM].Add(bkghists[histoPrefix+'_'+bkg])
		
		#Group EWK processes
		hewk[isEM] = bkghists[histoPrefix+'_'+ewkList[0]].Clone(histoPrefix+'__ewk')
		for bkg in ewkList:
			if bkg!=ewkList[0]: hewk[isEM].Add(bkghists[histoPrefix+'_'+bkg])
		
		#Group TOP processes
		htop[isEM] = bkghists[histoPrefix+'_'+topList[0]].Clone(histoPrefix+'__top')
		for bkg in topList:
			if bkg!=topList[0]: htop[isEM].Add(bkghists[histoPrefix+'_'+bkg])
		
		#get signal
		for signal in sigList.keys(): hsig[isEM+signal] = sighists[histoPrefix+'_'+signal].Clone(histoPrefix+'__'+sigList[signal])
		#get total signal
		for signal in signals: 
			hsig[isEM+signal] = sighists[histoPrefix+'_'+signal+decays[0]].Clone(histoPrefix+'__'+signal)
			for decay in decays: 
				if decay!=decays[0]: hsig[isEM+signal].Add(sighists[histoPrefix+'_'+signal+decay])

		#systematics
		if doAllSys:
			for systematic in systematicList:
				if systematic=='pdfNew' or systematic=='muRFcorrdNew' or systematic=='muRFdecorrdNew': continue
				for ud in ['Up','Down']:
					if systematic!='toppt':
						hqcd[isEM+systematic+ud] = bkghists[histoPrefix.replace(discriminant,discriminant+systematic+ud)+'_'+qcdList[0]].Clone(histoPrefix+'__qcd'+'__'+systematic+'__'+ud.replace('Up','plus').replace('Down','minus'))
						hewk[isEM+systematic+ud] = bkghists[histoPrefix.replace(discriminant,discriminant+systematic+ud)+'_'+ewkList[0]].Clone(histoPrefix+'__ewk'+'__'+systematic+'__'+ud.replace('Up','plus').replace('Down','minus'))
						htop[isEM+systematic+ud] = bkghists[histoPrefix.replace(discriminant,discriminant+systematic+ud)+'_'+topList[0]].Clone(histoPrefix+'__top'+'__'+systematic+'__'+ud.replace('Up','plus').replace('Down','minus'))
						for signal in sigList.keys(): hsig[isEM+signal+systematic+ud] = sighists[histoPrefix.replace(discriminant,discriminant+systematic+ud)+'_'+signal].Clone(histoPrefix+'__'+sigList[signal]+'__'+systematic+'__'+ud.replace('Up','plus').replace('Down','minus'))
						for signal in signals: 
							hsig[isEM+signal+systematic+ud] = sighists[histoPrefix.replace(discriminant,discriminant+systematic+ud)+'_'+signal+decays[0]].Clone(histoPrefix+'__'+signal+'__'+systematic+'__'+ud.replace('Up','plus').replace('Down','minus'))
							for decay in decays: 
								if decay!=decays[0]: hsig[isEM+signal+systematic+ud].Add(sighists[histoPrefix.replace(discriminant,discriminant+systematic+ud)+'_'+signal+decay])
						for bkg in qcdList: 
							if bkg!=qcdList[0]: hqcd[isEM+systematic+ud].Add(bkghists[histoPrefix.replace(discriminant,discriminant+systematic+ud)+'_'+bkg])
						for bkg in ewkList: 
							if bkg!=ewkList[0]: hewk[isEM+systematic+ud].Add(bkghists[histoPrefix.replace(discriminant,discriminant+systematic+ud)+'_'+bkg])
						for bkg in topList: 
							if bkg!=topList[0]: htop[isEM+systematic+ud].Add(bkghists[histoPrefix.replace(discriminant,discriminant+systematic+ud)+'_'+bkg])
					if systematic=='toppt': # top pt is only on the ttbar sample, so it needs special treatment!
						htop[isEM+systematic+ud] = bkghists[histoPrefix.replace(discriminant,discriminant+systematic+ud)+'_'+ttjetList[0]].Clone(histoPrefix+'__top'+'__'+systematic+'__'+ud.replace('Up','plus').replace('Down','minus'))
						for bkg in ttjetList: 
							if bkg!=ttjetList[0]: htop[isEM+systematic+ud].Add(bkghists[histoPrefix.replace(discriminant,discriminant+systematic+ud)+'_'+bkg])
						for bkg in topList: 
							if bkg not in ttjetList: htop[isEM+systematic+ud].Add(bkghists[histoPrefix+'_'+bkg])

			htop[isEM+'muRFcorrdNewUp'] = htop[isEM+'muRFcorrdUp'].Clone(histoPrefix+'__top__muRFcorrdNew__plus')
			htop[isEM+'muRFcorrdNewDown'] = htop[isEM+'muRFcorrdUp'].Clone(histoPrefix+'__top__muRFcorrdNew__minus')
			hewk[isEM+'muRFcorrdNewUp'] = hewk[isEM+'muRFcorrdUp'].Clone(histoPrefix+'__ewk__muRFcorrdNew__plus')
			hewk[isEM+'muRFcorrdNewDown'] = hewk[isEM+'muRFcorrdUp'].Clone(histoPrefix+'__ewk__muRFcorrdNew__minus')
			hqcd[isEM+'muRFcorrdNewUp'] = hqcd[isEM+'muRFcorrdUp'].Clone(histoPrefix+'__qcd__muRFcorrdNew__plus')
			hqcd[isEM+'muRFcorrdNewDown'] = hqcd[isEM+'muRFcorrdUp'].Clone(histoPrefix+'__qcd__muRFcorrdNew__minus')
			for signal in sigList.keys(): hsig[isEM+signal+'muRFcorrdNewUp'] = hsig[isEM+signal+'muRFcorrdUp'].Clone(histoPrefix+'__'+sigList[signal]+'__muRFcorrdNew__plus')
			for signal in sigList.keys(): hsig[isEM+signal+'muRFcorrdNewDown'] = hsig[isEM+signal+'muRFcorrdUp'].Clone(histoPrefix+'__'+sigList[signal]+'__muRFcorrdNew__minus')
			for signal in signals: 
				hsig[isEM+signal+'muRFcorrdNewUp'] = hsig[isEM+signal+decays[0]+'muRFcorrdUp'].Clone(histoPrefix+'__'+signal+'__muRFcorrdNew__plus')
				hsig[isEM+signal+'muRFcorrdNewDown'] = hsig[isEM+signal+decays[0]+'muRFcorrdUp'].Clone(histoPrefix+'__'+signal+'__muRFcorrdNew__minus')

			htop[isEM+'muRFdecorrdNewUp'] = htop[isEM+'muRFcorrdUp'].Clone(histoPrefix+'__top__muRFdecorrdNew__plus')
			htop[isEM+'muRFdecorrdNewDown'] = htop[isEM+'muRFcorrdUp'].Clone(histoPrefix+'__top__muRFdecorrdNew__minus')
			hewk[isEM+'muRFdecorrdNewUp'] = hewk[isEM+'muRFcorrdUp'].Clone(histoPrefix+'__ewk__muRFdecorrdNew__plus')
			hewk[isEM+'muRFdecorrdNewDown'] = hewk[isEM+'muRFcorrdUp'].Clone(histoPrefix+'__ewk__muRFdecorrdNew__minus')
			hqcd[isEM+'muRFdecorrdNewUp'] = hqcd[isEM+'muRFcorrdUp'].Clone(histoPrefix+'__qcd__muRFdecorrdNew__plus')
			hqcd[isEM+'muRFdecorrdNewDown'] = hqcd[isEM+'muRFcorrdUp'].Clone(histoPrefix+'__qcd__muRFdecorrdNew__minus')
			for signal in sigList.keys(): hsig[isEM+signal+'muRFdecorrdNewUp'] = hsig[isEM+signal+'muRFcorrdUp'].Clone(histoPrefix+'__'+sigList[signal]+'__muRFdecorrdNew__plus')
			for signal in sigList.keys(): hsig[isEM+signal+'muRFdecorrdNewDown'] = hsig[isEM+signal+'muRFcorrdUp'].Clone(histoPrefix+'__'+sigList[signal]+'__muRFdecorrdNew__minus')
			for signal in signals: 
				hsig[isEM+signal+'muRFdecorrdNewUp'] = hsig[isEM+signal+decays[0]+'muRFcorrdUp'].Clone(histoPrefix+'__'+signal+'__muRFdecorrdNew__plus')
				hsig[isEM+signal+'muRFdecorrdNewDown'] = hsig[isEM+signal+decays[0]+'muRFcorrdUp'].Clone(histoPrefix+'__'+signal+'__muRFdecorrdNew__minus')

			# nominal,renormWeights[4],renormWeights[2],renormWeights[1],renormWeights[0],renormWeights[5],renormWeights[3]
			histPrefixList = ['','muRUp','muRDown','muFUp','muFDown','muRFcorrdUp','muRFcorrdDown']
			for ibin in range(1,htop[isEM].GetNbinsX()+1):
				weightListTop = [htop[isEM+item].GetBinContent(ibin) for item in histPrefixList]	
				weightListEwk = [hewk[isEM+item].GetBinContent(ibin) for item in histPrefixList]	
				weightListQcd = [hqcd[isEM+item].GetBinContent(ibin) for item in histPrefixList]	
				weightListSig = {}
				for signal in sigList.keys()+signals: weightListSig[signal] = [hsig[isEM+signal+item].GetBinContent(ibin) for item in histPrefixList]
				indTopRFcorrdUp = weightListTop.index(max(weightListTop))
				indTopRFcorrdDn = weightListTop.index(min(weightListTop))
				indEwkRFcorrdUp = weightListEwk.index(max(weightListEwk))
				indEwkRFcorrdDn = weightListEwk.index(min(weightListEwk))
				indQcdRFcorrdUp = weightListQcd.index(max(weightListQcd))
				indQcdRFcorrdDn = weightListQcd.index(min(weightListQcd))
				indSigRFcorrdUp = {}
				indSigRFcorrdDn = {}
				for signal in sigList.keys()+signals: 
					indSigRFcorrdUp[signal] = weightListSig[signal].index(max(weightListSig[signal]))
					indSigRFcorrdDn[signal] = weightListSig[signal].index(min(weightListSig[signal]))

				indTopRFdecorrdUp = weightListTop.index(max(weightListTop[:-2]))
				indTopRFdecorrdDn = weightListTop.index(min(weightListTop[:-2]))
				indEwkRFdecorrdUp = weightListEwk.index(max(weightListEwk[:-2]))
				indEwkRFdecorrdDn = weightListEwk.index(min(weightListEwk[:-2]))
				indQcdRFdecorrdUp = weightListQcd.index(max(weightListQcd[:-2]))
				indQcdRFdecorrdDn = weightListQcd.index(min(weightListQcd[:-2]))
				indSigRFdecorrdUp = {}
				indSigRFdecorrdDn = {}
				for signal in sigList.keys()+signals: 
					indSigRFdecorrdUp[signal] = weightListSig[signal].index(max(weightListSig[signal][:-2]))
					indSigRFdecorrdDn[signal] = weightListSig[signal].index(min(weightListSig[signal][:-2]))
				
				htop[isEM+'muRFcorrdNewUp'].SetBinContent(ibin,htop[isEM+histPrefixList[indTopRFcorrdUp]].GetBinContent(ibin))
				htop[isEM+'muRFcorrdNewDown'].SetBinContent(ibin,htop[isEM+histPrefixList[indTopRFcorrdDn]].GetBinContent(ibin))
				hewk[isEM+'muRFcorrdNewUp'].SetBinContent(ibin,hewk[isEM+histPrefixList[indEwkRFcorrdUp]].GetBinContent(ibin))
				hewk[isEM+'muRFcorrdNewDown'].SetBinContent(ibin,hewk[isEM+histPrefixList[indEwkRFcorrdDn]].GetBinContent(ibin))
				hqcd[isEM+'muRFcorrdNewUp'].SetBinContent(ibin,hqcd[isEM+histPrefixList[indQcdRFcorrdUp]].GetBinContent(ibin))
				hqcd[isEM+'muRFcorrdNewDown'].SetBinContent(ibin,hqcd[isEM+histPrefixList[indQcdRFcorrdDn]].GetBinContent(ibin))
				for signal in sigList.keys()+signals: 
					hsig[isEM+signal+'muRFcorrdNewUp'].SetBinContent(ibin,hsig[isEM+signal+histPrefixList[indSigRFcorrdUp[signal]]].GetBinContent(ibin))
					hsig[isEM+signal+'muRFcorrdNewDown'].SetBinContent(ibin,hsig[isEM+signal+histPrefixList[indSigRFcorrdDn[signal]]].GetBinContent(ibin))
				htop[isEM+'muRFdecorrdNewUp'].SetBinContent(ibin,htop[isEM+histPrefixList[indTopRFdecorrdUp]].GetBinContent(ibin))
				htop[isEM+'muRFdecorrdNewDown'].SetBinContent(ibin,htop[isEM+histPrefixList[indTopRFdecorrdDn]].GetBinContent(ibin))
				hewk[isEM+'muRFdecorrdNewUp'].SetBinContent(ibin,hewk[isEM+histPrefixList[indEwkRFdecorrdUp]].GetBinContent(ibin))
				hewk[isEM+'muRFdecorrdNewDown'].SetBinContent(ibin,hewk[isEM+histPrefixList[indEwkRFdecorrdDn]].GetBinContent(ibin))
				hqcd[isEM+'muRFdecorrdNewUp'].SetBinContent(ibin,hqcd[isEM+histPrefixList[indQcdRFdecorrdUp]].GetBinContent(ibin))
				hqcd[isEM+'muRFdecorrdNewDown'].SetBinContent(ibin,hqcd[isEM+histPrefixList[indQcdRFdecorrdDn]].GetBinContent(ibin))
				for signal in sigList.keys()+signals: 
					hsig[isEM+signal+'muRFdecorrdNewUp'].SetBinContent(ibin,hsig[isEM+signal+histPrefixList[indSigRFdecorrdUp[signal]]].GetBinContent(ibin))
					hsig[isEM+signal+'muRFdecorrdNewDown'].SetBinContent(ibin,hsig[isEM+signal+histPrefixList[indSigRFdecorrdDn[signal]]].GetBinContent(ibin))

				htop[isEM+'muRFcorrdNewUp'].SetBinError(ibin,htop[isEM+histPrefixList[indTopRFcorrdUp]].GetBinError(ibin))
				htop[isEM+'muRFcorrdNewDown'].SetBinError(ibin,htop[isEM+histPrefixList[indTopRFcorrdDn]].GetBinError(ibin))
				hewk[isEM+'muRFcorrdNewUp'].SetBinError(ibin,hewk[isEM+histPrefixList[indEwkRFcorrdUp]].GetBinError(ibin))
				hewk[isEM+'muRFcorrdNewDown'].SetBinError(ibin,hewk[isEM+histPrefixList[indEwkRFcorrdDn]].GetBinError(ibin))
				hqcd[isEM+'muRFcorrdNewUp'].SetBinError(ibin,hqcd[isEM+histPrefixList[indQcdRFcorrdUp]].GetBinError(ibin))
				hqcd[isEM+'muRFcorrdNewDown'].SetBinError(ibin,hqcd[isEM+histPrefixList[indQcdRFcorrdDn]].GetBinError(ibin))
				for signal in sigList.keys()+signals: 
					hsig[isEM+signal+'muRFcorrdNewUp'].SetBinError(ibin,hsig[isEM+signal+histPrefixList[indSigRFcorrdUp[signal]]].GetBinError(ibin))
					hsig[isEM+signal+'muRFcorrdNewDown'].SetBinError(ibin,hsig[isEM+signal+histPrefixList[indSigRFcorrdDn[signal]]].GetBinError(ibin))
				htop[isEM+'muRFdecorrdNewUp'].SetBinError(ibin,htop[isEM+histPrefixList[indTopRFdecorrdUp]].GetBinError(ibin))
				htop[isEM+'muRFdecorrdNewDown'].SetBinError(ibin,htop[isEM+histPrefixList[indTopRFdecorrdDn]].GetBinError(ibin))
				hewk[isEM+'muRFdecorrdNewUp'].SetBinError(ibin,hewk[isEM+histPrefixList[indEwkRFdecorrdUp]].GetBinError(ibin))
				hewk[isEM+'muRFdecorrdNewDown'].SetBinError(ibin,hewk[isEM+histPrefixList[indEwkRFdecorrdDn]].GetBinError(ibin))
				hqcd[isEM+'muRFdecorrdNewUp'].SetBinError(ibin,hqcd[isEM+histPrefixList[indQcdRFdecorrdUp]].GetBinError(ibin))
				hqcd[isEM+'muRFdecorrdNewDown'].SetBinError(ibin,hqcd[isEM+histPrefixList[indQcdRFdecorrdDn]].GetBinError(ibin))
				for signal in sigList.keys()+signals: 
					hsig[isEM+signal+'muRFdecorrdNewUp'].SetBinError(ibin,hsig[isEM+signal+histPrefixList[indSigRFdecorrdUp[signal]]].GetBinError(ibin))
					hsig[isEM+signal+'muRFdecorrdNewDown'].SetBinError(ibin,hsig[isEM+signal+histPrefixList[indSigRFdecorrdDn[signal]]].GetBinError(ibin))

			for pdfInd in range(100):
				hqcd[isEM+'pdf'+str(pdfInd)] = bkghists[histoPrefix.replace(discriminant,discriminant+'pdf'+str(pdfInd))+'_'+qcdList[0]].Clone(histoPrefix+'__qcd__pdf'+str(pdfInd))
				hewk[isEM+'pdf'+str(pdfInd)] = bkghists[histoPrefix.replace(discriminant,discriminant+'pdf'+str(pdfInd))+'_'+ewkList[0]].Clone(histoPrefix+'__ewk__pdf'+str(pdfInd))
				htop[isEM+'pdf'+str(pdfInd)] = bkghists[histoPrefix.replace(discriminant,discriminant+'pdf'+str(pdfInd))+'_'+topList[0]].Clone(histoPrefix+'__top__pdf'+str(pdfInd))
				for signal in sigList.keys(): hsig[isEM+signal+'pdf'+str(pdfInd)] = sighists[histoPrefix.replace(discriminant,discriminant+'pdf'+str(pdfInd))+'_'+signal].Clone(histoPrefix+'__'+signal+'__pdf'+str(pdfInd))
				for signal in signals: 
					hsig[isEM+signal+'pdf'+str(pdfInd)] = sighists[histoPrefix.replace(discriminant,discriminant+'pdf'+str(pdfInd))+'_'+signal+decays[0]].Clone(histoPrefix+'__'+signal+'__pdf'+str(pdfInd))
					for decay in decays: 
						if decay!=decays[0]: hsig[isEM+signal+'pdf'+str(pdfInd)].Add(sighists[histoPrefix.replace(discriminant,discriminant+'pdf'+str(pdfInd))+'_'+signal+decay])
				for bkg in qcdList: 
					if bkg!=qcdList[0]: hqcd[isEM+'pdf'+str(pdfInd)].Add(bkghists[histoPrefix.replace(discriminant,discriminant+'pdf'+str(pdfInd))+'_'+bkg])
				for bkg in ewkList: 
					if bkg!=ewkList[0]: hewk[isEM+'pdf'+str(pdfInd)].Add(bkghists[histoPrefix.replace(discriminant,discriminant+'pdf'+str(pdfInd))+'_'+bkg])
				for bkg in topList: 
					if bkg!=topList[0]: htop[isEM+'pdf'+str(pdfInd)].Add(bkghists[histoPrefix.replace(discriminant,discriminant+'pdf'+str(pdfInd))+'_'+bkg])
			htop[isEM+'pdfNewUp'] = htop[isEM+'pdf0'].Clone(histoPrefix+'__top__pdfNew__plus')
			htop[isEM+'pdfNewDown'] = htop[isEM+'pdf0'].Clone(histoPrefix+'__top__pdfNew__minus')
			hewk[isEM+'pdfNewUp'] = hewk[isEM+'pdf0'].Clone(histoPrefix+'__ewk__pdfNew__plus')
			hewk[isEM+'pdfNewDown'] = hewk[isEM+'pdf0'].Clone(histoPrefix+'__ewk__pdfNew__minus')
			hqcd[isEM+'pdfNewUp'] = hqcd[isEM+'pdf0'].Clone(histoPrefix+'__qcd__pdfNew__plus')
			hqcd[isEM+'pdfNewDown'] = hqcd[isEM+'pdf0'].Clone(histoPrefix+'__qcd__pdfNew__minus')
			for signal in sigList.keys(): hsig[isEM+signal+'pdfNewUp'] = hsig[isEM+signal+'pdf0'].Clone(histoPrefix+'__'+sigList[signal]+'__pdfNew__plus')
			for signal in sigList.keys(): hsig[isEM+signal+'pdfNewDown'] = hsig[isEM+signal+'pdf0'].Clone(histoPrefix+'__'+sigList[signal]+'__pdfNew__minus')
			for signal in signals: 
				hsig[isEM+signal+'pdfNewUp'] = hsig[isEM+signal+decays[0]+'pdf0'].Clone(histoPrefix+'__'+signal+'__pdfNew__plus')
				hsig[isEM+signal+'pdfNewDown'] = hsig[isEM+signal+decays[0]+'pdf0'].Clone(histoPrefix+'__'+signal+'__pdfNew__minus')
			for ibin in range(1,htop[isEM+'pdfNewUp'].GetNbinsX()+1):
				weightListTop = [htop[isEM+'pdf'+str(pdfInd)].GetBinContent(ibin) for pdfInd in range(100)]
				weightListEwk = [hewk[isEM+'pdf'+str(pdfInd)].GetBinContent(ibin) for pdfInd in range(100)]
				weightListQcd = [hqcd[isEM+'pdf'+str(pdfInd)].GetBinContent(ibin) for pdfInd in range(100)]
				weightListSig = {}
				for signal in sigList.keys()+signals: weightListSig[signal] = [hsig[isEM+signal+'pdf'+str(pdfInd)].GetBinContent(ibin) for pdfInd in range(100)]
				indTopPDFUp = sorted(range(len(weightListTop)), key=lambda k: weightListTop[k])[83]
				indTopPDFDn = sorted(range(len(weightListTop)), key=lambda k: weightListTop[k])[15]
				indEwkPDFUp = sorted(range(len(weightListEwk)), key=lambda k: weightListEwk[k])[83]
				indEwkPDFDn = sorted(range(len(weightListEwk)), key=lambda k: weightListEwk[k])[15]
				indQcdPDFUp = sorted(range(len(weightListQcd)), key=lambda k: weightListQcd[k])[83]
				indQcdPDFDn = sorted(range(len(weightListQcd)), key=lambda k: weightListQcd[k])[15]
				indSigPDFUp = {}
				indSigPDFDn = {}
				for signal in sigList.keys()+signals: 
					indSigPDFUp[signal] = sorted(range(len(weightListSig[signal])), key=lambda k: weightListSig[signal][k])[83]
					indSigPDFDn[signal] = sorted(range(len(weightListSig[signal])), key=lambda k: weightListSig[signal][k])[15]
				
				htop[isEM+'pdfNewUp'].SetBinContent(ibin,htop[isEM+'pdf'+str(indTopPDFUp)].GetBinContent(ibin))
				htop[isEM+'pdfNewDown'].SetBinContent(ibin,htop[isEM+'pdf'+str(indTopPDFDn)].GetBinContent(ibin))
				hewk[isEM+'pdfNewUp'].SetBinContent(ibin,hewk[isEM+'pdf'+str(indEwkPDFUp)].GetBinContent(ibin))
				hewk[isEM+'pdfNewDown'].SetBinContent(ibin,hewk[isEM+'pdf'+str(indEwkPDFDn)].GetBinContent(ibin))
				hqcd[isEM+'pdfNewUp'].SetBinContent(ibin,hqcd[isEM+'pdf'+str(indQcdPDFUp)].GetBinContent(ibin))
				hqcd[isEM+'pdfNewDown'].SetBinContent(ibin,hqcd[isEM+'pdf'+str(indQcdPDFDn)].GetBinContent(ibin))
				for signal in sigList.keys()+signals: 
					hsig[isEM+signal+'pdfNewUp'].SetBinContent(ibin,hsig[isEM+signal+'pdf'+str(indSigPDFUp[signal])].GetBinContent(ibin))
					hsig[isEM+signal+'pdfNewDown'].SetBinContent(ibin,hsig[isEM+signal+'pdf'+str(indSigPDFDn[signal])].GetBinContent(ibin))

				htop[isEM+'pdfNewUp'].SetBinError(ibin,htop[isEM+'pdf'+str(indTopPDFUp)].GetBinError(ibin))
				htop[isEM+'pdfNewDown'].SetBinError(ibin,htop[isEM+'pdf'+str(indTopPDFDn)].GetBinError(ibin))
				hewk[isEM+'pdfNewUp'].SetBinError(ibin,hewk[isEM+'pdf'+str(indEwkPDFUp)].GetBinError(ibin))
				hewk[isEM+'pdfNewDown'].SetBinError(ibin,hewk[isEM+'pdf'+str(indEwkPDFDn)].GetBinError(ibin))
				hqcd[isEM+'pdfNewUp'].SetBinError(ibin,hqcd[isEM+'pdf'+str(indQcdPDFUp)].GetBinError(ibin))
				hqcd[isEM+'pdfNewDown'].SetBinError(ibin,hqcd[isEM+'pdf'+str(indQcdPDFDn)].GetBinError(ibin))
				for signal in sigList.keys()+signals: 
					hsig[isEM+signal+'pdfNewUp'].SetBinError(ibin,hsig[isEM+signal+'pdf'+str(indSigPDFUp[signal])].GetBinError(ibin))
					hsig[isEM+signal+'pdfNewDown'].SetBinError(ibin,hsig[isEM+signal+'pdf'+str(indSigPDFDn[signal])].GetBinError(ibin))
					
		if doQ2sys: #Q^2 systematic exists for certain backgrounds, so we do it separately
			htop[isEM+'q2Up'] = bkghists[histoPrefix+'_'+q2UpList[0]].Clone(histoPrefix+'__top__q2__plus')
			htop[isEM+'q2Down'] = bkghists[histoPrefix+'_'+q2DownList[0]].Clone(histoPrefix+'__top__q2__minus')
			for ind in range(1,len(q2UpList)):
				htop[isEM+'q2Up'].Add(bkghists[histoPrefix+'_'+q2UpList[ind]])
				htop[isEM+'q2Down'].Add(bkghists[histoPrefix+'_'+q2DownList[ind]])
		
		#Group data processes
		hdata[isEM] = datahists[histoPrefix+'_'+dataList[0]].Clone(histoPrefix+'__DATA')
		for dat in dataList:
			if dat!=dataList[0]: hdata[isEM].Add(datahists[histoPrefix+'_'+dat])

		#prepare yield table

		yieldTable[histoPrefix]['top']    = htop[isEM].Integral()
		yieldTable[histoPrefix]['ewk']    = hewk[isEM].Integral()
		yieldTable[histoPrefix]['qcd']    = hqcd[isEM].Integral()
		yieldTable[histoPrefix]['totBkg'] = htop[isEM].Integral()+hewk[isEM].Integral()+hqcd[isEM].Integral()
		yieldTable[histoPrefix]['data']   = hdata[isEM].Integral()
		yieldTable[histoPrefix]['dataOverBkg']= yieldTable[histoPrefix]['data']/yieldTable[histoPrefix]['totBkg']
		yieldTable[histoPrefix]['WJets']  = hwjets[isEM].Integral()
		yieldTable[histoPrefix]['ZJets']  = hzjets[isEM].Integral()
		yieldTable[histoPrefix]['VV']     = hvv[isEM].Integral()
		yieldTable[histoPrefix]['TTV']    = httv[isEM].Integral()
		yieldTable[histoPrefix]['TTJets'] = httjets[isEM].Integral()
		yieldTable[histoPrefix]['T']      = ht[isEM].Integral()
		yieldTable[histoPrefix]['QCD']    = hqcd[isEM].Integral()
		for signal in sigList.keys(): yieldTable[histoPrefix][signal] = hsig[isEM+signal].Integral()
		for signal in signals: yieldTable[histoPrefix][signal] = hsig[isEM+signal].Integral()
		
		#+/- 1sigma variations of shape systematics
		if doAllSys:
			for systematic in systematicList:
				for ud in ['Up','Down']:
					yieldTable[histoPrefix+systematic+ud]['top']    = htop[isEM+systematic+ud].Integral()
					if systematic!='toppt':
						yieldTable[histoPrefix+systematic+ud]['ewk']    = hewk[isEM+systematic+ud].Integral()
						yieldTable[histoPrefix+systematic+ud]['qcd']    = hqcd[isEM+systematic+ud].Integral()
						yieldTable[histoPrefix+systematic+ud]['totBkg'] = htop[isEM+systematic+ud].Integral()+hewk[isEM+systematic+ud].Integral()+hqcd[isEM+systematic+ud].Integral()
						for signal in sigList.keys(): yieldTable[histoPrefix+systematic+ud][signal] = hsig[isEM+signal+systematic+ud].Integral()
						for signal in signals: yieldTable[histoPrefix+systematic+ud][signal] = hsig[isEM+signal+systematic+ud].Integral()
					
		if doQ2sys:
			yieldTable[histoPrefix+'q2Up']['top']    = htop[isEM+'q2Up'].Integral()
			yieldTable[histoPrefix+'q2Down']['top']    = htop[isEM+'q2Up'].Integral()

		#prepare MC yield error table
		yieldErrTable[histoPrefix]['top']    = 0.
		yieldErrTable[histoPrefix]['ewk']    = 0.
		yieldErrTable[histoPrefix]['qcd']    = 0.
		yieldErrTable[histoPrefix]['totBkg'] = 0.
		yieldErrTable[histoPrefix]['data']   = 0.
		yieldErrTable[histoPrefix]['dataOverBkg']= 0.
		yieldErrTable[histoPrefix]['WJets']  = 0.
		yieldErrTable[histoPrefix]['ZJets']  = 0.
		yieldErrTable[histoPrefix]['VV']     = 0.
		yieldErrTable[histoPrefix]['TTV']    = 0.
		yieldErrTable[histoPrefix]['TTJets'] = 0.
		yieldErrTable[histoPrefix]['T']      = 0.
		yieldErrTable[histoPrefix]['QCD']    = 0.
		for signal in sigList.keys(): yieldErrTable[histoPrefix][signal] = 0.
		for signal in signals: yieldErrTable[histoPrefix][signal] = 0.

		for ibin in range(1,hsig[isEM+signal].GetXaxis().GetNbins()+1):
			yieldErrTable[histoPrefix]['top']    += htop[isEM].GetBinError(ibin)**2
			yieldErrTable[histoPrefix]['ewk']    += hewk[isEM].GetBinError(ibin)**2
			yieldErrTable[histoPrefix]['qcd']    += hqcd[isEM].GetBinError(ibin)**2
			yieldErrTable[histoPrefix]['totBkg'] += htop[isEM].GetBinError(ibin)**2+hewk[isEM].GetBinError(ibin)**2+hqcd[isEM].GetBinError(ibin)**2
			yieldErrTable[histoPrefix]['data']   += hdata[isEM].GetBinError(ibin)**2
			yieldErrTable[histoPrefix]['WJets']  += hwjets[isEM].GetBinError(ibin)**2
			yieldErrTable[histoPrefix]['ZJets']  += hzjets[isEM].GetBinError(ibin)**2
			yieldErrTable[histoPrefix]['VV']     += hvv[isEM].GetBinError(ibin)**2
			yieldErrTable[histoPrefix]['TTV']    += httv[isEM].GetBinError(ibin)**2
			yieldErrTable[histoPrefix]['TTJets'] += httjets[isEM].GetBinError(ibin)**2
			yieldErrTable[histoPrefix]['T']      += ht[isEM].GetBinError(ibin)**2
			yieldErrTable[histoPrefix]['QCD']    += hqcd[isEM].GetBinError(ibin)**2
			for signal in sigList.keys(): yieldErrTable[histoPrefix][signal] += hsig[isEM+signal].GetBinError(ibin)**2
			for signal in signals: yieldErrTable[histoPrefix][signal] += hsig[isEM+signal].GetBinError(ibin)**2
			
		yieldErrTable[histoPrefix]['top']    += (corrdSys*yieldTable[histoPrefix]['top'])**2+(topXsecSys*yieldTable[histoPrefix]['top'])**2+(CRuncert['top'+isEM]*yieldTable[histoPrefix]['top'])**2
		yieldErrTable[histoPrefix]['ewk']    += (corrdSys*yieldTable[histoPrefix]['ewk'])**2+(ewkXsecSys*yieldTable[histoPrefix]['ewk'])**2+(CRuncert['ewk'+isEM]*yieldTable[histoPrefix]['ewk'])**2
		yieldErrTable[histoPrefix]['qcd']    += (corrdSys*yieldTable[histoPrefix]['qcd'])**2+(qcdXsecSys*yieldTable[histoPrefix]['qcd'])**2
		yieldErrTable[histoPrefix]['totBkg'] += (corrdSys*yieldTable[histoPrefix]['totBkg'])**2+(topXsecSys*yieldTable[histoPrefix]['top'])**2+(CRuncert['top'+isEM]*yieldTable[histoPrefix]['top'])**2+(ewkXsecSys*yieldTable[histoPrefix]['ewk'])**2+(CRuncert['ewk'+isEM]*yieldTable[histoPrefix]['ewk'])**2+(qcdXsecSys*yieldTable[histoPrefix]['qcd'])**2
		yieldErrTable[histoPrefix]['WJets']  += (corrdSys*yieldTable[histoPrefix]['WJets'])**2+(ewkXsecSys*yieldTable[histoPrefix]['WJets'])**2+(CRuncert['ewk'+isEM]*yieldTable[histoPrefix]['WJets'])**2
		yieldErrTable[histoPrefix]['ZJets']  += (corrdSys*yieldTable[histoPrefix]['ZJets'])**2+(ewkXsecSys*yieldTable[histoPrefix]['ZJets'])**2+(CRuncert['ewk'+isEM]*yieldTable[histoPrefix]['ZJets'])**2
		yieldErrTable[histoPrefix]['VV']     += (corrdSys*yieldTable[histoPrefix]['VV'])**2+(ewkXsecSys*yieldTable[histoPrefix]['VV'])**2+(CRuncert['ewk'+isEM]*yieldTable[histoPrefix]['VV'])**2
		yieldErrTable[histoPrefix]['TTV']    += (corrdSys*yieldTable[histoPrefix]['TTV'])**2+(topXsecSys*yieldTable[histoPrefix]['TTV'])**2+(CRuncert['top'+isEM]*yieldTable[histoPrefix]['TTV'])**2
		yieldErrTable[histoPrefix]['TTJets'] += (corrdSys*yieldTable[histoPrefix]['TTJets'])**2+(topXsecSys*yieldTable[histoPrefix]['TTJets'])**2+(CRuncert['top'+isEM]*yieldTable[histoPrefix]['TTJets'])**2
		yieldErrTable[histoPrefix]['T']      += (corrdSys*yieldTable[histoPrefix]['T'])**2+(topXsecSys*yieldTable[histoPrefix]['T'])**2+(CRuncert['top'+isEM]*yieldTable[histoPrefix]['T'])**2
		yieldErrTable[histoPrefix]['QCD']    += (corrdSys*yieldTable[histoPrefix]['QCD'])**2+(qcdXsecSys*yieldTable[histoPrefix]['qcd'])**2
		for signal in sigList.keys(): yieldErrTable[histoPrefix][signal] += (corrdSys*yieldTable[histoPrefix][signal])**2
		for signal in signals: yieldErrTable[histoPrefix][signal] += (corrdSys*yieldTable[histoPrefix][signal])**2

		Ratio = yieldTable[histoPrefix]['data']/yieldTable[histoPrefix]['totBkg']
		yieldErrTable[histoPrefix]['dataOverBkg'] = (Ratio**2) * ((yieldErrTable[histoPrefix]['data']/(yieldTable[histoPrefix]['data']+1e-20))**2 + (yieldErrTable[histoPrefix]['totBkg']/(yieldTable[histoPrefix]['totBkg']+1e-20))**2)

		hdata[isEM].Write()
		#write theta histograms in root file, avoid having processes with no event yield (to make theta happy) 
		for signal in sigList.keys()+signals: 
			if hsig[isEM+signal].Integral() > 0:  
				hsig[isEM+signal].Write()
				if doAllSys:
					for systematic in systematicList:
						if systematic=='toppt': continue
						hsig[isEM+signal+systematic+'Up'].Write()
						hsig[isEM+signal+systematic+'Down'].Write()
					for pdfInd in range(100): hsig[isEM+signal+'pdf'+str(pdfInd)].Write()
		if htop[isEM].Integral() > 0:  
			htop[isEM].Write()
			if doAllSys:
				for systematic in systematicList:
					htop[isEM+systematic+'Up'].Write()
					htop[isEM+systematic+'Down'].Write()
				for pdfInd in range(100): htop[isEM+'pdf'+str(pdfInd)].Write()
			if doQ2sys:
				htop[isEM+'q2Up'].Write()
				htop[isEM+'q2Down'].Write()
		if hewk[isEM].Integral() > 0:  
			hewk[isEM].Write()
			if doAllSys:
				for systematic in systematicList:
					if systematic=='toppt': continue
					hewk[isEM+systematic+'Up'].Write()
					hewk[isEM+systematic+'Down'].Write()
				for pdfInd in range(100): hewk[isEM+'pdf'+str(pdfInd)].Write()
		if hqcd[isEM].Integral() > 0:  
			hqcd[isEM].Write()
			if doAllSys:
				for systematic in systematicList:
#					if systematic=='toppt' or systematic == 'pdf' or systematic == 'pdfNew' or systematic == 'muR' or systematic == 'muF' or systematic == 'muRFcorrd' or systematic == 'muRFcorrdNew' or systematic == 'muRFdecorrdNew': continue
					if systematic=='toppt': continue
					hqcd[isEM+systematic+'Up'].Write()
					hqcd[isEM+systematic+'Down'].Write()
				for pdfInd in range(100): hqcd[isEM+'pdf'+str(pdfInd)].Write()
		if hwjets[isEM].Integral() > 0: hwjets[isEM].Write()
		if hzjets[isEM].Integral() > 0: hzjets[isEM].Write()
		if httjets[isEM].Integral()> 0: httjets[isEM].Write()
		if ht[isEM].Integral() > 0    : ht[isEM].Write()
		if httv[isEM].Integral() > 0  : httv[isEM].Write()
		if hvv[isEM].Integral() > 0   : hvv[isEM].Write()
	outputRfile.Close()

	stdout_old = sys.stdout
	logFile = open(outDir+'/yields_'+discriminant+'_'+lumiStr.replace('.','p')+'fb.txt','a')
	sys.stdout = logFile

	## PRINTING YIELD TABLE WITH UNCERTAINTIES ##
	#first print table without background grouping
	ljust_i = 1
	print 'CUTS:',cutString
	print
	print 'YIELDS'.ljust(20*ljust_i), 
	for bkg in bkgStackList: print bkg.ljust(ljust_i),
	print 'data'.ljust(ljust_i),
	print
	for isEM in isEMlist:
		histoPrefix=discriminant+'_'+lumiStr+'fb_'+isEM
		print (isEM).ljust(ljust_i),
		for bkg in bkgStackList:
			print str(yieldTable[histoPrefix][bkg])+'\t',
		print str(yieldTable[histoPrefix]['data']),
		print

	print 'YIELDS STATISTICAL + NORM. SYS. ERRORS'
	for isEM in isEMlist:
		histoPrefix=discriminant+'_'+lumiStr+'fb_'+isEM
		print (isEM).ljust(ljust_i),
		for bkg in bkgStackList:
			print str(math.sqrt(yieldErrTable[histoPrefix][bkg])).ljust(ljust_i),
		print str(math.sqrt(yieldErrTable[histoPrefix]['data'])).ljust(ljust_i),
		print

	#now print with top,ewk,qcd grouping
	print
	print 'YIELDS'.ljust(20*ljust_i), 
	print 'ewk'.ljust(ljust_i),
	print 'top'.ljust(ljust_i),
	print 'qcd'.ljust(ljust_i),
	print 'data'.ljust(ljust_i),
	print
	for isEM in isEMlist:
		histoPrefix=discriminant+'_'+lumiStr+'fb_'+isEM
		print (isEM).ljust(ljust_i),
		print str(yieldTable[histoPrefix]['ewk']).ljust(ljust_i),
		print str(yieldTable[histoPrefix]['top']).ljust(ljust_i),
		print str(yieldTable[histoPrefix]['qcd']).ljust(ljust_i),
		print str(yieldTable[histoPrefix]['data']).ljust(ljust_i),
		print

	print 'YIELDS STATISTICAL + NORM. SYS. ERRORS'
	for isEM in isEMlist:
		histoPrefix=discriminant+'_'+lumiStr+'fb_'+isEM
		print (isEM).ljust(ljust_i),
		print str(math.sqrt(yieldErrTable[histoPrefix]['ewk'])).ljust(ljust_i),
		print str(math.sqrt(yieldErrTable[histoPrefix]['top'])).ljust(ljust_i),
		print str(math.sqrt(yieldErrTable[histoPrefix]['qcd'])).ljust(ljust_i),
		print str(math.sqrt(yieldErrTable[histoPrefix]['data'])).ljust(ljust_i),
		print

	#print yields for signals
	print
	print 'YIELDS'.ljust(20*ljust_i), 
	for sig in signalList: print sig.ljust(ljust_i),
	print
	for isEM in isEMlist:
		histoPrefix=discriminant+'_'+lumiStr+'fb_'+isEM
		print (isEM).ljust(ljust_i),
		for sig in signalList:
			print str(yieldTable[histoPrefix][sig]).ljust(ljust_i),
		print

	print 'YIELDS STATISTICAL + NORM. SYS. ERRORS'
	for isEM in isEMlist:
		histoPrefix=discriminant+'_'+lumiStr+'fb_'+isEM
		print (isEM).ljust(ljust_i),
		for sig in signalList:
			print str(math.sqrt(yieldErrTable[histoPrefix][sig])).ljust(ljust_i),
		print

	#print yields for total signals
	print
	print 'YIELDS'.ljust(20*ljust_i), 
	for sig in signals: print sig.ljust(ljust_i),
	print
	for isEM in isEMlist:
		histoPrefix=discriminant+'_'+lumiStr+'fb_'+isEM
		print (isEM).ljust(ljust_i),
		for sig in signals:
			print str(yieldTable[histoPrefix][sig]).ljust(ljust_i),
		print

	print 'YIELDS STATISTICAL + NORM. SYS. ERRORS'
	for isEM in isEMlist:
		histoPrefix=discriminant+'_'+lumiStr+'fb_'+isEM
		print (isEM).ljust(ljust_i),
		for sig in signals:
			print str(math.sqrt(yieldErrTable[histoPrefix][sig])).ljust(ljust_i),
		print
				
	#print for AN tables
	print
	print 'YIELDS'.ljust(20*ljust_i), 
	for isEM in isEMlist:
		histoPrefix=discriminant+'_'+lumiStr+'fb_'+isEM
		print histoPrefix.ljust(ljust_i),
	print
	for process in bkgStackList+['ewk','top','qcd','totBkg','data','dataOverBkg']+signals+signalList:
		print process.ljust(ljust_i),
		for isEM in isEMlist:
			histoPrefix=discriminant+'_'+lumiStr+'fb_'+isEM
			print ' & '+str(round_sig(yieldTable[histoPrefix][process],4))+' $\pm$ '+str(round_sig(math.sqrt(yieldErrTable[histoPrefix][process]),2)),
		print '\\\\',
		print
				
	sys.stdout = stdout_old
	logFile.close()

###########################################################
###################### LOAD HISTS #########################
###########################################################

def findfiles(path, filtre):
    for root, dirs, files in os.walk(path):
        for f in fnmatch.filter(files, filtre):
            yield os.path.join(root, f)

distList = []
for file in findfiles(outDir+'/'+isEMlist[0]+'/', '*.p'):
    if 'bkghists' not in file: continue
    distList.append(file.split('_')[-1][:-2])

for dist in distList:
	print "DISTRIBUTION: ",dist
	datahists = {}
	bkghists  = {}
	sighists  = {}
	#if dist!='minMlb' and dist!='HT':continue
	for isEM in isEMlist:
		print "LOADING: ",isEM
		datahists.update(pickle.load(open(outDir+'/'+isEM+'/datahists_'+dist+'.p','rb')))
		bkghists.update(pickle.load(open(outDir+'/'+isEM+'/bkghists_'+dist+'.p','rb')))
		sighists.update(pickle.load(open(outDir+'/'+isEM+'/sighists_'+dist+'.p','rb')))
	makeCats(datahists,sighists,bkghists,dist)

print 'AFTER YOU CHECK THE OUTPUT FILES, DELETE THE PICKLE FILES !!!!!!!'
print("--- %s minutes ---" % (round((time.time() - start_time)/60,2)))

