import pandas as pd
import stem
from abc import ABCMeta, abstractmethod
from bs4 import BeautifulSoup
from requests.exceptions import ProxyError, Timeout, HTTPError, RequestException
from stem import Signal
from stem.control import Controller

from skogkatt.commons.http.request import request
from skogkatt.conf.app_conf import app_config
from skogkatt.conf.crawl_conf import PROXIES
from skogkatt.core import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


def read_from(file_path) -> BeautifulSoup:
    """
    HTML 파일을 읽어서 BeautifulSoup 반환
    :param file_path: str, file path
    :return:
        BeautifulSoup
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        contents = file.read()
        return BeautifulSoup(contents, 'html5lib')


def remove_style(source, tag, style_txt=None):
    """
    html style attribute 제거. 특정 값을 가진 스타일만 제거할 때는
    style_txt를 지정
    :param source: bs4.element.Tag, html source
    :param tag: str, 대상 html tag
    :param style_txt: str, optional
        제거할 style 속성
    :return:
    """

    if style_txt is None:
        target = source.find_all(tag)
    else:
        target = source.find_all(tag, {"style": style_txt})

    for element in target:
        if element.has_attr('style'):
            del element.attrs['style']


def remove_tag(source, tag_name, style_class=None):
    """
    html tag 제거. 특정 클래스가 지정된 태그를 제거할 때는 style_class 지정
    :param source: bs4.element.Tag, html source
    :param tag_name: str, 제거할 tag 명
    :param style_class: str, optional
    :return:
    """
    if style_class is None:
        target = source.find_all(tag_name)
    else:
        target = source.find_all(tag_name, {"class": style_class})

    [tag.decompose() for tag in target]


def scrape(url, payload, use_proxy: bool = False) -> BeautifulSoup:
    """
    GET 방식으로 html을 읽어서 BeautifulSoup 객체 반환
    :param url: str, URL to read
    :param payload: dict, parameters
    :param use_proxy: bool, use proxy sever
    :return:
        BeautifulSoup
    """
    res = None
    if use_proxy:
        try:
            res = request.get(url=url, payload=payload, proxies=PROXIES)
        except ProxyError:
            logger.fatal("Proxy Server is not running.")
            raise
    else:
        res = request.get(url=url, payload=payload)

    return BeautifulSoup(res.content, "html5lib")


def to_dataframe(data_table, header_index=0, replace_column: dict = None):
    """
    HTML을 Dataframe으로 변환
    :param data_table: str, html
    :param header_index: int, 헤더 인덱스
    :param replace_column: dict, optional
        이름을 바꿀 컬럼 dict. ex) {'구분': 'LINE_ITEM'}
    :return:
        Dataframe
    """
    df = pd.read_html(str(data_table), header=[header_index])[0]

    if replace_column is not None:
        for src, rep in replace_column.items():
            df = df.rename(columns={src: rep})

    return df


def renew_connection():
    """
    signal TOR for a new connection
    """
    try:
        with Controller.from_port(port=9051) as controller:
            controller.authenticate(password=app_config.get('TOR_PASSWORD'))
            controller.signal(Signal.NEWNYM)
            controller.close()
    except stem.SocketError:
        logger.fatal("Tor Service is not running.")
        raise

    try:
        res = request.get(url='http://icanhazip.com/', payload={}, proxies=PROXIES)
        ip = res.text.strip()
        logger.debug(f'IP Address: {ip}')
    except (Timeout, ConnectionError, HTTPError, RequestException) as err:
        logger.info(err)


class UrlBuilder(metaclass=ABCMeta):

    def __init__(self):
        self._url = None
        self._payload = None

    @abstractmethod
    def build(self, **kwargs):
        pass

    @property
    def url(self):
        return self._url

    @property
    def payload(self):
        return self._payload
