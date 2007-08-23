"""Helper functions

Consists of functions to typically be used within templates, but also available
to Controllers. This module is available to both as 'h'.
"""
from webhelpers import *
from pylons.i18n import get_lang, set_lang
from genshi.builder import tag
from genshi.core import Markup
from decorator import decorator
from babel.dates import format_datetime, format_date, format_time, get_timezone_name
import pytz
import logging

log = logging.getLogger(__name__)

def wrap_helpers(localdict):
    def helper_wrapper(func):
        def wrapped_helper(*args, **kw):
            return Markup(func(*args, **kw))
        wrapped_helper.__name__ = func.__name__
        return wrapped_helper
    for name, func in localdict.iteritems():
        if not callable(func) or not \
            func.__module__.startswith('webhelpers.rails'):
            continue
        localdict[name] = helper_wrapper(func)
wrap_helpers(locals())

def get_perms(openid):
    from oil import model
    if openid == {}: return None
    user = model.Session.query(model.Admin).filter_by(openid=openid).first()
    if not user:
        user = model.Session.query(model.Manager).filter_by(openid=openid).first()
    if not user:
        user = model.Session.query(model.User).filter_by(openid=openid).first()
    return user


import pylons
from paste.util.multidict import UnicodeMultiDict
import formencode
import formencode.variabledecode as variabledecode
from decorator import decorator
from pylons.decorators import determine_response_charset
from pylons.templating import render
from genshi.filters import HTMLFormFiller
from genshi.template import MarkupTemplate

def validate(template=None, schema=None, validators=None, form=None, variable_decode=False,
             dict_char='.', list_char='-', post_only=True, **htmlfill_kwargs):
    """Validate input either for a FormEncode schema, or individual validators

    Given a form schema or dict of validators, validate will attempt to
    validate the schema or validator list.

    If validation was succesfull, the valid result dict will be saved
    as ``self.form_result``. Otherwise, the action will be re-run as if it was
    a GET, and the output will be filled by FormEncode's htmlfill to fill in
    the form field errors.

    If you'd like validate to also check GET (query) variables (**not** GET
    requests!) during its validation, set the ``post_only`` keyword argument
    to False.

    .. warning::
        ``post_only`` applies to *where* the arguments to be validated come
        from. It does *not* restrict the form to only working with post, merely
        only checking POST vars.

    Example:

    .. code-block:: Python

        class SomeController(BaseController):

            def create(self, id):
                return render('/myform.mako')

            @validate(schema=model.forms.myshema(), form='create')
            def update(self, id):
                # Do something with self.form_result
                pass
    """
    def wrapper(func, self, *args, **kwargs):
        """Decorator Wrapper function"""
        request = pylons.request._current_obj()
        errors = {}
        if post_only:
            params = request.POST
        else:
            params = request.params
        is_unicode_params = isinstance(params, UnicodeMultiDict)
        params = params.mixed()
        if variable_decode:
            log.debug("Running variable_decode on params:")
            decoded = variabledecode.variable_decode(params, dict_char,
                                                     list_char)
            log.debug(decoded)
        else:
            decoded = params

        if schema:
            log.debug("Validating against a schema")
            try:
                self.form_result = schema.to_python(decoded)
            except formencode.Invalid, e:
                errors = e.unpack_errors(variable_decode, dict_char, list_char)
        if validators:
            log.debug("Validating against provided validators")
            if isinstance(validators, dict):
                if not hasattr(self, 'form_result'):
                    self.form_result = {}
                for field, validator in validators.iteritems():
                    try:
                        self.form_result[field] = \
                            validator.to_python(decoded.get(field))
                    except formencode.Invalid, error:
                        errors[field] = error
        if errors:
            log.debug("Errors found in validation, parsing form with htmlfill "
                      "for errors")
            request.environ['REQUEST_METHOD'] = 'GET'
            pylons.c.form_errors = errors

            # If there's no form supplied, just continue with the current
            # function call.
            if not form:
                raise Exception('You MUST pass a form to display errors')
                return func(self, *args, **kwargs)

            log.debug(errors)
            pylons.c.errors = errors
            pylons.c.form_result = decoded

            return render(template)
        return func(self, *args, **kwargs)
    return decorator(wrapper)