"""自定义数据库模型迁移逻辑

在多项目协同开发的情况下，生产环境部署项目时经常会出现数据库的migrate文件不一致，导致django的migrate执行失败问题。为了更好的使用migrate功能，
当前的模型迁移逻辑进行如下基本定义与设计：
1.生产环境中，每一次的部署所产生的migrate文件，全部存储进当前生产环境所连接的数据库中，这样可以保证，当前数据库的所有表结构和表设计，
与migrate文件保持一致
2.如果生产环境发生了变动，需要重新部署，可以通过拉取数据库中的所有migrate文件，来保证新生成的migrate文件可以和变动之前完美续接，
不会出现新生成的migrate文件执行一个已存在的表或者字段
3.鉴于以上的逻辑，建议每次执行makemigrations之前，先将数据库中的migrate文件load到本地环境中，然后再执行makemigrations，同时执行完migrate之后，
将新生成的migrate文件save到数据库中
4.上述逻辑已经在makemigrations和migrate命令中进行了自定义重载

Date: 2023/9/19 15:31

Author: Fengchunyang

Contact: fengchunyang

Record:
    2023/9/19 Create file.

"""
import json
import os

from django.conf import settings

from app.management.base import SingleArgBaseCommand
from app.models import MigrationsHistory
from app.utils.formatter import output_formatter


class Command(SingleArgBaseCommand):
    """自定义migrations文件管理命令"""

    help_info = """同步迁移文件，save为保存，load为加载，initial为初始化"""
    action_choice = ('save', 'load', 'initial')
    migrations_dir_name = "migrations"

    def get_app_migrations_dir(self):
        """获取当前项目下所有app的migrations目录

        Returns:
            app_migrations_dir(list): migrations目录列表
        """
        app_migrations_dir = dict()
        for app in settings.INSTALLED_APPS:
            app_path = os.sep.join(app.split("."))
            abs_app_path = os.path.join(settings.BASE_DIR, app_path)

            if os.path.exists(abs_app_path):
                absolute_dir = os.path.join(abs_app_path, self.migrations_dir_name)
                app_migrations_dir[app_path] = absolute_dir
        return app_migrations_dir

    @staticmethod
    def get_app_migrations_file(path):
        """获取指定路径的migrations文件

        Args:
            path(str): 目录名称

        Returns:
            app_migrations_file(list): migrations文件的绝对路径列表
        """
        app_migrations_file = []

        if os.path.exists(path):
            _, _, file_list = list(os.walk(path))[0]
            file_list.remove("__init__.py")
            for file in file_list:
                if file == "__init__.py" or file.split(".")[-1] == 'pyc':
                    continue
                app_migrations_file.append(os.path.join(path, file))
        return app_migrations_file

    def save(self):
        """保存当前项目中的migrations文件

        Returns:
            result(bool): None
        """
        app_migrations_dir = self.get_app_migrations_dir()

        for app, path in app_migrations_dir.items():
            file_list = self.get_app_migrations_file(path)
            for file in file_list:
                with open(file, "r", encoding='UTF-8') as f:
                    _, status = MigrationsHistory.objects.get_or_create(
                        app_name=app, file_name=file.split(".")[0],
                        defaults={"file_content": json.dumps(f.readlines())}
                    )
                    if status:
                        msg = f"app {app} 下的迁移文件 {file} 成功保存至数据库中！"
                    else:
                        msg = f"app {app} 下的迁移文件 {file} 已保存，本次对其操作将忽略！"
                    print(output_formatter(msg))

    def load(self):
        """从后端数据库加载当前项目的migrations文件

        Returns:
            result(bool): None
        """
        app_migrations_dir = self.get_app_migrations_dir()

        for app, path in app_migrations_dir.items():
            # 创建migrations文件夹
            if os.path.exists(path) is False:
                os.mkdir(path)

            # 创建migrations文件夹的包文件
            f_init = open(os.path.join(path, "__init__.py"), "w", encoding='UTF-8')
            f_init.close()

            for migrations in MigrationsHistory.objects.filter(app_name=app):
                with open(os.path.join(path, f"{migrations.file_name}.py"), "w", encoding='UTF-8') as file:
                    file.write('# coding:utf-8\n')  # 防止乱码
                    for line in json.loads(migrations.file_content):
                        file.write(line)
            print(output_formatter(f"app {app} 历史迁移文件加载完毕！"))

    def initial(self):
        """初始化migrate环境

        Returns:
            result(bool): None
        """
        print("initial")
