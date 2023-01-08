"""
parse
"""

import util


class Const:
    URL_EMBED_URL = r"https://www.fanbox.cc/@%s/posts/%s"


class MuteText:
    def __init__(self):
        self._context = ""

    def append(self, other: str):
        self._context += other

    def replace(self, *args, **kwargs):
        self._context = self._context.replace(*args, **kwargs)

    def to_str(self) -> str:
        return self._context


class _ArticleParser:
    def __init__(self):
        self._parse_func = {
            "blocks": self._blocks,
            "imageMap": self._image_map,
            "fileMap": self._file_map,
            "embedMap": self._embed_map,
            "urlEmbedMap": self._url_embed_map
        }
        self._url_embed_parse_func = {
            "fanbox.post": self.__url_embed_fanbox_post,
            "html.card": self.__url_embed_html_card,
            "html": self.__url_embed_html_card
        }

    @staticmethod
    def __url_embed_fanbox_post(url_embed, texts: MuteText, files: list):
        post_info = url_embed["postInfo"]
        key = url_embed["id"]

        info_id = post_info["id"]
        info_creator_id = post_info["creatorId"]
        url = Const.URL_EMBED_URL % (info_creator_id, info_id)

        info_title = post_info["title"]
        texts.replace(
            f"[type=url_embed, id={key}]",
            f"[type=url_embed, title={info_title}, url={url}]"
        )

    @staticmethod
    def __url_embed_html_card(url_embed, texts: MuteText, files: list):
        html = url_embed["html"]
        key = url_embed["id"]
        files.append((f"{key}.html", "text", html))

    def _url_embed_map(self, body, texts: MuteText, files: list):
        if _map := body["urlEmbedMap"]:
            for key in _map.keys():
                url_embed = _map[key]

                url_embed_type = url_embed["type"]
                if url_embed_type not in self._url_embed_parse_func.keys():
                    raise TypeError(f"意外的 url_embed 类型: {url_embed_type}")

                self._url_embed_parse_func[url_embed_type](url_embed, texts, files)

    @staticmethod
    def _embed_map(body, texts: MuteText, files: list):
        if _map := body["embedMap"]:
            for key in _map.keys():
                embed = _map[key]

                embed_id = embed["id"]
                service_provider = embed["serviceProvider"]
                content_id = embed["contentId"]

                texts.replace(
                    f"[type=embed, id={key}]",
                    f"[type=embed, id={embed_id}, " +
                    f"service_provider={service_provider}, " +
                    f"content_id={content_id}]"
                )

    @staticmethod
    def _file_map(body, texts: MuteText, files: list):
        if _map := body["fileMap"]:
            for key in _map.keys():
                file = _map[key]

                file_url = file["url"]
                file_name = "[%s] %s.%s" % (file["id"], file["name"], file["extension"])

                files.append((file_name, "url", file_url))

    @staticmethod
    def _image_map(body, texts: MuteText, files: list):
        if _map := body["imageMap"]:
            for key in _map.keys():
                img = _map[key]

                file_url = img["originalUrl"]
                file_name = util.get_filename(file_url)

                files.append((file_name, "url", file_url))

    @staticmethod
    def _blocks(body, texts: MuteText, files: list):
        blocks: list = body["blocks"]

        for block in blocks:
            if block["type"] == "p":
                text = block["text"]
                texts.append(f"{text}\n")
            elif block["type"] == "header":
                text = block["text"]
                texts.append(f"## {text}\n")
            else:
                _type = block["type"]
                if _type not in ["image", "file", "embed", "url_embed"]:
                    raise TypeError(f"block_type: {_type}")
                if _type == "url_embed":
                    _id = block["urlEmbedId"]
                else:
                    _id = block[f"{_type}Id"]
                texts.append(f"[type={_type}, id={_id}]\n")

    def parse(self, body_type, body, texts, files):
        if body_type not in self._parse_func.keys():
            raise TypeError(f"意外的 Article 内容类型: {body_type}")
        return self._parse_func[body_type](body, texts, files)


_article_parser = _ArticleParser()


def _article(body: dict):
    # 存在 text.txt 中
    texts = MuteText()
    # 要下载的文件，[(file_name, data_type, data_content), ...]
    files = []

    for key in body.keys():
        _article_parser.parse(key, body, texts, files)

    return texts.to_str(), files


def _image(body: dict):
    texts = body["text"]
    files = []
    for img in body["images"]:
        file_url = img["originalUrl"]
        file_name = util.get_filename(file_url)

        files.append((file_name, "url", file_url))
    return texts, files


_parser = {
    "image": _image,
    "article": _article
}


def parse(type_name, body):
    if type_name not in _parser.keys():
        raise TypeError(f"意外的发电内容类型: {type_name}")
    return _parser[type_name](body)
