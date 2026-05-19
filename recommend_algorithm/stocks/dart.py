import requests
from django.conf import settings

DART_URL = "https://opendart.fss.or.kr/api"


def get_financial_info(corp_code, year="2023"):
    url = f"{DART_URL}/fnlttSinglAcnt.json"

    params = {
        "crtfc_key": settings.DART_API_KEY,
        "corp_code": corp_code,
        "bsns_year": year,
        "reprt_code": "11011"
    }

    res = requests.get(url, params=params)
    return res.json()