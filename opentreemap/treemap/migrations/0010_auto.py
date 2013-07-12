# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding M2M table for field boundaries on 'Instance'
        db.create_table(u'treemap_instance_boundaries', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('instance', models.ForeignKey(orm[u'treemap.instance'], null=False)),
            ('boundary', models.ForeignKey(orm[u'treemap.boundary'], null=False))
        ))
        db.create_unique(u'treemap_instance_boundaries', ['instance_id', 'boundary_id'])


    def backwards(self, orm):
        # Removing M2M table for field boundaries on 'Instance'
        db.delete_table('treemap_instance_boundaries')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'treemap.audit': {
            'Meta': {'object_name': 'Audit'},
            'action': ('django.db.models.fields.IntegerField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'current_value': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'field': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['treemap.Instance']", 'null': 'True', 'blank': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'model_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'previous_value': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'ref_id': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['treemap.Audit']", 'null': 'True'}),
            'requires_auth': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['treemap.User']"})
        },
        u'treemap.boundary': {
            'Meta': {'object_name': 'Boundary'},
            'category': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'geom': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {'srid': '3857'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'sort_order': ('django.db.models.fields.IntegerField', [], {})
        },
        u'treemap.fieldpermission': {
            'Meta': {'object_name': 'FieldPermission'},
            'field_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['treemap.Instance']"}),
            'model_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'permission_level': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['treemap.Role']"})
        },
        u'treemap.importevent': {
            'Meta': {'object_name': 'ImportEvent'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'imported_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['treemap.User']"}),
            'imported_on': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'treemap.instance': {
            'Meta': {'object_name': 'Instance'},
            'basemap_data': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'basemap_type': ('django.db.models.fields.CharField', [], {'default': "u'google'", 'max_length': '255'}),
            'boundaries': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['treemap.Boundary']", 'null': 'True', 'blank': 'True'}),
            'center': ('django.contrib.gis.db.models.fields.PointField', [], {'srid': '3857'}),
            'default_role': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'default_role'", 'to': u"orm['treemap.Role']"}),
            'geo_rev': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'treemap.instancespecies': {
            'Meta': {'object_name': 'InstanceSpecies'},
            'common_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['treemap.Instance']"}),
            'species': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['treemap.Species']"})
        },
        u'treemap.plot': {
            'Meta': {'object_name': 'Plot'},
            'address_city': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'address_street': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'address_zip': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['treemap.User']"}),
            'geom': ('django.contrib.gis.db.models.fields.PointField', [], {'srid': '3857', 'db_column': "u'the_geom_webmercator'"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'import_event': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['treemap.ImportEvent']", 'null': 'True', 'blank': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['treemap.Instance']"}),
            'length': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'owner_orig_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'readonly': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'width': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'})
        },
        u'treemap.reputationmetric': {
            'Meta': {'object_name': 'ReputationMetric'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'approval_score': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'denial_score': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'direct_write_score': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['treemap.Instance']", 'null': 'True', 'blank': 'True'}),
            'model_name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'treemap.role': {
            'Meta': {'object_name': 'Role'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['treemap.Instance']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'rep_thresh': ('django.db.models.fields.IntegerField', [], {})
        },
        u'treemap.species': {
            'Meta': {'object_name': 'Species'},
            'bloom_period': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'common_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'cultivar_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'fact_sheet': ('django.db.models.fields.URLField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'fall_conspicuous': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'flower_conspicuous': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'fruit_period': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'genus': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_dbh': ('django.db.models.fields.IntegerField', [], {'default': '200'}),
            'max_height': ('django.db.models.fields.IntegerField', [], {'default': '800'}),
            'native_status': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'palatable_human': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'plant_guide': ('django.db.models.fields.URLField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'species': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'symbol': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'wildlife_value': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'})
        },
        u'treemap.tree': {
            'Meta': {'object_name': 'Tree'},
            'canopy_height': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['treemap.User']"}),
            'date_planted': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'date_removed': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'diameter': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'height': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'import_event': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['treemap.ImportEvent']", 'null': 'True', 'blank': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['treemap.Instance']"}),
            'plot': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['treemap.Plot']"}),
            'readonly': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'species': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['treemap.Species']", 'null': 'True', 'blank': 'True'})
        },
        u'treemap.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'reputation': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'roles': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['treemap.Role']", 'null': 'True', 'blank': 'True'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        }
    }

    complete_apps = ['treemap']