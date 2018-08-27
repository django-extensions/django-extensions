from django.template import Template, Context


class ModelGenerator(object):

    FIELD_TYPE_AUTOCOMPLETE_KEYWORDS = [
        'char', 'text', 'date', 'datetime', 'decimal',
        'email', 'float', 'int', 'url', 'bool', 'nullbool', 'fkey', 'mtm'
    ]
    FIELD_TYPES_WITH_MAX_LENGTH_OPTION = [
        'CharField', 'DecimalField', 'EmailField', 'FloatField', 'IntegerField', 'URLField'
    ]
    FIELD_TYPES_WITH_UNIQUE_OPTION = [
        'CharField'
    ]
    FIELD_TYPES_WITHOUT_NULL_OPTION = [
        'ManyToManyField'
    ]

    def __init__(self, model_name, model_skeleton, models_file_resource, command_instance):
        self.model_name = model_name
        self.model_skeleton = model_skeleton
        self.models_file_resource = models_file_resource
        self.templates = dict(
            field='%s = models.%s(%s)',
            max_length='max_length=%s',
            null='null=%s',
            blank='blank=%s',
            unique='unique=%s',
            verbose_name='verbose_name=\'%s\'',
            auto_now_add='auto_now_add=%s',
            auto_now='auto_now=%s',
            on_del='on_delete=%s',
            to='to=%s',
            through='through=\'%s\'',
            through_fields='through_fields=(\'%s\', \'%s\')'
        )
        self.fieldTypePairs = dict(
            char='CharField', text='TextField', date='DateField', datetime='DateTimeField',
            decimal='DecimalField', email='EmailField', float='FloatField', int='IntegerField',
            url='URLField', bool='BooleanField', nullbool='NullBooleanField', fkey='ForeignKey',
            mtm='ManyToManyField'
        )
        self.fields = []
        self.command_instance = command_instance

    def ask(self):
        has_relation = False  # we have to comment model field line with relation if related model doesn't exist yet
        typed_right_field_type = False
        field_options = ''
        field_name = raw_input('Field name? ')

        if field_name == '':
            return True

        guessed_field_type = self.guess_field_type(field_name)

        if guessed_field_type != '':
            while not typed_right_field_type:
                field_type = raw_input('Field type?[%s] ' % guessed_field_type)
                if field_type == '' or field_type in self.FIELD_TYPE_AUTOCOMPLETE_KEYWORDS:
                    field_type = self.fieldTypePairs[guessed_field_type]
                    typed_right_field_type = True
                else:
                    self.command_instance.stdout.write('\nWrong type! Choose one from list: ' + self.FIELD_TYPE_AUTOCOMPLETE_KEYWORDS.__str__())

        else:
            while not typed_right_field_type:
                field_type = raw_input('Field type? ')
                if field_type not in self.FIELD_TYPE_AUTOCOMPLETE_KEYWORDS:
                    self.command_instance.stdout.write('\nWrong type! Choose one from list: ' + self.FIELD_TYPE_AUTOCOMPLETE_KEYWORDS.__str__())
                else:
                    field_type = self.fieldTypePairs[field_type]
                    typed_right_field_type = True

        field_options += self.templates['verbose_name'] % field_name

        if field_type in self.FIELD_TYPES_WITH_MAX_LENGTH_OPTION:
            field_options += ', ' + self.templates['max_length'] % raw_input('Max length? ')

        if field_type in self.FIELD_TYPES_WITH_UNIQUE_OPTION:
            unique = raw_input('Unique?[False] ')
            field_options += ', ' + self.templates['unique'] % 'False' if unique == '' else ', ' + self.templates['unique'] % unique

        if field_type == 'ForeignKey':
            related_model = raw_input('Related model name?[%s] ' % field_name.capitalize())
            field_options += ', ' + self.templates['to'] % field_name.capitalize() if related_model == '' else ', ' + self.templates['to'] % related_model

            on_delete = raw_input('On delete?[models.CASCADE] ')
            field_options += ', ' + self.templates['on_del'] % 'models.CASCADE' if on_delete == '' else ', ' + self.templates['on_del'] % on_delete
            has_relation = True

        if field_type == 'ManyToManyField':
            related_model = raw_input('ManyToMany model name? ')
            through_model = self.templates['through'] % raw_input('Through model?: ')
            through_fields = self.templates['through_fields'] % (self.model_name.lower(), related_model.lower())

            related_model = self.templates['to'] % related_model

            field_options += ', %s, %s, %s' % (related_model, through_model, through_fields)
            has_relation = True

        if field_type not in self.FIELD_TYPES_WITHOUT_NULL_OPTION:
            nullable = raw_input('Null?[False] ')
            field_options += ', ' + self.templates['null'] % 'False' if nullable == '' else ', ' + self.templates['null'] % nullable

        self.command_instance.stdout.write('\n')

        if has_relation:
            self.fields.append('#' + self.templates['field'] % (field_name, field_type, field_options))
        else:
            self.fields.append(self.templates['field'] % (field_name, field_type, field_options))

        if raw_input('Add more fields?[yes] ').lower() == 'no':
            return True

        return False

    def generate(self):
        template = Template(self.model_skeleton)
        context = Context(dict(model_name=self.model_name, fields=self.fields))

        generated = template.render(context)

        self.models_file_resource.write(generated)
        self.models_file_resource.close()

    def guess_field_type(self, field_name):
        if field_name.startswith('is'):
            return 'bool'
        elif field_name.endswith('_at'):
            return 'datetime'
        else:
            return ''
