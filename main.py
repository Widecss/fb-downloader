"""
主脚本

由于 fanbox 的设计, 数据接口是倒过来的, 所以此脚本会从最新爬到最老
"""
import json
import logging
import sys
from io import BytesIO

import parse
import util
from api import APIWrapper
from config import Logger, File, Script


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
        if util.check_cookie() is False:
            sys.exit(-1)

        self.api = APIWrapper()

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

        for file_name, data_type, data_content in files:
            if data_type == "url":
                buffer = self.api.open_download_buffer(data_content)
            elif data_type == "text":
                buffer = BytesIO(data_content.encode(File.encoding))
            else:
                raise TypeError(f"意外的保存文件类型：{data_type}")

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

        if File.save_raw_json and item:
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

        logging.info(f"{count} 个内容保存完毕")

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
