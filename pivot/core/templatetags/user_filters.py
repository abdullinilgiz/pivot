from django import template


register = template.Library()


@register.filter
def addclass(field, css):
    return field.as_widget(attrs={'class': css})


@register.filter
def text_for_title(text, number_of_symbols):
    return text[0:number_of_symbols]
