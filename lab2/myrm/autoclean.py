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


def autoclean_by_date(trash):
    """Очищает по дате удаления.

    Позицонные аргументы:
    * trash -- объект корзины

    """
    file_time_list = trash.get_file_time_list()
    now = datetime.datetime.utcnow()
    clear_days = trash.cfg["trash"]["autoclean"]["days"]
    old_files = ((f, t) for f, t in file_time_list
                 if (now - t).days > clear_days)

    for path, dtime in old_files:
        debug_fmt = ("Removing {path}(removed time: {dtime}) "
                     "becouse it's too old.")
        debug_line = debug_fmt.format(path=path, dtime=dtime)
        logging.debug(debug_line)
        path_int = trash.to_internal(path)
        last_version = len(stamp.get_versions_list(path_int)) - 1
        trash.remove(path, last_version)


def autoclean_by_files_count(trash):
    """Очищает по числу файлов. Возвращает новый список файлов.

    Позицонные аргументы:
    * trash -- объект корзины

    """
    file_time_list = trash.get_file_time_list()
    clean_count = trash.cfg["trash"]["autoclean"]["count"]
    
    i = 0
    while clean_count <= trash.files_count:
        path, dtime = file_time_list[i]
        debug_fmt = ("Removing {path}(removed time: {dtime}) "
                     "to free bukkit({excess} files excess)")
        excess = trash.files_count - clean_count + 1
        debug_line = debug_fmt.format(path=path, dtime=dtime,
                                      excess=excess)
        logging.debug(debug_line)
        path_int = trash.to_internal(path)
        last_version = len(stamp.get_versions_list(path_int)) - 1
        trash.remove(path, last_version)
        i += 1


def autoclean_by_trash_size(trash):
    """Очищает по размеру файлов.

    Позицонные аргументы:
    * trash -- объект корзины

    """
    file_time_list = trash.get_file_time_list()
    clean_size = trash.cfg["trash"]["autoclean"]["size"]
    
    i = 0
    while  clean_size <= trash.trash_size:
        path, dtime = file_time_list[i]
        debug_fmt = ("Removing {path} (removed time: {dtime})" 
                     "to free bukkit({excess} bytes excess)")
        debug_line = debug_fmt.format(path=path, dtime=dtime, 
                                      excess=trash.trash_size - clean_size)
        logging.debug(debug_line)
        path_int = trash.to_internal(path)
        last_version = len(stamp.get_versions_list(path_int)) - 1
        trash.remove(path, last_version)
        i += 1


def autoclean_by_same_count(trash):
    """Очищает файлы с одинаковые.

    Позицонные аргументы:
    * trash -- объект корзины

    """
    file_time = trash.get_file_time_list()
    dct = stamp.get_file_list_dict(file_time)
    clean_samename = trash.cfg["trash"]["autoclean"]["samename"]
    for path, versions in dct.iteritems():
        if len(versions) > clean_samename:
            for dtime in reversed(versions[clean_samename - 1:]):
                debug_fmt = ("Removing {path} (removed time: {dtime}) "
                             "becouse  there are a lot of same file")
                debug_line = debug_fmt.format(path=path, dtime=dtime)
                logging.debug(debug_line)
                path_int = trash.to_internal(path)
                last_version = len(stamp.get_versions_list(path_int)) - 1
                trash.remove(path, last_version)


def autoclean(trash):
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
    was_locked = trash.locked
    if not was_locked:
        trash.lock()
    
    delta_count = trash.files_count
    delta_size = trash.trash_size
    
    autoclean_by_date(trash,)
    autoclean_by_same_count(trash)
    autoclean_by_files_count(trash)
    autoclean_by_trash_size(trash)
    
    delta_count -= trash.files_count
    delta_size -= trash.trash_size

    if not was_locked:
        trash.unlock()
    
    return delta_count, delta_size 
