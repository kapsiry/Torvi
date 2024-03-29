# Generated by Django 3.2.13 on 2022-05-15 18:55

from django.db import migrations, models
import django.db.models.deletion
import news.utils


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='News',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creator', models.CharField(blank=True, max_length=256, verbose_name='Creator')),
                ('sender', models.EmailField(default='tiedotus@tuki.kapsi.fi', max_length=256, verbose_name='Sender')),
                ('subject', models.CharField(blank=True, max_length=512, verbose_name='Subject')),
                ('message', models.CharField(blank=True, max_length=50000, validators=[news.utils.testXML], verbose_name='Message')),
                ('email_message', models.CharField(blank=True, max_length=50000, verbose_name='Email message')),
                ('modifed', models.DateTimeField(auto_now=True)),
                ('published', models.DateTimeField(blank=True, default=None, null=True)),
                ('publishid', models.IntegerField(blank=True, null=True, unique=True)),
                ('totwitter', models.BooleanField(default=False, verbose_name='Tweet?')),
                ('toemail', models.CharField(blank=True, max_length=8096)),
                ('tofacebook', models.BooleanField(default=False, verbose_name='Facebook?')),
            ],
            options={
                'ordering': ['modifed'],
            },
        ),
        migrations.CreateModel(
            name='Logs',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('action', models.CharField(max_length=50000)),
                ('error', models.BooleanField(default=False)),
                ('source', models.CharField(choices=[('F', 'Facebook'), ('T', 'Twitter'), ('E', 'Email'), ('P', 'Publish'), ('U', 'Unpublish'), ('M', 'Modifed'), ('O', 'Other')], default='O', max_length=1)),
                ('news', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='news.news')),
            ],
        ),
    ]
