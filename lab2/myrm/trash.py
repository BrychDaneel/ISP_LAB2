# -*- coding: utf-8 -*-


"""Содержит класс Tash, управляющий содержимым корзины.

Вспомогательный класс:
    * TrashLocker - для блокировки корзины через менеджер контента.

Вспомогательный декоратор:
    * need_lock_decodator -- возбуждает исключение если корзина
            не заблокированна.

Исключения модуля:
    LimitExcessException -- выбрасывается при превышении лимита
"""


import os
import datetime
import logging
import myrm.utils as utils
import myrm.stamp as stamp


class LimitExcessException(Exception):
    """Возбуждается при превышения пользовательского лимита.
    """
    pass


class TrashLocker(object):
    """Используется для блокировки корзины через менеджер контента.

    Конструктор принимает в себя класс корзины.
    """

    def __init__(self, trash):
        """Создает объект для указанной корзины.
        """
        self.trash = trash
        self._was_locked = trash.is_locked()

    def __enter__(self):
        """Блокирует корзину.
        """
        if not self._was_locked:
            self.trash.set_lock()

    def __exit__(self, exp_type, exp_value, traceback):
        """Разблокирует корзину.
        """
        if not self._was_locked:
            self.trash.unset_lock()


class Trash(object):

    """Класс управляет содержимым корзины.

    Поля класса:
    * cfg -- объект конфигурации,
             содержащий информацию по работе с корзиной
    * locked -- заблокированна ли корзина в текущий момент

    Следующие поля используются только на протяжении блокировки:
    * trash_dir -- путь к папке с корзиной
    * lock_file -- имя файла блокировки
    * trash_ size -- текущий размер корзины
    * files_count -- текущее число файлов в корзине

    Методы класса:
    * lock_file_path -- возвращает полный путь к файлу блокировки
    * lock -- блокирует корзину
    * unlock -- разблокирует корзину

    * to_internal -- преобразует путь во внутренний путь корзины
    * to_external -- преобразует путь во внешний путь корзины

    Следующие методы возможны во время блокировки:
    * add -- добавляет элемент в корзину
    * rs -- востанавливает элемент из корзины
    * rm -- удаляет элемент навсегда

    Следующие методы не рекомендуется использовать вне класса:
    * add_file -- добавляет файл в корзину
    * add_dir -- добавляет папку в корзину
    * restore_file -- востанавливает файл из корзины
    * restore_dir -- востанавливает папку из корзины
    """

    def __init__(self, **kargs):
        """Создает объект корзины по указанному объекту конфигурации.

        Непозиционные аргументы:
        * directory -- папка корзины
        * lock_file -- путь к файлу блокировки относительно корзины
        * max_size -- максимальный суммарный размер корзины
        * max_count -- максимальное количество файлов корзины

        """
        self.configurate(**kargs)
        self._locked = False

        # Значения известны только во время блокировки
        self._size = None
        self._count = None

    def configurate(self, directory="~/.trash", lock_file="lock",
                    max_size=1024*1024*1024, max_count=10*1000*1000):
        """
        """
        self.directory = directory
        self.lock_file = lock_file

        self.max_size = max_size
        self.max_count = max_count

    def get_size(self):
        """
        """
        if self._locked:
            return self._size
        else:
            lock_file = self.get_lock_file_path()
            size = utils.files_size(self.directory)

            # Файл блокировки также содержиться в корзине
            size -= utils.files_size(lock_file)

            return size

    def get_count(self):
        """
        """
        if self._locked:
            return self._count
        else:
            lock_file = self.get_lock_file_path()
            count = utils.files_count(self.directory)

            # Файл блокировки также содержиться в корзине
            count -= utils.files_count(lock_file)

            return count

    def get_lock_file_path(self):
        """Возвращает путь к файлу блокировки.
        """
        trash_dir = utils.absolute_path(self.directory)
        return os.path.join(trash_dir, self.lock_file)

    def set_lock(self):
        """Производит блокировку корзины.

        Сохраняет текущее значения пути к корзине и
        имя файла блокировки из объекта конфигурации.

        В папке с корзиной создает файл блокировки.

        Рассчитывает текущий размер корзины и количество файлов.

        """
        trash_dir = utils.absolute_path(self.directory)
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

        Очищает все сохранённые ранее значения.
        Удаляет файл блокировки.

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
        """Блокировка через менеджер контента
        """
        return TrashLocker(self)

    def to_internal(self, path):
        """Возвращает путь файла, переподвешанного к корзине.

        Позиционные аргументы:
        path -- исходный путь

        Определяется как путь к файлу, подвешанный к
        папке с корзиной.

        Протокол шифруется как последовательность кодов символов.

        """
        trash_dir = utils.absolute_path(self.directory)
        path_full = utils.absolute_path(path)

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
        trash_dir = utils.absolute_path(self.directory)
        full_path = utils.absolute_path(path)

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
        trash_dir = utils.absolute_path(self.directory)

        root_list = os.listdir(trash_dir)
        root_list_full = [os.path.join(trash_dir, path)
                          for path in root_list]
        trash_protocols = (d for d in root_list_full if os.path.isdir(d))
        files = []
        for protocol_path in trash_protocols:
            for dirpath, dirnames, filenames in os.walk(protocol_path):
                files.extend([os.path.join(dirpath, f) for f in filenames])

        files_ext = [self.to_external(f) for f in files]
        file_time_list = [stamp.split_stamp(f) for f in files_ext]

        file_time_list.sort(key=lambda (file_name, vers): vers)

        return file_time_list

    def add_file(self, file_name):
        """Перемещает файл в корзину.

        Не следует использовать эту функцию вне класса
        во время блокировки.

        Позиционные аргументы:
        file_name -- исходный путь к файлу

        Добаление вроизовдиться путем пермещение файла.
        Путь файла переподвешивается относительно папки корзины.
        Протокол шивруется как последовательность символов.
        К файлу добавляется штамп текущего времени UTC.

        """
        old_path = utils.absolute_path(file_name)
        new_path = self.to_internal(old_path)
        now = datetime.datetime.now()
        full_new_path = stamp.add_stamp(new_path, now)
        debug_fmt = "Moving file {old_path} to {new_path}"
        debug_msg = debug_fmt.format(old_path=old_path, new_path=full_new_path)
        logging.debug(debug_msg)

        if not os.path.exists(os.path.dirname(full_new_path)):
            os.makedirs(os.path.dirname(full_new_path))
        os.rename(old_path, full_new_path)

    def add_dir(self, dir_name):
        """Премещает папку в корзину.

        Не следует использовать эту функцию вне класса
        во время блокировки.

        Позиционные аргументы:
        dir_name -- исходный путь к папке

        Перемещение происходит рекурсивно.
        Для этого в корзине создаются все недостающие папки и
        перемещаются файлы.

        """
        old_path = utils.absolute_path(dir_name)

        if os.path.ismount(old_path):
            raise IOError("Can't remove mount point.")

        new_path = self.to_internal(old_path)

        if not os.path.exists(new_path):
            debug_msg = "Make dir {directory} ".format(directory=new_path)
            logging.debug(debug_msg)
            os.makedirs(new_path)

        for element in os.listdir(old_path):
            element_path = os.path.join(old_path, element)
            isdir = os.path.isdir(element_path)
            if  isdir:
                self.add_dir(element_path)
            else:
                self.add_file(element_path)

        os.rmdir(old_path)

    def restore_file(self, file_name, how_old=0):
        """Перемещает файл из корзины в первоначалое местоположение.

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
        new_path = utils.absolute_path(file_name)
        old_path = self.to_internal(new_path)
        old_path_full = stamp.get_version(old_path, how_old)

        if os.path.exists(new_path):
            os.remove(new_path)

        if not os.path.exists(os.path.dirname(new_path)):
            debug_msg = "Make dir {directory} ".format(directory=new_path)
            logging.debug(debug_msg)
            os.makedirs(os.path.dirname(new_path))

        debug_fmt = "Moving file {old_path} to {new_path}"
        debug_msg = debug_fmt.format(old_path=old_path, new_path=new_path)
        logging.debug(debug_msg)
        os.rename(old_path_full, new_path)

        if os.listdir(os.path.dirname(old_path)) == 0:
            os.rmdir(os.path.dirname(old_path))

    def restore_dir(self, dir_name, how_old=0):
        """Премешает папку из корзины обратно.

        Не следует использовать эту функцию вне класса
        во время блокировки.

        Позиционные аргументы:
        dir_name -- путь к папке в корзине

        Непозиционные аргументы:
        how_old -- версия файла в порядке устарения даты удаления.
                   По умолчанию: 0 (последняя версия)

        Перемещение происходит рекурсивно.
        Для этого в создаются все недостающие папки и
        востанавливаются файлы.

        """
        new_path = utils.absolute_path(dir_name)
        old_path = self.to_internal(new_path)

        if not os.path.exists(new_path):
            debug_msg = "Make dir {directory} ".format(directory=new_path)
            logging.debug(debug_msg)
            os.makedirs(new_path)

        mask = os.path.join(new_path, "*")
        elements = self.search(mask)
        for path in elements:
            is_dir = os.path.exists(self.to_internal(path))
            if is_dir:
                self.restore_dir(path, how_old=how_old)
            else:
                self.restore_file(path, how_old=how_old)

        if len(os.listdir(old_path)) == 0:
            os.rmdir(old_path)

    def add(self, path):
        """Добавляет элемент в корзину.

        Возвращает количестов удаленных файлов и их размер.

        Работа возможна только во время блокировки корзины.

        Позиционные аргументы:
        dir_name -- исходный путь к элементу

        Перед выполнением операции происходит проверка на
        превышения лимита корзины.

        Эффективно пересчитывает новый размер корзины и
        количество файлов в ней.

        """
        delta_size = utils.files_size(path)
        delta_count = utils.files_count(path)
        new_size = self.get_size() + delta_size
        new_count = self.get_count() + delta_count

        trash_dir = utils.absolute_path(self.directory)
        if os.path.commonprefix((path, trash_dir)) == trash_dir:
            raise ValueError("You can't remove anythin from trash.")

        if new_size > self.max_size:
            raise LimitExcessException("Size limit excess.")
        if new_count > self.max_count:
            raise LimitExcessException("Files count limit excess.")

        if os.path.isdir(path):
            self.add_dir(path)
        else:
            self.add_file(path)

        if self.is_locked():
            self._size = new_size
            self._count = new_count

        return delta_count, delta_size

    def restore(self, path, how_old=0):
        """Востанавливает элемент из корзины.

        Возвращает количестов востановленных файлов и их размер.

        Работа возможна только во время блокировки корзины.

        Позиционные аргументы:
        dir_name -- путь к элементу в корзине

        Непозиционные аргументы:
        how_old -- версия файла в порядке устарения даты удаления.
                   По умолчанию: 0 (последняя версия)

        Эффективно пересчитывает новый размер корзины и
        количество файлов в ней.

        """
        new_path = utils.absolute_path(path)
        old_path = self.to_internal(new_path)

        if not os.path.isdir(old_path):
            old_path = stamp.get_version(old_path, how_old)
        delta_size = utils.files_size(old_path)
        delta_count = utils.files_count(old_path)

        if os.path.isdir(old_path):
            self.restore_dir(path, how_old=how_old)
        else:
            self.restore_file(path, how_old=how_old)

        if self.is_locked():
            self._size -= delta_size
            self._count -= delta_count

        return delta_count, delta_size

    def remove(self, path, how_old=-1):
        """Удаляет элемент из корзины навсегда.

        Возвращает количестов очищенных файлов и их размер.

        Работа возможна только во время блокировки корзины.

        Позиционные аргументы:
        dir_name -- путь к элементу в корзине

        Непозиционные аргументы:
        how_old -- версия файла в порядке устарения даты удаления.
                   По умолчанию: -1 (все версии)

        Эффективно пересчитывает новый размер корзины и
        количество файлов в ней.

        """
        path = self.to_internal(path)

        delta_size = 0
        delta_count = 0

        if not os.path.isdir(path):
            if how_old >= 0:
                full_path = stamp.get_version(path, how_old)
                delta_size = delta_size + utils.files_size(full_path)
                delta_count = delta_count + utils.files_count(full_path)
                os.remove(full_path)
            else:
                for vers in stamp.get_versions_list(path):
                    full_path = stamp.add_stamp(path, vers)
                    delta_size = delta_size + utils.files_size(full_path)
                    delta_count = delta_count + utils.files_count(full_path)
                    os.remove(full_path)
        else:
            delta_size = delta_size + utils.files_size(path)
            delta_count = delta_count + utils.files_count(path)

            for dirpath, dirnames, filenames in os.walk(path, topdown=False):
                for element in filenames:
                    os.remove(os.path.join(dirpath, element))
                os.rmdir(dirpath)

        if self.is_locked():
            self._size = self._size - delta_size
            self._count = self._count - delta_count

        return delta_count, delta_size

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

