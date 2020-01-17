from flask import g, render_template, request, redirect, url_for, session, jsonify

from securitas import app
from securitas.controller.authentication import login, logout  # noqa: F401
from securitas.controller.group import group, groups  # noqa: F401
from securitas.controller.password import password_reset  # noqa: F401
from securitas.controller.registration import register  # noqa: F401
from securitas.controller.user import user  # noqa: F401
from securitas.form.register_user import RegisterUserForm
from securitas.representation.group import Group
from securitas.representation.user import User
from securitas.security.ipa import maybe_ipa_session  # noqa: F401
from securitas.utility import gravatar, with_ipa  # noqa: F401


@app.context_processor
def inject_global_template_vars():
    # TODO: move project out to config var
    return dict(
        project="The Fedora Project",
        gravatar=gravatar,
        ipa=g.ipa if 'ipa' in g else None,
        current_user=g.current_user if 'current_user' in g else None,
        current_username=session.get('securitas_username'),
    )


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/')
def root():
    ipa = maybe_ipa_session(app, session)
    username = session.get('securitas_username')
    if ipa and username:
        return redirect(url_for('user', username=username))
    # Kick any non-authed user back to the login form.
    register_form = RegisterUserForm()
    return render_template('index.html', register_form=register_form)


@app.route('/search/json')
@with_ipa(app, session)
def search_json(ipa):
    username = request.args.get('username')
    groupname = request.args.get('group')

    res = []

    if username:
        users_ = [User(u) for u in ipa.user_find(username)['result']]

        for user_ in users_:
            uid = user_.username
            cn = user_.name
            if uid is not None:
                # If the cn is None, who cares?
                res.append({'uid': uid, 'cn': cn})

    if groupname:
        groups_ = [Group(g) for g in ipa.group_find(groupname)['result']]
        for group_ in groups_:
            cn = group_.name
            description = group_.description
            if cn is not None:
                # If the description is None, who cares?
                res.append({'cn': cn, 'description': description})

    return jsonify(res)
