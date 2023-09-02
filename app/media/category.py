import os
import shutil

import ruamel.yaml

import log
from app.utils import ExceptionUtils
from config import Config
from app.utils.commons import singleton


@singleton
class Category:
    _category_path = None
    _categorys = None
    _tv_categorys = None
    _movie_categorys = None
    _anime_categorys = None

    def __init__(self):
        self.init_config()

    def init_config(self):
        self._category_path = Config().category_path
        if not self._category_path:
            return
        category_name, _ = os.path.splitext(os.path.basename(self._category_path))
        if category_name == "config":
            log.warn(f"【Config】二级分类策略 {category_name} 名称非法")
            return
        try:
            if not os.path.exists(self._category_path):
                shutil.copy(os.path.join(Config().get_inner_config_path(), "default-category.yaml"),
                            self._category_path)
                log.warn(f"【Config】二级分类策略 {category_name} 配置文件不存在，已按模板生成...")
            with open(self._category_path, mode='r', encoding='utf-8') as f:
                try:
                    yaml = ruamel.yaml.YAML()
                    self._categorys = yaml.load(f)
                except Exception as e:
                    ExceptionUtils.exception_traceback(e)
                    log.warn(f"【Config】二级分类策略 {category_name} 配置文件格式出现严重错误！请检查：{str(e)}")
                    self._categorys = {}
        except Exception as err:
            ExceptionUtils.exception_traceback(err)
            log.warn(f"【Config】二级分类策略 {category_name} 配置文件加载出错：{str(e)}")
            return False

        if self._categorys:
            self._movie_categorys = self._categorys.get('movie')
            self._tv_categorys = self._categorys.get('tv')
            self._anime_categorys = self._categorys.get('anime')
        log.info(f"【Config】已加载二级分类策略 {category_name}")

    @property
    def movie_category_flag(self):
        """
        获取电影分类标志
        """
        if self._movie_categorys:
            return True
        return False

    @property
    def tv_category_flag(self):
        """
        获取电视剧分类标志
        """
        if self._tv_categorys:
            return True
        return False

    @property
    def anime_category_flag(self):
        """
        获取动漫分类标志
        """
        if self._anime_categorys:
            return True
        return False

    @property
    def movie_categorys(self):
        """
        获取电影分类清单
        """
        if not self._movie_categorys:
            return []
        return self._movie_categorys.keys()

    @property
    def tv_categorys(self):
        """
        获取电视剧分类清单
        """
        if not self._tv_categorys:
            return []
        return self._tv_categorys.keys()

    @property
    def anime_categorys(self):
        """
        获取动漫分类清单
        """
        if not self._anime_categorys:
            return []
        return self._anime_categorys.keys()

    def get_movie_category(self, tmdb_info):
        """
        判断电影的分类
        :param tmdb_info: 识别的TMDB中的信息
        :return: 二级分类的名称
        """
        return self.get_category(self._movie_categorys, tmdb_info)

    def get_tv_category(self, tmdb_info):
        """
        判断电视剧的分类
        :param tmdb_info: 识别的TMDB中的信息
        :return: 二级分类的名称
        """
        return self.get_category(self._tv_categorys, tmdb_info)

    def get_anime_category(self, tmdb_info):
        """
        判断动漫的分类
        :param tmdb_info: 识别的TMDB中的信息
        :return: 二级分类的名称
        """
        return self.get_category(self._anime_categorys, tmdb_info)

    @staticmethod
    def get_category(categorys, tmdb_info):
        """
        根据 TMDB信息与分类配置文件进行比较，确定所属分类
        :param categorys: 分类配置
        :param tmdb_info: TMDB信息
        :return: 分类的名称
        """
        if not tmdb_info:
            return ""
        if not categorys:
            return ""
        for key, item in categorys.items():
            if not item:
                return key
            match_flag = True
            for attr, value in item.items():
                if not value:
                    continue
                
                # ^开头为逆向匹配，获取attr的真正名称
                reverse_condition = False
                if attr.startswith("^"):
                    reverse_condition = True
                    attr = attr[1:]

                info_value = tmdb_info.get(attr)
                if not info_value:
                    match_flag = False
                    continue
                elif attr == "production_countries":
                    info_values = [str(val.get("iso_3166_1")).upper() for val in info_value]
                else:
                    if isinstance(info_value, list):
                        info_values = [str(val).upper() for val in info_value]
                    else:
                        info_values = [str(info_value).upper()]

                if value.find(",") != -1:
                    values = [str(val).upper() for val in value.split(",")]
                else:
                    values = [str(value).upper()]

                if not set(values).intersection(set(info_values)):
                    match_flag = False
                    
                # 如果逆向匹配则反转结果
                match_flag = not match_flag if reverse_condition else match_flag
            if match_flag:
                return key
        return ""
    
    def get_multi_categories(self, tmdb_info):
        """
        根据 TMDB信息与分类配置文件进行比较，确定所有的类别
        :param tmdb_info: TMDB信息
        :return: 多类别的名称数组
        """
        if not tmdb_info:
            return []
        if not self._movie_categorys:
            return []
        multi_categories = []
        for key, item in self._movie_categorys.items():
            if not item:
                # “其他”类别最后匹配，因此如果第一个匹配到的是“其他”类型说明没有匹配到“其他”之外的类型，此时可以添加“其他”到多类别
                # 反之只要有“其他”之外的类型已经匹配，则不添加“其他”到多类别                
                if len(multi_categories) == 0 or not key.startswith("其他"):
                    multi_categories.append(key)
                else:
                    log.info(f"【Meta】「其他」非唯一类别，忽略「{key}」，不添加多类别")
                continue
            match_flag = True
            for attr, value in item.items():
                if not value:
                    continue
                
                # ^开头为逆向匹配，获取attr的真正名称
                reverse_condition = False
                if attr.startswith("^"):
                    reverse_condition = True
                    attr = attr[1:]
                    
                info_value = tmdb_info.get(attr)
                if not info_value:
                    match_flag = False
                    continue
                elif attr == "production_countries":
                    # 拆分国家，非国产的即便包含'CN','HK','TW'，也忽略，否则包含'CN','HK','TW'的非国产会被归类到国产片
                    domestic = []
                    non_domestic = []
                    for val in info_value:
                        country = str(val.get("iso_3166_1")).upper()
                        if country in ['CN','HK','TW']:
                            domestic.append(country)
                        else:
                            non_domestic.append(country)
                    info_values = non_domestic if len(non_domestic) > 0 else domestic
                else:
                    if isinstance(info_value, list):
                        info_values = [str(val).upper() for val in info_value]
                    else:
                        info_values = [str(info_value).upper()]

                if value.find(",") != -1:
                    values = [str(val).upper() for val in value.split(",")]
                else:
                    values = [str(value).upper()]

                if not set(values).intersection(set(info_values)):
                    match_flag = False
                    
                # 如果逆向匹配则反转结果
                match_flag = not match_flag if reverse_condition else match_flag
                
            if match_flag:
                # “其他”类别最后匹配，因此如果第一个匹配到的是“其他”类型说明没有匹配到“其他”之外的类型，此时可以添加“其他”到多类别
                # 反之只要有“其他”之外的类型已经匹配，则不添加“其他”到多类别
                if len(multi_categories) == 0 or not key.startswith("其他"):
                    multi_categories.append(key)
                else:
                    log.info(f"【Meta】「其他」非唯一类别，忽略「{key}」，不添加多类别")

        log.info(f"【Meta】识别到多类别：{multi_categories}")
        return multi_categories