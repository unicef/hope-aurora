from django.db.models.signals import post_delete, post_save

from aurora.core.models import FlexForm, FlexFormField, Validator


def update_cache(sender, instance, **kwargs):
    if isinstance(instance, Validator):
        if instance.target == Validator.FIELD:
            for r in instance.flexformfield_set.all():
                r.save()
        elif instance.target == Validator.FORM:
            for r in instance.flexform_set.all():
                r.save()
        elif instance.target == Validator.MODULE:
            for r in instance.registration_set.all():
                r.save()

    elif isinstance(instance, FlexFormField):
        instance.flex_form.save()
    elif isinstance(instance, FlexForm):
        for r in instance.registration_set.all():
            r.save()


def cache_handler():
    post_save.connect(update_cache, sender=FlexForm, dispatch_uid="form_dip")
    post_save.connect(update_cache, sender=FlexFormField, dispatch_uid="field_dip")

    post_delete.connect(update_cache, sender=FlexForm, dispatch_uid="form_del_dip")
    post_delete.connect(update_cache, sender=FlexFormField, dispatch_uid="field_del_dip")
