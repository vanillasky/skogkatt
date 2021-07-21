import importlib
import os
import zipfile
from pathlib import Path

from appdirs import user_cache_dir


def get_module(module_name, class_name=None):
    module = importlib.import_module(module_name)
    if class_name is not None:
        instance = getattr(module, class_name)
        return instance()
    else:
        return module


def create_folder(path: str):
    """
    폴더 생성
    :param path: str
    :return:
    """
    import pathlib
    try:
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)
    except FileExistsError:
        pass
    except OSError:
        raise


def get_cache_folder():
    """
    Create cache folder
    :return: str
        Cache Folder Path
    """
    app_name = 'skogkatt'
    cache_dir = user_cache_dir(app_name)
    create_folder(cache_dir)
    return cache_dir


def unzip(file: str, path: str = None, new_folder: bool = True) -> str:
    """
    Extract zip file
    :param file: str, zip 파일
    :param path: str, unzip 경로
    :param new_folder: 폴더 생성여부
    :return: str,  unzip 경로
    """
    os.path.altsep = '\\'
    head, tail = os.path.split(file)

    if path:
        extract_path = path
    else:
        extract_path = head

    with zipfile.ZipFile(file, 'r') as zip_ref:
        if new_folder:
            folder = tail.replace('.zip', '')
            extract_path = os.path.join(extract_path, folder)

        zip_ref.extractall(path=extract_path)

    return extract_path


def save_file(content: str, file_path: Path, file_name: str, use_user_home: bool = False):
    file_dir = file_path

    if use_user_home:
        home = Path.home()
        file_dir = home.joinpath(file_path)

    file_dir.mkdir(parents=True, exist_ok=True)
    filepath = file_dir.joinpath(f'{file_name}')

    with open(filepath, 'w', encoding='utf-8') as file:
        file.write(content)
