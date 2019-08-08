Permissions
==============

:synopsis: Permissions Mixins to limit access and model instances in a view.

Introduction
------------
Django Extensions offers mixins for Class Based Views that make it easier to
query and limit access to certain views.

Current Mixins
---------------------------------
* *UserPermissionMixin* - A Class Based View mixin that limits the accessibility to the view based on the "owner" of the view.
This will check if the currently logged in user (``self.request.user``) matches the owner of the model instance.
By default, the "owner" will be called "user".

.. code-block:: python

   # models.py

   from django.db import models
   from django.conf import settings

   class MyModel(models.Model):
      author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete = models.CASCADE)
      content = models.TextField()


.. code-block:: python

   # views.py

   from django.views.generic import UpdateView

   from django_extensions.auth.mixins import UserPermissionMixin

   from .models import MyModel

   class MyModelUpdateView(UserPermissionMixin, UpdateView):
      model = MyModel
      template_name = 'mymodels/update.html'
      model_permission_user_field = 'author'
