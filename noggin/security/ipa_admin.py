import random
from functools import wraps

from flask import current_app

from .ipa import Client


class IPAAdmin:

    __WRAPPED_METHODS = (
        "user_show",
        "user_mod",
        "stageuser_add",
        "stageuser_show",
        "stageuser_activate",
        "stageuser_mod",
        "ping",
    )
    __WRAPPED_METHODS_TESTING = (
        "user_add",
        "user_del",
        "group_add",
        "group_del",
        "group_find",
        "group_add_member",
        "group_add_member_manager",
        "pwpolicy_add",
        "pwpolicy_mod",
        "pwpolicy_show",
        "otptoken_add",
        "otptoken_del",
        "otptoken_find",
        "stageuser_del",
        "stageuser_mod",
        "batch",
        "fasagreement_add",
        "fasagreement_add_group",
        "fasagreement_del",
        "fasagreement_remove_group",
        "fasagreement_remove_user",
        "fasagreement_disable",
    )

    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.extensions["ipa-admin"] = {
            "username": app.config['FREEIPA_ADMIN_USER'],
            "password": app.config['FREEIPA_ADMIN_PASSWORD'],
        }
        app.config['FREEIPA_ADMIN_USER'] = '***'
        app.config['FREEIPA_ADMIN_PASSWORD'] = '***'  # nosec

    # Attempt to obtain an administrative IPA session
    def __maybe_ipa_admin_session(self):
        username = current_app.extensions["ipa-admin"]["username"]
        password = current_app.extensions["ipa-admin"]["password"]
        client = Client(
            random.choice(current_app.config['FREEIPA_SERVERS']),
            verify_ssl=current_app.config['FREEIPA_CACERT'],
        )
        client.login(username, password)
        client.ping()
        return client

    def __wrap_method(self, method_name):
        @wraps(getattr(Client, method_name))
        def wrapper(*args, **kwargs):
            ipa = self.__maybe_ipa_admin_session()
            ipa_method = getattr(ipa, method_name)
            res = ipa_method(*args, **kwargs)
            ipa.logout()
            return res

        return wrapper

    def __getattr__(self, name):
        wrapped_methods = list(self.__WRAPPED_METHODS)
        if current_app.config.get('TESTING'):  # pragma: no cover
            wrapped_methods.extend(self.__WRAPPED_METHODS_TESTING)
        if name in wrapped_methods:
            return self.__wrap_method(name)
        raise AttributeError(name)
