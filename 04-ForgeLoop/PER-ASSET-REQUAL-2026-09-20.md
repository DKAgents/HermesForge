# PER-ASSET G3 RE-QUALIFICATION — 2026-09-20

All 14 PROMOTE strategies from BATCH-SWEEP-2026-09-19 re-qualified on a per-asset basis.

**Methodology:**
- Group backtest CSV trades by symbol
- Apply cost drag: `cost_r = venue_cost_bps / 10000 / risk_pct` (stock=2bps, crypto=12bps)
- Compute per-symbol: avg net R, win rate, trade count, PF
- ELIGIBLE: ≥5 trades AND avg net R > 0
- REJECTED: ≥5 trades AND avg net R ≤ 0
- INSUFFICIENT_DATA: <5 trades

**Cost model:** cost_adjuster.py VENUE_COSTS — stock=2.0 bps, crypto=12.0 bps

---

## PER-STRATEGY BREAKDOWN

### 1. STR-20260906-BTC-SUPPLY-CRUNCH
- **Asset class:** crypto
- **CSV:** STR-20260906-BTC-SUPPLY-CRUNCH-phase1a.csv (65 trades, 1 symbol)
- **ELIGIBLE (1):** BTC (+0.24R net, 65t, WR=52.3%, PF=1.72)
- **REJECTED:** none
- **INSUFFICIENT_DATA:** none
- **Note:** Single-symbol crypto strategy. Narrow edge but passes G3. BTC-only.

### 2. STR-B-macd-histogram-divergence
- **Asset class:** stock
- **CSV:** STR-B-macd-histogram-divergence-phase1a.csv (3,121 trades, 514 symbols)
- **ELIGIBLE (254):** See full list below. Top: PANW(+8.75R), ES(+6.72R), AMCR(+5.51R), HRL(+5.26R), EG(+5.14R)
- **REJECTED (97):** AAPL, ACN, ADSK, AES, ALL, AMP, APTV, BNY, BSX, CBOE, CF, CFG, CHD, CINF, CMI, CNC, COF, COST, CPT, CRL, CSX, CVX, D, DASH, DD, DIS, DLTR, DUK, ELV, ETR, FE, FIX, FLEX, GD, GILD, GIS, GM, GOOGL, HD, HLT, HWM, IRM, IT, IVZ, IWM, JBL, L, LIN, LRCX, MA, MAA, MAR, MCD, MCK, MDLZ, MDT, MMM, NDAQ, NEM, NVR, NWSA, OKE, PG, PNC, PNW, PPL, RCL, RJF, ROST, RSG, SBAC, SMH, SNA, SNPS, SPGI, SPY, SYF, SYY, TGT, TJX, TRGP, TSM, TT, TTD, URI, USB, VRTX, VTI, WAB, WBD, WEC, WELL, WFC, WM, WSM, ZS, ZTS
- **INSUFFICIENT (163)**
- **Existing ELIGIBLE entry DISCREPANCIES:**
  - SPY → REJECTED (was listed as eligible)
  - IWM → REJECTED (was listed as eligible)
  - AAPL → REJECTED (was listed as eligible)
  - GOOGL → REJECTED (was listed as eligible)
  - NVDA → INSUFFICIENT_DATA (3 trades only, was listed as eligible)
  - AMZN → INSUFFICIENT_DATA (3 trades only, was listed as eligible)
  - META → INSUFFICIENT_DATA (4 trades only, was listed as eligible)
  - BTC, ETH, SOL → NOT IN CSV (was listed as eligible, no backtest data)
  - **Kept:** QQQ, DIA, MSFT, TSLA

**ELIGIBLE (254):** A, ABBV, ACGL, ADP, AEP, AFL, AIZ, AJG, ALLE, AMCR, AME, AMT, ANET, AON, APH, ARE, ARES, ATO, AVB, AWK, AXON, AZO, BAC, BALL, BDX, BF-B, BG, BKNG, BLK, BMY, BRK-B, BRO, C, CAH, CASY, CB, CBRE, CCI, CDW, CHTR, CIEN, CL, CLX, CMCSA, CME, CMG, CMS, CNP, COO, COP, COR, CPAY, CPRT, CRH, CRM, CSCO, CTAS, CTVA, DAL, DE, DECK, DG, DGX, DIA, DLR, DOV, DTE, DVA, DXCM, EA, ECL, ED, EFX, EG, EIX, EMR, EQIX, EQR, ERIE, ES, ESS, ETN, EVRG, EW, EXE, EXPD, FAST, FDS, FFIV, FICO, FIS, FISV, FTNT, FTV, GDDY, GE, GEN, GL, GLD, GLW, GOOG, GPC, GPN, GRMN, GS, HAL, HAS, HBAN, HIG, HON, HPE, HRL, HST, HSY, HUBB, HUM, IBKR, IBM, ICE, IEX, IFF, INCY, INTU, IR, ITW, J, JCI, JNJ, JPM, KEY, KEYS, KHC, KKR, KMB, KMI, KO, KR, KVUE, LDOS, LEN, LH, LHX, LMT, LNT, LOW, LULU, LYV, MAS, MCO, MET, MGM, MKC, MLM, MO, MPC, MRK, MRSH, MS, MSFT, MSI, MTD, NDSN, NEE, NFLX, NI, NOC, NRG, NSC, NTRS, NUE, NWS, O, ODFL, OMC, ORCL, ORLY, OTIS, PANW, PAYX, PCAR, PEG, PEP, PFG, PGR, PH, PKG, PLD, PM, PNR, PODD, PRU, PSA, PWR, QQQ, REGN, RF, RL, RMD, ROK, ROL, ROP, RTX, SBUX, SHW, SJM, SO, SPOT, STE, STT, STZ, SWK, T, TAP, TDG, TECH, TFC, TLT, TMUS, TRMB, TRV, TSLA, TXN, TYL, UAL, UDR, UNH, UNP, V, VLTO, VMC, VRSK, VRSN, VTR, VZ, WAT, WMB, WMT, WST, WTW, WY, XEL, XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLU, XLV, XLY, XOM, XYL, YUM

### 3. STR-20260730-atr-contraction-breakout
- **Status: UNIVERSE_ONLY** — No per-trade CSV found. Cannot perform per-asset analysis without re-running backtest with per-trade export.
- **Recommendation:** Re-run backtest with ticker-level trade export before qualifying for per-asset eligibility.

### 4. STR-DEBASEMENT-treasury-buyback
- **Asset class:** crypto
- **CSV:** STR-DEBASEMENT-phase1a.csv (65 trades, 1 symbol)
- **ELIGIBLE (1):** BTC (+0.28R net, 65t, WR=53.8%, PF=1.77)
- **REJECTED:** none
- **INSUFFICIENT_DATA:** none
- **Note:** BTC-only crypto strategy. Thin edge but passes G3.

### 5. STR-20260728-adaptive-trend (STR-I)
- **Asset class:** stock
- **CSV:** STR-20260728-adaptive-trend-phase1a.csv (1,730 trades, 381 symbols)
- **ELIGIBLE (91):** ALB, AMD, ANET, APP, ARM, ASML, AVGO, BA, CCL, CDNS, CEG, CIEN, COHR, COIN, COP, CRWD, CVNA, DASH, DDOG, DECK, DELL, DVA, DVN, DXCM, ECHO, EME, EOG, EQT, EXPE, FANG, FCX, FDX, FICO, FLEX, FSLR, FTNT, GEN, HAL, HOOD, HWM, INTC, IVZ, JBL, LLY, LRCX, LUV, LVS, MCHP, META, MOS, MPWR, MRNA, MRVL, MU, NCLH, NRG, NUE, NVDA, ON, ORCL, OXY, PANW, PLTR, PODD, PSKY, PSX, PWR, QCOM, RCL, SHOP, SLB, SMCI, SNDK, SNOW, STX, TEAM, TECH, TER, TPL, TPR, TSLA, UAL, UBER, VRT, VST, WBD, WDC, WSM, WYNN, XYZ, ZS
- **Top 5 by net R:** SNDK(+1.50R), TPR(+1.35R), FDX(+1.16R), NVDA(+1.15R), HOOD(+1.05R)
- **REJECTED (29):** ABNB, AES, ALGN, AMAT, APA, AXON, BBY, BIIB, BLDR, CF, CMG, CSX, DG, DHI, EL, ENPH, ESTC, EXAS, FIS, GFS, GLW, HSY, IBM, IP, KKR, LHX, NEM, NOW, SBUX
- **INSUFFICIENT_DATA (261)**
- **Note:** Growth/momentum heavy. Most eligible tickers are tech/crypto-adjacent names.

### 6. STR-20260901-oil-shock-sector-rotation
- **Asset class:** stock
- **CSV:** STR-OIL-SHOCK-phase1a.csv (148 trades, 4 symbols)
- **ELIGIBLE (4):** CVX (+0.07R, 37t), XLE (+0.23R, 37t), XLY (+0.10R, 37t), XOM (+0.32R, 37t)
- **REJECTED:** none
- **INSUFFICIENT_DATA:** none
- **Note:** Narrow sector strategy. Only 4 tickers total, all pass. XOM strongest.

### 7. STR-20260917-CAP-BOTTOM
- **Asset class:** crypto
- **CSV:** STR-CAP-BOTTOM-CRYPTO-CAPITULATION-BOUNCE-phase1a.csv (139 trades, 3 symbols)
- **ELIGIBLE (2):** ETH (+0.17R, 47t, WR=53.2%, PF=1.31), SOL (+0.22R, 56t, WR=57.1%, PF=1.55)
- **REJECTED (1):** BTC (-0.07R, 36t, WR=50.0%, PF=0.93)
- **INSUFFICIENT_DATA:** none
- **Note:** Only crypto strategy with multi-asset qualification. BTC surprisingly fails per-asset despite universe-level G3 pass.

### 8. STR-VIXC-vix-contango-breakout
- **Asset class:** stock
- **CSV:** STR-20260816-VIX-VRP-CONTANGO-phase1a.csv (15,518 trades, 527 symbols)
- **ELIGIBLE (349):** Broad eligibility across sectors. See full list below.
- **Top 5 by net R:** PFE(+0.81R), SOLV(+0.65R), CF(+0.61R), NDAQ(+0.60R), SNDK(+0.59R)
- **REJECTED (177)**
- **INSUFFICIENT_DATA (1)**
- **ELIGIBLE (349):** AAPL, ABBV, ABNB, ABT, ACGL, ACN, ADM, ADP, ADSK, AEE, AEP, AES, AIZ, AJG, AKAM, ALB, ALL, ALLE, AMAT, AMD, AME, AMGN, AMP, ANET, AON, AOS, APA, APD, APO, APP, ARE, ARES, ASML, AVGO, AXP, AZO, BA, BAC, BALL, BBY, BEN, BG, BIIB, BKR, BLK, BRO, BX, BXP, C, CARR, CASY, CAT, CB, CBOE, CBRE, CEG, CF, CFG, CHD, CHTR, CIEN, CL, CLX, CMG, CMI, CMS, CNC, COF, COHR, COIN, COP, COST, CRH, CRL, CRM, CRWD, CSX, CTAS, CTSH, CTVA, CVNA, CVX, DAL, DASH, DD, DDOG, DECK, DELL, DHI, DIA, DLR, DLTR, DOC, DOV, DPZ, DUK, DVA, DVN, DXCM, ECHO, ECL, EG, EIX, EL, EME, EOG, EQIX, ERIE, ES, ESS, ETN, ETR, EVRG, EW, F, FANG, FAST, FCX, FDX, FE, FFIV, FIS, FITB, FIX, FLEX, FOXA, FTNT, FTV, GE, GEN, GILD, GL, GLD, GLW, GM, GNRC, GOOG, GOOGL, GPC, GRMN, GS, GWW, HAL, HAS, HBAN, HCA, HD, HIG, HII, HON, HOOD, HPE, HPQ, HSY, HUM, HWM, IBKR, IBM, ICE, IEX, INCY, INTU, INVH, IR, IRM, ISRG, IT, ITW, IVZ, IWM, J, JBHT, JCI, JKHY, JNJ, JPM, KEY, KHC, KIM, KKR, KLAC, KMI, KO, KVUE, LDOS, LEN, LH, LITE, LLY, LMT, LRCX, LUV, LVS, LYB, LYV, MAR, MAS, MCD, MCHP, MCK, MET, MGM, MKC, MLM, MO, MPC, MPWR, MRNA, MS, MSCI, MSI, MTB, MU, NCLH, NDAQ, NDSN, NEE, NEM, NOW, NRG, NSC, NTAP, NUE, NVDA, NXPI, ODFL, OKE, ON, ORCL, ORLY, OTIS, PANW, PAYX, PCG, PEG, PFE, PFG, PG, PGR, PH, PHM, PKG, PLD, PNC, PNR, PNW, PODD, PPG, PRU, PSA, PSX, PWR, QCOM, QQQ, RCL, REGN, RF, RL, ROK, ROST, RSG, RTX, RVTY, SBAC, SCHW, SHW, SJM, SLB, SMCI, SMH, SNDK, SNOW, SNPS, SO, SOLV, SPG, SPGI, SRE, STE, STLD, STX, STZ, SYF, SYY, T, TDG, TDY, TEAM, TER, TFC, TGT, TKO, TMO, TMUS, TPL, TPR, TRGP, TROW, TRV, TSLA, TSM, TT, TTD, TYL, UBER, UDR, UHS, ULTA, UNH, UNP, URI, USB, V, VICI, VLO, VMC, VRSK, VRT, VST, VTI, VTR, VTRS, VZ, WAB, WAT, WBD, WDC, WEC, WELL, WFC, WM, WMB, WMT, WRB, WSM, WY, XBI, XLB, XLE, XLF, XLI, XLK, XLP, XLU, XLV, XLY, XOM, XYL, XYZ

### 9. STR-20260818-lowcorr-regime
- **Asset class:** stock
- **CSV:** scanner_lowcorr_regime-phase1a.csv (31,464 trades, 506 symbols)
- **ELIGIBLE (317):** Largest sample. Broad rotation strategy.
- **Top 5 by net R:** HUBB(+1.09R), SNA(+0.85R), TPR(+0.74R), NWS(+0.72R), PPG(+0.71R)
- **REJECTED (167)**
- **INSUFFICIENT_DATA (22)**
- **ELIGIBLE (317):** AAPL, ABBV, ABT, ACGL, ACN, ADBE, ADI, ADM, ADP, AEE, AEP, AES, AFL, AIG, AIZ, AJG, AKAM, ALB, ALGN, ALL, AMD, AMGN, AMZN, ANET, AON, APD, APH, APO, APP, APTV, ARE, ARES, ARKK, ARM, ASML, ATO, AVB, AWK, AZO, BA, BALL, BG, BKNG, BKR, BLDR, BMY, BXP, CAH, CASY, CB, CBOE, CBRE, CCI, CDNS, CDW, CEG, CHD, CHRW, CHTR, CI, CINF, CMCSA, CME, CMG, CMS, CNC, CNP, COIN, COR, COST, CPRT, CPT, CRH, CRM, CRWD, CSCO, CSX, CVNA, CVS, CVX, D, DD, DDOG, DE, DECK, DELL, DGX, DHI, DHR, DLTR, DOC, DPZ, DTE, DUK, DVA, DXCM, EA, EBAY, ECHO, ECL, ED, EG, EIX, EL, ELV, EME, EMR, EQIX, EQR, EQT, ERIE, ES, ETN, ETR, EVRG, EW, EXC, EXE, EXPE, EXR, F, FDS, FE, FFIV, FICO, FIX, FLEX, FOX, FOXA, FTNT, GD, GDDY, GE, GEHC, GEN, GEV, GILD, GLD, GLW, GM, GOOG, GOOGL, HD, HIG, HII, HPE, HPQ, HSIC, HSY, HUBB, HUM, HWM, IBKR, IFF, INTC, INTU, INVH, IP, IQV, IR, IRM, IVZ, J, JBHT, JBL, JCI, JKHY, JNJ, KDP, KMI, KO, KR, KVUE, LEN, LH, LHX, LITE, LLY, LMT, LNT, LOW, LRCX, LULU, MAA, MAS, MCD, MCK, MDLZ, MDT, MET, META, MGM, MLM, MMM, MNST, MO, MPC, MPWR, MRK, MRSH, MRVL, MSCI, MSFT, MU, NEE, NEM, NI, NKE, NOC, NOW, NRG, NVDA, NVR, NWS, NWSA, NXPI, OKE, OMC, ON, ORCL, ORLY, OTIS, PANW, PAYX, PCAR, PCG, PEP, PFG, PG, PGR, PHM, PKG, PLD, PLTR, PM, PNW, PODD, PPG, PSA, PSX, PTC, PWR, PYPL, QCOM, REGN, RMD, ROK, ROP, ROST, RSG, RTX, RVTY, SBUX, SCHW, SHOP, SJM, SMCI, SNA, SNDK, SNOW, SNPS, SO, SPOT, SRE, STLD, STX, SW, SWKS, T, TDY, TEAM, TECH, TER, TJX, TKO, TMO, TPR, TRGP, TRV, TSCO, TSLA, TSM, TT, TTD, TXT, TYL, UDR, UNH, UPS, VEEV, VICI, VLO, VRSK, VRSN, VRT, VRTX, VST, VTR, VZ, WAB, WBD, WDAY, WDC, WEC, WELL, WM, WMB, WMT, WRB, WSM, WST, WTW, XEL, XLU, XOM, XYZ, ZBH

### 10. STR-20260719-sr-role-reversal-entry (STR-D)
- **Asset class:** stock
- **CSV:** STR-D-sr-role-reversal-phase1a.csv (2,387 trades, 492 symbols)
- **ELIGIBLE (119):** ABBV, ADBE, ADI, AEP, AES, AFL, AKAM, ALLE, AMCR, AMZN, AOS, APO, ARES, AWK, AXP, BA, BAC, BAX, BDX, BLDR, BRK-B, CAT, CCI, CF, CL, CLX, CME, CMG, CMS, CNP, CPAY, CRWD, CSCO, CTAS, CTVA, DDOG, DGX, DPZ, DRI, DTE, DXCM, EA, ECL, EFX, ESS, ETN, ETR, EVRG, EXC, FDS, FDX, FE, FFIV, FICO, FTV, GLD, GLW, GM, GOOG, HD, HII, HPE, HSY, HUM, IBKR, IFF, IT, IVZ, IWM, J, JCI, JKHY, JNJ, KEYS, KKR, KO, KR, LITE, LNT, LOW, LULU, MAS, MCHP, MLM, MMM, MNST, MRNA, MS, MTB, MTD, NEM, NSC, NWSA, NXPI, O, PFE, PM, PNC, PNW, PTC, REGN, RF, RJF, SCHW, SNPS, STE, STZ, SWKS, SYY, TT, TTWO, VTR, WDAY, WDC, WEC, WFC, WY, XLY, XOM
- **Top 5:** STZ(+2.85R), ESS(+2.70R), CTAS(+2.02R), EA(+1.96R), CRWD(+1.95R)
- **REJECTED (114)**
- **INSUFFICIENT_DATA (259)**

### 11. STR-20260908-SKEW-PREDICTED
- **Asset class:** stock
- **CSV:** STR-SKEW-PRED-phase1a.csv (17,214 trades, 529 symbols)
- **ELIGIBLE (297):** A, AAPL, ABNB, ABT, ACN, ADBE, ADI, ADM, ADP, AEE, AEP, AES, AFL, AIZ, AKAM, ALLE, AMD, AMGN, AMT, ANET, AON, AOS, APA, APD, APO, APP, ARE, ARKK, ARM, AVY, AXON, BAC, BAX, BF-B, BIIB, BKR, BLDR, BLK, BMY, BNY, BR, BRO, BSX, BX, C, CAH, CCI, CCL, CDW, CEG, CF, CFG, CHRW, CHTR, CMCSA, CMG, CMI, CNC, CNP, COF, COHR, COIN, COP, COST, CPAY, CPRT, CPT, CRM, CRWD, CSCO, CSX, CTAS, CTSH, CVNA, DAL, DASH, DD, DDOG, DG, DIA, DIS, DLTR, DOC, DOV, DOW, DRI, DVA, DXCM, ECHO, ECL, ED, EFX, EL, EMR, EQIX, EQR, EQT, ESS, ETR, EW, EXE, EXPE, F, FANG, FCX, FDX, FE, FFIV, FIS, FISV, FIX, FLEX, FOX, FOXA, FSLR, FTNT, FTV, GD, GDDY, GE, GILD, GIS, GL, GLD, GLW, GM, GPC, GWW, HAL, HAS, HBAN, HIG, HII, HLT, HON, HPE, HPQ, HSIC, HST, HWM, ICE, IDXX, IEX, IFF, IRM, ISRG, IT, IVZ, IWM, JBHT, JBL, JKHY, KDP, KEY, KEYS, KHC, KIM, KKR, KLAC, KMI, KVUE, LDOS, LLY, LNT, LOW, LUV, LVS, LYB, MA, MAR, MAS, MCHP, MET, MGM, MKC, MLM, MRK, MRNA, MRSH, MRVL, MSFT, MTB, NCLH, NDAQ, NDSN, NFLX, NI, NOW, NTAP, NUE, NVDA, NWS, NWSA, NXPI, OMC, ON, ORCL, ORLY, OTIS, OXY, PANW, PAYX, PCAR, PEG, PFE, PFG, PH, PHM, PLTR, PM, PNC, PNR, PODD, PRU, PYPL, QCOM, RCL, RJF, RMD, ROL, RSG, RTX, RVTY, SBAC, SHW, SLB, SMCI, SMH, SNDK, SNOW, SNPS, SO, SPY, STT, STZ, SWKS, SYF, SYY, T, TDG, TEAM, TER, TFC, TGT, TJX, TKO, TLT, TPL, TPR, TRGP, TRMB, TRV, TSCO, TSLA, TT, TTD, TXN, TXT, TYL, UAL, UBER, UDR, ULTA, UNH, UNP, UPS, URI, USB, VICI, VLO, VRSK, VRSN, VRT, VRTX, VST, VTI, VTR, VTRS, VZ, WAT, WDAY, WDC, WFC, WM, WMB, WMT, WSM, WTW, WY, XBI, XLB, XLE, XLF, XLU, XLV, XYL, ZBRA
- **Top 5:** PNR(+0.95R), SNDK(+0.94R), GL(+0.93R), PNC(+0.86R), KIM(+0.83R)
- **REJECTED (229)**
- **INSUFFICIENT_DATA (3)**

### 12. STR-A-ma-pullback-fibonacci
- **Asset class:** stock
- **CSV:** STR-A-ma-pullback-fibonacci-phase1a.csv (1,123 trades, 455 symbols)
- **ELIGIBLE (19):** AMP, ARES, AXP, BAC, BALL, CHRW, CMI, CPRT, DECK, ETN, FIX, HCA, HLT, INCY, JPM, LEN, MO, RSG, SMH
- **REJECTED (22):** AJG, ALL, AVB, CAH, COO, EME, EMR, FICO, GDDY, HPQ, KEYS, NDAQ, NSC, PKG, RCL, RJF, SPG, TPR, TRGP, UAL, WY, XLU
- **INSUFFICIENT_DATA (414)**
- **Existing ELIGIBLE entry DISCREPANCIES:**
  - SPY, IWM, MSFT → NOT IN CSV (was listed as eligible)
  - QQQ → INSUFFICIENT_DATA (4 trades, was listed as eligible)
  - AAPL → INSUFFICIENT_DATA (3 trades, was listed as eligible)
  - NVDA → INSUFFICIENT_DATA (3 trades, was listed as eligible)
  - **Kept:** None of the original entries survive per-asset re-qual.
- **Note:** Most symbols have <5 trades. Only 19 pass with sufficient data. SPY, QQQ, IWM, AAPL, MSFT, NVDA do NOT appear or have insufficient data.

### 13. STR-G-relative-strength
- **Asset class:** stock
- **CSV:** STR-G-relative-strength-rotation-phase1a.csv (21,593 trades, 528 symbols)
- **ELIGIBLE (316):** Quarterly rotation strategy. Broad eligibility.
- **Top 5:** GD(+478.48R outlier, likely data artifact), MSFT(+4.29R), MRNA(+0.74R), GLD(+0.70R), APP(+0.69R)
- **REJECTED (212)**
- **INSUFFICIENT_DATA (0)**
- **Note:** GD at +478R is likely a data error in the CSV. Exclude from paper unless verified.
- **ELIGIBLE (316):** A, AAPL, ABNB, ABT, ACGL, ACN, ADBE, ADI, ADM, ADP, ADSK, AES, AFL, AIZ, AJG, AKAM, ALB, ALGN, ALLE, AMAT, AMD, AME, AMP, AMZN, AON, AOS, APA, APH, APO, APP, ARES, ARM, ASML, ATO, AVGO, AXON, AXP, AZO, BAC, BBY, BF-B, BKNG, BKR, BLDR, BLK, BMY, BRO, BSX, BX, C, CAH, CARR, CAT, CCI, CCL, CDNS, CDW, CFG, CHD, CHRW, CME, CMI, CNC, CNP, COF, COHR, COIN, COO, COR, COST, CPRT, CPT, CRH, CRL, CRM, CRWD, CSCO, CSGP, CSX, CTAS, CTVA, CVX, DDOG, DECK, DELL, DHI, DHR, DIA, DIS, DLTR, DOV, DOW, DTE, DVA, DVN, EBAY, EFX, EL, ELV, EME, EMR, ESS, ETN, EW, EXE, EXPD, EXR, F, FCX, FDS, FDX, FFIV, FICO, FITB, FIX, FLEX, FOX, FOXA, FRT, FSLR, FTV, GD, GEN, GEV, GILD, GLD, GM, GNRC, GOOG, GOOGL, GRMN, GS, GWW, HAL, HD, HIG, HII, HON, HOOD, HPE, HPQ, HSIC, HWM, IBKR, ICE, INCY, INTC, INTU, IP, IQV, ITW, IVZ, IWM, JBHT, JCI, JNJ, KHC, KIM, KLAC, KMI, KO, KR, LDOS, LH, LHX, LII, LLY, LMT, LOW, LRCX, LULU, LUV, LYB, MA, MAA, MCHP, MCK, MCO, MDLZ, MET, META, MLM, MMM, MNST, MO, MPC, MRK, MRNA, MRSH, MRVL, MS, MSFT, MSI, MTB, MTD, MU, NCLH, NDAQ, NEM, NI, NOC, NUE, NVDA, ODFL, OKE, ORLY, OXY, PAYX, PCAR, PCG, PFE, PFG, PGR, PH, PHM, PKG, PLD, PLTR, PM, PNC, PNR, PPG, PPL, PSKY, PSX, PWR, PYPL, Q, QQQ, RCL, REG, REGN, RF, RJF, RL, ROK, ROST, RSG, RTX, RVTY, SBUX, SCHW, SHOP, SLB, SMCI, SMH, SNDK, SNOW, SNPS, SOLV, SPG, SPGI, SPOT, STLD, STX, SWKS, SYF, SYK, TAP, TDG, TDY, TECH, TEL, TER, TJX, TKO, TMO, TMUS, TPL, TRGP, TRMB, TROW, TSCO, TSLA, TSM, TSN, TT, TTD, TTWO, TYL, UBER, UHS, ULTA, UPS, URI, USB, VEEV, VICI, VLO, VRSK, VRT, VST, VTI, VTR, VTRS, WAB, WDC, WM, WMB, WMT, WRB, WSM, WST, WY, XBI, XEL, XLB, XLC, XLF, XLI, XLV, XOM, XYL, XYZ, ZS, ZTS

### 14. STR-C-breakout-volume-trend
- **Asset class:** stock
- **CSV:** STR-C-breakout-volume-phase1a.csv (12,070 trades, 529 symbols)
- **ELIGIBLE (239):** A, ABBV, ACGL, ADBE, ADM, ADP, AEE, AEP, AIZ, AMD, AME, AMGN, AMP, AON, APH, APP, ARE, ASML, AWK, AXON, BA, BBY, BDX, BEN, BF-B, BKNG, BKR, BLDR, BMY, BRK-B, BRO, BX, C, CAH, CAT, CB, CBOE, CBRE, CCI, CDW, CEG, CF, CFG, CHTR, CL, CMS, COF, COIN, COP, CRM, CSCO, CSX, CTVA, CVNA, CVS, CVX, DASH, DDOG, DE, DELL, DGX, DHI, DIA, DIS, DOC, DVA, DVN, EBAY, ECHO, ED, EIX, ELV, EQIX, ERIE, ES, ESS, EVRG, EXC, EXR, F, FCX, FITB, FIX, FLEX, FSLR, FTNT, FTV, GE, GLD, GNRC, GRMN, GS, GWW, HAL, HAS, HBAN, HII, HON, HOOD, HPE, HSY, HUM, HWM, IBM, ICE, IFF, ISRG, IVZ, IWM, JCI, JKHY, JPM, KEY, KIM, KLAC, KO, KR, KVUE, L, LDOS, LIN, LLY, LOW, LVS, LYB, LYV, MAA, MAR, MCK, MMM, MOS, MPC, MRNA, MRSH, MRVL, MS, MSCI, MSFT, MSI, MTD, MU, NDAQ, NDSN, NEE, NFLX, NKE, NRG, NTAP, NVDA, NWS, NWSA, OKE, ORCL, ORLY, OTIS, PAYX, PCAR, PEP, PFE, PGR, PH, PHM, PKG, PLD, PLTR, PM, PNC, PNR, PODD, PPG, PPL, PSA, PSX, PWR, Q, QQQ, RCL, REGN, ROK, ROL, ROST, RTX, SBAC, SHOP, SHW, SMCI, SMH, SNDK, SNOW, SO, SOLV, SPGI, SPOT, SRE, STT, STX, STZ, T, TDY, TECH, TEL, TER, TKO, TLT, TPL, TPR, TRGP, TRMB, TSLA, TXN, UAL, UHS, UNH, UNP, UPS, URI, USB, VLO, VRSK, VRT, VTR, WBD, WDC, WEC, WM, WMT, WSM, WST, WY, WYNN, XBI, XLE, XLK, XLU, XOM, XYL, XYZ, ZS, ZTS
- **Top 5:** COF(+6.92R, likely outlier), FSLR(+4.32R), Q(+3.60R), ECHO(+3.59R), AME(+3.31R)
- **REJECTED (290)**
- **INSUFFICIENT_DATA (0)**

---

## SUMMARY TABLE

| # | Strategy | ELIGIBLE | REJECTED | INSUFFICIENT | Status |
|---|---|---|---|---|---|
| 1 | STR-20260906-BTC-SUPPLY-CRUNCH | 1 | 0 | 0 | crypto BTC-only |
| 2 | STR-B-macd-histogram-divergence | 254 | 97 | 163 | qualified |
| 3 | STR-20260730-atr-contraction-breakout | — | — | — | UNIVERSE_ONLY |
| 4 | STR-DEBASEMENT-treasury-buyback | 1 | 0 | 0 | crypto BTC-only |
| 5 | STR-20260728-adaptive-trend | 91 | 29 | 261 | qualified |
| 6 | STR-20260901-oil-shock-sector-rotation | 4 | 0 | 0 | qualified |
| 7 | STR-20260917-CAP-BOTTOM | 2 | 1 | 0 | qualified |
| 8 | STR-VIXC-vix-contango-breakout | 349 | 177 | 1 | qualified |
| 9 | STR-20260818-lowcorr-regime | 317 | 167 | 22 | qualified |
| 10 | STR-20260719-sr-role-reversal-entry | 119 | 114 | 259 | qualified |
| 11 | STR-20260908-SKEW-PREDICTED | 297 | 229 | 3 | qualified |
| 12 | STR-A-ma-pullback-fibonacci | 19 | 22 | 414 | qualified |
| 13 | STR-G-relative-strength | 316 | 212 | 0 | qualified |
| 14 | STR-C-breakout-volume-trend | 239 | 290 | 0 | qualified |
| **TOTAL** | | **2,009** | **1,338** | **1,125** | |

**Total eligible strategy×asset pairs: 2,009**

---

## EXISTING ELIGIBILITY DISCREPANCIES (STR-B, STR-A)

### STR-B-macd-histogram-divergence
Previously listed as eligible but REJECTED on re-qual: **SPY, IWM, AAPL, GOOGL**
Previously listed but INSUFFICIENT_DATA: **NVDA, AMZN, META**
Previously listed but NOT IN CSV: **BTC, ETH, SOL** (no crypto trades in backtest CSV)

### STR-A-ma-pullback-fibonacci
Previously listed but NOT IN CSV or INSUFFICIENT_DATA: **ALL original entries** (SPY, QQQ, IWM, AAPL, MSFT, NVDA). None of these survive per-asset re-qual. The 19 newly qualified tickers replace the old list entirely.

---

## METHODOLOGY NOTES

1. All backtest CSVs found to have proper header rows (earlier analysis had a header-skipping bug).
2. Cost drag computed per trade: `(venue_cost_bps / 10000) / risk_pct` where `risk_pct = |entry - stop| / entry`.
3. Venue costs: stock=2.0 bps, crypto=12.0 bps (from cost_adjuster.py).
4. Asset class auto-detected from ticker — BTC/ETH/SOL treated as crypto.
5. STR-20260730-atr-contraction-breakout has no per-trade CSV; requires backtest re-run.
6. Several strategies show extreme outlier PFs (e.g., GD in STR-G at +478R). These are flagged as likely data artifacts requiring manual review before paper trading.