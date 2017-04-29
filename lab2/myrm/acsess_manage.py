# -*- coding: utf-8 -*-


"""Содержит класс AcsessManager.

Экспортируемые классы:
    * AcsessManager -- управляет доступом к операциям над корзиной,
                    основываясь на информации из объекта конфигурации.
                    Производит логирование операций.

Экспортируемые функции:
* ask -- отправляет запрос в консоль и считывает ответ.

"""


import logging


def ask(operation, path):
    """Отправляет запрос в консоль. Возвращает ответ пользователя.

    Позицонные аргументы:
    operation -- название операции над объектом
    path -- путь объекта

    Формат запроса:
    "Do you want to {operation} '{path}'? [Y/n]"

    Возвращает True, если
    * Пользователь ввел пустую строку.
    * Пользователь ввел 'У' или 'y'.

    """
    ask_fmt = "Do you want to {operation} '{path}'? [Y/n]"
    ask_string = ask_fmt.format(operation=operation, path=path)
    user_ans = raw_input(ask_string)
    user_ans = user_ans.lower()
    yes = not user_ans or user_ans == 'y'
    return yes


class AcsessManager(object):
    """Управляет доступом к операциям над корзиной.

    Доступ осуществляется на информации из объекта конфигурации.
    Объект конфигурации передается через констрктор.

    Методы класса:

    * remove_acsess -- проверяет доступ к операции удалению объекта.

    * restore_acsess -- проверяет доступ к операции
       востанавления объекта.

    * clean_acsess -- проверяет доступ к операции очистке объекта.

    * autoclean_acsess -- проверяет доступ к операции автоматической
      очистке корзины.

    Поля класса:
    * cfg - объект конфигурации

    """

    def __init__(self, cfg):
        """Создает класс с заданным объектом конфигурации.
        """
        self.cfg = cfg

    def remove_acsess(self, path):
        """Возвращает есть ли доступ к операции удалению объекта.

        Учитываемые параметры файла конфигурации:
        interactive -- режим опроса пользователя
        dryrun -- режим, иммитирующий работу корзины

        """
        if self.cfg["interactive"] and not ask('remove', path):
            return False
        log_msg = "Remove '{path}'".format(path=path)
        logging.info(log_msg)
        if self.cfg["dryrun"]:
            return False
        return True

    def restore_acsess(self, path):
        """Возвращает есть ли доступ к востанавлению объекта.

        Учитываемые параметры файла конфигурации:
        interactive -- режим опроса пользователя
        dryrun -- режим, иммитирующий работу корзины

        """
        if self.cfg["interactive"] and not ask("restore", path):
            return False
        log_msg = "Restore '{path}'".format(path=path)
        logging.info(log_msg)
        if self.cfg["dryrun"]:
            return False
        return True
    
    def replace_acsess(self, path):
        """Возвращает есть ли доступ к востанавлению объекта.

        Учитываемые параметры файла конфигурации:
        interactive -- режим опроса пользователя
        dryrun -- режим, иммитирующий работу корзины

        """
        if self.cfg["dryrun"]:
            return False
        if self.cfg["replace"]:
            log_msg = "Replace '{path}'".format(path=path)
            logging.info(log_msg)
            return True
        if ask("REPLACE", path):
            log_msg = "Replace '{path}'".format(path=path)
            logging.info(log_msg)
            return True
        return True

    def clean_acsess(self, path):
        """Возвращает есть ли доступ к очистке объекта.

        Учитываемые параметры файла конфигурации:
        interactive -- режим опроса пользователя
        dryrun -- режим, иммитирующий работу корзины

        """
        if self.cfg["interactive"] and not ask("clean(forever)", path):
            return False
        log_msg = "Clean '{path}'".format(path=path)
        logging.info(log_msg)
        if self.cfg["dryrun"]:
            return False
        return True

    def autoclean_acsess(self):
        """Возвращает есть ли доступ к автоочистке корзины.

        Учитываемые параметры файла конфигурации:
        interactive -- режим опроса пользователя
        dryrun -- режим, иммитирующий работу корзины

        """
        operation = "autoclean file(forever)"
        trash_path = self.cfg["trash"]["dir"]
        if self.cfg["interactive"] and not ask(operation, trash_path):
            return False
        log_msg = "Autoclean '{trash_path}'".format(trash_path=trash_path)
        logging.info(log_msg)
        if self.cfg["dryrun"]:
            return False
        return True

