import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0003_follow_and_more'),
    ]

    operations = [
        # 포트폴리오 공유 기능 제외 — 모델 삭제 (자식 먼저). docs/추천_장투_DB결정.md §2-11
        migrations.DeleteModel(name='SharedPortfolioItem'),
        migrations.DeleteModel(name='SharedPortfolio'),
        # 글/댓글 수정 추적용 updated_at (기존 행은 일회성 timezone.now로 채움)
        migrations.AddField(
            model_name='comment',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='communitypost',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
