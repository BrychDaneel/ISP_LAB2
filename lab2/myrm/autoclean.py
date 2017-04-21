# -*- coding: utf-8 -*-

"""Здесь собранны функции очистки корзины по разным критериям.

Функции, экспортируемые данным модулем:
    * _clean_by_date -- очиска по дате удаления
    * _clean_by_files_count -- очиска по числу файлов
    * _clean_by_trash_size -- очиска по размеру файлов
    * _clean_by_same_count -- очиска файлов с одинаковым именем
    * autoclean -- очистка по всем критериям

"""


import os
import logging
import datetime
import myrm.stamp as stamp


def _clean_by_date(trash, file_time_list):
    """Очищает по дате удаления. Возвращает новый список файлов.

    Позицонные аргументы:
    file_time_list -- содержимое корзины. Список кортежей
                      (Путь, Время удаления).

    """
    now = datetime.datetime.utcnow()
    clear_days = trash.cfg["trash"]["autoclean"]["days"]
    old_files = [(f, t) for f, t in file_time_list
                 if (now - t).days > clear_days]

    for file_name, dtime in old_files:
        path = stamp.add_stamp(file_name, dtime)
        debug_fmt = "{} is too old"
        debug_line = debug_fmt.format(path)
        logging.debug(debug_line)
        trash.rm(path)

    new_files = set(file_time_list).difference(old_files)
    return list(new_files)


def _clean_by_files_count(trash, file_time_list):
    """Очищает по числу файлов. Возвращает новый список файлов.

    Позицонные аргументы:
    file_time_list -- содержимое корзины. Список кортежей
                      (Путь, Время удаления).

    """
    file_time_list = sorted(file_time_list, key=lambda (f, t): t,
                            reverse=True)

    clean_count = trash.cfg["trash"]["autoclean"]["count"]
    while clean_count <= trash.elems:
        file_name, dtime = file_time_list[-1]
        path = stamp.add_stamp(file_name, dtime)
        debug_fmt = "Removing {} to free bukkit({} files excess)"
        debug_line = debug_fmt.format(path, trash.elems - clean_count + 1)
        logging.debug(debug_line)
        trash.rm(path)
        file_time_list.pop(-1)
    return file_time_list


def _clean_by_trash_size(trash, file_time):
    """Очищает по размеру файлов. Возвращает новый список файлов.

    Позицонные аргументы:
    file_time_list -- содержимое корзины. Список кортежей
                      (Путь, Время удаления).

    """
    file_time = sorted(file_time, key=lambda (f, t): t, reverse=True)

    clean_size = trash.cfg["trash"]["autoclean"]["size"]
    while  clean_size <= trash.size:
        file_name, dtime = file_time[-1]
        path = stamp.add_stamp(file_name, dtime)
        debug_fmt = "Removing {} to free bukkit({} bytes excess)"
        debug_line = debug_fmt.format(path, trash.size - clean_size)
        logging.debug(debug_line)
        trash.rm(path)
        file_time.pop(-1)
    return file_time


def _clean_by_same_count(trash, file_time):
    """Очищает файлы с одинаковые. Возвращает новый список файлов.

    Позицонные аргументы:
    file_time_list -- содержимое корзины. Список кортежей
                      (Путь, Время удаления).

    """
    file_time = file_time[:]
    dct = stamp.get_file_list_dict(file_time)

    clean_samename = trash.cfg["trash"]["autoclean"]["samename"]
    for path, versions in dct.iteritems():
        if len(versions) > clean_samename:
            for dtime in versions[clean_samename:]:
                full_path = stamp.add_stamp(path, dtime)
                debug_fmt = "Removing {} becouse  there are a lot of same file"
                debug_line = debug_fmt.format(full_path)
                logging.debug(debug_line)
                trash.rm(full_path)
                file_time.remove((path, dtime))
    return file_time


def autoclean(trash):
    """Производит очиску корзины по различным критериям.

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
    was_locked = trash.locked
    if not was_locked:
        trash.lock()

    files = []
    for dirpath, dirnames, filenames in os.walk(trash.dirpath):
        files.extend([os.path.join(dirpath, f) for f in filenames])

    full_lock_path = trash.fullLockfile()
    files = [fn for fn in files if not os.path.samefile(fn, full_lock_path)]

    file_time_list = [stamp.split_stamp(f) for f in files]
    file_time_list = _clean_by_date(trash, file_time_list)
    file_time_list = _clean_by_same_count(trash, file_time_list)
    file_time_list = _clean_by_files_count(trash, file_time_list)
    file_time_list = _clean_by_trash_size(trash, file_time_list)

    if not was_locked:
        trash.unlock()
