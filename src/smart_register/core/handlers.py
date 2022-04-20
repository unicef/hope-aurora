from django.db.models.signals import post_delete, post_save

from smart_register.core.models import FlexForm, FlexFormField, FormSet


def update_cache(sender, instance, **kwargs):
    if isinstance(instance, FlexFormField):
        instance.flex_form.save()
    elif isinstance(instance, FlexForm):
        for r in instance.formset_set.all():
            r.parent.save()
        for r in instance.registration_set.all():
            r.save()


def cache_handler():
    post_save.connect(update_cache, sender=FlexForm, dispatch_uid="form_dip")
    post_save.connect(update_cache, sender=FlexFormField, dispatch_uid="field_dip")
    post_save.connect(update_cache, sender=FormSet, dispatch_uid="formset_dip")

    post_delete.connect(update_cache, sender=FlexForm, dispatch_uid="form_del_dip")
    post_delete.connect(update_cache, sender=FlexFormField, dispatch_uid="field_del_dip")
    post_delete.connect(update_cache, sender=FormSet, dispatch_uid="formset_del_dip")
