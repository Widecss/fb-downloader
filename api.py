"""
api
"""
import logging
import time

import requests


class ApiUrl:
    PAGINATE_CREATOR = r"https://api.fanbox.cc/post.paginateCreator"
    POST_INFO = r"https://api.fanbox.cc/post.info"


def _retry(func):
    def _func(*args, **kwargs):
        count = 0
        while True:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                count += 1
                logging.error(e)
                logging.info(f"请求失败，正在重试...({count})")

    return _func


def _log_info(func):
    def _func(*args, **kwargs):
        logging.info(f"{func.__name__}: {args[1:]} - {kwargs}")
        return func(*args, **kwargs)

    return _func


def _return_body_or_log_error(func):
    def _func(*args, **kwargs):
        response = func(*args, **kwargs)
        if response.status_code == 200:
            return response.json()["body"]
            # return response.text
        else:
            logging.error(f"{response.status_code}: {response.text}")
            return None

    return _func


class DownloadBuffer:
    # 1MB/read
    ONCE_READ = 1024 * 1024

    def __init__(self, response: requests.Response = None, limit_speed: int = 0):
        self.response = response
        self.limit_speed = limit_speed
        self.last_read_time = 0

    @_retry
    def read(self):
        """while chunk := buffer.read()"""
        if self.response is None:
            return None

        return self.response.raw.read(self.ONCE_READ)


class _NetworkWrapper:
    def __init__(self):
        self.headers = {
            "origin": r"https://www.fanbox.cc",
            "user-agent": r"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          r"AppleWebKit/537.36 (KHTML, like Gecko) "
                          r"Chrome/97.0.4692.99 "
                          r"Safari/537.36"
        }
        self.proxies = {}
        self.sleep_time = 1
        self.limit_speed = 0

    def set_cookie(self, cookie):
        self.headers["cookie"] = cookie

    def set_proxies(self, url):
        if url:
            self.proxies["http"] = url
            self.proxies["https"] = url

    def set_request_time_sleep(self, sleep_time):
        self.sleep_time = sleep_time

    def set_stream_speed_limit(self, limit_speed):
        self.limit_speed = limit_speed

    @staticmethod
    def _get_body_or_log_error(method, response):
        if response.status_code == 200:
            return response.json()["body"]
            # return response.text
        else:
            logging.error(f"{method}: {response.status_code}: {response.text}")
            return None

    @_retry
    def _request(self, method, *args, **kwargs) -> requests.Response:
        time.sleep(self.sleep_time)
        if self.proxies:
            _proxies = self.proxies
        else:
            _proxies = None

        return method(*args, **kwargs, proxies=_proxies, headers=self.headers)


class APIWrapper(_NetworkWrapper):
    @_return_body_or_log_error
    @_log_info
    def paginate_creator(self, creator_id: str):
        """
        返回所有页面的地址
        :param creator_id: 作者id
        :return: List[STR_URL]
        """
        data = {
            "creatorId": creator_id
        }
        return self._request(method=requests.get, url=ApiUrl.PAGINATE_CREATOR, params=data)

    @_return_body_or_log_error
    @_log_info
    def list_creator(self, url):
        """
        请求页面地址获得每页的所有物品
        :param url: 页面地址
        :return: List[Item]
        """
        return self._request(method=requests.get, url=url)

    @_return_body_or_log_error
    @_log_info
    def post_info(self, post_id):
        data = {
            "postId": post_id
        }
        return self._request(method=requests.get, url=ApiUrl.POST_INFO, params=data)

    @_log_info
    def open_download_buffer(self, url) -> DownloadBuffer:
        response = self._request(method=requests.get, url=url, stream=True)
        if response.status_code == 200:
            return DownloadBuffer(response, self.limit_speed)
        else:
            logging.error(f"download file url({url}) error: {response.status_code}")
            return DownloadBuffer(None, self.limit_speed)


if __name__ == '__main__':
    pass
