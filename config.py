"""
配置文件
"""


class Script:
    creator_id: str = r"shiratamaco"
    """作者 ID (作者主页的 URL 里那个)"""

    start_item_id: str = ""
    """从这个 ID 开始, ID 在链接末尾, 为空从最新开始"""

    end_item_id: str = ""
    """爬完这个 ID 就终止脚本, 为空则爬到最早"""

    """需要单爬一个的时候，只需要把 start_item_id 和 end_item_id 设置成一样的就行了"""


class Network:
    cookie: str = r""
    """Cookie, 其实只填 FANBOXSESSID 就行了, 如果希望保险一点可以填全部"""

    proxy: str or dict = ""
    """代理"""

    sleep_time: float = 1
    """防止 429: Too Many Requests 的间隔, 单位秒, 觉得太慢了改成 0 也行"""

    user_agent = (
        r"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        r"AppleWebKit/537.36 (KHTML, like Gecko) "
        r"Chrome/111.0.0.0 "
        r"Safari/537.36"
    )
    """UA"""


class File:
    default_dir: str = f"./{Script.creator_id}"
    """输出文件夹, 默认是和作者 ID 一致"""

    save_restricted_tip: bool = True
    """遇到受限制的, 把 ``月费高于 xxx 才能浏览`` 这个提示保存下来"""

    save_raw_json: bool = True
    """保存完整的原数据，方便 debug 或者排查是否有遗漏"""

    illegal_character: list = ["\\", "/", ":", "*", "?", "\"", "<", ">", "|"]
    """排除的文件名非法字符"""

    encoding: str = "utf-8"
    """文件编码"""


class Logger:
    logger_level: str = "info"
    """显示的日志等级"""


class ApiUrl:
    HOME_PAGE: str = "https://www.fanbox.cc/"
    PAGINATE_CREATOR: str = "https://api.fanbox.cc/post.paginateCreator"
    POST_INFO: str = "https://api.fanbox.cc/post.info"
