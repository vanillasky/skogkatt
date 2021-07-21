import re
import time
import os
import requests

from functools import lru_cache
from fake_useragent import UserAgent
from urllib.parse import unquote


@lru_cache()
def get_user_agent():

    ua = UserAgent()
    agent = ua.chrome
    return str(agent)


class Request(object):

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'user-agent': get_user_agent()})
        self.delay = 1

    def request(self, url: str, method: str = 'GET', payload: dict = None, referer: str = None, proxies: dict = None, timeout: int = 120):
        """
        Send http request
        :param url: URL
        :param method: str, optional
            GET, POST, OPTIONS, PUT, PATCH or DELETE
        :param payload: dict, optional
            Request parameters
        :param referer: str, optional
            Temporary referer
        :param proxies: dict, optional
            Proxy settings
        :param timeout: int, optional
            default 120s
        :return:
            requests.Response
        """
        if proxies is not None:
            self.session.proxies = proxies

        headers = self.session.headers
        if referer is not None:
            headers['referer'] = referer

        req = requests.Request(method, url=url, params=payload, headers=headers)
        prepped = self.session.prepare_request(req)
        resp = self.session.send(prepped, timeout=timeout)
        if self.delay is not None:
            time.sleep(self.delay)
        return resp

    def get(self, url: str, payload: dict = None, referer: str = None, proxies: dict = None, timeout: int = 120):
        """
        Send GET request
        :param url: URL
        :param payload: dict, optional
            Request parameters
        :param referer: str, optional
            Temporary referer
        :param proxies: dict, optional
            proxy settings
        :param timeout: int, optional
            default 120s
        :return:
            requests.Response
        """

        return self.request(url=url, method='GET', payload=payload, referer=referer, proxies=proxies, timeout=timeout)

    def post(self, url: str, payload: dict = None, referer: str = None, timeout: int = 120):
        """
        Send POST request
        :param url: URL
        :param payload: dict, optional
            Request parameters
        :param referer: str, optional
            Temporary referer
        :param timeout: int, optional
            default 120s
        :return:
            requests.Response
        """

        return self.request(url=url, method='POST', payload=payload, referer=referer, timeout=timeout)

    def download(self, url: str, path: str, filename: str = None, method: str = 'GET', payload: dict = None, referer: str = None, timeout: int = 120):
        """
        Download File
        :param url: str
            Request URL
        :param path: str
            Download path
        :param filename: str
            Filename to save
        :param method: str, optional
            Request method
        :param payload: dict, optional
            Request parameters
        :param referer: str, optional
            Temporary referer
        :param timeout: int, optional 120s
        :return: dict
            filename, path, full_path
        """

        import pathlib
        try:
            pathlib.Path(path).mkdir(parents=True, exist_ok=True)
        except FileExistsError:
            pass
        except OSError:
            raise

        res = self.request(url=url, method=method, payload=payload, referer=referer, timeout=timeout)

        headers = res.headers.get('Content-Disposition')
        if headers is None or not re.search('attachment', headers):
            raise FileNotFoundError('Target does not exist')

        # total_size = int(res.headers.get('content-length', 0))
        block_size = 8192

        extracted_filename = unquote(re.findall(r'filename="?([^"]*)"?', headers)[0])

        if filename is None:
            filename = extracted_filename
        else:
            filename = filename.format(extracted_filename)

        file_path = os.path.join(path, filename)
        with open(file_path, 'wb') as f:
            for chunk in res.iter_content(chunk_size=block_size):
                if chunk is not None:
                    f.write(chunk)
        res.close()

        self.session.close()

        return {'filename': filename, 'path': path, 'full_path': file_path}


request = Request()

