from django.db import models
from popolo import models as popolo_models


class Person(popolo_models.Person):
    origin_id = models.CharField(max_length=50, db_index=True)


class Organization(popolo_models.Organization):
    id = models.CharField(max_length=50, primary_key=True)
    origin_id = models.CharField(max_length=50, db_index=True)
    abbreviation = models.CharField(max_length=20)
    # In Helsinki, an organization can have more than one parent.
    parents = models.ManyToManyField('Organization', related_name='all_children')
    deleted = models.BooleanField(default=False)


class OrganizationContactDetail(popolo_models.OrganizationContactDetail):
    postcode = models.CharField(max_length=10)


# Generate concrete model classes for those Popolo models that the user didn't
# explicitly define.
for name, popolo_class in popolo_models.__dict__.items():
    if popolo_class == popolo_models.PopoloModel:
        continue
    try:
        if not issubclass(popolo_class, popolo_models.PopoloModel):
            continue
    except TypeError:
        continue

    # If the class is already defined, do not replace it.
    for g_name, g_class in globals().items():
        if g_class == popolo_class:
            continue
        try:
            if issubclass(g_class, popolo_class):
                break
        except TypeError:
            continue
    else:
        globals()[name] = type(name, (popolo_class,), {
            '__module__': __name__
        })
