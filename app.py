"""
主脚本

由于 fanbox 的设计, 数据接口是倒过来的, 所以此脚本会从最新爬到最老
"""
import json
import logging

import parse
import util
from api import APIWrapper


class Script:
    creator_id = r"shiratamaco"
    """作者 ID (作者主页的 URL 里那个)"""

    start_item_id = "4070200"
    """从这个 ID 开始, ID 在链接末尾, 为空从最新开始"""

    end_item_id = ""
    """爬完这个 ID 就终止脚本, 为空则爬到最早"""

    """需要单爬一个的时候，只需要把 start_item_id 和 end_item_id 设置成一样的就行了"""


class Network:
    cookie = r""
    """Cookie, 其实只填 FANBOXSESSID 就行了, 如果希望保险一点可以填全部"""

    proxy = ""
    """代理"""

    sleep_time = 1
    """每次网络请求的停顿时间, 单位秒, 觉得太慢了改成 0 也行（笑"""


class File:
    default_dir = f"./{Script.creator_id}"
    """输出文件夹, 默认是和作者 ID 一致"""

    save_restricted_tip = True
    """遇到受限制的, 把月费高于 xxx 才能浏览这个提示保存下来"""


class Logger:
    logger_level = "info"
    """显示的日志等级"""


class FileMixin:

    @staticmethod
    def create_dir(_id, _title):
        dir_name = util.ensure_file_name(f"{_id} {_title}")

        # 先清空确保没有旧数据
        if util.file_exists(dir_name):
            util.file_delete(dir_name)

        util.mkdir(dir_name)
        logging.info(f"create_dir: {dir_name}")
        return dir_name

    @staticmethod
    def save_restricted(dir_name, item):
        fee = item["feeRequired"]
        logging.info(f"save_restricted: 限制.txt")
        util.save_data(
            dir_name,
            "限制.txt",
            f"赞助月费高于 {fee} 日元即可浏览"
        )

    @staticmethod
    def save_raw(dir_name, item):
        logging.info(f"save_raw: raw.json")
        util.save_data(
            dir_name,
            "raw.json",
            json.dumps(item, indent=4)
        )


class Crawler(FileMixin):
    def __init__(self):
        # ---------- logging ----------
        level_name = Logger.logger_level.upper()
        level = logging.getLevelName(level_name)
        logging.basicConfig(
            level=level
        )

        # ---------- api ----------
        api = APIWrapper()
        api.set_cookie(Network.cookie)
        api.set_proxies(Network.proxy)
        api.set_request_time_sleep(Network.sleep_time)
        self.api = api

        # ---------- util ----------
        util.set_default_dir(File.default_dir)

        # ---------- other ----------
        self.start_switch = False
        self._reset_switch()

    def _reset_switch(self):
        if Script.start_item_id:
            self.start_switch = False
        else:
            self.start_switch = True

    def reset(self):
        self._reset_switch()

    def save_body(self, dir_name, item):
        logging.info(f"save_body: text.txt, ...")
        body = item["body"]

        text, files = parse.parse(item["type"], body)
        util.save_data(dir_name, "text.txt", text)

        for file_name, file_url in files:
            buffer = self.api.open_download_buffer(file_url)

            # if util.file_exists(dir_name, file_name):
            #     file_name = util.add_suffix(dir_name, file_name)

            util.save_buffer(dir_name, file_name, buffer)

    def save_cover_image(self, dir_name, item):
        url = item["coverImageUrl"]

        filename = util.get_filename(url)
        logging.info(f"save_cover_image: [cover] {filename}")

        buffer = self.api.open_download_buffer(url)
        util.save_buffer(dir_name, f"[cover] {filename}", buffer)

    def save_item(self, item: dict):
        _id = item["id"]
        _title = item["title"]
        logging.info(f"save_item: id={_id} title={_title}")

        dir_name = self.create_dir(_id, _title)

        if item:
            self.save_raw(dir_name, item)

        if item["coverImageUrl"]:
            self.save_cover_image(dir_name, item)

        if item["isRestricted"]:
            if File.save_restricted_tip:
                self.save_restricted(dir_name, item)
            # 如果是比当前发电等级更高的, 那肯定没有 body, 直接完成
            return

        if item["body"]:
            self.save_body(dir_name, item)

        logging.info("---------- ID(%s) 下载完毕 ----------" % item["id"])

    def loop_item(self, items):
        for item in items:
            # 是空的
            if not item:
                continue

            # 遇到起始 ID
            if Script.start_item_id == item["id"]:
                self.start_switch = True

            # 开关状态
            if self.start_switch is False:
                logging.info("跳过 ID(%s) ..." % item["id"])
                continue

            # 保存
            item_info = self.api.post_info(item["id"])
            self.save_item(item_info)

            # 是结束 ID
            if Script.end_item_id and item["id"] == Script.end_item_id:
                return True

    def loop_page(self, page_url_list: list[str]):
        # 开始
        count = 0
        for page_url in page_url_list:
            body = self.api.list_creator(page_url)

            # 是空的
            if not body:
                break

            # 保存项
            items = body["items"]
            count += len(items)
            if self.loop_item(items):
                return

        logging.info(f"{count} 个项目保存完毕")

    def run(self):
        page_url_list = self.api.paginate_creator(creator_id=Script.creator_id)
        # 是空的
        if not page_url_list:
            return

        # 从第一页开始保存
        self.loop_page(page_url_list)


if __name__ == '__main__':
    try:
        Crawler().run()
    except KeyboardInterrupt:
        print("Ctrl + C")
