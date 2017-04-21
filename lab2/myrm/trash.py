# -*- coding: utf-8 -*-


"""Содержит класс Tash, управляющий содержимым корзины.

Вспомогательный декоратор:
    * need_lock_decodator -- возбуждает исключение если корзина
            не заблокированна.
"""


import os
import datetime
import logging
import myrm.utils as utils
import myrm.stamp as stamp


def _need_lock_decodator(func):
    """Возбуждает исключение если корзина не заблокированна.

    Работает только на методах Trash.

    """
    def result_func(self, *args, **kargs):
        if self.locked:
            return func(self, *args, **kargs)
        else:
            assert False
    return result_func


class Trash(object):

    """Класс управляет содержимым корзины.

    Поля класса:
    * cfg -- объект конфигурации,
             содержащий информацию по работе с корзиной
    * locked -- заблокированна ли корзина в текущий момент

    Следующие поля используются только на протяжении блокировки:
    * thash_dir -- путь к папке с корзиной
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
    * rs_file -- востанавливает файл из корзины
    * rs_dir -- востанавливает папку из корзины
    """

    def __init__(self, cfg):
        """Создает объект корзины по указанному объекту конфигурации.
        """
        self.cfg = cfg

        # Значения известны только во время блокировки
        self.thash_dir = None
        self.lock_file = None
        self.trash_size = None
        self.files_count = None

        self.locked = False

    def lock_file_path(self):
        """Возвращает путь к файлу блокировки.
        """
        thash_dir = self.cfg["trash"]["dir"]
        lock_file = self.cfg["trash"]["lockfile"]
        return os.path.join(thash_dir, lock_file)

    def lock(self):
        """Производит блокировку корзины.

        Сохраняет текущее значения пути к корзине и
        имя файла блокировки из объекта конфигурации.

        В папке с корзиной создает файл блокировки.

        Рассчитывает текущий размер корзины и количество файлов.

        """
        thash_dir = self.cfg["trash"]["dir"]
        if not os.path.exists(thash_dir):
            os.makedirs(thash_dir)

        lock_file = self.lock_file_path()
        assert not os.path.exists(lock_file)
        open(lock_file, "w").close()
        self.thash_dir = thash_dir

        # Файл блокировки также содержиться в корзине
        self.files_count = utils.files_count(thash_dir) - 1

        self.trash_size = utils.files_size(thash_dir)
        self.trash_size -= utils.files_size(lock_file)
        self.lock_file = lock_file
        self.locked = True

    def unlock(self):
        """Производит разблокировку корзины.

        Очищает все сохранённые ранее значения.
        Удаляет файл блокировки.

        """
        os.remove(self.lock_file)

        # Значения известны только во время блокировки
        self.thash_dir = None
        self.lock_file = None
        self.trash_size = None
        self.files_count = None

        self.locked = False

    def to_internal(self, path):
        """Возвращает путь файла, переподвешанного к корзине.

        Позиционные аргументы:
        path -- исходный путь

        Определяется как путь к файлу, подвешанный к
        папке с корзиной.

        Протокол шифруется как последовательность кодов символов.

        """
        thash_dir = self.cfg["trash"]["dir"]

        path = os.path.abspath(path)
        splitted_path = utils.split_path(path)

        protocol = splitted_path[0]
        protocol_code = ' '.join([str(ord(char)) for char in protocol])
        splitted_path[0] = protocol_code

        new_path = os.path.join(thash_dir, splitted_path)
        return new_path

    def to_external(self, path):
        """Возвращает первоначальный путь файла.

        Позиционные аргументы:
        path -- исходный путь

        Папка с корзином считается корнем.
        Протокол дешефруется из последовательности кодов символов.

        """
        thash_dir = self.cfg["trash"]["dir"]
        path = os.path.abspath(path)
        path = os.path.relpath(path, thash_dir)
        splitted_path = utils.split_path(path)[1:]
        protocol_code = splitted_path[0]
        protocol = ''.join(chr(int(s)) for s in protocol_code.split(' '))
        splitted_path[0] = protocol
        path = os.path.join(*splitted_path)

        path = os.path.relpath(path)
        return path

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
        old_name = os.path.abspath(file_name)
        new_name = self.to_internal(old_name)
        now = datetime.datetime.utcnow()
        new_name = stamp.add_stamp(new_name, now)
        logging.debug("Moving file {old_name} to {new_name}",
                      old_name=old_name, new_name=new_name)
        if not os.path.exists(os.path.dirname(new_name)):
            os.makedirs(os.path.dirname(new_name))
        os.rename(old_name, new_name)

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
        old_name = os.path.abspath(dir_name)
        new_name = self.to_internal(old_name)

        if not os.path.exists(new_name):
            logging.debug("Make dir {directory} ", directory=new_name)
            os.makedirs(new_name)

        for element in os.listdir(dir_name):
            path = os.path.join(dir_name, element)
            isdir = os.path.isdir(path)
            if  isdir:
                self.add_dir(path)
            else:
                self.add_file(path)
        os.rmdir(old_name)

    def rs_file(self, file_name, how_old=0):
        """Перемещает файл из корзины в первоначалое местоположение.

        Позиционные аргументы:
        file_name -- путь к файлу в корзине

        Непозиционные аргументы:
        how_old -- версия файла в порядке устарения даты удаления.
                   По умолчанию: 0 (последняя версия)

        Не следует использовать эту функцию вне класса
        во время блокировки.

        Из файла удаляется штамп времени.
        Файл переповешивается из папке корзины в корень.

        """
        old_name = stamp.get_version(file_name, how_old)
        old_name = os.path.abspath(old_name)
        new_name = self.to_external(old_name)

        if not os.path.exists(os.path.dirname(new_name)):
            logging.debug("Make dir {directory} ", directory=new_name)
            os.makedirs(os.path.dirname(new_name))

        logging.debug("Moving file {old_name} to {new_name}",
                      old_name=old_name, new_name=new_name)
        os.rename(old_name, new_name)

    def rs_dir(self, dir_name, how_old=0):
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
        old_name = os.path.abspath(dir_name)
        new_name = self.to_external(old_name)

        if not os.path.exists(new_name):
            logging.debug("Make dir {directory} ", directory=new_name)
            os.makedirs(new_name)

        for element in os.listdir(dir_name):
            path = os.path.join(dir_name, element)
            isdir = os.path.isdir(path)
            if  isdir:
                self.rs_dir(path, how_old=how_old)
            else:
                self.rs_file(path, how_old=how_old)

    @_need_lock_decodator
    def add(self, path):
        """Добавляет элемент в корзину.

        Работа возможна только во время блокировки корзины.

        Позиционные аргументы:
        dir_name -- исходный путь к элементу

        Перед выполнением операции происходит проверка на
        превышения лимита корзины.

        Эффективно пересчитывает новый размер корзины и
        количество файлов в ней.

        """
        new_size = self.trash_size + utils.files_size(path)
        new_count = self.files_count + utils.files_count(path)

        assert new_size <= self.cfg["trash"]["max"]["size"]
        assert new_count <= self.cfg["trash"]["max"]["count"]

        if os.path.isdir(path):
            self.add_dir(path)
        else:
            self.add_file(path)

        self.trash_size = new_size
        self.files_count = new_count
        return True

    @_need_lock_decodator
    def restore(self, path, how_old=0):
        """Добавляет элемент в корзину.

        Работа возможна только во время блокировки корзины.

        Позиционные аргументы:
        dir_name -- путь к элементу в корзине

        Непозиционные аргументы:
        how_old -- версия файла в порядке устарения даты удаления.
                   По умолчанию: 0 (последняя версия)

        Эффективно пересчитывает новый размер корзины и
        количество файлов в ней.

        """
        new_size = self.trash_size + utils.files_size(path)
        new_count = self.files_count + utils.files_count(path)

        if os.path.isdir(path):
            self.rs_dir(path, how_old=how_old)
        else:
            self.rs_file(path, how_old=how_old)

        self.trash_size = new_size
        self.files_count = new_count

        return True

    @_need_lock_decodator
    def remove(self, path, how_old=-1):
        """Удаляет элемент из корзины навсегда.

        Работа возможна только во время блокировки корзины.

        Позиционные аргументы:
        dir_name -- путь к элементу в корзине

        Непозиционные аргументы:
        how_old -- версия файла в порядке устарения даты удаления.
                   По умолчанию: -1 (все версии)

        Эффективно пересчитывает новый размер корзины и
        количество файлов в ней.

        """
        new_size = self.trash_size - utils.files_size(path)
        new_count = self.files_count - utils.files_count(path)

        if not os.path.isdir(path):
            if how_old >= 0:
                os.remove(stamp.get_version(path, how_old))
            else:
                for vers in stamp.get_versions_list(path):
                    os.remove(stamp.add_stamp(path, vers))
        else:
            for dirpath, dirnames, filenames in os.walk(path, topdown=True):
                for element in filenames:
                    os.remove(element)
                os.rmdir(dirpath)

        self.trash_size = new_size
        self.files_count = new_count
        return True

