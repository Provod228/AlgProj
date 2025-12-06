import os

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.text import slugify
import transliterate


# Create your models here.

class Content(models.Model):
    title = models.CharField(
        max_length=255,
        help_text="Введите название товара",
        verbose_name="Название товара",
    )
    summary = models.TextField(
        help_text="Введите описание товара",
        verbose_name="Описание товара",
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=False,
        blank=False,
        help_text="Введите цену товара",
        verbose_name="Цена товара",
    )
    category = models.ManyToManyField(
        'Category',
        help_text="Выберите категорию товара",
        verbose_name="Категория товара",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Создатель контента",
    )
    is_published = models.BooleanField(
        help_text="Выберите опубликовать или нет",
        verbose_name="Публикация",
    )
    is_digital = models.BooleanField(
        default=False,
        help_text="Выберите электронный источник или нет",
        verbose_name="Источник",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Время создания",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Время обновления",
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name="Slug продукта",
    )
    image = models.ImageField(
        null=False,
        blank=False,
        upload_to='content_images/%Y/%m/%d/',
    )


    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ['-created_at']


    def save(self, *args, **kwargs):
        # Генерируем slug только для новых объектов или если slug пустой
        if not self.slug:
            # Проверяем, что author существует
            if self.author_id and self.title:
                # если транлит не перевел, значит вся строка в латинице и надо использовать другой slugify
                base_slug = transliterate.slugify(f"{self.author.username}-{self.title}")
                if base_slug is None:
                    base_slug = slugify(f"{self.author.username}-{self.title}", allow_unicode=False)
            else:
                base_slug = transliterate.slugify(self.title) if self.title else "untitled"
                if base_slug is None:
                    base_slug = slugify(self.title, allow_unicode=False) if self.title else "untitled"

            # Если transliterate вернул пустую строку
            if not base_slug:
                base_slug = "product"

            # Проверяем уникальность
            original_slug = base_slug
            counter = 1
            while Content.objects.filter(slug=base_slug).exclude(pk=self.pk).exists():
                base_slug = f"{original_slug}-{counter}"
                counter += 1

            self.slug = base_slug

        super().save(*args, **kwargs)


    def delete(self, *args, **kwargs):
        self._delete_image_file()
        super().delete(*args, **kwargs)


    def _delete_image_file(self):
        if self.image:
            try:
                if os.path.isfile(self.image.path):
                    os.remove(self.image.path)
            except (OSError, ValueError):
                pass


class CategoryContent(models.Model):
    VOTE_CHOICES = [
        (1, 'За'),
        (-1, 'Против'),
        (0, 'Воздержался'),
    ]

    content = models.ForeignKey(
        'Content',
        on_delete=models.CASCADE,
        verbose_name="Товар",
        related_name='category_votes'
    )
    category = models.ForeignKey(
        'Category',
        on_delete=models.CASCADE,
        verbose_name="Категория"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь"
    )
    vote = models.IntegerField(
        choices=VOTE_CHOICES,
        default=0,
        verbose_name="Голос",
        help_text="Голос за или против категории"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Голос за категорию"
        verbose_name_plural = "Голоса за категории"
        unique_together = ['content', 'category', 'user']
        ordering = ['-created_at']

    def __str__(self):
        vote_display = dict(self.VOTE_CHOICES)[self.vote]
        return f"{self.user.username} - {self.content.title} - {self.category.name} ({vote_display})"


class Category(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name="Название категории",
        help_text="Введите название категории",
        unique=True,
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание категории"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['name']

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class Rating(models.Model):
    RATING_CHOICES = [
        (1, '1 - Очень плохо'),
        (2, '2 - Плохо'),
        (3, '3 - Удовлетворительно'),
        (4, '4 - Хорошо'),
        (5, '5 - Отлично'),
    ]

    content = models.ForeignKey(
        Content,
        on_delete=models.CASCADE,
        verbose_name="Товар",
        related_name='ratings'
    )
    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Оценка",
        help_text="Выберите оценку от 1 до 5"
    )
    text = models.TextField(
        blank=True,
        verbose_name="Комментарий",
        help_text="Введите комментарий к оценке",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор оценки",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Время создания оценки"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Время обновления оценки"
    )

    class Meta:
        verbose_name = "Оценка"
        verbose_name_plural = "Оценки"
        ordering = ['-created_at']
        unique_together = ['content', 'author']

    def __str__(self):
        return f"{self.author.username} - {self.content.title} - {self.rating}"

    def save(self, *args, **kwargs):
        if self.rating < 1 or self.rating > 5:
            raise ValueError("Рейтинг должен быть от 1 до 5")
        super().save(*args, **kwargs)


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name='favorites'
    )

    content = models.ForeignKey(
        Content,
        on_delete=models.CASCADE,
        verbose_name="Товар",
        related_name='favorited_by'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата добавления"
    )

    class Meta:
        verbose_name = "Избранный товар"
        verbose_name_plural = "Избранные товары"
        ordering = ['-created_at']
        unique_together = ['user', 'content']  # Один товар может быть в избранном у пользователя только один раз

    def __str__(self):
        return f"{self.user.username} - {self.content.title} - favorite"


