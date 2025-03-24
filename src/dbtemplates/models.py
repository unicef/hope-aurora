from django.contrib.sites.managers import CurrentSiteManager
from django.contrib.sites.models import Site
from django.db import models
from django.db.models import signals
from django.template import TemplateDoesNotExist
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from natural_keys import NaturalKeyModel, NaturalKeyModelManager

from dbtemplates.conf import settings
from dbtemplates.utils.cache import add_template_to_cache, remove_cached_template
from dbtemplates.utils.template import get_template_source


class Template(NaturalKeyModel, models.Model):
    """
    Defines a template model for use with the database template loader.

    The field ``name`` is the equivalent to the filename of a static template.
    """

    _natural_key = ("name",)

    name = models.CharField(
        _("name"),
        max_length=100,
        unique=True,
        help_text=_("Example: 'flatpages/default.html'"),
    )
    content = models.TextField(_("content"), blank=True)
    sites = models.ManyToManyField(Site, verbose_name=_("sites"), blank=True)
    creation_date = models.DateTimeField(_("creation date"), default=now)
    last_changed = models.DateTimeField(_("last changed"), default=now)
    active = models.BooleanField(default=True, blank=True)

    objects = NaturalKeyModelManager()
    on_site = CurrentSiteManager("sites")

    class Meta:
        app_label = "dbtemplates"
        db_table = "django_template"
        verbose_name = _("template")
        verbose_name_plural = _("templates")
        ordering = ("name",)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.last_changed = now()
        # If content is empty look for a template with the given name and
        # populate the template instance with its content.
        if settings.DBTEMPLATES_AUTO_POPULATE_CONTENT and not self.content:
            self.populate()
        super().save(*args, **kwargs)

    def populate(self, name=None):
        """Try to find a template with the same name and populates the content field if found."""
        if name is None:
            name = self.name
        try:
            source = get_template_source(name)
            if source:
                self.content = source
        except TemplateDoesNotExist:
            pass


def add_default_site(instance, **kwargs):
    """
    Cache the templates.

    Called via Django's signal
    If the template in the database was added or changed, only if DBTEMPLATES_ADD_DEFAULT_SITE setting is set.
    """
    if not settings.DBTEMPLATES_ADD_DEFAULT_SITE:
        return
    current_site = Site.objects.get_current()
    if current_site not in instance.sites.all():
        instance.sites.add(current_site)


signals.post_save.connect(add_default_site, sender=Template)
signals.post_save.connect(add_template_to_cache, sender=Template)
signals.pre_delete.connect(remove_cached_template, sender=Template)
