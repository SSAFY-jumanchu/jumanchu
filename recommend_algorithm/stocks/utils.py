import xml.etree.ElementTree as ET
import zipfile
import io
import requests
from django.conf import settings


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