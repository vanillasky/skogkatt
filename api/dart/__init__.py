import os

from skogkatt.commons.http.request import request
from skogkatt.commons.util.file import get_cache_folder, unzip
from skogkatt.conf.app_conf import app_config


def get_corp_code_file(url=None):
    """
    DART API 를 통해 회사목록 파일을 받아와서 임시 폴더에 저장.
    :param url: optional, str, DART API URL
    :return:
        회사목록 파일
    """
    import tempfile

    with tempfile.TemporaryDirectory() as path:
        url = url if url is not None else 'https://opendart.fss.or.kr/api/corpCode.xml'
        file_name = 'CORPCODE.xml'

        # Set API KEY
        api_key = app_config.get('DART_API_KEY')
        payload = {'crtfc_key': api_key}

        res = request.download(url=url, path=path, payload=payload)
        download_path = res['full_path']
        cache_folder = get_cache_folder()

        unzip_path = unzip(file=download_path, path=cache_folder)
        file = os.path.join(unzip_path, file_name)

        return file

