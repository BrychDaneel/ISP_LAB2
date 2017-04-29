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
        Только последний элемент пути может быть маской.

        Позиионные аргументы:
        path_mask -- маска

        Непозиционные аргументы:
        recursive -- производить ли поиск в подпапках.
                     По умолчанию: False

        Используется _lock_decodator.

        """
        path_mask = os.path.expanduser(path_mask)
        path_mask = os.path.abspath(path_mask)
        size = 0
        count = 0
        directory, mask = os.path.split(path_mask)
        found = utils.search(directory, mask, mask, recursive=recursive)
        for path in found:
            if  self.acsess_manager.remove_acsess(path):
                try:
                    try:
                        delta_count, delta_size = self.trash.add(path)
                    except trash.LimitExcessException:
                        if self.cfg["trash"]["allowautoclean"]:
                            log_msg = ("Bukkit limit excess. " 
                                       "Try to autoclean.")
                            logging.info(log_msg)
                            
                            dcount, dsize = autoclean.autoclean(self.trash)
                            log_fmt = "{count} files({size} bytes) cleaned."
                            log_msg = log_fmt.format(count=dcount, size=dsize)
                            
                            delta_count, delta_size = self.trash.add(path)
                        else:
                            raise
                except Exception:
                    if not self.cfg["force"]:
                        raise
                    
                size += delta_size
                count += delta_count
        return count, size

    @_lock_decodator
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

        Используется _lock_decodator.

        """
        path_mask = os.path.expanduser(path_mask)
        path_mask = os.path.abspath(path_mask)
        size = 0
        count = 0
        files_versions = self.trash.search(path_mask, recursive=recursive)
        for path in files_versions:
            if  self.acsess_manager.restore_acsess(path):
                if (not os.path.exists(path) or 
                        self.acsess_manager.replace_acsess(path)):
                    try:
                        delta_count_size = self.trash.restore(path, 
                                                            how_old=how_old)
                    except Exception:
                        if not self.cfg["force"]:
                            raise
                    count += delta_count_size[0]
                    size += delta_count_size[1]
        return count, size

    @_lock_decodator
    def lst(self, path_mask="*", recursive=False, versions=True):
        """Возвращает список файлов в корзине по заданной маске.

        Маска задается в формате Unix filename pattern.
        Только последний элемент пути может быть маской.

        Непозиционные аргументы:
        path_mask -- маска (по умолчанию: '*')
        recursive -- производить лиpath поиск в подпапках.
        versions -- показывать все версии файла (По-умолчанию: True)

        Используется _lock_decodator.

        """
        path_mask = os.path.expanduser(path_mask)
        path_mask = os.path.abspath(path_mask)
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
        Только последний элемент пути может быть маской.

        Непозиционные аргументы:
        path_mask -- маска. Если None, удаляется вся корзина.
                     (по умолчанию: 'None')
        recursive -- производить ли поиск в подпапках.
        how_old -- версия файла в порядке устарения даты удаления.
                   Если больше числа файлов, берется последняя версия.
                   По умолчанию: -1 (все версии)

        Используется _lock_decodator.

        """
        path_mask = os.path.expanduser(path_mask)
        path_mask = os.path.abspath(path_mask)
        size = 0
        count = 0
        
        if path_mask is None:
            path_mask = self.cfg["trash"]["dir"]
        files_versions = self.trash.search(path_mask, 
                                    recursive=recursive, find_all=True)

        for path in files_versions:
            if  self.acsess_manager.clean_acsess(path):
                try:
                    delta_count_size = self.trash.remove(path, how_old=how_old)
                except Exception:
                    if not self.cfg["force"]:
                        raise    
                count += delta_count_size[0]
                size += delta_count_size[1]
        return count, size

    @_lock_decodator
    def autoclean(self):
        """Выполняет очистку. Возвращает кол-во очищ файлов и размер.

        Информаия о политиках берется из файла конфигурации.

        """
        if  self.acsess_manager.autoclean_acsess():
            return autoclean.autoclean(self.trash)
        return 0, 0


def get_default_myrm():
    """Возвращает объект MyRm c файлом конфигурации по-умолчанию.
    """
    cfg = config.get_default_config()
    return MyRm(cfg)


def main(rm_only=False):
    """Главная точка входа.

    Операциии и аргументы беруться из командной строки.
    """
    parser = argparse.ArgumentParser(prog="myrm")

    if not rm_only:
        parser.add_argument("command",
                            choices=["rm", "rs", "ls", "clear", "autoclear"])
    parser.add_argument("filemasks", nargs='+')
    parser.add_argument("-r", "-R", "--recursive",
                        dest="recursive", action="store_true")
    
    parser.add_argument("-o", "--old", dest="old", default=0, 
                        help="Choose version of file.")
    parser.add_argument("-a", "--all", dest="versions",
                        action="store_const", const=True, 
                        help="display all versions of files.")
    
    parser.add_argument("--config", default=None)
    parser.add_argument("--jsonconfig", default=None)

    parser.add_argument("-v", "--verbose", dest="verbose",
                        action="store_const", const=True, 
                        help="show list of operate files.")
    parser.add_argument("-d", "--dryrun", dest="dryrun",
                        action="store_const", const=True, 
                        help="just emulate work.")
    parser.add_argument("-f", "--force", dest="force",
                        action="store_const", const=True, 
                        help="igrnore errors.")
    parser.add_argument("-i", "--interactive", dest="interactive",
                        action="store_const", const=True, 
                        help="ask you before operation.")

    args = parser.parse_args()
    cfg = config.get_default_config()

    if args.config is not None:
        cfg = config.load_from_cfg(args.config)

    if args.jsonconfig is not None:
        cfg = config.load_from_json(args.config)

    if args.force is not None:
        cfg["force"] = args.force
    if args.dryrun is not None:
        cfg["dryrun"] = args.dryrun
    if args.verbose is not None:
        cfg["verbose"] = args.verbose
    if args.interactive is not None:
        cfg["interactive"] = args.interactive

    if cfg["verbose"]:
        logging.basicConfig(format="%(message)s", level=logging.INFO)

    mrm = MyRm(cfg)
    
    count = 0
    size = 0
    for fime_mask in args.filemasks:
        if rm_only:
            dcount, dsize = mrm.remove(fime_mask, recursive=args.recursive)
            count += dcount
            size += dsize
        else:
            cmd = args.command
            if cmd == "rm":
                dcount, dsize = mrm.remove(fime_mask , 
                                        recursive=args.recursive)
                count += dcount
                size += dsize
                
            elif cmd == "rs":
                dcount, dsize = mrm.restore(fime_mask, recursive=args.recursive, 
                                          how_old=args.old)
                count += dcount
                size += dsize       
                
            elif cmd == "ls":
                files = mrm.lst(fime_mask, recursive=args.recursive,
                                versions=args.versions)
                for path, version in files:
                    if version == None or not args.versions:
                        log_msg = path
                    else:
                        log_msg = "{} ({})".format(path, 
                                                version.isoformat())
                    logging.info(log_msg)                    
                    
            elif cmd == "clear":
                dcount, dsize = mrm.clean(fime_mask, recursive=args.recursive, 
                                        how_old=args.old)
                count += dcount
                size += dsize

            elif cmd == "autoclear":
                dcount, dsize = mrm.autoclean()
                count += dcount
                size += dsize

    if rm_only:
        log_fmt = "{count} files ({size} bytes) was removed."
        log_msg = log_fmt.format(count=count, size=size) 
        logging.info(log_msg)
    else:
        cmd = args.command
        if cmd == "rm":
            log_fmt = "{count} files ({size} bytes) was removed."
            log_msg = log_fmt.format(count=count, size=size) 
            logging.info(log_msg)
            
        elif cmd == "rs":
            log_fmt = "{count} files ({size} bytes) was restored."
            log_msg = log_fmt.format(count=count, size=size) 
            logging.info(log_msg)         
                
        elif cmd == "clear":
            log_fmt = "{count} files ({size} bytes) was cleaned."
            log_msg = log_fmt.format(count=count, size=size) 
            logging.info(log_msg)

        elif cmd == "autoclear":
            log_fmt = "{count} files ({size} bytes) was cleaned."
            log_msg = log_fmt.format(count=count, size=size) 
            logging.info(log_msg)

def shor_rm():
    """Красткая точка входа. Выполняет удаление в корзину.
    """
    main(rm_only=True)


if __name__ == "__main__":
    main()

