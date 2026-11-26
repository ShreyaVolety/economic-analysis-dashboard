import pandas as pd
import numpy as np
import datetime 
from datetime import datetime

def read_latest_data():
    FRED_DAILY_TICKERS = [
    "DGS2",                
    "DGS10",               
    "DFII10",              
    "T10YIE",              
    "T5YIE",              
    "T10Y2Y",              
    "T10Y3M",              
    "DCOILWTICO",         
    "DTWEXBGS",            
    "GVZCLS"             
]

    final_daily = pd.DataFrame()
    count = 0

    for ticker in FRED_DAILY_TICKERS:
        
        print(f'Reading: {ticker}')
        if count==0:
            temp = pd.read_csv(f'raw_data/latest_pull_{ticker}_2026-05-07.csv',index_col=0)
            temp = temp.dropna()
            temp = temp.reset_index()
            final_daily['Date'] = temp['index']
            final_daily[ticker] = temp[ticker]

        else:
            temp = pd.read_csv(f'raw_data/latest_pull_{ticker}_2026-05-07.csv',index_col=0)
            temp = temp.dropna()
            temp = temp.reset_index()
            temp.columns = ['Date',ticker]
            final_daily = final_daily.merge(temp, on='Date', how='left')
        

        count+=1
        
    FRED_MONTHLY_TICKERS = [
        "CPIAUCSL",            
        "CPILFESL",            
        "PPIACO",              
        "MICH",                
        "FEDFUNDS",                   
        "M2SL",                          
        "UNRATE",             
        "PAYEMS",              
        "AHETPI",              
        "JTSJOL",              
        "CSUSHPISA",           
        "USREC",               
        "RECPROUSM156N",
        'BOGMBASE',                     
    ]

    final_monthly = pd.DataFrame()
    count = 0

    for ticker in FRED_MONTHLY_TICKERS:
        
        print(f'Reading: {ticker}')
        if count==0:
            temp = pd.read_csv(f'raw_data/latest_pull_{ticker}_2026-05-07.csv',index_col=0)
            temp = temp.dropna()
            temp = temp.reset_index()
            final_monthly['Date'] = temp['index']
            final_monthly[ticker] = temp[ticker]

        else:
            temp = pd.read_csv(f'raw_data/latest_pull_{ticker}_2026-05-07.csv',index_col=0)
            temp = temp.dropna()
            temp = temp.reset_index()
            temp.columns = ['Date',ticker]
            final_monthly = final_monthly.merge(temp, on='Date', how='left')
        

        count+=1

    final_weekly = pd.read_csv(f'raw_data/latest_pull_MORTGAGE30US_2026-05-07.csv',index_col=0)
    print('Reading: MORTGAGE30US')
    final_weekly = final_weekly.reset_index()
    final_weekly.columns = ['Date','MORTGAGE30US']

    final_daily['Date']   = pd.to_datetime(final_daily['Date'])
    final_weekly['Date']  = pd.to_datetime(final_weekly['Date'])
    final_monthly['Date'] = pd.to_datetime(final_monthly['Date'])

    # resample to month end
    final_daily_m   = final_daily.resample("ME",  on="Date").last()
    final_weekly_m  = final_weekly.resample("ME", on="Date").last()
    final_monthly_m  = final_monthly.resample("ME", on="Date").last()



    df = pd.concat([final_daily_m, final_weekly_m, final_monthly_m], axis=1)
    df = df.loc[:, ~df.columns.duplicated(keep="first")]
    df = df.ffill()



    df["CPI_YOY"] = df["CPIAUCSL"].pct_change(12) * 100
    df["CPI_MOM"] = df["CPIAUCSL"].pct_change(1) * 100
    df["REAL_FEDFUNDS"] = df["FEDFUNDS"] - df["CPI_YOY"]
    df["CURVE_INVERTED"] = (df["T10Y2Y"] < 0).astype(int)

    return df, final_daily, final_monthly, final_weekly
