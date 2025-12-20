from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('market', '0005_product_old_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='response',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='review',
            name='response_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
