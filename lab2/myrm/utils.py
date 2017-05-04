# -*- coding: utf-8 -*-


"""Содержит функции общего назначения, используемые модулем myrm.

Список экспортируемых  функций
    * search -- производит поиск объектов по маске
    * files_count -- считает количество файлов
    * files_size -- считает размер файлов
    * split_path -- разбивает путь на состовляющие

"""


import os
import re
import fnmatch


def search(directory, dir_mask, file_mask, recursive=False, find_all=False):
    """Производит поиск объектов по маске. Возвращает итератор.

    Маска задается в формате Unix filename pattern.

    Позицонные аргументы:
    directory -- корневая директория
    dir_mask -- критерий совпадения папки.
    dir_mask -- критерий совпадения файлов.

    Непозиционные аргументы:
    recursive -- производить поиск в подпапках (по-умолчанию False)
    find_all -- углублять в подпапки,
                    если они соответствуют маске (по-умолчанию False)

    """
    if len(directory) == 0:
        directory = '.'

    file_re = re.compile(fnmatch.translate(file_mask))
    dir_re = re.compile(fnmatch.translate(dir_mask))
    for found in os.listdir(directory):
        found_path = os.path.join(directory, found)
        isdir = os.path.isdir(found_path)
        if not isdir and file_re.match(found):
            yield  found_path
        if isdir and dir_re.match(found):
            yield found_path
        if isdir and recursive and (not dir_re.match(found) or find_all):
            for match in search(found_path, dir_mask, file_mask,
                                recursive=recursive, find_all=find_all):
                yield match


def split_path(path):
    """Возвращает список составлющих пути.

    Позицонные аргументы:
    path -- путь

    """
    result = []
    prefix, node = os.path.split(path)
    while node:
        result.append(node)
        prefix, node = os.path.split(prefix)
    result.append(prefix)
    result.reverse()
    return result


def files_count(path):
    """Возвращает количество файлов в заданном пути.

    Если переданна папка, рекурсивно считает
    файлы в ней. Иначе, возвращает 1.

    """
    if not os.path.isdir(path):
        return 1 if os.path.exists(path) else 0
    ans = 0
    for dirpath, dirnames, filenames in os.walk(path):
        ans += len(filenames)
    return ans


def files_size(path):
    """Возвращает занимаемое на диске место данного объекта.
    """
    if not os.path.isdir(path):
        if os.path.exists(path):
            return os.lstat(path).st_size
        else
            return 0
    ans = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for somefile in filenames:
            file_path = os.path.join(dirpath, somefile)
            ans += os.lstat(file_path).st_size
    return ans


def absolute_path(path):
    path_expand = os.path.expanduser(path)
    path_abs = os.path.abspath(path_expand)
    return path_abs 

