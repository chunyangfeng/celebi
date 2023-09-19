"""通用视图混入类
Date: 2023/9/19 16:29

Author: Fengchunyang

Contact: fengchunyang

Record:
    2023/9/19 Create file.

"""
import copy

from django.db import transaction
from django.http import HttpResponse
from rest_framework import status as drf_status
from rest_framework.response import Response
from rest_framework import mixins

from app import params, permissions


class BasicResponseMixin:
    """Http响应混合类"""
    extra_data = dict()
    _total_count = 0

    def set_extra(self, key, value):
        """设置响应数据的额外内容

        Args:
            key(str): key
            value(any): value
        """
        self.extra_data[key] = value

    @property
    def main_body(self):
        """消息主体结构

        Returns:
            dict: 响应数据结构
        """
        return {
            "result": "",
            "total": 0,
            "extra": dict(),
            "data": "",
        }

    def set_response(self, result='success', data=None, extra=None, status=drf_status.HTTP_200_OK):
        """设置响应数据

        Args:
            result(str): 结果
            data(str|list|dict): 数据主体
            extra(dict): 额外的数据主体
            status(str): 状态码

        Returns:
            response(Response): 响应数据
        """
        response = self.main_body
        response["result"] = result
        response["data"] = data if data is not None else dict()
        response["extra"] = extra if extra is not None else dict()
        response["total"] = len(data) if isinstance(data, list) else 0
        return Response(data=response, status=status)

    def set_json(self, data):
        """设置前端响应json数据

        Args:
            data(list): 数据主体

        Returns:
            response(dict): 符合规范的响应数据字典
        """
        return {
            "code": 0,  # 状态码，暂无特殊含义，默认为0
            "msg": "Success" if len(data) else "暂无数据",  # 响应消息
            "count": self._total_count,  # 数据总数
            "data": data,  # 响应数据
            "extra": self.extra_data,
        }


class BasicListModelMixin(mixins.ListModelMixin, BasicResponseMixin):
    """资源列表批量获取的混合类"""
    query_string_check = ()  # 待校验的查询字符串，如果设置了字段值，则会尝试在执行list流程前对这些字段进行必要性检查

    def paginate(self, request, *args, **kwargs):
        """分页

        Args:
            request(Request): DRF Request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            query_set(QuerySet): 结果集
        """
        page = request.query_params.get(params.PAGINATE_PAGE)
        limit = request.query_params.get(params.PAGINATE_LIMIT)
        paginate_disable = request.META.get(params.PAGINATE_DISABLE)

        # 统计原始数据集总量
        query_set = self.filter_queryset(self.get_queryset())
        total_count = len(query_set)
        self._total_count = total_count

        # 如果禁用了分页，则不进行分页操作直接返回所有数据
        if paginate_disable is not None:
            return query_set

        # 如果未指定完整的分页数据，则返回全集数据
        if not any([page, limit]):
            return query_set

        start = (int(page) - 1) * int(limit)
        end = int(page) * int(limit)

        # 如果进行查询时，前端指定了异常的分页数据，则重置分页起始值
        if start >= self._total_count:
            start, end = 0, int(limit)
        return query_set[start:end]

    def _pre_process_list(self, request, *args, **kwargs):
        """list请求预处理

        Args:
            request(Request): DRF Request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
        """
        for _query_string in self.query_string_check:
            value = request.query_params.get(_query_string)
            if value is None:
                return f'Query String {_query_string} is required', f'查询字符串 {_query_string} 为必传字段'
        return None, ''

    def _post_process_list(self, request, response, *args, **kwargs):
        """list请求后处理

        Args:
            request(Request): DRF Request
            response(HttpResponse): list函数的响应数据
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
            response(Response): 响应数据
        """
        return None, '', response

    def _perform_list(self, request, *args, **kwargs):
        """执行list请求

        Args:
            request(Request): DRF Request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            response(Response): 响应数据
        """
        # 分页处理
        query_set = self.paginate(request, *args, **kwargs)

        # 获取序列化器
        serializer = self.get_serializer_class()

        # 序列化queryset
        data = serializer(query_set, many=True).data

        # 构造json数据
        json_data = self.set_json(data)
        return Response(data=json_data, status=drf_status.HTTP_200_OK)

    @transaction.atomic()
    def list(self, request, *args, **kwargs):
        """list请求,设置事务，并在异常的时候进行回滚

        Args:
            request(Request): DRF Request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            response(Response): 响应数据
        """
        # list请求预处理
        error, reason = self._pre_process_list(request, *args, **kwargs)
        if error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}, {reason}")
            return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)

        # list请求
        try:
            response = self._perform_list(request, *args, **kwargs)
        except Exception as error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}")
            return self.set_response('Failed to get model list', f'获取资源数据列表失败,错误信息为{error}',
                                     status=drf_status.HTTP_400_BAD_REQUEST)

        # list请求后处理
        error, reason, response = self._post_process_list(request, response, *args, **kwargs)
        if error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}, {reason}")
            return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)
        return response


class BasicRetrieveModelMixin(mixins.RetrieveModelMixin, BasicResponseMixin):
    """单个资源处理流程"""

    def _pre_process_retrieve(self, request, *args, **kwargs):
        """retrieve查询预处理

        Args:
            request(Request): DRF Request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
        """
        return None, ''

    def _perform_retrieve(self, request, instance, *args, **kwargs):
        """retrieve查询

        Args:
            request(Request): DRF Request
            instance(models.Model): model instance
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
            response(Response): 响应数据
        """
        serializer = self.get_serializer_class()
        data = serializer(instance, many=False).data
        response = self.set_response(result='Success', data=data, status=drf_status.HTTP_200_OK)
        return None, '', response

    def _post_process_retrieve(self, request, instance, *args, **kwargs):
        """retrieve查询后处理

        Args:
            request(Request): DRF Request
            instance(object): 实例
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
        """
        return None, ''

    @transaction.atomic()
    def retrieve(self, request, *args, **kwargs):
        """执行retrieve操作

        Args:
            request(Request): DRF Request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            response(Response): 对请求的响应
        """
        # 查询预处理
        error, reason = self._pre_process_retrieve(request, *args, **kwargs)
        if error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}, {reason}")
            return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)

        # 获取model instance
        instance = self.get_object(*args, **kwargs)

        # 查询
        error, reason, response = self._perform_retrieve(request, instance, *args, **kwargs)
        if error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}, {reason}")
            return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)

        # 查询后处理
        error, reason = self._post_process_retrieve(request, instance, *args, **kwargs)
        if error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}, {reason}")
            return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)

        return response


class BasicBulkCreateModelMixin(mixins.CreateModelMixin, BasicResponseMixin):
    """资源批量创建的混合类"""
    data_field_check = ()  # post请求体字段校验列表

    def _pre_process_create(self, request, *args, **kwargs):
        """创建请求预处理

        Args:
            request(Request): DRF Request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
        """
        for field in self.data_field_check:
            value = request.data.get(field)
            if value is None:
                return f'field {field} is required', f'字段 {field} 为必填字段'
        return None, ''

    def _pre_validate_create(self, request, *args, **kwargs):
        """创建请求预校验

        Args:
            request(Request): DRF Request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
        """
        return None, ''

    def _perform_create(self, request, serializer, *args, **kwargs):
        """执行create处理流程

        Args:
            request(Request): DRF Request
            serializer(serializer): DRF serializer
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            inst(object): 创建完成的资源实例
        """
        inst = serializer.save()
        return inst

    def _post_process_create(self, request, instance, *args, **kwargs):
        """执行create后的处理流程

        Args:
            request(Request): DRF Request
            instance(Object): 保存数据后的实例对象
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
        """
        try:
            data_type = getattr(instance, params.DATA_TYPE_FIELD)
        except AttributeError:
            return None, ''

        # 如果资源为通用数据类型，则添加默认属性
        if data_type == params.DATA_TYPE_COMMON:
            instance.creator = request.user.username
            instance.last_operator = request.user.username
            instance.last_operation = params.DATA_OPERATION_ADD
            instance.save()
        return None, ''

    @transaction.atomic()
    def create(self, request, *args, **kwargs):
        """资源创建，设置事务，出现错误时进行回滚

        Args:
            request(Request): DRF Request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            response(Response): 响应数据
        """
        # 请求消息预处理
        error, reason = self._pre_process_create(request, *args, **kwargs)
        if error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}, {reason}")
            return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)

        # 创建请求预校验
        error, reason = self._pre_validate_create(request, *args, **kwargs)
        if error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}, {reason}")
            return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)

        # 获取serializer
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            transaction.set_rollback(True)
            logger.error(f"序列化器校验失败:{serializer.errors}")
            return self.set_response('serializer is invalid', f'序列化器校验失败:{serializer.errors}',
                                     status=drf_status.HTTP_400_BAD_REQUEST)

        # 执行创建
        try:
            instances = self._perform_create(request, serializer, *args, **kwargs)
        except Exception as error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}")
            return self.set_response('Failed to create models', f'执行创建失败,错误信息为:{error}',
                                     status=drf_status.HTTP_400_BAD_REQUEST)

        # 创建后处理
        error, reason = self._post_process_create(request, instances, *args, **kwargs)
        if error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}, {reason}")
            return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)
        return self.set_response(params.HTTP_SUCCESS, "创建成功", status=drf_status.HTTP_201_CREATED)


class BasicCreateModelMixin(mixins.CreateModelMixin, BasicResponseMixin):
    """单个资源创建的混合类"""

    def _pre_process_create(self, request, *args, **kwargs):
        """创建请求预处理

        Args:
            request(Request): DRF Request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
        """
        return None, ''

    def _pre_validate_create(self, request, *args, **kwargs):
        """创建请求预校验

        Args:
            request(Request): DRF Request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
        """
        return None, ''

    def _perform_create(self, request, serializer, *args, **kwargs):
        """执行create处理流程

        Args:
            request(Request): DRF Request
            serializer(serializer): DRF serializer
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            inst(object): 创建完成的资源实例
        """
        inst = serializer.save()
        return inst

    def _post_process_create(self, request, instances, *args, **kwargs):
        """执行create后的处理流程

        Args:
            request(Request): DRF Request
            instances (list): 保存数据后的实例列表
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
        """
        return None, ''

    @transaction.atomic()
    def create(self, request, *args, **kwargs):
        """资源创建，设置事务，出现错误时进行回滚

        Args:
            request(Request): DRF Request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            response(Response): 响应数据
        """
        # 请求消息预处理
        error, reason = self._pre_process_create(request, *args, **kwargs)
        if error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}, {reason}")
            return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)

        # 创建请求预校验
        error, reason = self._pre_validate_create(request, *args, **kwargs)
        if error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}, {reason}")
            return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)

        # 获取serializer
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            transaction.set_rollback(True)
            logger.error(f"序列化器校验失败:{serializer.errors}")
            return self.set_response('serializer is invalid', f'序列化器校验失败:{serializer.errors}',
                                     status=drf_status.HTTP_400_BAD_REQUEST)

        # 执行创建
        try:
            instances = self._perform_create(request, serializer, *args, **kwargs)
        except Exception as error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}")
            return self.set_response('Failed to create models', f'执行创建失败,错误信息为:{error}',
                                     status=drf_status.HTTP_400_BAD_REQUEST)

        # 创建后处理
        error, reason = self._post_process_create(request, instances, *args, **kwargs)
        if error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}, {reason}")
            return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)
        return self.set_response(params.HTTP_SUCCESS, "创建成功", status=drf_status.HTTP_201_CREATED)


class BasicBulkUpdateModelMixin(mixins.UpdateModelMixin, BasicResponseMixin):
    """批量更新model混合类"""

    def _pre_process_update(self, request, *args, **kwargs):
        """更新预处理

        Args:
            request(Request): DRF Request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
        """
        return None, ''

    def _validate_update(self, request, *args, **kwargs):
        """更新预校验

        Args:
            request(Request): DRF Request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
        """
        return None, ''

    def _perform_update(self, request, *args, **kwargs):
        """执行更新操作

        Args:
            request (Request): request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
            instances(QuerySet): 数据集
        """
        # 获取更新数据
        data = copy.deepcopy(request.data)

        # 获取待更新的实例
        instances_id = data.pop('instances_id')
        data = data.dict()

        queryset = self.get_queryset(*args, **kwargs)
        queryset = queryset.filter(id__in=instances_id)

        # 执行更新
        queryset.update(**data)
        return None, '', queryset

    def _post_process_update(self, request, instances, *args, **kwargs):
        """更新完成后处理流程

        Args:
            request(Request): DRF Request
            instances(QuerySet): 数据集
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
        """
        return None, ''

    @transaction.atomic()
    def update(self, request, *args, **kwargs):
        """更新操作，设置事务，出现错误时进行数据回滚

        Args:
            request(Request): DRF Request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            response(Response): 响应数据
        """
        # 更新前预处理
        error, reason = self._pre_process_update(request, *args, **kwargs)
        if error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}, {reason}")
            return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)

        # 更新前预校验
        error, reason = self._validate_update(request, *args, **kwargs)
        if error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}, {reason}")
            return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)

        # 执行更新操作
        try:
            error, reason, instances = self._perform_update(request, *args, **kwargs)
        except Exception as error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}")
            return self.set_response('Update failed', f'更新失败，错误信息为:{error}',
                                     status=drf_status.HTTP_400_BAD_REQUEST)
        if error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}, {reason}")
            return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)

        # 更新后预处理
        error, reason = self._post_process_update(request, instances, *args, **kwargs)
        if error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}, {reason}")
            return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)

        return self.set_response(params.HTTP_SUCCESS, '批量更新成功')


class BasicUpdateModelMixin(mixins.UpdateModelMixin, BasicResponseMixin):
    """更新model混合类"""

    def _pre_process_update(self, request, *args, **kwargs):
        """更新预处理

        Args:
            request(Request): DRF Request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
        """
        return None, ''

    def _validate_update(self, request, *args, **kwargs):
        """更新预校验

        Args:
            request(Request): DRF Request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
        """
        return None, ''

    def _perform_update(self, serializer, *args, **kwargs):
        """执行更新操作

        Args:
            serializer (serializer.Serializer): 序列化器
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
        """
        serializer.save()
        return None, ''

    def _perform_partial_update(self, request, instance, *args, **kwargs):
        """执行部分更新

        Args:
            request(Request): DRF Request
            instance(models.Model): model instance
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
        """
        # 执行部分更新
        try:
            for key, value in request.data.items():
                setattr(instance, key, value)
            instance.save()
        except Exception as error:
            logger.error(f"部分更新失败: {instance.__dict__}")
            return error, '部分更新失败'
        return None, ''

    def _post_process_update(self, request, instance, *args, **kwargs):
        """更新完成后处理流程

        Args:
            request(Request): DRF Request
            instance (models.Models): 数据实例
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
        """
        try:
            data_type = getattr(instance, params.DATA_TYPE_FIELD)
        except AttributeError:
            return None, ''

        # 更新操作后设置默认数据
        if data_type == params.DATA_TYPE_COMMON:
            instance.last_operator = request.user.username
            instance.last_operation = params.DATA_OPERATION_MODIFY
            instance.save()
        return None, ''

    @transaction.atomic()
    def update(self, request, *args, **kwargs):
        """更新操作，设置事务，出现错误时进行数据回滚

        Args:
            request(Request): DRF Request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            response(Response): 响应数据
        """
        # 更新前预处理
        error, reason = self._pre_process_update(request, *args, **kwargs)
        if error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}, {reason}")
            return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)

        # 更新前预校验
        error, reason = self._validate_update(request, *args, **kwargs)
        if error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}, {reason}")
            return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)

        # 获取model instance
        instance = self.get_object(*args, **kwargs)

        # 如果希望调用部分更新的接口逻辑，需要在请求中添加partial字段作为query string
        is_partial_update = request.query_params.get('partial')
        if is_partial_update is not None:
            # 执行部分更新
            error, reason = self._perform_partial_update(request, instance, *args, **kwargs)
            if error:
                transaction.set_rollback(True)
                logger.error(f"请求异常：{error}, {reason}")
                return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)
        else:
            # 获取序列化器
            serializer = self.get_serializer(instance, data=request.data)
            if not serializer.is_valid():
                transaction.set_rollback(True)
                logger.error(f"序列化器校验失败，错误信息为:{serializer.errors}")
                return self.set_response('Serializer validate failed', f'序列化器校验失败，错误信息为:{serializer.errors}',
                                         status=drf_status.HTTP_400_BAD_REQUEST)

            # 执行全量更新操作
            try:
                error, reason = self._perform_update(serializer, *args, **kwargs)
            except Exception as error:
                transaction.set_rollback(True)
                logger.error(f"请求异常：{error}")
                return self.set_response('Update failed', f'更新失败，错误信息为:{error}',
                                         status=drf_status.HTTP_400_BAD_REQUEST)
            if error:
                transaction.set_rollback(True)
                logger.error(f"请求异常：{error}, {reason}")
                return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)

        # 更新后预处理
        error, reason = self._post_process_update(request, instance, *args, **kwargs)
        if error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}, {reason}")
            return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)

        return self.set_response(params.HTTP_SUCCESS, '更新成功')


class BasicBulkDestroyModelMixin(mixins.DestroyModelMixin, BasicResponseMixin):
    """批量删除model"""

    def _pre_process_delete(self, request, *args, **kwargs):
        """删除预处理

        Args:
            request(Request): DRF Request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
        """
        return None, ''

    def _validate_delete(self, request, *args, **kwargs):
        """删除预校验

        Args:
            request(Request): DRF Request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
        """
        return None, ''

    def _perform_delete(self, instances, *args, **kwargs):
        """执行删除

        Args:
            instances(QuerySet): 数据实例集
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
            instances(object): 已逻辑删除的实例(物理删除的实例则为None)
        """
        # 逻辑删除
        logic_delete = kwargs.get('logic_delete', False)
        if logic_delete:
            instances.update(is_delete=True)
            return None, '', instances

        # 物理删除
        instances.delete()
        return None, '', None

    def _post_process_delete(self, request, instances=None, *args, **kwargs):
        """删除后处理

        Args:
            request(Request): DRF Request
            instances(object): 已逻辑删除的实例(物理删除的实例无需传递)
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
        """
        return None, ''

    def get_delete_instances(self, request, *args, **kwargs):
        """获取待删除的实例集

        Args:
            request(Request): http request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            instances(QuerySet): 实例集
        """
        delete_data = request.data.get('deleted', '')
        query_set = self.get_queryset(*args, **kwargs)
        instances = query_set.filter(id__in=delete_data.split(params.SPLIT_COMMA))
        return instances

    @transaction.atomic()
    def destroy(self, request, *args, **kwargs):
        """删除主流程

        Args:
            request(Request): DRF Request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            response(Response): 对请求的响应
        """
        # 删除预处理
        error, reason = self._pre_process_delete(request, *args, **kwargs)
        if error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}, {reason}")
            return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)

        # 删除预校验
        error, reason = self._validate_delete(request, *args, **kwargs)
        if error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}, {reason}")
            return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)

        # 获取待删除的实例集
        insts = self.get_delete_instances(request, *args, **kwargs)

        # 执行删除
        try:
            error, reason, instances = self._perform_delete(insts, *args, **kwargs)
        except Exception as error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}")
            return self.set_response('Delete failed', f'删除失败，错误信息为:{error}',
                                     status=drf_status.HTTP_400_BAD_REQUEST)
        if error:
            logger.error(f"请求异常：{error}, {reason}")
            return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)

        # 删除后处理
        error, reason = self._post_process_delete(request, instances, *args, **kwargs)
        if error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}, {reason}")
            return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)

        return self.set_response(params.HTTP_SUCCESS, '删除成功', status=drf_status.HTTP_200_OK)


class BasicDestroyModelMixin(mixins.DestroyModelMixin, BasicResponseMixin):
    """删除model"""

    def _pre_process_delete(self, request, *args, **kwargs):
        """删除预处理

        Args:
            request(Request): DRF Request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
        """
        return None, ''

    def _validate_delete(self, request, *args, **kwargs):
        """删除预校验

        Args:
            request(Request): DRF Request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
        """
        return None, ''

    def _perform_delete(self, instance, *args, **kwargs):
        """执行删除,默认情况下都是物理删除，如果需要执行逻辑删除，则需要在API地址后面加上查询字符串logic_delete即可实现逻辑删除功能

        Args:
            instance(models.Model): 数据实例
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
            instances(object): 已逻辑删除的实例(物理删除的实例则为None)
        """
        # 执行逻辑删除
        logic_delete = self.request.query_params.get('logic_delete', False)
        if logic_delete:
            instance.is_delete = True
            instance.save()
            return None, '', instance

        # 执行物理删除
        instance.delete()
        return None, '', None

    def _post_process_delete(self, request, instance, *args, **kwargs):
        """删除后处理，如果为逻辑删除，则记录逻辑删除操作相关的操作审计信息

        Args:
            request(Request): DRF Request
            instances(object): 已逻辑删除的实例(物理删除的实例为None)
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
        """
        try:
            data_type = getattr(instance, params.DATA_TYPE_FIELD)
        except AttributeError:
            return None, ''

        # 逻辑删除操作后设置默认数据
        logic_delete = request.query_params.get('logic_delete', False)
        if data_type == params.DATA_TYPE_COMMON and logic_delete:
            instance.last_operator = request.user.username
            instance.last_operation = params.DATA_OPERATION_DELETE
            instance.save()
        return None, ''

    @transaction.atomic()
    def destroy(self, request, *args, **kwargs):
        """删除主流程

        Args:
            request(Request): DRF Request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            response(Response): 对请求的响应
        """
        # 删除预处理
        error, reason = self._pre_process_delete(request, *args, **kwargs)
        if error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}, {reason}")
            return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)

        # 删除预校验
        error, reason = self._validate_delete(request, *args, **kwargs)
        if error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}, {reason}")
            return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)

        # 获取数据对象
        inst = self.get_object(*args, **kwargs)

        # 执行删除
        try:
            error, reason, instance = self._perform_delete(inst, *args, **kwargs)
        except Exception as error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}")
            return self.set_response('Delete failed', f'删除失败，错误信息为:{error}',
                                     status=drf_status.HTTP_400_BAD_REQUEST)
        if error:
            logger.error(f"请求异常：{error}, {reason}")
            return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)

        # 删除后处理
        error, reason = self._post_process_delete(request, instance, *args, **kwargs)
        if error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}, {reason}")
            return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)

        return self.set_response(params.HTTP_SUCCESS, '删除成功', status=drf_status.HTTP_200_OK)


class BasicBulkPatchModelMixin(BasicResponseMixin):
    """批量处理patch请求的混合类"""

    def _pre_process_patch(self, request, *args, **kwargs):
        """patch请求预处理

        Args:
            request(Request): DRF Request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
        """
        return None, ''

    def _validate_patch(self, request, *args, **kwargs):
        """patch请求校验

        Args:
            request(Request): DRF Request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
        """
        return None, ''

    def _perform_patch(self, request, instances, *args, **kwargs):
        """执行patch请求

        Args:
            request(Request): DRF Request
            instances(QuerySet): query set
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
            response(Response): 请求响应数据
        """
        # 执行部分更新
        instances.update(**request.data)

        response = self.set_response(params.HTTP_SUCCESS, data="批量部分更新成功")
        return None, '', response

    def _post_process_patch(self, request, instances, *args, **kwargs):
        """patch请求后处理

        Args:
            request(Request): DRF Request
            instances(QuerySet): QuerySet
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
        """
        return None, ''

    @transaction.atomic()
    def extra(self, request, *args, **kwargs):
        """

        Args:
            request(Request): DRF Request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
        """
        # patch请求预处理
        error, reason = self._pre_process_patch(request, *args, **kwargs)
        if error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}, {reason}")
            return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)

        # patch请求预校验
        error, reason = self._validate_patch(request, *args, **kwargs)
        if error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}, {reason}")
            return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)

        # 获取数据对象
        instances = self.get_queryset()

        # patch请求执行
        try:
            error, reason, response = self._perform_patch(request, instances, *args, **kwargs)
            if error:
                transaction.set_rollback(True)
                logger.error(f"请求异常：{error}, {reason}")
                return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}")
            return self.set_response('Failed to patch', f'patch请求处理失败,错误原因:{error}')

        # patch请求后处理
        error, reason = self._post_process_patch(request, instances, *args, **kwargs)
        if error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}, {reason}")
            return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)

        return response


class BasicPatchModelMixin(BasicResponseMixin):
    """patch请求的混合类"""

    def _pre_process_patch(self, request, *args, **kwargs):
        """patch请求预处理

        Args:
            request(Request): DRF Request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
        """
        return None, ''

    def _validate_patch(self, request, *args, **kwargs):
        """patch请求校验

        Args:
            request(Request): DRF Request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
        """
        return None, ''

    def _perform_patch(self, request, instance, *args, **kwargs):
        """执行patch请求的部分更新

        Args:
            request(Request): DRF Request
            instance(models.Model): model instance
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
            response(Response): 请求响应数据
        """
        # 执行部分更新
        for key, value in request.data.items():
            setattr(instance, key, value)

        instance.save()

        response = self.set_response(result=params.HTTP_SUCCESS, data="部分更新成功")
        return None, '', response

    def _post_process_patch(self, request, instance, *args, **kwargs):
        """patch请求后处理

        Args:
            request(Request): DRF Request
            instance(model.Model): ORM 实例
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
        """
        try:
            data_type = getattr(instance, params.DATA_TYPE_FIELD)
        except AttributeError:
            return None, ''

        # 更新操作后设置默认数据
        if data_type == params.DATA_TYPE_COMMON:
            instance.last_operator = request.user.username
            instance.last_operation = params.DATA_OPERATION_MODIFY
            instance.save()
        return None, ''

    @transaction.atomic()
    def extra(self, request, *args, **kwargs):
        """

        Args:
            request(Request): DRF Request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            error(str): 错误信息，没有错误为None
            reason(str): 错误原因，没有错误为''
        """
        # patch请求预处理
        error, reason = self._pre_process_patch(request, *args, **kwargs)
        if error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}, {reason}")
            return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)

        # patch请求预校验
        error, reason = self._validate_patch(request, *args, **kwargs)
        if error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}, {reason}")
            return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)
        # 获取数据对象
        instance = self.get_object(*args, **kwargs)

        # patch请求执行
        try:
            error, reason, response = self._perform_patch(request, instance, *args, **kwargs)
            if error:
                transaction.set_rollback(True)
                logger.error(f"请求异常：{error}, {reason}")
                return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            transaction.set_rollback(True)
            logger.error(f"请求异常：{error}")
            return self.set_response('Failed to patch', f'patch请求处理失败,错误原因:{error}')

        # patch请求后处理
        error, reason = self._post_process_patch(request, instance, *args, **kwargs)
        if error:
            transaction.set_rollback(True)
            return self.set_response(error, reason, status=drf_status.HTTP_400_BAD_REQUEST)

        return response


class BasicAuthPermissionViewMixin(BasicResponseMixin):
    """授权认证/权限校验混合类"""
    permission_name = permissions.PER_BASE  # 权限名称
    authentication_enable = True  # 是否启用认证检查
    permission_enable = True  # 是否启用权限检查
    http_method_names = ('get', 'post', 'put', 'delete', 'patch')

    def dispatch(self, request, *args, **kwargs):
        """路由分发

        Args:
            request(Request): http request
            *args(list): 可变参数
            **kwargs(dict): 可变关键字参数

        Returns:
            response(Response): 响应数据
        """
        # 自定义认证校验
        is_auth, user = self.check_authentication(request, *args, **kwargs)
        setattr(request, 'user', user)

        if is_auth is False:
            return HttpResponse("Unauthorized", status=drf_status.HTTP_401_UNAUTHORIZED)

        # 自定义权限校验
        has_perm = self.check_permission(request, *args, **kwargs)
        if has_perm is False:
            return HttpResponse("No permission", status=drf_status.HTTP_403_FORBIDDEN)

        response = super().dispatch(request, *args, **kwargs)
        return response

    def check_authentication(self, request, *args, **kwargs):
        """认证检查

        Args:
            request(Request): request
            *args(list): args
            **kwargs(dict): kwargs

        Returns:
            is_auth(bool): 是否认证
            user(model.Models): 用户实例
        """
        if self.authentication_enable is False:
            return True, None

        # TODO 认证检查需要由子系统自行定义，此处的逻辑后续补充
        user = object()
        return True, user

    def check_permission(self, request, *args, **kwargs):
        """权限检查

        Args:
            request(Request): request
            *args(list): args
            **kwargs(dict): kwargs

        Returns:
            has_perm(bool): 是否拥有权限
        """
        has_perm = True

        # 如果启用的是根权限，则默认所有用户都拥有此权限
        if self.permission_name == permissions.PER_BASE:
            return has_perm

        if self.permission_enable:
            # TODO 权限检查需要由子系统自行定义，此处的逻辑后续补充
            pass
        return has_perm


class BasicCommonViewMixin:
    """视图集的通用混合类，提供通用的处理方法"""
    data_type = params.DATA_TYPE_COMMON  # 数据类型

    @staticmethod
    def _clear_query_params(value):
        """清洗查询参数中的异常字符
            1.undefined/null: None
            2.左右两侧空格: ''
            3.'true'/'false': True/False

        Args:
            value(any): 待处理查询参数

        Returns:
            value(any): 清洗完毕后的查询参数
        """
        # 有些时候，某些查询字段可能不是单纯的字符串，如果清洗时有非字符串类型的查询参数，则认为其合法并直接返回
        if isinstance(value, str) is False:
            return value

        value = value.rstrip(' ')
        value = value.lstrip(' ')

        if value in ('undefined', 'null'):
            value = params.QUERY_STRING_ILLEGAL_VALUE

        if value == 'true':
            value = True

        if value == 'false':
            value = False

        if value == 'None':
            value = None

        return value

    def initial_query_params(self):
        """初始化查询参数"""
        self.request.query_params._mutable = True  # 将QueryDict修改为可变

        _pop_key = list()

        for key, value in self.request.query_params.items():
            # 清洗value
            value = self._clear_query_params(value)

            if isinstance(value, bool):
                continue

            if value == params.QUERY_STRING_ILLEGAL_VALUE:
                _pop_key.append(key)

            if value == '':
                _pop_key.append(key)

        # 如果value没有传值，则从查询参数中删除
        for pop_key in _pop_key:
            self.request.query_params.pop(pop_key)

        self.request.query_params._mutable = False
        return
