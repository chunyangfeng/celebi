"""序列化器
Date: 2023/9/14 18:13

Author: Fengchunyang

Contact: fengchunyang

Record:
    2023/9/14 Create file.

"""
from rest_framework import serializers


class SerializerDataCache:
    """序列化器数据缓存，用于缓存查询的数据"""
    _cache = dict()

    @property
    def cache(self):
        return self._cache

    @cache.setter
    def cache(self, data):
        self._cache = data


class DoNothingSerializer(serializers.ModelSerializer):
    """什么都不做的序列化器，用于部分不需要序列化数据的接口"""
    pass


class BasicCommonModelSerializer(serializers.ModelSerializer):
    """基础通用模型序列化器"""
    context = dict()  # 数据缓存字典

    @staticmethod
    def _pack_uniq_key(key, salt):
        """拼装唯一键值

        Args:
            key(str): 键值
            salt(str): 唯一混入值

        Returns:
            uniq_key(str): 唯一键值
        """
        return f"{key}-{salt}"

    def set_cache(self, key, obj, salt):
        """设置数据缓存，通常情况下，表字段的值应该都在当前表的模型内获取到结果，但是有些时候，为了解除表和表的强关联，
        会不使用外键，而只是使用关联表的唯一ID进行表关系的维护，这种情况下，如果在序列化器中需要使用到关联表的数据，
        需要使用SerializerMethod方法，通过关联表的唯一ID进行查询，再返回具体的内容，如果一个序列化器中有很多这种字段，那么每次返回
        数据的时候，都需要进行查询，而这些查询，实际上只需要有一次就行了，因此需要进行数据的缓存，遇到这种查询的时候，优先从
        缓存中查询结果，缓存命中失败的时候，才需要主动发起真实查询

        Args:
            key(str): 缓存的键值
            obj(any): 缓存的值，可以是任意对象
            salt(str|int): 缓存键值的混入值，用于区分相同种类的不同数据实体，通常情况下为数据的唯一ID

        Returns:
            None
        """
        # 缓存只会保存最新的值，不会进行更新
        uniq_key = self._pack_uniq_key(key, salt)
        self.context[uniq_key] = obj
        return

    def get_cache(self, key, salt):
        """获取缓存数据

        Args:
            key(str): 缓存键值
            salt(str|int): 缓存键值的混入值

        Returns:
            status(bool): 是否命中，True为命中，False为未命中
            cache(any): 缓存值，如果未命中则为None
        """
        uniq_key = self._pack_uniq_key(key, salt)
        value = self.context.get(uniq_key)
        if value is None:
            return False, None
        return True, value
