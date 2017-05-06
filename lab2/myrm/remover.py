#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-


"""Содержит главный класс myrm - Remover.
"""


import os
import logging

import myrm.control as control
import myrm.utils as utils

from myrm.trash import Trash
from myrm.trash import LimitExcessException
from myrm.autocleaner import Autocleaner


class Remover(object):

    """Утилита для удаления файлов с использованием корзины.

    Поля класса:
    * trash -- объект контролирующий файлы в корзине
    * autocleaner -- объект, производящий автоочистку
    
    * force -- режим игнорирования исключений
    * dryrun -- не проводить операции
    * interactive -- режим подробного опроса пользвателя
    * auto_replace -- автоматическая замена при востановлении
    * allow_autoclean -- разрешить автоочистку

    Методы класса:

    """

    def __init__(self, **kargs):
        """Строит класс по заданному объекту конфигурации.
        
        Непозиционные аргументы:
        * force -- режим игнорирования исключений
        * dryrun -- не проводить операции
        * interactive -- режим подробного опроса пользвателя
        * auto_replace -- автоматическая замена при востановлении
        * allow_autoclean -- разрешить автоочистку

        """
        self.trash = Trash()
        self.autocleaner = Autocleaner(self.trash)
        self.configurate(**kargs)

    def configurate(self, force=False, dryrun=False, interactive=False,
                    auto_replace=False, allow_autoclean=True,
                    trash={}, autoclean={}):
        """Обновляет поля объекта.
        
        Непозиционные аргументы:
        * force -- режим игнорирования исключений
        * dryrun -- не проводить операции
        * interactive -- режим подробного опроса пользвателя
        * auto_replace -- автоматическая замена при востановлении
        * allow_autoclean -- разрешить автоочистку

        """
        self.force = force
        self.dryrun = dryrun
        self.interactive = interactive
        self.auto_replace = auto_replace
        self.allow_autoclean = allow_autoclean

        self.trash.configurate(**trash)
        self.autocleaner.configurate(**autoclean)

    def remove(self, path_mask, recursive=False):
        """Удаляет фалйы по маске в корзину.

        Возвращает количестов удаленных файлов и их размер.

        Маска задается в формате Unix filename pattern.
        Только последний элемент пути может быть маской.

        Позиионные аргументы:
        path_mask -- маска

        Непозиционные аргументы:
        recursive -- производить ли поиск в подпапках.
                     По умолчанию: False

        Корзина блокируется.

        """
        path_mask = os.path.expanduser(path_mask)
        path_mask = os.path.abspath(path_mask)
        size = 0
        count = 0
        directory, mask = os.path.split(path_mask)

        with self.trash.lock():
            found = utils.search(directory, mask, mask, recursive=recursive)
            for path in found:

                if  not control.remove(path, interactive=self.interactive,
                                       dryrun=self.dryrun):
                    continue

                try:
                    try:
                        delta_count, delta_size = self.trash.add(path)
                    except LimitExcessException:
                        if self.allow_autoclean:
                            log_msg = ("Bukkit limit excess. "
                                       "Trying to autoclean.")
                            logging.info(log_msg)

                            dcount, dsize = self.autocleaner.autoclean()
                            log_fmt = "{count} files({size} bytes) cleaned."
                            log_msg = log_fmt.format(count=dcount, size=dsize)
                            delta_count, delta_size = self.trash.add(path)
                        else:
                            raise
                except Exception:
                    if not self.force:
                        raise

                size += delta_size
                count += delta_count
        return count, size

    def restore(self, path_mask, recursive=False, how_old=0):
        """Удаляет файлы в корзину по заданной маске.

        Возвращает количестов удаленных файлов и их размер.

        Маска задается в формате Unix filename pattern.
        Только последний элемент пути может быть маской.

        Позиионные аргументы:
        path_mask -- маска

        Непозиционные аргументы:
        recursive -- производить ли поиск в подпапках.
        how_old -- версия файла в порядке устарения даты удаления.
                   Если больше числа файлов, берется последняя версия.
                   По умолчанию: 0 (последняя версия)

        Корзина блокируется.

        """
        size = 0
        count = 0

        with self.trash.lock():
            files_versions = self.trash.search(path_mask, recursive=recursive)
            for path in files_versions:

                if  not control.restore(path, interactive=self.interactive,
                                        dryrun=self.dryrun):
                    continue

                if os.path.exists(path):
                    if not control.replace(path, auto_replace=self.auto_replace,
                                           dryrun=self.dryrun):
                        continue

                try:
                    delta_count_size = self.trash.restore(path, how_old=how_old)
                except Exception:
                    if not self.force:
                        raise
                count += delta_count_size[0]
                size += delta_count_size[1]

        return count, size

    def lst(self, path_mask="*", recursive=False, versions=True):
        """Возвращает список файлоzв в корзине по заданной маске.

        Маска задается в формате Unix filename pattern.
        Только последний элемент пути может быть маской.

        Непозиционные аргументы:
        path_mask -- маска (по умолчанию: '*')
        recursive -- производить лиpath поиск в подпапках.
        versions -- показывать все версии файла (По-умолчанию: True)

        Корзина блокируется.

        """
        result = []

        with self.trash.lock():
            files_versions = self.trash.search(path_mask, recursive=recursive,
                                               find_all=True)
            files = files_versions.keys()
            files.sort(key=lambda f: (f.count(os.sep), f))
            for path in files:
                for dtime in files_versions[path]:
                    result.append((path, dtime))
                    if not versions:
                        break
        return result

    def clean(self, path_mask=None, recursive=False, how_old=-1):
        """Удаляет файлы из корзины навсегда.

        Возвращает количестов очищенных файлов и их размер.
        Только последний элемент пути может быть маской.

        Непозиционные аргументы:
        path_mask -- маска. Если None, удаляется вся корзина.
                     (по умолчанию: 'None')
        recursive -- производить ли поиск в подпапках.
        how_old -- версия файла в порядке устарения даты удаления.
                   Если больше числа файлов, берется последняя версия.
                   По умолчанию: -1 (все версии)

        Корзина блокируется.

        """
        size = 0
        count = 0

        if path_mask is None:
            path_mask = self.trash.directory

        with self.trash.lock():
            files_versions = self.trash.search(path_mask, recursive=recursive,
                                               find_all=True)

            for path in files_versions:

                if  not control.clean(path, interactive=self.interactive,
                                      dryrun=self.dryrun):
                    continue

                try:
                    delta_count_size = self.trash.remove(path, how_old=how_old)
                except Exception:
                    if not self.force:
                        raise

                count += delta_count_size[0]
                size += delta_count_size[1]
        return count, size

    def autoclean(self):
        """Выполняет очистку. Возвращает кол-во очищ файлов и размер.

        Информаия о политиках берется из файла конфигурации.

        """
        if  control.autoclean(interactive=self.interactive, dryrun=self.dryrun):
            with self.trash.lock():
                return self.autocleaner.autoclean()
        return 0, 0
