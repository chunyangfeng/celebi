"""模型层
Date: 2023/9/14 18:13

Author: Fengchunyang

Contact: fengchunyang

Record:
    2023/9/14 Create file.

"""
import datetime

from django.db import models

from app import params


class BasicModel(models.Model):
    """抽象基类"""
    is_delete = models.BooleanField(verbose_name='是否删除', default=False)
    desc = models.CharField(verbose_name="描述", max_length=255, blank=True, null=True)
    ctime = models.DateTimeField(verbose_name="创建时间", auto_now_add=datetime.datetime.now())
    mtime = models.DateTimeField(verbose_name="修改时间", auto_now=datetime.datetime.now())

    class Meta:
        abstract = True


class BasicModelManager(models.Manager):
    """通用模型管理器"""
    def get_queryset(self):
        """显式定义默认管理器行为，在models.objects的基础上，扩展额外的行为

        Returns:
            QuerySet: 结果集
        """
        return super().get_queryset()


class CommonDataModel(BasicModel):
    """通用数据类抽象model"""
    data_type = models.CharField(verbose_name="数据类型", max_length=16, default=params.DATA_TYPE_COMMON)
    creator = models.CharField(verbose_name="创建者", max_length=64, blank=True, null=True)
    last_operator = models.CharField(verbose_name="最后操作人", max_length=64, blank=True, null=True)
    last_operation = models.CharField(verbose_name="最后操作类型", max_length=64, blank=True, null=True)

    class Meta:
        abstract = True


class MigrationsHistory(BasicModel):
    app_name = models.CharField(verbose_name="app名称", max_length=255)
    file_name = models.CharField(verbose_name="文件名称", max_length=255)
    file_content = models.TextField(verbose_name="文件内容")

    class Meta:
        db_table = 'common_migrations_history'
        verbose_name = "迁移文件备份表"
