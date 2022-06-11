managestate
==========

:synopsis: Saves current applied migrations to a file or applies migrations from this file.

The `managestate` command fetches last applied migrations from a specified database
and saves them to a specified file. After that, you may easily apply saved migrations.
The advantage of this approach is that you may have at hand several database states
and quickly switch between them.

Why?
----

While you develop several features or fix some bugs at the same time you often meet
the situation when you need to apply or unapply database migrations before you check out
to another feature/bug branch. You always need to view current migrations by `showmigrations`,
then apply or unapply it manually using `migrate` and there is no problem if you work with
one Django app. But when there is more than one, it starts to annoy. To forget about the problem
and quickly switch between branches use the `managestate` command.

How?
----

To dump current migrations use::

    $ ./manage.py managestate dump

A state will be saved to `managestate.json` just about the following::

    {
      "default": {
        "admin": "0003_logentry_add_action_flag_choices",
        "auth": "0012_alter_user_first_name_max_length",
        "contenttypes": "0002_remove_content_type_name",
        "sessions": "0001_initial",
        "sites": "0002_alter_domain_unique",
        "myapp": "zero"
      },
      "updated_at": "2021-06-27 10:42:50.364070"
    }

As you see, migrations have been saved as the state called "default".
You can specify it using the positional argument::

    $ ./manage.py managestate dump my_feature_branch

Then migrations will be added to `managestate.json` under the key "my_feature_branch".
To change the filename use `-f` or `--filename` flag.

When you load a state from a file, you may also use all arguments defined for the `migrate` command.

Examples
----

Save an initial database state of the branch "master/main" before developing features::

    $ ./manage.py managestate dump master

Check out to your branch, develop your feature, and dump its state when you are going to get reviewed::

    $ ./manage.py managestate dump super-feature

Check out to the "master" branch back and rollback a database state with just one command::

    $ ./manage.py managestate load master

If you need to add some improvements to your feature, just use::

    $ ./manage.py managestate load super-feature
