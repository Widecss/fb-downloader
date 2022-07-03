"""
parse
"""

import util


class Const:
    URL_EMBED_URL = r"https://www.fanbox.cc/@%s/posts/%s"


def _article(body: dict):
    texts = ""
    files = []

    if "blocks" in body.keys():
        blocks: list = body["blocks"]

        for block in blocks:
            if block["type"] == "p":
                text = block["text"]
                texts += f"{text}\n"
            elif block["type"] == "header":
                text = block["text"]
                texts += f"## {text}\n"
            else:
                _type = block["type"]
                if _type not in ["image", "file", "embed", "url_embed"]:
                    raise TypeError(f"block_type: {_type}")
                if _type == "url_embed":
                    _id = block["urlEmbedId"]
                else:
                    _id = block[f"{_type}Id"]
                texts += f"[type={_type}, id={_id}]\n"

    if "imageMap" in body.keys():
        if _map := body["imageMap"]:
            for key in _map.keys():
                img = _map[key]

                file_url = img["originalUrl"]
                file_name = util.get_filename(file_url)

                files.append((file_name, file_url))

    if "fileMap" in body.keys():
        if _map := body["fileMap"]:
            for key in _map.keys():
                file = _map[key]

                file_url = file["url"]
                file_name = "[%s] %s.%s" % (file["id"], file["name"], file["extension"])

                files.append((file_name, file_url))

    if "embedMap" in body.keys():
        if _map := body["embedMap"]:
            for key in _map.keys():
                embed = _map[key]

                embed_id = embed["id"]
                service_provider = embed["serviceProvider"]
                content_id = embed["contentId"]

                texts = texts.replace(
                    f"[type=embed, id={key}]",
                    f"[type=embed, id={embed_id}, " +
                    f"service_provider={service_provider}, " +
                    f"content_id={content_id}]"
                )

    if "urlEmbedMap" in body.keys():
        if _map := body["urlEmbedMap"]:
            for key in _map.keys():
                url_embed = _map[key]

                url_embed_type = url_embed["type"]
                if url_embed_type not in ["fanbox.post"]:
                    raise TypeError(f"url_embed type: {url_embed_type}")

                post_info = url_embed["postInfo"]

                info_id = post_info["id"]
                info_creator_id = post_info["creatorId"]
                url = Const.URL_EMBED_URL % (info_creator_id, info_id)

                info_title = post_info["title"]
                texts = texts.replace(
                    f"[type=url_embed, id={key}]",
                    f"[type=url_embed, title={info_title}, url={url}]"
                )

    return texts, files


def _image(body: dict):
    texts = body["text"]
    files = []
    for img in body["images"]:
        file_url = img["originalUrl"]
        file_name = util.get_filename(file_url)

        files.append((file_name, file_url))
    return texts, files


_parser = {
    "image": _image,
    "article": _article
}


def parse(type_name, body):
    if type_name not in _parser.keys():
        raise TypeError(f"body_type: {type_name}")
    return _parser[type_name](body)
