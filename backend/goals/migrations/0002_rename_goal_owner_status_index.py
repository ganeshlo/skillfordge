from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("goals", "0001_initial")]
    operations = [
        migrations.RenameIndex(
            model_name="learninggoal",
            old_name="goals_learn_owner_i_6d3b2e_idx",
            new_name="goals_learn_owner_i_b09d76_idx",
        ),
    ]
