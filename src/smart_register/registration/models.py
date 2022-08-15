import base64
import json
import logging

from concurrency.fields import AutoIncVersionField
from Crypto.PublicKey import RSA
from django import forms
from django.conf import settings
from django.contrib.postgres.fields import CICharField
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.text import slugify
from natural_keys import NaturalKeyModel

from smart_register.core.crypto import Crypto, crypt, decrypt
from smart_register.core.models import FlexForm, Validator
from smart_register.core.utils import dict_setdefault, get_client_ip, jsonfy, safe_json, total_size, cache_aware_reverse
from smart_register.i18n.models import I18NModel
from smart_register.registration.fields import ChoiceArrayField
from smart_register.registration.storage import router
from smart_register.state import state
from smart_register.steficon.models import RuleCommit

logger = logging.getLogger(__name__)

undefined = object()


class Registration(NaturalKeyModel, I18NModel, models.Model):
    ADVANCED_DEFAULT_ATTRS = {
        "smart": {
            "wizard": False,
            "buttons": {
                "link": {"widget": {"attrs": {}}},
            },
        }
    }
    I18N_FIELDS = ["intro", "footer"]

    version = AutoIncVersionField()
    last_update_date = models.DateTimeField(auto_now=True)

    name = CICharField(max_length=255, unique=True)
    title = models.CharField(max_length=500, blank=True, null=True)
    slug = models.SlugField(max_length=500, blank=True, null=True, unique=True)

    flex_form = models.ForeignKey(FlexForm, on_delete=models.PROTECT)
    start = models.DateField(default=timezone.now, editable=True)
    end = models.DateField(blank=True, null=True)
    active = models.BooleanField(default=False)
    locale = models.CharField(
        verbose_name="Default locale", max_length=10, choices=settings.LANGUAGES, default=settings.LANGUAGE_CODE
    )
    locales = ChoiceArrayField(models.CharField(max_length=10, choices=settings.LANGUAGES), blank=True, null=True)
    intro = models.TextField(blank=True, null=True, default="")
    footer = models.TextField(blank=True, null=True, default="")
    client_validation = models.BooleanField(blank=True, null=False, default=False)
    validator = models.ForeignKey(
        Validator,
        limit_choices_to={"target": Validator.MODULE},
        related_name="validator_for",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    pre_save = models.ForeignKey(RuleCommit, blank=True, null=True,
                                 on_delete=models.SET_NULL,
                                 help_text="Custom Rule to run BEFORE record is saved")
    scripts = models.ManyToManyField(
        Validator, related_name="script_for", limit_choices_to={"target": Validator.SCRIPT}, blank=True
    )
    unique_field = models.CharField(
        max_length=255, blank=True, null=True, help_text="Form field to be used as unique key"
    )
    unique_field_error = models.CharField(
        max_length=255, blank=True, null=True, help_text="Error message in case of duplicate 'unique_field'"
    )
    public_key = models.TextField(
        blank=True,
        null=True,
    )
    encrypt_data = models.BooleanField(default=False)
    advanced = models.JSONField(default=dict, blank=True)

    class Meta:
        get_latest_by = "start"
        permissions = (("can_manage", "Can Manage"),)

    @property
    def media(self):
        return forms.Media(js=[script.get_script_url() for script in self.scripts.all()])

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return cache_aware_reverse("register", args=[self.slug, self.version])

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.title:
            self.title = self.name
        dict_setdefault(self.advanced, self.ADVANCED_DEFAULT_ATTRS)
        super().save(force_insert, force_update, using, update_fields)

    def translations(self):
        return Registration.objects.filter(slug=self.slug, active=True)

    def setup_encryption_keys(self):
        key = RSA.generate(2048)
        private_pem = key.export_key()
        public_pem: bytes = key.publickey().export_key()

        self.public_key: str = public_pem.decode()
        self.public_key2 = public_pem
        self.save()
        return private_pem, public_pem

    def encrypt(self, value):
        if not isinstance(value, str):
            value = safe_json(value)
        return crypt(value, self.public_key)

    def add_record(self, fields_data):
        fields, files = router.decompress(fields_data)
        if self.pre_save:
            from smart_register.steficon.result import DictResult
            result: DictResult = self.pre_save.execute({"fields": fields,
                                                        "files": files})
            fields.update(**result.data)

        if self.public_key:
            kwargs = {
                # "storage": self.encrypt(fields_data),
                "files": self.encrypt(files),
                "fields": base64.b64encode(self.encrypt(fields)).decode(),
            }
        elif self.encrypt_data:
            kwargs = {
                # "storage": Crypto().encrypt(fields_data).encode(),
                "files": Crypto().encrypt(files).encode(),
                "fields": Crypto().encrypt(fields),
            }
        else:
            kwargs = {
                # "storage": safe_json(fields_data).encode(),
                "files": safe_json(files).encode(),
                "fields": jsonfy(fields),
            }

        if self.unique_field and self.unique_field in fields:
            kwargs["unique_field"] = fields.get(self.unique_field, None) or None
        # This code is only for UKR
        kwargs.update({
            "size": total_size(fields) + total_size(files),
            "counters": fields_data.get("counters", {}),
            "index1": fields_data.get("index1", None),
        })
        return Record.objects.create(registration=self, **kwargs)

    @cached_property
    def languages(self):
        return [(k, v) for k, v in settings.LANGUAGES if k in self.all_locales]

    @cached_property
    def all_locales(self):
        locales = [self.locale]
        if self.locales:
            locales += self.locales
        return set(locales)


class RemoteIp(models.GenericIPAddressField):
    def pre_save(self, model_instance, add):
        if add:
            value = get_client_ip(getattr(state, "request", None))
            setattr(model_instance, self.attname, value)
        return getattr(model_instance, self.attname)


class Record(models.Model):
    registration = models.ForeignKey(Registration, on_delete=models.PROTECT)
    unique_field = models.CharField(blank=True, null=True, max_length=255, db_index=True)
    remote_ip = RemoteIp(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    storage = models.BinaryField(null=True, blank=True)
    ignored = models.BooleanField(default=False, blank=True, null=True)
    size = models.IntegerField(blank=True, null=True)
    counters = models.JSONField(blank=True, null=True)

    fields = models.JSONField(null=True, blank=True)
    files = models.BinaryField(null=True, blank=True)

    index1 = models.CharField(null=True, blank=True, max_length=255)
    index2 = models.CharField(null=True, blank=True, max_length=255)
    index3 = models.CharField(null=True, blank=True, max_length=255)

    class Meta:
        unique_together = ("registration", "unique_field")

    def decrypt(self, private_key=undefined, secret=undefined):
        if private_key != undefined:
            # return json.loads(decrypt(self.storage, private_key))
            files = json.loads(decrypt(self.files, private_key))
            fields = json.loads(decrypt(base64.b64decode(self.fields), private_key))
            return router.compress(fields, files)
        elif secret != undefined:
            files = json.loads(Crypto(secret).decrypt(self.files))
            fields = json.loads(Crypto(secret).decrypt(self.fields))
            return router.compress(fields, files)

    @property
    def unicef_id(self):
        ts = self.timestamp.strftime("%Y%m%d")
        return f"HOPE-{ts}-{self.registration.id}/{self.id}"

    @property
    def data(self):
        if self.registration.public_key:
            return {"Forbidden": "Cannot access encrypted data"}
        elif self.registration.encrypt_data:
            return self.decrypt(secret=None)
        else:
            files = {}
            if self.files:
                files = json.loads(self.files.tobytes().decode())
            return merge(files, self.fields)


def merge(a, b, path=None, update=True):
    """merges b into a"""
    if path is None:
        path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                pass  # same leaf value
            elif isinstance(a[key], list) and isinstance(b[key], list):
                for idx, val in enumerate(b[key]):
                    a[key][idx] = merge(a[key][idx], b[key][idx], path + [str(key), str(idx)], update=update)
            elif update:
                a[key] = b[key]
            else:
                raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
        else:
            a[key] = b[key]
    return a
