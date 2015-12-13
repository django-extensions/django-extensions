Command Signals
===============

:synopsis: Signals fired before and after a command is executed.

A signal is thrown pre/post each management command allowing your application 
to hook into each commands execution.


Basic Example
-------------

An example hooking into show_template_tags:

::

  from django_extensions.management.signals import pre_command, post_command
  from django_extensions.management.commands.show_template_tags import Command
  
  def pre_receiver(sender, args, kwargs):
    # I'm executed prior to the management command
  
  def post_receiver(sender, args, kwargs, outcome):
    # I'm executed after the management command
  
  pre_command.connect(pre_receiver, Command)
  post_command.connect(post_receiver, Command)


Custom Permissions For All Models
---------------------------------
 
You can use the post signal to hook into the ``update_permissions`` command so that 
you can add your own permissions to each model.
 
For instance, lets say you want to add ``list`` and ``view`` permissions to 
each model. You could do this by adding them to the ``permissions`` tuple inside
your models ``Meta`` class but this gets pretty tedious.
 
An easier solution is to hook into the ``update_permissions`` call, as follows;
 
::

  from django.db.models.signals import post_syncdb
  from django.contrib.contenttypes.models import ContentType
  from django.contrib.auth.models import Permission
  from django_extensions.management.signals import post_command
  from django_extensions.management.commands.update_permissions import Command as UpdatePermissionsCommand
  
  def add_permissions(sender, **kwargs):
    """
    Add view and list permissions to all content types.
    """
    # for each of our content types
    for content_type in ContentType.objects.all():
      
      for action in ['view', 'list']:
        # build our permission slug
        codename = "%s_%s" % (action, content_type.model)
        
        try:
          Permission.objects.get(content_type=content_type, codename=codename)
          # Already exists, ignore
        except Permission.DoesNotExist:
          # Doesn't exist, add it
          Permission.objects.create(content_type=content_type,
                        codename=codename,
                        name="Can %s %s" % (action, content_type.name))
          print "Added %s permission for %s" % (action, content_type.name)
  post_command.connect(add_permissions, UpdatePermissionsCommand)
 
Each time ``update_permissions`` is called ``add_permissions`` will be called which 
ensures there are view and list permissions to all content types.


Using pre/post signals on your own commands
-------------------------------------------
 
The signals are implemented using a decorator on the handle method of a management command, 
thus using this functionality in your own application is trivial:

::

  from django_extensions.management.utils import signalcommand
   
  class Command(BaseCommand):
   
    @signalcommand
    def handle(self, *args, **kwargs):
      ...
      ...
