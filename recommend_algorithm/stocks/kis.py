import requests
from django.conf import settings


def get_access_token():
    url = f"{settings.KIS_URL}/oauth2/tokenP"

    body = {
        "grant_type": "client_credentials",
        "appkey": settings.KIS_APP_KEY,
        "appsecret": settings.KIS_APP_SECRET
    }

    res = requests.post(url, json=body)
    return res.json()["access_token"]


def get_stock_info(token, code):
    url = f"{settings.KIS_URL}/uapi/domestic-stock/v1/quotations/inquire-price"

    headers = {
        "authorization": f"Bearer {token}",
        "appkey": settings.KIS_APP_KEY,
        "appsecret": settings.KIS_APP_SECRET,
        "tr_id": "FHKST01010100"
    }

    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": code
    }

    res = requests.get(url, headers=headers, params=params)
    return res.json()