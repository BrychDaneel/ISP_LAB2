# -*- coding: utf-8 -*-

"""Содержит класс Autocleaner, который производит автоочистку корзины.
"""


import logging
import datetime
import myrm.stamp as stamp


DEFAULT_CLEAN_COUNT = 1000*1000
DEFAULT_CLEAN_SIZE = 512*1024*1024
DEFAULT_CLEAN_DAYS = 90
DEFAULT_CLEAN_SAME_COUNT = 10


class Autocleaner(object):
    """Производит автоочистку корзины

    Поля класса:
    * trash -- объект корзины

    Критерии очистки
    * count -- число файлов
    * size -- размер
    * days -- количество дней
    * same_count -- число файлов

    Методы класса:
    * clean_by_date -- очиска по дате удаления
    * clean_by_files_count -- очиска по числу файлов
    * clean_by_trash_size -- очиска по размеру файлов
    * clean_by_same_count -- очиска файлов с одинаковым именем
    * autoclean -- очистка по всем критериям

    """

    def __init__(self, trash,
                 count=DEFAULT_CLEAN_COUNT,
                 size=DEFAULT_CLEAN_SIZE,
                 days=DEFAULT_CLEAN_DAYS,
                 same_count=DEFAULT_CLEAN_SAME_COUNT
                ):
        """Создает объект для определенной корзины.

        Непозиционные аргументы:
        * count -- число файлов для очистки
        * size -- размер для очистки
        * days -- количество дней для очистки
        * same_count -- число файлов для очистки

        """
        self.trash = trash
        self.configurate(count, size, days, same_count)

    def configurate(self,
                    count=DEFAULT_CLEAN_COUNT,
                    size=DEFAULT_CLEAN_SIZE,
                    days=DEFAULT_CLEAN_DAYS,
                    same_count=DEFAULT_CLEAN_SAME_COUNT
                   ):
        """Обновляет поля объекта.

        Непозиционные аргументы:
        * count -- число файлов для очистки
        * size -- размер для очистки
        * days -- количество дней для очистки
        * same_count -- число файлов для очистки

        """
        self.count = count
        self.size = size
        self.days = days
        self.same_count = same_count

    def autoclean_by_date(self):
        """Очищает корзину по дате удаления.
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
        """Очищает по числу файлов.
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
        """Очищает корзину по размеру файлов.
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
                        self.trash.remove(path, last_version)
                        last_version -= 1

    def autoclean(self):
        """Производт очиску корзины. Возвращает кол-во файлов и размер.

        Критерии очистки:
        * по дате удаления
        * по числу файлов
        * по размеру файлов
        * очиска файлов с одинаковым именем

        Блокирует корзину.

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

