"""
Date: 2023/9/19 15:33

Author: Fengchunyang

Contact: fengchunyang

Record:
    2023/9/19 Create file.

"""
import datetime

from app.params import DATETIME_STANDARD


def strftime(obj, formatter=DATETIME_STANDARD):
    """转化datetime.datetime对象为标准时间字符串

    Args:
        obj(datetime.datetime): 时间日期对象
        formatter(str): 标准时间字符串格式化类型

    Returns:
        result(str): 标准时间字符串
    """
    return datetime.datetime.strftime(obj, formatter) if obj else obj


def strptime(time, formatter=DATETIME_STANDARD):
    """转化datetime.datetime对象为标准时间字符串

    Args:
        time(str): 标准时间字符串
        formatter(str): 标准时间字符串格式化类型

    Returns:
        result(datetime.datetime): 时间日期对象
    """
    return datetime.datetime.strptime(time, formatter) if time else time


def output_formatter(message, color="green", bgcolor="black", display="高亮"):
    """将指定字符串格式化为对应颜色文本输出

    Args:
        message(str): 文本消息
        color(str): 字体颜色，默认为绿色
        bgcolor(str): 背景颜色，默认为黑色
        display(str): 显示方式，默认高亮

    Returns:
        message(str): 格式化后的message
    """
    colors = {
        "black": 30,
        "red": 31,
        "green": 32,
        "yellow": 33,
        "blue": 34,
        "pink": 35,
        "cyan": 36,
        "white": 37,
    }
    bgcolors = {
        "black": 40,
        "red": 41,
        "green": 42,
        "yellow": 43,
        "blue": 44,
        "pink": 45,
        "cyan": 46,
        "white": 47,
    }
    displays = {
        "终端默认": 0,
        "高亮": 1,
        "非高亮": 22,
        "下划线": 4,
        "去下划线": 24,
        "闪烁": 5,
        "去闪烁": 25,
        "反白": 7,
        "非反白": 27,
        "不可见": 8,
        "可见": 28,
    }
    formatter = "\033[{0};{1};{2}m{3}\033[0m"
    return formatter.format(
        displays.get(display, "终端默认"),
        colors.get(color, "green"),
        bgcolors.get(bgcolor, "black"),
        message
    )


def get_week(date=None):
    """获取指定日期所在周的周一至周日的日期

    Args:
        date(str|None): 指定日期，如果不传，则默认使用当前日期

    Returns:
        week(list): 指定日期所在周的周一至周日的日期列表
    """
    week = list()
    date = datetime.date.today() if date is None else datetime.datetime.strptime(date, "%Y-%m-%d").date()
    sunday = date + datetime.timedelta(days=7 - date.isoweekday())
    for i in range(7):
        tmp = sunday - datetime.timedelta(days=i)
        week.insert(0, tmp.strftime("%Y-%m-%d"))
    return week
