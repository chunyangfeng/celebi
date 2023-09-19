"""视图层
Date: 2023/9/14 18:13

Author: Fengchunyang

Contact: fengchunyang

Record:
    2023/9/14 Create file.

"""
from django.db.models import QuerySet

from app.exceptions.http import ModelPrimaryKeyError
from app.mixin import views as views_mixin
from rest_framework.generics import GenericAPIView

from app import params
from app.serializers import DoNothingSerializer


class BasicListViewSet(views_mixin.BasicAuthPermissionViewMixin,
                       GenericAPIView,
                       views_mixin.BasicCommonViewMixin,
                       views_mixin.BasicBulkCreateModelMixin,
                       views_mixin.BasicListModelMixin,
                       views_mixin.BasicBulkUpdateModelMixin,
                       views_mixin.BasicBulkDestroyModelMixin,
                       views_mixin.BasicBulkPatchModelMixin):
    """
    批量进行资源的CRUD操作，支持以下操作：
    1.资源的批量创建
    2.资源的批量查询
    3.资源的批量更新
    4.资源的批量删除
    5.资源的批量处理（通过patch方法进行额外的逻辑控制，比如字段查重等）
    """

    def filter_queryset(self, queryset):
        """过滤QuerySet

        Args:
            queryset(QuerySet): QuerySet

        Returns:
            QuerySet: 过滤后的QuerySet
        """
        self.initial_query_params()

        _query_params = dict()

        # 处理查询条件
        for key, value in self.request.query_params.items():
            if key not in (params. PAGINATE_PAGE, params.PAGINATE_LIMIT):
                value = self._clear_query_params(value)
                _query_params[key] = value
        queryset = queryset.filter(**_query_params)

        return queryset

    def get(self, request, *args, **kwargs):
        """批量获取资源数据

        Args:
            request(Request): http request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            response(Response): 响应数据
        """
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """批量创建资源数据

        Args:
            request(Request): http request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            response(Response): 响应数据
        """
        return self.create(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """批量删除资源数据

        Args:
            request(Request): http request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            response(Response): 响应数据
        """
        return self.destroy(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        """批量获取资源数据

        Args:
            request(Request): http request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            response(Response): 响应数据
        """
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        """额外的逻辑控制

        Args:
            request(Request): http request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            response(Response): 响应数据
        """
        return self.extra(request, *args, **kwargs)


class BasicInfoViewSet(views_mixin.BasicAuthPermissionViewMixin,
                       GenericAPIView,
                       views_mixin.BasicCommonViewMixin,
                       views_mixin.BasicCreateModelMixin,
                       views_mixin.BasicRetrieveModelMixin,
                       views_mixin.BasicUpdateModelMixin,
                       views_mixin.BasicDestroyModelMixin,
                       views_mixin.BasicPatchModelMixin):
    """
    单个资源的CRUD操作，支持以下操作：
    1.资源创建
    2.资源查询
    3.资源更新
    4.资源删除
    5.资源处理（通过patch方法进行额外的逻辑控制，比如字段查重、局部更新等）
    """

    def get_object(self, *args, **kwargs):
        """获取models.Model对象

        Args:
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            instance(models.Model): 单个model实例对象
        """
        pk = kwargs.get(params.DEFAULT_PK)

        if not pk:
            raise ModelPrimaryKeyError('There is no primary key settled')

        instance = self.get_queryset().get(**{params.DEFAULT_PK: pk})
        return instance

    def get(self, request, *args, **kwargs):
        """获取资源数据

        Args:
            request(Request): http request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            response(Response): 响应数据
        """
        return self.retrieve(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """创建资源数据

        Args:
            request(Request): http request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            response(Response): 响应数据
        """
        return self.create(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """删除资源数据

        Args:
            request(Request): http request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            response(Response): 响应数据
        """
        return self.destroy(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        """获取资源数据

        Args:
            request(Request): http request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            response(Response): 响应数据
        """
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        """额外的逻辑控制

        Args:
            request(Request): http request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            response(Response): 响应数据
        """
        return self.extra(request, *args, **kwargs)


class BasicChoiceListViewSet(BasicListViewSet):
    """处理models模型中的choice字段数据"""
    queryset = QuerySet()
    serializer_class = DoNothingSerializer
    http_method_names = ('get', )
    choice = ()

    def get(self, request, *args, **kwargs):
        data = list()
        for _index, _choice in enumerate(self.choice):
            value, label = _choice
            data.append({
                "id": _index,
                "label": label,
                "value": value
            })
        return self.set_response(result='success', data=data)


class BasicCustomizeViewSet(BasicListViewSet):
    """自定义视图集，主要用于不需要使用序列化器和模型数据的第三方数据接口"""
    queryset = QuerySet()
    serializer_class = DoNothingSerializer
    http_method_names = ('get', 'post', 'put', 'delete', 'patch')