from modeltranslation.translator import translator, TranslationOptions
from .models import *


class OrganizationTranslationOptions(TranslationOptions):
    fields = ('name',)
translator.register(Organization, OrganizationTranslationOptions)
