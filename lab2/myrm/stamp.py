 # -*- coding: utf-8 -*-


"""Содержит функции для работы со штампами времени файлов.

Список экспортируемых функций:
    * get_time_stamp -- преобразует объект datetime в штамп
    * add_stamp -- добавляет штамп к имени файла
    * split_stamp -- отделяет имя файла и штамп
    * extend_mask_by_stamp -- расширяет маску маской штампа
    * get_versions_list  -- возвращает список версий файла
    * get_version -- возвращает путь к файлу с заданной версией
    * get_file_list_dict -- создает словарь версий файлов
    * files_to_file_dict -- преобразует список файлов в словарь версий

"""


import os
import datetime
import myrm.utils as utils


def get_time_stamp(dtime):
    """Возвращает POSIX время, и Количество микросекунд.

     Позицонные аргументы:
    dtime -- Объект datetime

    """
    days = dtime.toordinal() - datetime.date(1970, 1, 1).toordinal()
    sec = days * 24 * 60 * 60
    sec += dtime.hour * 60 * 60
    sec += dtime.minute * 60
    sec += dtime.second
    return sec, dtime.microsecond


def add_stamp(path, dtime):
    """Возвращает Путь файла рассширенный штампом времени

    Позицонные аргументы:
    path -- путь к файлу
    dtime -- Объект datetime

    Формат возвращаемого имени:
    "{path}_rmdt={posix_sec}_rmmsec={microsec}_"

    """
    if dtime is None:
        return path
    sec, msec = get_time_stamp(dtime)
    fmt = "{path}_rmdt={posix_sec}_rmmsec={microsec}_"
    return fmt.format(path=path, posix_sec=sec, microsec=msec)


def split_stamp(path):
    """Отделяет штамп времени. Возвращает Путь и Время.

    Позицонные аргументы:
    path -- путь к файлу

    Формат принимаемого имени:
    "{path}_rmdt={posix_sec}_rmmsec={microsec}_"

    """
    first_prefix, sep, sufix = path.rpartition("_")
    if sep != "_" or len(sufix) > 0:
        return path, None

    second_prefix, sep, rm_msec = first_prefix.rpartition("_rmmsec=")
    if sep != "_rmmsec=":
        return path, None

    filename, sep, rm_dt = second_prefix.rpartition("_rmdt=")
    if sep != "_rmdt=":
        return path, None

    try:
        sec = int(rm_dt)
        msec = int(rm_msec)
        dtime = datetime.datetime.fromtimestamp(sec)
        dtime += datetime.timedelta(microseconds=msec)
        return filename, dtime
    except ValueError:
        return path, None


def extend_mask_by_stamp(mask):
    """Возвращает маску файла расширенную форматом штампа времени

    Позицонные аргументы:
    mask -- маска файла

    Формат расширенной маски:
    "{mask}_rmdt=*_rmmsec=*_"

    """
    return "{mask}_rmdt=*_rmmsec=*_".format(mask=mask)


def get_versions_list(path):
    """Возвращает список штампом времени добавленных к файлу

    Позицонные аргументы:
    path -- путь к файлу

    Формат штампов:
    "{path}_rmdt={posix_sec}_rmmsec={microsec}_"

    """
    directory, file_name = os.path.split(path)
    extend_file_name = extend_mask_by_stamp(file_name)
    files = utils.search(directory, '', extend_file_name)
    versions = [split_stamp(f)[1] for f in files]
    versions.sort(reverse=True)
    return versions


def get_version(path, how_old):
    """Возвращает версию файла под номером how_old

    Позицонные аргументы:
    path -- путь к файлу
    how_old -- номер версии файла

    Формат штампов:
    "{path}_rmdt={posix_sec}_rmmsec={microsec}_"

    """
    versions = get_versions_list(path)
    count = len(versions)
    how_old = how_old if how_old < count else count - 1
    return add_stamp(path, versions[how_old])


def get_file_list_dict(file_time_list):
    """get_file_list_dict(file_time_list) -> словарь версий

    Преобразует список кортежей (файл, дата_время) в словарь, ключами
    которого являются имена файлов, а значениями - отсортированный список
    объектов дата_время

    """
    result = {}
    for somefile, dtime in file_time_list:
        if somefile not in result:
            result[somefile] = []
        result[somefile].append(dtime)
    for somefile, versions in result.iteritems():
        versions.sort(reverse=True)
    return result


def files_to_file_dict(files):
    """files_to_file_dict(files) -> словарь версий

    Разделяет штамп временини файлов и возвращает словарь, ключами
    которого являются имена файлов, а значениями - отсортированный список
    объектов дата_время

    """
    file_time_list = [split_stamp(somefile) for somefile in files]
    return get_file_list_dict(file_time_list)

