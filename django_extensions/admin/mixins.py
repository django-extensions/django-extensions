from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


class AdminInstanceActionsMixin:
    """Admin actions.

    Example:
    ```
    list_display = (
        'instance_actions_display',
    )
    fields = (
        'instance_actions_display',
    )
    readonly_fields = (
        'instance_actions_display',
    )
    instance_actions = (
        'run',
    )

    def run(self, request, object_id):
        obj = self.get_object(request, object_id)
        return self.redirect_to_referer(request)
    ```
    """

    instance_actions = ()

    def get_urls(self):
        app_label = self.model._meta.app_label
        model_name = self.model._meta.model_name
        urls = super().get_urls()

        admin_action_urls = []

        for name in self.instance_actions:
            admin_action_urls.append(
                path(
                    f'<slug:object_id>/{name}/',
                    self.admin_site.admin_view(getattr(self, name)),
                    name=f'{app_label}_{model_name}_{name}',
                ),
            )

        return admin_action_urls + urls

    def instance_actions_display(self, obj):
        style = """
        .instance_actions {
            padding: 0;
            font-weight: 300;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            color: rgba(68, 126, 155);
        }
        .instance_actions a {
            border-bottom: 1px solid rgba(68, 126, 155, 0.25);
        }
        """

        actions = [
            self.get_instance_action_link(
                action_name=name,
                instance=obj,
            )
            for name in self.instance_actions
        ]

        html = '<style>{}</style><div class="instance_actions">{}</div>'.format(
            style,
            ' / '.join(actions),
        )

        return mark_safe(html)

    instance_actions_display.short_description = _('Actions')

    @staticmethod
    def get_instance_action_link(instance, action_name):
        """Return html link for admin action."""

        link = reverse(
            'admin:{}_{}_{}'.format(
                instance._meta.app_label,
                instance._meta.model_name,
                action_name,
            ),
            args=(instance.id,),
        )
        html = '<a href="{}">{}</a>'.format(
            link,
            _(action_name.replace('_', ' ').title()),
        )

        return html

    @staticmethod
    def redirect_to_instance(instance) -> HttpResponseRedirect:
        """Return HttpResponseRedirect for admin action."""

        link = reverse(
            'admin:{}_{}_change'.format(
                instance._meta.app_label,
                instance._meta.model_name,
            ),
            args=(instance.id,),
        )

        return HttpResponseRedirect(link)

    def redirect_to_referer(self, request) -> HttpResponseRedirect:
        link = request.META.get('HTTP_REFERER')

        if not link:
            link = reverse(
                'admin:{}_{}_changelist'.format(
                    self.model._meta.app_label,
                    self.model._meta.model_name,
                ),
            )

        return HttpResponseRedirect(link)
