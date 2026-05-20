import xml.etree.ElementTree as ET
import zipfile
import io
import requests
from django.conf import settings
import FinanceDataReader as fdr
import numpy as np

def get_corp_code_dict():
    url = "https://opendart.fss.or.kr/api/corpCode.xml"
    params = {"crtfc_key": settings.DART_API_KEY}

    res = requests.get(url, params=params)

    z = zipfile.ZipFile(io.BytesIO(res.content))
    xml_file = z.open(z.namelist()[0])

    tree = ET.parse(xml_file)
    root = tree.getroot()

    corp_map = {}

    for item in root.findall('list'):
        stock_code = item.find('stock_code').text
        corp_code = item.find('corp_code').text

        if stock_code:
            corp_map[stock_code] = corp_code

    return corp_map

def calculate_beta(code, start='2024-01-01'):
    try:
        stock = fdr.DataReader(code, start)
        market = fdr.DataReader('KS11', start)

        stock['return'] = stock['Close'].pct_change()
        market['return'] = market['Close'].pct_change()

        df = stock[['return']].join(
            market[['return']],
            lsuffix='_stock',
            rsuffix='_market'
        ).dropna()

        if len(df) < 30:
            return None

        cov = np.cov(df['return_stock'], df['return_market'])[0][1]
        var = np.var(df['return_market'])

        beta = cov / var if var != 0 else None

        return round(beta, 4)

    except Exception as e:
        print(f"베타 계산 실패 {code}: {e}")
        return None