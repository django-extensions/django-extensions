

def modify_fields(**kwargs):
    """
        A decorator to modify field properties for a child model
        With regards to http://stackoverflow.com/a/24475838/6245268

        Usage:
            ```
                class AbstractVehicle(models.Model):
                    owner = models.ForeignKey(User)

                    class Meta:
                        abstract = True


                @modify_fields(
                    user={
                        'related_name': 'cars',
                        'verbose_name': 'Car owner',
                    }
                )
                class Car(AbstractVehicle):
                    pass


                @modify_fields(
                    user={
                        'related_name': 'bicycles',
                        'verbose_name': 'Bicyle owner',
                    }
                )
                class Bicylce(AbstractVehicle):
                    pass

            ```

        :param kwargs:
        :return:
    """

    def wrap(cls):
        for field, prop_dict in kwargs.items():
            for prop, val in prop_dict.items():
                setattr(cls._meta.get_field(field), prop, val)
        return cls

    return wrap
