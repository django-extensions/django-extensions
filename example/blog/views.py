from django.shortcuts import render_to_response
from django.contrib.auth.models import User
from django.forms.models import ModelForm, ModelChoiceField
from example.blog.models import Entry
from django_extensions.forms.widgets import ForeignKeySearchInput

related_search_fields = {
   'author': ('username', 'first_name', 'email'),
}

class EntryForm(ModelForm):
    author = ModelChoiceField(queryset=User.objects.all(),
        widget=ForeignKeySearchInput(model=User, field_name='author',
            search_fields=related_search_fields))
    class Meta:
        model = Entry

def test_form(request):
    if request.method == 'POST':
        form = EntryForm(request.POST)
        if form.is_valid():
            return HttpResponseRedirect('/test_form/?done=1')
    else:
        form = EntryForm()
    return render_to_response('blog/test_form.html', {'form': form})
