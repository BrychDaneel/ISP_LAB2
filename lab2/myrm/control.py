# -*- coding: utf-8 -*-


"""Содержит функции контроля операций.

Функции производят логирования.
Возвращают нужно ли выполнить операцию.

Экспортируемые функции:
* ask -- отправляет запрос в консоль и считывает ответ.
* remove -- контролирует удаление объекта.
* restore -- контролирует востановление объекта.
* replace -- контролирует замену объекта.
* clean -- контролирует очистку объекта.
* autoclean -- контролирует автоочистку корзины.

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
    user_ans = raw_input(ask_string).lower()
    yes = not user_ans or user_ans == 'y'
    return yes


def remove(path, interactive=False):
    """Возвращает есть ли доступ к операции удалению объекта.

    Позицонные аргументы:
    path -- путь объекта

    Непозиционные аргументы:
    interactive -- режим опроса пользователя

    """
    if interactive and not ask('remove', path):
        return False
    log_msg = "Remove '{path}'".format(path=path)
    logging.info(log_msg)
    return True


def restore(path, interactive=False):
    """Возвращает есть ли доступ к востанавлению объекта.

    Позицонные аргументы:
    path -- путь объекта

    Непозиционные аргументы:
    interactive -- режим опроса пользователя

    """
    if interactive and not ask("restore", path):
        return False
    log_msg = "Restore '{path}'".format(path=path)
    logging.info(log_msg)
    return True


def replace(path, auto_replace=True):
    """Возвращает есть ли доступ к востанавлению объекта.

    Позицонные аргументы:
    path -- путь объекта

    Непозиционные аргументы:
    auto_replace -- режим замены без опроса пользователя

    """
    log_msg = "'{path}' allready exists".format(path=path)
    logging.info(log_msg)
    if auto_replace:
        log_msg = "Replace '{path}'".format(path=path)
        logging.info(log_msg)
        return True
    if ask("REPLACE", path):
        log_msg = "Replace '{path}'".format(path=path)
        logging.info(log_msg)
        return True
    log_msg = "Replace '{path}' denided".format(path=path)
    logging.info(log_msg)
    return False


def clean(path, interactive=False):
    """Возвращает есть ли доступ к очистке объекта.

    Позицонные аргументы:
    path -- путь объекта

    Непозиционные аргументы:
    interactive -- режим опроса пользователя

    """
    if interactive and not ask("clean(forever)", path):
        return False
    log_msg = "Clean '{path}'".format(path=path)
    logging.info(log_msg)
    return True


def autoclean(path, interactive=False):
    """Возвращает есть ли доступ к автоочистке корзины.

    Позицонные аргументы:
    path -- путь к корзине

    Непозиционные аргументы:
    interactive -- режим опроса пользователя

    """
    operation = "autoclean file(forever)"
    if interactive and not ask(operation, path):
        return False
    log_msg = "Autoclean '{trash_path}'".format(trash_path=path)
    logging.info(log_msg)
    return True

