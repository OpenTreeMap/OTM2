from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

from django.contrib.gis.db import models
from django.db import IntegrityError
from treemap.audit import Auditable, Authorizable, FieldPermission, Role

from django.contrib.auth.models import AbstractUser

import hashlib


class Instance(models.Model):
    """
    Each "Tree Map" is a single instance
    """
    name = models.CharField(max_length=255)

    """
    Basemap type     Basemap data
    ------------     -----------------
    Google           Google_API_Key
    Bing             Bing_API_Key
    TMS              TMS URL with {x},{y},{z}
    """
    basemap_type = models.CharField(max_length=255,
                                    choices=(("google", "Google"),
                                             ("bing", "Bing"),
                                             ("tms", "Tile Map Service")),
                                    default="google")
    basemap_data = models.CharField(max_length=255, null=True, blank=True)

    """
    The current database revision for the instance

    This revision is used to determine if tiles should be cached.
    In particular, the revision has *no* effect on the actual
    data.

    Generally we make tile requests like:
    http://tileserver/tile/{layer}/{rev}/{Z}/{Y}/{X}

    There is a database trigger that updates the
    revision whenever an edit to a geometry field is made
    so you don't have to worry about it.

    You should *not* edit this field.
    """
    geo_rev = models.IntegerField(default=1)

    """ Center of the map when loading the instance """
    center = models.PointField(srid=3857)

    default_role = models.ForeignKey('Role', related_name='default_role')

    boundaries = models.ManyToManyField('Boundary', null=True, blank=True)

    objects = models.GeoManager()

    def __unicode__(self):
        return self.name

    @property
    def geo_rev_hash(self):
        return hashlib.md5(str(self.geo_rev)).hexdigest()

    @property
    def center_lat_lng(self):
        return self.center.transform(4326, clone=True)

    def scope_model(self, model):
        qs = model.objects.filter(instance=self)
        return qs


class User(Auditable, AbstractUser):
    roles = models.ManyToManyField(Role, blank=True, null=True)
    reputation = models.IntegerField(default=0)

    def get_instance_permissions(self, instance, model_name=None):
        roles = self.roles.filter(instance=instance)

        if len(roles) > 1:
            error_message = ("%s cannot have more than one role per"
                             " instance. Something might be very "
                             "wrong with your database configuration." %
                             self.pk)
            raise IntegrityError(error_message)

        elif len(roles) == 1:
            perms = FieldPermission.objects.filter(role=roles[0])
        else:
            perms = FieldPermission.objects.filter(role=instance.default_role)

        if model_name:
            perms = perms.filter(model_name=model_name)

        return perms


class Species(models.Model):
    """
    http://plants.usda.gov/adv_search.html
    """
    ### Base required info
    symbol = models.CharField(max_length=255)
    genus = models.CharField(max_length=255)
    species = models.CharField(max_length=255, null=True, blank=True)
    cultivar_name = models.CharField(max_length=255, null=True, blank=True)
    gender = models.CharField(max_length=50, null=True, blank=True)
    common_name = models.CharField(max_length=255, null=True, blank=True)

    ### Copied from original OTM ###
    native_status = models.CharField(max_length=255, null=True, blank=True)
    bloom_period = models.CharField(max_length=255, null=True, blank=True)
    fruit_period = models.CharField(max_length=255, null=True, blank=True)
    fall_conspicuous = models.NullBooleanField()
    flower_conspicuous = models.NullBooleanField()
    palatable_human = models.NullBooleanField()
    wildlife_value = models.NullBooleanField()

    fact_sheet = models.URLField(max_length=255, null=True, blank=True)
    plant_guide = models.URLField(max_length=255, null=True, blank=True)

    ### Used for validation
    max_dbh = models.IntegerField(default=200)
    max_height = models.IntegerField(default=800)

    objects = models.GeoManager()

    @property
    def scientific_name(self):
        name = self.genus
        if self.species:
            name += " " + self.species
        if self.cultivar_name:
            name += " '%s'" % self.cultivar_name
        return name

    class Meta:
        verbose_name_plural = "Species"


class InstanceSpecies(Auditable, models.Model):
    instance = models.ForeignKey(Instance)
    species = models.ForeignKey(Species)
    common_name = models.CharField(max_length=255, null=True, blank=True)


class ImportEvent(models.Model):
    imported_by = models.ForeignKey(User)
    imported_on = models.DateField(auto_now_add=True)


#TODO:
# Exclusion Zones
# Proximity validation
class Plot(Authorizable, Auditable, models.Model):
    instance = models.ForeignKey(Instance)
    geom = models.PointField(srid=3857, db_column='the_geom_webmercator')

    width = models.FloatField(null=True, blank=True)
    length = models.FloatField(null=True, blank=True)

    address_street = models.CharField(max_length=255, blank=True, null=True)
    address_city = models.CharField(max_length=255, blank=True, null=True)
    address_zip = models.CharField(max_length=30, blank=True, null=True)

    import_event = models.ForeignKey(ImportEvent, null=True, blank=True)
    created_by = models.ForeignKey(User)
    owner_orig_id = models.CharField(max_length=255, null=True, blank=True)
    readonly = models.BooleanField(default=False)

    objects = models.GeoManager()

    @property
    def hash(self):
        string_to_hash = super(Plot, self).hash

        # The hash state for a given plot also includes the hash
        # state for all of the trees on it as well
        tree_hashes = [t.hash for t in self.tree_set.all()]
        string_to_hash += "," + ",".join(tree_hashes)

        return hashlib.md5(string_to_hash).hexdigest()

    @property
    def zones(self):
        if self.geom:
            return Boundary.objects\
                           .filter(geom__contains=self.goem)\
                           .order('sort_order')
        else:
            return []


class Tree(Authorizable, Auditable, models.Model):
    """
    Represents a single tree, belonging to an instance
    """
    instance = models.ForeignKey(Instance)

    plot = models.ForeignKey(Plot)
    species = models.ForeignKey(Species, null=True, blank=True)
    created_by = models.ForeignKey(User)
    import_event = models.ForeignKey(ImportEvent, null=True, blank=True)

    readonly = models.BooleanField(default=False)
    diameter = models.FloatField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)
    canopy_height = models.FloatField(null=True, blank=True)
    date_planted = models.DateField(null=True, blank=True)
    date_removed = models.DateField(null=True, blank=True)

    objects = models.GeoManager()


class Boundary(models.Model):
    """
    A plot can belong to many different boundary zones. Boundary zones are
    always sorted by 'sort_order' before displaying. An example output
    for a given tree could be:
    { name } ({category}, {sort order})
    +- United States (Country, 0)
     +- Pennsylvania (State, 1)
      +- Philadelphia (County, 2)
       +- Philadelphia (City, 3)
        +- 19107 (Zip Code, 4)
        +- Callowhill (Neighborhood, 4)
    """
    geom = models.MultiPolygonField(srid=3857, db_column='the_geom_webmercator')
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    sort_order = models.IntegerField()

    objects = models.GeoManager()

    def __unicode__(self):
        return self.name
