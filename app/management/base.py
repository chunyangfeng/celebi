"""
Date: 2023/9/19 15:32

Author: Fengchunyang

Contact: fengchunyang

Record:
    2023/9/19 Create file.

"""
from django.core.management.base import BaseCommand

from app.utils.formatter import output_formatter


class SingleArgBaseCommand(BaseCommand):
    """单参数命令基类"""

    help_info = """Help Info"""
    action = "action"  # 参数名称
    action_choice = tuple()

    def __new__(cls):
        """实现类创建时的方法校验
        Returns:
            cls(object): 类
        """
        error_list = []
        for choice in cls.action_choice:
            try:
                getattr(cls, choice)
            except AttributeError:
                error_list.append(choice)

        if len(error_list) > 0:
            error = output_formatter(
                f"Command action {error_list} undefined, please contact your administrator!", "red"
            )
            raise AttributeError(error)
        return BaseCommand.__new__(cls)

    def add_arguments(self, parser):
        """参数管理
        Args:
            parser(parser.Parser): 参数管理器
        """
        parser.add_argument(
            dest=self.action,
            type=str,
            help=self.help_info,
            choices=self.action_choice,
        )

    def handle(self, *args, **options):
        """命令处理
        Args:
            *args(list): 可变参数
            **options: 可变关键字参数
        """
        action = options.get(self.action)
        run_func = getattr(self, action)
        run_func()
