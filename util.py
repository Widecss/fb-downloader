"""
util
"""
import ntpath
import os
import shutil


class Settings:
    """文件设置"""

    default_dir = "./out"
    """默认输出的文件夹"""

    illegal_character = ["\\", "/", ":", "*", "?", "\"", "<", ">", "|"]
    """排除的文件名非法字符"""


def get_filename(path) -> str:
    return ntpath.split(path)[1]


def split_file_suffix(file_name) -> tuple:
    return ntpath.splitext(file_name)


def ensure_file_name(name):
    _name = str(name)
    for c in Settings.illegal_character:
        if c in _name:
            _name = _name.replace(c, "_")
    return _name


def mkdir(name):
    os.makedirs(f"{Settings.default_dir}/{name}", exist_ok=True)


def save_data(dir_name, path_name, data):
    if isinstance(data, str):
        mode = "w"
    elif isinstance(data, bytes):
        mode = "wb"
    else:
        raise TypeError(f"unknown value type: {type(data)}")

    with open(f"{Settings.default_dir}/{dir_name}/{path_name}", mode=mode, encoding="utf-8") as file:
        file.write(data)


def save_buffer(dir_name, path_name, buffer):
    with open(f"{Settings.default_dir}/{dir_name}/{path_name}", "wb") as file:
        while chk := buffer.read():
            file.write(chk)


def set_default_dir(_dir):
    Settings.default_dir = _dir


def file_exists(dir_name, file_name=""):
    return ntpath.exists(f"{Settings.default_dir}/{dir_name}/{file_name}")


def file_delete(dir_name, file_name=""):
    shutil.rmtree(f"{Settings.default_dir}/{dir_name}/{file_name}")


def add_suffix(dir_name, file_name=None):
    count = 1
    if file_name is None:
        while file_exists(dir_name + f"-{count}"):
            count += 1
        return dir_name + f"-{count}"
    else:
        _file_name, _suffix = split_file_suffix(file_name)
        while file_exists(dir_name, _file_name + f"-{count}." + _suffix):
            count += 1
        return _file_name + f"-{count}." + _suffix
