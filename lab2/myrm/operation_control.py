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


def remove_control(path, interactive=False, dryrun=False):
    """Возвращает есть ли доступ к операции удалению объекта.

    Учитываемые параметры файла конфигурации:
    interactive -- режим опроса пользователя
    dryrun -- режим, иммитирующий работу корзины

    """
    if interactive and not ask('remove', path):
        return False
    log_msg = "Remove '{path}'".format(path=path)
    logging.info(log_msg)
    if dryrun:
        return False
    return True


def restore_control(path, interactive=False, dryrun=False):
    """Возвращает есть ли доступ к востанавлению объекта.

    Учитываемые параметры файла конфигурации:
    interactive -- режим опроса пользователя
    dryrun -- режим, иммитирующий работу корзины

    """
    if interactive and not ask("restore", path):
        return False
    log_msg = "Restore '{path}'".format(path=path)
    logging.info(log_msg)
    if dryrun:
        return False
    return True


def replace_control(path, auto_replace=True, dryrun=False):
    """Возвращает есть ли доступ к востанавлению объекта.

    Учитываемые параметры файла конфигурации:
    interactive -- режим опроса пользователя
    dryrun -- режим, иммитирующий работу корзины

    """
    if dryrun:
        return False
    if auto_replace:
        log_msg = "Replace '{path}'".format(path=path)
        logging.info(log_msg)
        return True
    if ask("REPLACE", path):
        log_msg = "Replace '{path}'".format(path=path)
        logging.info(log_msg)
        return True
    return True


def clean_control(path, interactive=False, dryrun=False):
    """Возвращает есть ли доступ к очистке объекта.

    Учитываемые параметры файла конфигурации:
    interactive -- режим опроса пользователя
    dryrun -- режим, иммитирующий работу корзины

    """
    if interactive and not ask("clean(forever)", path):
        return False
    log_msg = "Clean '{path}'".format(path=path)
    logging.info(log_msg)
    if dryrun:
        return False
    return True


def autoclean_control(path, interactive=False, dryrun=False):
    """Возвращает есть ли доступ к автоочистке корзины.

    Учитываемые параметры файла конфигурации:
    interactive -- режим опроса пользователя
    dryrun -- режим, иммитирующий работу корзины

    """
    operation = "autoclean file(forever)"
    if interactive and not ask(operation, path):
        return False
    log_msg = "Autoclean '{trash_path}'".format(trash_path=path)
    logging.info(log_msg)
    if dryrun:
        return False
    return True

