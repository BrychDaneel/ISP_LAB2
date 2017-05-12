# -*- coding: utf-8 -*-


"""Содержит класс Tash, управляющий содержимым корзины.

Вспомогательный класс:
    * TrashLocker - для блокировки корзины через менеджер контента.
    * Dryruner - для включения dryrun через менеджер контента.

Исключения модуля:
    LimitExcessException -- выбрасывается при превышении лимита

"""


import os
import datetime
import logging
import myrm.utils as utils
import myrm.stamp as stamp


DEFAULT_DIRECTORY = "~/.trash"
DEFAULT_LOCK_FILE = "lock"
DEFAULT_MAX_SIZE = 1024*1024*1024
DEFAULT_MAX_COUNT = 10*1000*1000
DEFAULT_DRYRUN = False

class LimitExcessException(Exception):
    """Возбуждается при превышения пользовательского лимита.
    """
    pass


class TrashLocker(object):
    """Используется для блокировки корзины через менеджер контента.
    """

    def __init__(self, trash):
        """Создает объект для указанной корзины.
        """
        self.trash = trash
        self._was_locked = None

    def __enter__(self):
        """Блокирует корзину.

        Корзина не блокирется если она уже заблокированна.
        """
        self._was_locked = self.trash.is_locked()

        if not self._was_locked:
            self.trash.set_lock()

    def __exit__(self, exp_type, exp_value, traceback):
        """Разблокирует корзину.

        Корзина не разблокирется если она не была заблокированна.
        """
        if not self._was_locked:
            self.trash.unset_lock()


class Dryruner(object):
    """Используется для активации dryrun через менеджер контента.
    """

    def __init__(self, trash):
        """Создает объект для указанной корзины.
        """
        self.trash = trash
        self._was_dryrun = None

    def __enter__(self):
        """Активирует режим dryrun. Сохраняет старое состояние режима.
        """
        self._was_dryrun = self.trash.dryrun
        self.trash.dryrun = True

    def __exit__(self, exp_type, exp_value, traceback):
        """Возвращает dryrun в состояние до блокировки.
        """
        self.trash.dryrun = self._was_dryrun


class Trash(object):

    """Класс управляет содержимым корзины.

    Поля класса:
    * locked -- заблокированна ли корзина в текущий момент

    Следующие поля используются только на протяжении блокировки:
    * directory -- путь к папке с корзиной
    * lock_file -- имя файла блокировки
    * max_size -- максимальный размер
    * max_count -- максимальное число файлов

    Методы класса:
    * get_lock_file_path -- возвращает полный путь к файлу блокировки

    * set_lock -- блокирует корзину
    * unset_lock -- разблокирует корзину
    * lock -- возвращает менеджер контента для блокировки

    * dryrun -- возвращает менеджер контента для dryrun режима

    * get_size -- текущий размер корзины
    * get_count -- текущее число файлов в корзине

    * to_internal -- преобразует путь во внутренний путь корзины
    * to_external -- преобразует путь во внешний путь корзины

    * add -- добавляет элемент в корзину
    * restore -- востанавливает элемент из корзины
    * remove -- удаляет элемент навсегда

    Не следует использовать следущие функции вне класса
    во время блокировки:
    * add_file -- добавляет файл в корзину
    * add_dir -- добавляет папку в корзину
    * restore_file -- востанавливает файл из корзины
    * restore_dir -- востанавливает папку из корзины

    Блокировка ускоряет вычисление размера корзины
    и количество файлов в ней.

    При превышение ограничений на корзину
    возбуждается LimitExcessException

    """

    def __init__(self,
                 directory=DEFAULT_DIRECTORY,
                 lock_file=DEFAULT_LOCK_FILE,
                 max_size=DEFAULT_MAX_SIZE,
                 max_count=DEFAULT_MAX_COUNT,
                 dryrun=DEFAULT_DRYRUN
                ):
        """Создает с укзанными парметрами.

        Непозиционные аргументы:
        * directory -- папка корзины
        * lock_file -- путь к файлу блокировки относительно корзины
        * max_size -- максимальный суммарный размер корзины
        * max_count -- максимальное количество файлов корзины

        """
        self.configurate(directory, lock_file, max_size, max_count)

        self._locked = False

        # Значения известны только во время блокировки
        self._size = None
        self._count = None

    def configurate(self,
                    directory=DEFAULT_DIRECTORY,
                    lock_file=DEFAULT_LOCK_FILE,
                    max_size=DEFAULT_MAX_SIZE,
                    max_count=DEFAULT_MAX_COUNT,
                    dryrun=DEFAULT_DRYRUN
                   ):
        """Обновляет поля корзины.

        Непозиционные аргументы:
        * directory -- папка корзины
        * lock_file -- путь к файлу блокировки относительно корзины
        * max_size -- максимальный суммарный размер корзины
        * max_count -- максимальное количество файлов корзины

        """
        self.directory = directory
        self.lock_file = lock_file

        self.max_size = max_size
        self.max_count = max_count

        self.dryrun = dryrun

    def get_size(self):
        """Возвращает размер корзины.

        Если корзина заблокированна, возвращает кэшированное значение.
        """
        if self._locked:
            return self._size
        else:
            lock_file = self.get_lock_file_path()
            size = utils.get_files_size(self.directory)

            # Файл блокировки также содержиться в корзине
            size -= utils.get_files_size(lock_file)

            return size

    def get_count(self):
        """Возвращает количество файлов в корзине.

        Если корзина заблокированна, возвращает кэшированное значение.

        """
        if self._locked:
            return self._count
        else:
            lock_file = self.get_lock_file_path()
            count = utils.get_files_count(self.directory)

            # Файл блокировки также содержиться в корзине
            count -= utils.get_files_count(lock_file)

            return count

    def get_lock_file_path(self):
        """Возвращает путь к файлу блокировки.
        """
        trash_dir = utils.get_absolute_path(self.directory)
        return os.path.join(trash_dir, self.lock_file)

    def set_lock(self):
        """Производит блокировку корзины.

        В папке с корзиной создает файл блокировки.

        Кэшируется текущий размер корзины и количество файлов.

        """
        trash_dir = utils.get_absolute_path(self.directory)
        if not os.path.exists(trash_dir):
            os.makedirs(trash_dir)

        lock_file = self.get_lock_file_path()

        if os.path.exists(lock_file):
            raise IOError("Lock file already exists.")

        with open(lock_file, "w"):
            pass

        self._count = self.get_count()
        self._size = self.get_size()

        self._locked = True

    def unset_lock(self):
        """Производит разблокировку корзины.

        Удаляет файл блокировки.
        Очищает все кэшированные ранее значения.

        """
        os.remove(self.get_lock_file_path())

        # Значения известны только во время блокировки
        self._size = None
        self._count = None

        self._locked = False

    def is_locked(self):
        """Возвращает, заблокированна ли корзина.
        """
        return self._locked

    def lock(self):
        """Блокировка через менеджер контента.
        """
        return TrashLocker(self)

    def dryrun_mode(self):
        """Временное включение dryrun через менеджер контента.
        """
        return Dryruner(self)

    def to_internal(self, path):
        """Возвращает путь файла, переподвешанного к корзине.

        Позиционные аргументы:
        path -- исходный путь

        Определяется как путь к файлу, подвешанный к
        папке с корзиной.

        Протокол шифруется как последовательность кодов символов.

        """
        trash_dir = utils.get_absolute_path(self.directory)
        path_full = utils.get_absolute_path(path)

        splitted_path = utils.split_path(path_full)

        protocol = splitted_path[0]
        protocol_code = ' '.join([str(ord(char)) for char in protocol])
        splitted_path[0] = protocol_code

        int_path = os.path.join(trash_dir, *splitted_path)
        return int_path

    def to_external(self, path):
        """Возвращает первоначальный путь файла.

        Позиционные аргументы:
        path -- исходный путь

        Папка с корзином считается корнем.
        Протокол дешефруется из последовательности кодов символов.

        """
        trash_dir = utils.get_absolute_path(self.directory)
        full_path = utils.get_absolute_path(path)

        if os.path.commonprefix((full_path, trash_dir)) != trash_dir:
            error_fmt = "{path} is'n trash area({trash_dir})."
            error_msg = error_fmt.format(path=path, trash_dir=trash_dir)
            raise ValueError(error_msg)

        rel_path = os.path.relpath(full_path, trash_dir)
        splitted_path = utils.split_path(rel_path)[1:]

        protocol_code = splitted_path[0]
        protocol = ''.join(chr(int(s)) for s in protocol_code.split(' '))
        splitted_path[0] = protocol
        ext_path = os.path.join(*splitted_path)

        return ext_path

    def get_file_time_list(self):
        """Возвращает список всех файлов в корзине.

        Список сотоит из кортежей (путь, время удаления).

        Список сортируется по дате удаления.

        """
        trash_dir = utils.get_absolute_path(self.directory)

        root_list = os.listdir(trash_dir)
        root_list_full = [os.path.join(trash_dir, path)
                          for path in root_list]
        trash_protocols = (d for d in root_list_full if os.path.isdir(d))
        files = []
        for protocol_path in trash_protocols:
            for dirpath, _, filenames in os.walk(protocol_path):
                files.extend([os.path.join(dirpath, f) for f in filenames])

        files_ext = [self.to_external(f) for f in files]
        file_time_list = [stamp.split_stamp(f) for f in files_ext]

        file_time_list.sort(key=lambda (file_name, vers): vers)

        return file_time_list

    def add_file(self, file_name):
        """Перемещает файл в корзину.

        Возвращает колич. удаленх фалов, их размер, список путей.

        Не следует использовать эту функцию вне класса
        во время блокировки.

        Позиционные аргументы:
        file_name -- исходный путь к файлу

        Добаление вроизовдиться путем пермещение файла.
        Путь файла переподвешивается относительно папки корзины.
        Протокол шивруется как последовательность символов.
        К файлу добавляется штамп текущего времени UTC.

        """
        old_path = utils.get_absolute_path(file_name)
        new_path = self.to_internal(old_path)

        count = 1
        size = utils.get_files_size(old_path)

        now = datetime.datetime.now()
        full_new_path = stamp.add_stamp(new_path, now)
        debug_fmt = "Moving file {old_path} to {new_path}"
        debug_msg = debug_fmt.format(old_path=old_path, new_path=full_new_path)
        logging.debug(debug_msg)

        if not self.dryrun:
            if not os.path.exists(os.path.dirname(full_new_path)):
                os.makedirs(os.path.dirname(full_new_path))
            os.rename(old_path, full_new_path)

        return count, size, [old_path]

    def add_dir(self, dir_name):
        """Премещает папку в корзину.

        Возвращает колич. удаленх объектов, их размер, список путей.

        Не следует использовать эту функцию вне класса
        во время блокировки.

        Позиционные аргументы:
        dir_name -- исходный путь к папке

        Перемещение происходит рекурсивно.
        Для этого в корзине создаются все недостающие папки и
        перемещаются файлы.

        """
        old_path = utils.get_absolute_path(dir_name)

        count = 0
        size = 0
        result_list = [old_path]

        if os.path.ismount(old_path):
            raise IOError("Can't remove mount point.")

        new_path = self.to_internal(old_path)

        if not os.path.exists(new_path):
            debug_msg = "Make dir {directory} ".format(directory=new_path)
            logging.debug(debug_msg)
            if not self.dryrun:
                os.makedirs(new_path)

        for element in os.listdir(old_path):
            element_path = os.path.join(old_path, element)
            isdir = os.path.isdir(element_path)
            if  isdir:
                delta_count, delta_size, added = self.add_dir(element_path)
            else:
                delta_count, delta_size, added = self.add_file(element_path)
            count += delta_count
            size += delta_size
            result_list.extend(added)

        if not self.dryrun:
            os.rmdir(old_path)

        return count, size, result_list

    def restore_file(self, file_name, how_old=0):
        """Востанавливает файл из корзины.

        Возвращает колич. вост. объектов, их размер, список путей.

        Позиционные аргументы:
        file_name -- путь к файлу в корзине

        Непозиционные аргументы:files
        how_old -- версия файла в порядке устарения даты удаления.
                   По умолчанию: 0 (последняя версия)

        Не следует использовать эту функцию вне класса
        во время блокировки.

        Из файла удаляется штамп времени.
        Файл переповешивается из папке корзины в корень.

        """
        new_path = utils.get_absolute_path(file_name)
        old_path = self.to_internal(new_path)
        old_path_full = stamp.get_version(old_path, how_old)

        count = 1
        size = utils.get_files_size(old_path_full)

        if os.path.exists(new_path):
            os.remove(new_path)

        if not os.path.exists(os.path.dirname(new_path)):
            debug_msg = "Make dir {directory} ".format(directory=new_path)
            logging.debug(debug_msg)
            os.makedirs(os.path.dirname(new_path))

        debug_fmt = "Moving file {old_path} to {new_path}"
        debug_msg = debug_fmt.format(old_path=old_path, new_path=new_path)
        logging.debug(debug_msg)

        if not self.dryrun:
            os.rename(old_path_full, new_path)

        if not self.dryrun:
            if utils.is_empty(os.path.dirname(old_path_full)):
                os.rmdir(os.path.dirname(old_path_full))

        return count, size, [new_path]

    def restore_dir(self, dir_name, how_old=0):
        """Востанавливает папку из корзины.

        Возвращает колич. вост. объектов, их размер, список путей.

        Не следует использовать эту функцию вне класса
        во время блокировки.

        Позиционные аргументы:
        path -- исходный путь к элементу

        Непозиционные аргументы:
        how_old -- версия файла в порядке устарения даты удаления.
                   По умолчанию: 0 (последняя версия)

        Перемещение происходит рекурсивно.
        Для этого в создаются все недостающие папки и
        востанавливаются файлы.

        """
        new_path = utils.get_absolute_path(dir_name)
        old_path = self.to_internal(new_path)

        count = 0
        size = 0
        result_list = [new_path]

        if not os.path.exists(new_path):
            debug_msg = "Make dir {directory} ".format(directory=new_path)
            logging.debug(debug_msg)
            if not self.dryrun:
                os.makedirs(new_path)

        mask = os.path.join(new_path, "*")
        elements = self.search(mask)
        for path in elements:
            is_dir = os.path.exists(self.to_internal(path))
            if is_dir:
                dcount, dsize, restored = self.restore_dir(path,
                                                           how_old=how_old)
            else:
                dcount, dsize, restored = self.restore_file(path,
                                                            how_old=how_old)
            count += dcount
            size += dsize
            result_list.extend(restored)

        exist_and_empty = os.path.exists(old_path) and utils.is_empty(old_path) 
        if exist_and_empty and not self.dryrun:
            os.rmdir(old_path)

        return count, size, result_list

    def add(self, path):
        """Добавляет элемент в корзину.

        Возвращает количестов удаленных файлов, их размер,
        список удаленных объектов.

        Позиционные аргументы:
        path -- исходный путь к элементу

        Перед выполнением операции происходит проверка на
        превышения лимита корзины.

        Эффективно пересчитывает новый размер корзины и
        количество файлов в ней.

        При превышение ограничений на корзину
        возбуждается LimitExcessException

        """
        delta_size = utils.get_files_size(path)
        delta_count = utils.get_files_count(path)
        new_size = self.get_size() + delta_size
        new_count = self.get_count() + delta_count

        trash_dir = utils.get_absolute_path(self.directory)
        if os.path.commonprefix((path, trash_dir)) == trash_dir:
            raise ValueError("You can't remove anythin from trash.")

        if new_size > self.max_size:
            raise LimitExcessException("Size limit excess.")
        if new_count > self.max_count:
            raise LimitExcessException("Files count limit excess.")

        if os.path.isdir(path):
            _, _, added = self.add_dir(path)
        else:
            _, _, added = self.add_file(path)

        if self.is_locked() and not self.dryrun:
            self._size = new_size
            self._count = new_count

        return delta_count, delta_size, added

    def restore(self, path, how_old=0):
        """Востанавливает элемент из корзины.

        Возвращает количестов востановленных файлов, их размер,
        список востановленных объектов.

        Работа возможна только во время блокировки корзины.

        Позиционные аргументы:
        path -- путь к элементу в корзине

        Непозиционные аргументы:
        how_old -- версия файла в порядке устарения даты удаления.
                   По умолчанию: 0 (последняя версия)

        Эффективно пересчитывает новый размер корзины и
        количество файлов в ней.

        """
        new_path = utils.get_absolute_path(path)
        old_path = self.to_internal(new_path)

        if not os.path.isdir(old_path):
            old_path = stamp.get_version(old_path, how_old)

        if os.path.isdir(old_path):
            dcount, dsize, restored = self.restore_dir(path,
                                                       how_old=how_old)
        else:
            dcount, dsize, restored = self.restore_file(path,
                                                        how_old=how_old)

        if self.is_locked() and not self.dryrun:
            self._size -= dsize
            self._count -= dcount

        return dcount, dsize, restored

    def remove(self, path, how_old=-1):
        """Удаляет элемент из корзины навсегда.

        Возвращает количестов очищенных файлов и их размер,
        список очищенных объектов.

        Работа возможна только во время блокировки корзины.

        Позиционные аргументы:
        path -- путь к элементу в корзине

        Непозиционные аргументы:
        how_old -- версия файла в порядке устарения даты удаления.
                   По умолчанию: -1 (все версии)

        Эффективно пересчитывает новый размер корзины и
        количество файлов в ней.

        """
        removed = []

        path = self.to_internal(path)

        delta_count = 0
        delta_size = 0

        if not os.path.isdir(path):
            if how_old >= 0:
                full_path = stamp.get_version(path, how_old)
                delta_count += 1
                delta_size += utils.get_files_size(full_path)
                removed.append(full_path)
                if not self.dryrun:
                    os.remove(full_path)
            else:
                for vers in stamp.get_versions_list(path):
                    full_path = stamp.add_stamp(path, vers)
                    delta_count += 1
                    delta_size += utils.get_files_size(full_path)
                    removed.append(full_path)
                    if not self.dryrun:
                        os.remove(full_path)
        else:
            for dirpath, _, filenames in os.walk(path, topdown=False):
                removed.append(dirpath)
                for element in filenames:
                    full_path = os.path.join(dirpath, element)
                    delta_count += 1
                    delta_size += utils.get_files_size(full_path)
                    removed.append(full_path)
                    if not self.dryrun:
                        os.remove(full_path)
                if not self.dryrun:
                    os.rmdir(dirpath)

        if self.is_locked() and not self.dryrun:
            self._size -= delta_size
            self._count -= delta_count

        removed_stplited = [stamp.split_stamp(f) for f in removed]
        removed_stplited_ext = [(self.to_external(f), d) 
                                for f, d in removed_stplited]
        return delta_count, delta_size, removed_stplited_ext

    def search(self, path_mask, recursive=False, find_all=False):
        """Поиск в корзине по маске. Возвращает словарь с версиями.

        Маска задается в формате Unix filename pattern.
        Путь задается относительно

        Позиионные аргументы:
        path_mask -- маска

        Непозиционные аргументы:
        recursive -- производить лиpath поиск в подпапках.
        find_all -- углублять в подпапки,
                если они соответствуют маске (по-умолчанию False)

        """
        path_mask = self.to_internal(path_mask)
        directory, mask = os.path.split(path_mask)

        if not os.path.exists(directory):
            return {}
        file_mask = stamp.extend_mask_by_stamp(mask)
        files = utils.search(directory, mask, file_mask,
                             recursive=recursive, find_all=find_all)
        files = [self.to_external(f) for f in files]
        files_versions = stamp.files_to_file_dict(files)

        return files_versions

