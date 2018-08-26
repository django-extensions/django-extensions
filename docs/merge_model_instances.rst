merge_model_instances
==========================

:synopsis: Merges duplicate model instances by
  reassigning related model references to a chosen primary model instance.

*Note: This management command is in beta. Use with care, and make sure to test thoroughly before implementing.*

Allows the user to choose a model to de-duplicate and a field on which to de-duplicate model instances. Provides an interactive session with the user to select the model to de-duplicate and the field on which to de-duplicate model instances. After merging model instances to one instance, deletes the merged model instances. Use with care!

Example Usage
-------------

With *django-extensions* installed you merge model instances using the
*merge_model_instances* command::

  # Delete leftover migrations from the first squashed migration found in myapp
  $ ./manage.py merge_model_instances
