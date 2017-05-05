# -*- coding: utf-8 -*-

"""Здесь собранны функции очистки корзины по разным критериям.

Функции, экспортируемые данным модулем:
    * _clean_by_date -- очиска по дате удаления
    * _clean_by_files_count -- очиска по числу файлов
    * _clean_by_trash_size -- очиска по размеру файлов
    * _clean_by_same_count -- очиска файлов с одинаковым именем
    * autoclean -- очистка по всем критериям

"""


import logging
import datetime
import myrm.stamp as stamp


class Autocleaner(object):
    """
    """

    def __init__(self, trash, **kargs):
        """
        """
        self.trash = trash
        self.configurate(**kargs)

    def configurate(self, count=1000*1000, size=512*1024*1024,
                    days=90, same_count=10):
        """
        """
        self.count = count
        self.size = size
        self.days = days
        self.same_count = same_count


    def autoclean_by_date(self):
        """Очищает по дате удаления.

        Позицонные аргументы:
        * trash -- объект корзины

        """
        clear_days = self.days

        file_time_list = self.trash.get_file_time_list()
        now = datetime.datetime.utcnow()
        old_files = ((f, t) for f, t in file_time_list
                     if (now - t).days > clear_days)

        with self.trash.lock():
            for path, dtime in old_files:
                debug_fmt = ("Removing {path}(removed time: {dtime}) "
                             "becouse it's too old.")
                debug_line = debug_fmt.format(path=path, dtime=dtime)
                logging.debug(debug_line)
                path_int = self.trash.to_internal(path)
                last_version = len(stamp.get_versions_list(path_int)) - 1
                self.trash.remove(path, last_version)


    def autoclean_by_files_count(self):
        """Очищает по числу файлов. Возвращает новый список файлов.

        Позицонные аргументы:
        * trash -- объект корзины

        """
        clean_count = self.count

        file_time_list = self.trash.get_file_time_list()

        with self.trash.lock():
            index = 0
            while clean_count <= self.trash.get_count():
                path, dtime = file_time_list[index]
                debug_fmt = ("Removing {path}(removed time: {dtime}) "
                             "to free bukkit({excess} files excess)")
                excess = self.trash.get_count() - clean_count + 1
                debug_line = debug_fmt.format(path=path, dtime=dtime,
                                              excess=excess)
                logging.debug(debug_line)
                path_int = self.trash.to_internal(path)
                last_version = len(stamp.get_versions_list(path_int)) - 1
                self.trash.remove(path, last_version)
                index += 1


    def autoclean_by_trash_size(self):
        """Очищает по размеру файлов.

        Позицонные аргументы:
        * trash -- объект корзины

        """
        clean_size = self.size

        file_time_list = self.trash.get_file_time_list()

        with self.trash.lock():
            index = 0
            while  clean_size <= self.trash.get_size():
                path, dtime = file_time_list[index]
                debug_fmt = ("Removing {path} (removed time: {dtime})"
                             "to free bukkit({excess} bytes excess)")
                excess = self.trash.get_size() - clean_size
                debug_line = debug_fmt.format(path=path, dtime=dtime,
                                              excess=excess)
                logging.debug(debug_line)
                path_int = self.trash.to_internal(path)
                last_version = len(stamp.get_versions_list(path_int)) - 1
                self.trash.remove(path, last_version)
                index += 1


    def autoclean_by_same_count(self):
        """Очищает файлы с одинаковые.

        Позицонные аргументы:
        * trash -- объект корзины

        """
        clean_same_count = self.same_count

        file_time = self.trash.get_file_time_list()
        dct = stamp.get_file_list_dict(file_time)

        with self.trash.lock():
            for path, versions in dct.iteritems():
                if len(versions) > clean_same_count:
                    for dtime in reversed(versions[clean_same_count - 1:]):
                        debug_fmt = ("Removing {path} (removed time: {dtime}) "
                                     "becouse  there are a lot of same file")
                        debug_line = debug_fmt.format(path=path, dtime=dtime)
                        logging.debug(debug_line)
                        path_int = self.trash.to_internal(path)
                        last_version = len(stamp.get_versions_list(path_int))
                        last_version -= 1
                        self.trash.remove(path, last_version)


    def autoclean(self):
        """Производит очиску корзины. Возвращает кол-во файлов и размер.

        Позицонные аргументы:
        * trash -- объект корзины

        Критерии очистки:
        * по дате удаления
        * по числу файлов
        * по размеру файлов
        * очиска файлов с одинаковым именем

        Информациия для очистки берется из файла конфингурации корзины.

        Перед началом работы проверяет блокировку корзины и блокирует,
        если она отсутствует.

        """

        delta_count = self.trash.get_count()
        delta_size = self.trash.get_size()

        self.autoclean_by_date()
        self.autoclean_by_same_count()
        self.autoclean_by_files_count()
        self.autoclean_by_trash_size()

        delta_count -= self.trash.get_count()
        delta_size -= self.trash.get_size()

        return delta_count, delta_size
