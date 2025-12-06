import os
import sys
import random
import django
from datetime import timedelta

# Добавляем путь к проекту в Python path
project_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_path)

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SystemRecomandation.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth.models import User
from ContentApp.models import Content, Category, CategoryContent, Rating, Favorite


def generate_test_data():
    """Генерация тестовых данных для базы данных"""

    # Создаем тестовых пользователей
    users = []
    for i in range(1, 11):  # Увеличил количество пользователей до 10
        user, created = User.objects.get_or_create(
            username=f'test_user_{i}',
            defaults={
                'email': f'test{i}@example.com',
                'first_name': f'Test{i}',
                'last_name': f'User{i}'
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
        users.append(user)

    # Создаем категории
    categories_data = [
        {'name': 'Электроника', 'description': 'Смартфоны, ноутбуки, планшеты и другая электроника'},
        {'name': 'Книги', 'description': 'Художественная и образовательная литература'},
        {'name': 'Одежда', 'description': 'Мужская, женская и детская одежда'},
        {'name': 'Спорт', 'description': 'Спортивные товары и инвентарь'},
        {'name': 'Дом и сад', 'description': 'Товары для дома и садоводства'},
        {'name': 'Красота', 'description': 'Косметика и средства ухода'},
        {'name': 'Игрушки', 'description': 'Детские игрушки и игры'},
        {'name': 'Автотовары', 'description': 'Автомобильные аксессуары и запчасти'},
        {'name': 'Здоровье', 'description': 'Товары для здоровья и медицины'},
        {'name': 'Техника', 'description': 'Бытовая техника и приборы'},
        {'name': 'Мебель', 'description': 'Мебель для дома и офиса'},
        {'name': 'Продукты', 'description': 'Продукты питания и напитки'},
    ]

    categories = []
    for cat_data in categories_data:
        category, created = Category.objects.get_or_create(
            name=cat_data['name'],
            defaults={'description': cat_data['description']}
        )
        categories.append(category)

    # Данные для товаров - значительно расширены
    products_data = [
        # Электроника
        {
            'title': 'Смартфон Samsung Galaxy S23',
            'summary': 'Флагманский смартфон с лучшей камерой и производительностью',
            'price': 79999.99,
            'is_digital': False,
            'categories': ['Электроника']
        },
        {
            'title': 'Ноутбук Apple MacBook Pro 16"',
            'summary': 'Мощный ноутбук для профессиональной работы',
            'price': 249999.99,
            'is_digital': False,
            'categories': ['Электроника']
        },
        {
            'title': 'Наушники Sony WH-1000XM4',
            'summary': 'Беспроводные наушники с шумоподавлением',
            'price': 29999.99,
            'is_digital': False,
            'categories': ['Электроника']
        },
        {
            'title': 'Планшет iPad Air',
            'summary': 'Универсальный планшет для работы и развлечений',
            'price': 59999.99,
            'is_digital': False,
            'categories': ['Электроника']
        },
        {
            'title': 'Умные часы Apple Watch Series 9',
            'summary': 'Смарт-часы с функциями здоровья и фитнеса',
            'price': 39999.99,
            'is_digital': False,
            'categories': ['Электроника']
        },

        # Книги
        {
            'title': 'Книга "Мастер и Маргарита"',
            'summary': 'Классика русской литературы в твердом переплете',
            'price': 899.99,
            'is_digital': True,
            'categories': ['Книги']
        },
        {
            'title': 'Электронная книга Python Programming',
            'summary': 'Полное руководство по программированию на Python',
            'price': 1999.99,
            'is_digital': True,
            'categories': ['Книги', 'Электроника']
        },
        {
            'title': 'Книга "Война и мир" Л.Н. Толстой',
            'summary': 'Великий роман в четырех томах',
            'price': 1599.99,
            'is_digital': True,
            'categories': ['Книги']
        },
        {
            'title': 'Бизнес-книга "Богатый папа, бедный папа"',
            'summary': 'Финансовая грамотность и инвестиции',
            'price': 1299.99,
            'is_digital': True,
            'categories': ['Книги']
        },

        # Одежда
        {
            'title': 'Футболка хлопковая мужская',
            'summary': 'Удобная хлопковая футболка различных цветов',
            'price': 1299.99,
            'is_digital': False,
            'categories': ['Одежда']
        },
        {
            'title': 'Джинсы классические',
            'summary': 'Качественные джинсы прямого кроя',
            'price': 4599.99,
            'is_digital': False,
            'categories': ['Одежда']
        },
        {
            'title': 'Куртка зимняя пуховая',
            'summary': 'Теплая куртка для холодной погоды',
            'price': 12999.99,
            'is_digital': False,
            'categories': ['Одежда']
        },
        {
            'title': 'Платье вечернее',
            'summary': 'Элегантное платье для особых случаев',
            'price': 8999.99,
            'is_digital': False,
            'categories': ['Одежда']
        },

        # Спорт
        {
            'title': 'Беговая дорожка электрическая',
            'summary': 'Электрическая беговая дорожка для домашних тренировок',
            'price': 29999.99,
            'is_digital': False,
            'categories': ['Спорт']
        },
        {
            'title': 'Гантели наборные 20 кг',
            'summary': 'Набор гантелей для силовых тренировок',
            'price': 4599.99,
            'is_digital': False,
            'categories': ['Спорт']
        },
        {
            'title': 'Велосипед горный',
            'summary': 'Горный велосипед для активного отдыха',
            'price': 35999.99,
            'is_digital': False,
            'categories': ['Спорт']
        },
        {
            'title': 'Йога-мат премиум',
            'summary': 'Профессиональный коврик для йоги',
            'price': 2999.99,
            'is_digital': False,
            'categories': ['Спорт']
        },

        # Дом и сад
        {
            'title': 'Кофеварка автоматическая',
            'summary': 'Автоматическая кофеварка для приготовления эспрессо',
            'price': 15999.99,
            'is_digital': False,
            'categories': ['Дом и сад', 'Техника']
        },
        {
            'title': 'Набор садовых инструментов',
            'summary': 'Полный набор для работы в саду',
            'price': 5999.99,
            'is_digital': False,
            'categories': ['Дом и сад']
        },
        {
            'title': 'Гриль электрический',
            'summary': 'Электрический гриль для здорового питания',
            'price': 8999.99,
            'is_digital': False,
            'categories': ['Дом и сад', 'Техника']
        },

        # Красота
        {
            'title': 'Набор косметики люкс',
            'summary': 'Люкс набор косметики для ежедневного ухода',
            'price': 4599.99,
            'is_digital': False,
            'categories': ['Красота']
        },
        {
            'title': 'Парфюм Chanel №5',
            'summary': 'Классический женский парфюм',
            'price': 8999.99,
            'is_digital': False,
            'categories': ['Красота']
        },
        {
            'title': 'Эпилятор Braun',
            'summary': 'Эпилятор для деликатного удаления волос',
            'price': 6999.99,
            'is_digital': False,
            'categories': ['Красота', 'Техника']
        },

        # Игрушки
        {
            'title': 'Конструктор LEGO Technic',
            'summary': 'Развивающий конструктор для детей и взрослых',
            'price': 4999.99,
            'is_digital': False,
            'categories': ['Игрушки']
        },
        {
            'title': 'Кукла Barbie',
            'summary': 'Классическая кукла с аксессуарами',
            'price': 1999.99,
            'is_digital': False,
            'categories': ['Игрушки']
        },
        {
            'title': 'Настольная игра "Монополия"',
            'summary': 'Классическая экономическая игра',
            'price': 2999.99,
            'is_digital': False,
            'categories': ['Игрушки']
        },

        # Автотовары
        {
            'title': 'Коврики в салон автомобиля',
            'summary': 'Резиновые коврики в салон автомобиля',
            'price': 1999.99,
            'is_digital': False,
            'categories': ['Автотовары']
        },
        {
            'title': 'Автомобильное зарядное устройство',
            'summary': 'Зарядное устройство для автомобиля',
            'price': 2999.99,
            'is_digital': False,
            'categories': ['Автотовары', 'Электроника']
        },

        # Здоровье
        {
            'title': 'Тонометр электронный',
            'summary': 'Автоматический тонометр для измерения давления',
            'price': 3999.99,
            'is_digital': False,
            'categories': ['Здоровье']
        },
        {
            'title': 'Витаминный комплекс',
            'summary': 'Комплекс витаминов для поддержания иммунитета',
            'price': 1599.99,
            'is_digital': False,
            'categories': ['Здоровье']
        },

        # Мебель
        {
            'title': 'Диван угловой',
            'summary': 'Удобный угловой диван для гостиной',
            'price': 45999.99,
            'is_digital': False,
            'categories': ['Мебель']
        },
        {
            'title': 'Стол компьютерный',
            'summary': 'Эргономичный стол для работы за компьютером',
            'price': 8999.99,
            'is_digital': False,
            'categories': ['Мебель']
        },
    ]

    # Создаем товары
    contents = []
    for product_data in products_data:
        # Случайный автор
        author = random.choice(users)

        # Создаем товар
        content = Content.objects.create(
            title=product_data['title'],
            summary=product_data['summary'],
            price=product_data['price'],
            author=author,
            is_published=True,
            is_digital=product_data['is_digital'],
            image='content_images/2024/01/01/default_product.jpg'
        )

        # Добавляем категории через ManyToMany поле
        for category_name in product_data['categories']:
            category = next((cat for cat in categories if cat.name == category_name), None)
            if category:
                content.category.add(category)

        contents.append(content)

    # Генерируем голоса за категории (модель CategoryContent)
    category_content_records = []
    for content in contents:
        for category in content.category.all():
            # Для каждой категории товара создаем голоса от нескольких пользователей
            voters = random.sample(users, random.randint(3, 6))  # Увеличил количество голосующих
            for voter in voters:
                # Голоса только 0 или 1 (против или воздержался убраны)
                vote = random.choices([0, 1], weights=[0.3, 0.7])[0]  # 70% голосов "за"

                category_content, created = CategoryContent.objects.get_or_create(
                    content=content,
                    category=category,
                    user=voter,
                    defaults={'vote': vote}
                )
                if not created:
                    category_content.vote = vote
                    category_content.save()
                category_content_records.append(category_content)

    # Генерируем оценки и отзывы
    review_texts = [
        "Отличный товар! Рекомендую!",
        "Хорошее качество за свои деньги",
        "Не совсем то, что ожидал",
        "Прекрасный продукт, буду покупать еще",
        "Среднего качества, можно было и лучше",
        "Лучшая покупка за последнее время!",
        "Не рекомендую, есть недостатки",
        "Вполне доволен приобретением",
        "Отличное соотношение цены и качества",
        "Разочарован, не оправдал ожидания",
        "Быстрая доставка, товар соответствует описанию",
        "Качество на высоте, всем советую",
        "Неплохо, но есть мелкие недочеты",
        "Идеально подошло, спасибо!",
        "Долго искал такой товар, наконец нашел",
        "Не понравилось, вернул обратно",
        "Супер качество, буду заказывать еще",
        "Цена завышена для такого качества",
        "Лучшее, что покупал в этом году",
        "Ожидал большего, но в целом нормально"
    ]

    ratings = []
    for content in contents:
        # Каждый товар получает 4-7 оценок от разных пользователей
        reviewers = random.sample(users, random.randint(4, 7))
        for reviewer in reviewers:
            # Распределение оценок: больше хороших оценок
            rating_value = random.choices([1, 2, 3, 4, 5], weights=[0.05, 0.1, 0.2, 0.3, 0.35])[0]
            review_text = random.choice(review_texts)

            rating, created = Rating.objects.get_or_create(
                content=content,
                author=reviewer,
                defaults={
                    'rating': rating_value,
                    'text': review_text
                }
            )
            if not created:
                rating.rating = rating_value
                rating.text = review_text
                rating.save()
            ratings.append(rating)

    # Добавляем товары в избранное
    favorites = []
    for user in users:
        # Каждый пользователь добавляет 3-6 товаров в избранное
        favorite_contents = random.sample(contents, random.randint(3, 6))
        for content in favorite_contents:
            favorite, created = Favorite.objects.get_or_create(
                user=user,
                content=content
            )
            if created:
                favorites.append(favorite)

    print("Тестовые данные успешно сгенерированы!")
    print(f"Создано:")
    print(f"- Пользователей: {len(users)}")
    print(f"- Категорий: {len(categories)}")
    print(f"- Товаров: {len(contents)}")
    print(f"- Связей товаров с категориями: {sum(len(content.category.all()) for content in contents)}")
    print(f"- Голосов за категории (CategoryContent): {len(category_content_records)}")
    print(f"- Оценок: {len(ratings)}")
    print(f"- Избранных товаров: {len(favorites)}")

    # Дополнительная статистика по голосам
    votes_0 = CategoryContent.objects.filter(vote=0).count()
    votes_1 = CategoryContent.objects.filter(vote=1).count()
    print(f"  Из них голосов '0': {votes_0}, голосов '1': {votes_1}")


def clear_test_data():
    """Очистка тестовых данных"""
    # Удаляем в правильном порядке из-за foreign key constraints
    Rating.objects.all().delete()
    Favorite.objects.all().delete()
    CategoryContent.objects.all().delete()
    Content.objects.all().delete()
    Category.objects.all().delete()
    User.objects.filter(username__startswith='test_user_').delete()

    print("Тестовые данные очищены!")


# Для использования:
if __name__ == "__main__":
    # Запуск генерации данных
    generate_test_data()

    # Для очистки данных раскомментируйте следующую строку:
    # clear_test_data()