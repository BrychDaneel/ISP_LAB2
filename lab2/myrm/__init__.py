#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-


"""Содержит главный класс MyRm и точки входа.

Класс модуля:
MyRm -- Класс предоставляющий утилиту удаления с использование корзины.

Функции модуля:
* get_default_MyRm -- возвращает объект MyRm созданного при помощи
                      файла конфигурации по-умолчанию.
* main -- главная тока входа в скрипт
* mrm -- укороченная точка входа в скрипт

"""


import os
import datetime
import fnmatch
import logging
import argparse

import myrm.trash
import myrm.acsess_manage
import myrm.config as config
import myrm.utils as utils
import myrm.stamp as stamp
import myrm.autoclean as autoclean

from myrm.trash import Trash
from myrm.acsess_manage import AcsessManager


def _lock_decodator(func):
    """Блокирует корзину до метода. Разблокирует после.

    Доступен только для методов этого объекта.
    """
    def result_func(self, *args, **kargs):
        """Обертка.
        """
        self.trash.lock()
        try:
            return func(self, *args, **kargs)
        finally:
            self.trash.unlock()
    return result_func


class MyRm(object):
    
    """Утилита для удаления файлов с использованием корзины.

    Поля класса:
    cfg -- объект конфигурации
    trash -- объект контролирующий файлы в корзине
    acsess_manager -- объект, контролирующий доступ к операциям

    Методы класса:

    """

    def __init__(self, cfg):
        """Строит класс по заданному объекту конфигурации.
        """
        self.cfg = cfg
        self.trash = Trash(cfg)
        self.acsess_manager = AcsessManager(cfg)

    @_lock_decodator
    def remove(self, path_mask, recursive=False):
        """Удаляет фалйы по маске в корзину. 
        
        Возвращает количестов удаленных файлов и их размер.

        Маска задается в формате Unix filename pattern.

        Позиионные аргументы:
        path_mask -- маска

        Непозиционные аргументы:
        recursive -- производить ли поиск в подпапках.
                     По умолчанию: False

        Используется _lock_decodator.

        """
        size = 0
        count = 0
        directory, mask = os.path.split(path_mask)
        found = utils.search(directory, mask, mask, recursive=recursive)
        for path in found:
            if  self.acsess_manager.remove_acsess(path):
                delta_count, delta_size = self.trash.add(path)
                size += delta_size
                count += delta_count
        return count, size

    @_lock_decodator
    def restore(self, path_mask, recursive=False, how_old=0):
        """Удаляет файлы в корзину по заданной маске.

        Возвращает количестов удаленных файлов и их размер.

        Маска задается в формате Unix filename pattern.

        Позиионные аргументы:
        path_mask -- маска

        Непозиционные аргументы:
        recursive -- производить ли поиск в подпапках.
        how_old -- версия файла в порядке устарения даты удаления.
                   Если больше числа файлов, берется последняя версия.
                   По умолчанию: 0 (последняя версия)

        Используется _lock_decodator.

        """
        size = 0
        count = 0
        files_versions = self.trash.search(path_mask, recursive=recursive)
        for path in files_versions:
            ext_path = self.trash.to_internal(path)
            if  self.acsess_manager.restore_acsess(ext_path):
                delta_count_size = self.trash.restore(path, how_old=how_old)
                count += delta_count_size[0]
                size += delta_count_size[1]
        return count, size

    @_lock_decodator
    def lst(self, path_mask='*', recursive=False, versions=True):
        """Возвращает список файлов в корзине по заданной маске.

        Маска задается в формате Unix filename pattern.

        Непозиционные аргументы:
        path_mask -- маска (по умолчанию: '*')
        recursive -- производить лиpath поиск в подпапках.
        versions -- показывать все версии файла (По-умолчанию: True)

        Используется _lock_decodator.

        """
        result = []
        files_versions = self.trash.search(path_mask, 
                                           recursive=recursive, find_all=True)
        files = files_versions.keys()
        files.sort(key=lambda f: (f.count(os.sep), f))
        for path in files:
            for dtime in files_versions[path]:
                result.append((path, dtime))
                if not versions:
                    break
        return result

    @_lock_decodator
    def clean(self, path_mask=None, recursive=False, how_old=-1):
        """Удаляет файлы из корзины навсегда.
        
        Возвращает количестов очищенных файлов и их размер.

        Непозиционные аргументы:
        path_mask -- маска. Если None, удаляется вся корзина.
                     (по умолчанию: 'None')
        recursive -- производить ли поиск в подпапках.
        how_old -- версия файла в порядке устарения даты удаления.
                   Если больше числа файлов, берется последняя версия.
                   По умолчанию: 0 (последняя версия)

        Используется _lock_decodator.

        """
        size = 0
        count = 0
        
        if path_mask is None:
            path_mask = self.cfg["trash"]["dir"]
        files_versions = self.trash.search(path_mask, 
                                    recursive=recursive, find_all=True)

        for path in files_versions:
            if  self.acsess_manager.clean_acsess(path):
                delta_count_size = self.trash.remove(path, how_old=how_old)
                count += delta_count_size[0]
                size += delta_count_size[1]
        return count, size

    @_lock_decodator
    def autoclean(self):
        """Выполняет очистку корзины по разнам политикам.

        Информаия о политиках берется из файла конфигурации.

        """
        if  self.acsess_manager.autoclean_acsess():
            autoclean.autoclean(self.trash)


def get_default_myrm():
    """Возвращает объект MyRm c файлом конфигурации по-умолчанию.
    """
    cfg = config.get_default_config()
    return MyRm(cfg)


def main(rm_only=False):
    """Главная точка входа.

    Операциии и аргументы беруться из командной строки.
    """
    parser = argparse.ArgumentParser(prog='myrm')

    if not rm_only:
        parser.add_argument('command',
                            choices=['rm', 'rs', 'ls', 'clear', 'autoclear'])
    parser.add_argument('filemask')
    parser.add_argument('-r', '-R', '--recursive',
                        dest='recursive', action='store_true')
    parser.add_argument('-o', '--old', dest='old', default=0)

    parser.add_argument('--config', default=None)
    parser.add_argument('--jsonconfig', default=None)

    parser.add_argument('-v', '--verbose', dest='verbose',
                        action='store_const', const=True)
    parser.add_argument('-d', '--dryrun', dest='dryrun',
                        action='store_const', const=True)
    parser.add_argument('-f', '--force', dest='force',
                        action='store_const', const=True)
    parser.add_argument('-i', '--interactive', dest='interactive',
                        action='store_const', const=True)

    args = parser.parse_args()
    cfg = config.get_default_config()

    if args.config is not None:
        cfg = config.load_from_cfg(args.config)

    if args.jsonconfig is not None:
        cfg = config.load_from_json(args.config)

    if args.force is not None:
        cfg['force'] = args.force
    if args.dryrun is not None:
        cfg['dryrun'] = args.dryrun
    if args.verbose is not None:
        cfg['verbose'] = args.verbose
    if args.interactive is not None:
        cfg['interactive'] = args.interactive

    mrm = MyRm(cfg)

    if rm_only:
        mrm.remove(args.filemask, recursive=args.recursive)
    else:
        cmd = args.command
        if cmd == 'rm':
            mrm.remove(args.filemask, recursive=args.recursive)
        elif cmd == 'rs':
            mrm.restore(args.filemask, recursive=args.recursive, how_old=args.old)
        elif cmd == 'ls':
            files = mrm.lst(args.filemask, recursive=args.recursive)
            print files
        elif cmd == 'clear':
            mrm.clean(args.filemask, recursive=args.recursive, how_old=args.old)
        elif cmd == 'autoclear':
            mrm.autoclean()

def shor_rm():
    """Красткая точка входа. Выполняет удаление в корзину.
    """
    main(rm_only=True)


if __name__ == "__main__":
    main()

