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


DEFAULT_FORCE = False
DEFAULT_DRYRUN = False
DEFAULT_INTERACTIVE = False
DEFAULT_AUTO_REPLACE = False
DEFAULT_ALLOW_AUTOCLEAN = True


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
    * __init__ -- создает корзину по заданным параметрам
    * configurate -- конфигурирует корзину заданными параметрами
    * remove -- удаляет файлы по регулярному выражению
    * restore -- востанавливает файлы по регулярному выражению 
    * lst -- список файлов по регулярному выражению
    * autoclean -- выполняет автоочистку корзины

    """

    def __init__(self,
                 force=DEFAULT_FORCE,
                 dryrun=DEFAULT_DRYRUN,
                 interactive=DEFAULT_INTERACTIVE,
                 auto_replace=DEFAULT_AUTO_REPLACE,
                 allow_autoclean=DEFAULT_ALLOW_AUTOCLEAN,
                 trash={},
                 autoclean={}
                ):
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
        self.configurate(force, dryrun, interactive, auto_replace,
                         allow_autoclean, trash, autoclean)

    def configurate(self,
                    force=DEFAULT_FORCE,
                    dryrun=DEFAULT_DRYRUN,
                    interactive=DEFAULT_INTERACTIVE,
                    auto_replace=DEFAULT_AUTO_REPLACE,
                    allow_autoclean=DEFAULT_ALLOW_AUTOCLEAN,
                    trash={},
                    autoclean={}
                   ):
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
        files = []
        directory, mask = os.path.split(path_mask)

        with self.trash.lock():
            found = utils.search(directory, mask, mask, recursive=recursive)
            for path in found:

                if  not control.remove(path, interactive=self.interactive):
                    continue

                try:
                    try:
                        if self.dryrun:
                            with self.trash.dryrun_mode():
                                dcount, dsize, dfiles = self.trash.add(path)
                        else:
                            dcount, dsize, dfiles = self.trash.add(path)

                    except LimitExcessException:
                        if self.allow_autoclean and not self.dryrun:
                            log_msg = ("Bukkit limit excess. "
                                       "Trying to autoclean.")
                            logging.info(log_msg)

                            dcount, dsize = self.autocleaner.autoclean()
                            log_fmt = "{count} files({size} bytes) cleaned."
                            log_msg = log_fmt.format(count=dcount, size=dsize)

                            if self.dryrun:
                                with self.trash.dryrun_mode():
                                    dcount, dsize, dfiles = self.trash.add(path)
                            else:
                                dcount, dsize, dfiles = self.trash.add(path)
                        else:
                            raise
                except Exception:
                    if not self.force:
                        raise

                count += dcount
                size += dsize
                files.extend(dfiles)
        return count, size, files

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
        files = []

        with self.trash.lock():
            files_versions = self.trash.search(path_mask, recursive=recursive)
            for path in files_versions:

                if  not control.restore(path, interactive=self.interactive):
                    continue

                if os.path.exists(path):
                    if not control.replace(path,
                                           auto_replace=self.auto_replace):
                        continue

                try:
                    if self.dryrun:
                        with self.trash.dryrun_mode():
                            delta = self.trash.restore(path, how_old=how_old)
                    else:
                        delta = self.trash.restore(path, how_old=how_old)
                except Exception:
                    if not self.force:
                        raise
                count += delta[0]
                size += delta[1]
                files.extend(delta[2])

        return count, size, files

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
        files = []

        if path_mask is None:
            path_mask = self.trash.directory

        with self.trash.lock():
            files_versions = self.trash.search(path_mask, recursive=recursive,
                                               find_all=True)

            for path in files_versions:

                if  not control.clean(path, interactive=self.interactive):
                    continue

                try:
                    if self.dryrun:
                        with self.trash.dryrun_mode():
                            delta = self.trash.remove(path, how_old=how_old)
                    else:
                        delta = self.trash.remove(path, how_old=how_old)
                except Exception:
                    if not self.force:
                        raise

                count += delta[0]
                size += delta[1]
                files.extend(delta[2])

        return count, size, files

    def autoclean(self):
        """Выполняет очистку. Возвращает кол-во очищ файлов и размер.

        """
        if self.dryrun:
            raise ValueError("Unable to do autoclean in dryrun mode.")
        if  control.autoclean(interactive=self.interactive,
                              path=self.trash.directory):
            with self.trash.lock():
                return self.autocleaner.autoclean()
        return 0, 0
