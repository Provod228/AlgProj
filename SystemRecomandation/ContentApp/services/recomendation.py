from pprint import pprint

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Embedding, Flatten, Dense, Concatenate
from tensorflow.keras.optimizers import Adam
from django.db.models import Count, Avg
from ContentApp.services.data_get import ContentsService, ContentService
from django.utils import timezone


class RecommendationEngine:
    def __init__(self):
        self.content_similarity_matrix = None
        self.user_item_matrix = None
        self.deep_model = None
        self.content_features = None
        self.user_features = None


    def get_default_recommendations(self):
        contents = ContentsService.get_all_content()
        content_data = []

        for content in contents:
            rating_avg = ContentService.get_content_rating(content)
            categories = ContentService.get_real_content_category(content)
            content_data.append(
                {
                    'id': content.id,
                    'title': content.title,
                    'summary': content.summary,
                    'categories': categories,
                    'price': content.price,
                    'rating': rating_avg,
                    'author': content.author.username,
                }
            )

        df = pd.DataFrame(content_data)

        df['content_features'] = df['title'] + ' ' + df['summary'] + ' ' + df['author']

        tfidf = TfidfVectorizer(stop_words='english')
        tfidf_matrix = tfidf.fit_transform(df['content_features'])

        self.content_similarity_matrix = cosine_similarity(tfidf_matrix)
        self.content_features = df.set_index('id')['rating'].to_dict()


    def prepare_user_item_matrix(self):
        interactions = ContentsService.get_content_per_user()

        data = []
        for interaction in interactions:
            rating = ContentService.get_rating(user=interaction.user, content=interaction.content)
            data.append({
                'user_id': interaction.user.id,
                'content_id': interaction.content.id,
                'rating': rating if rating else 5,
                'created_at': interaction.created_at,
            })

        df = pd.DataFrame(data)

        df['weighted_rating'] = (
            df['rating'] * 0.6 +
            (timezone.now() - df['created_at']).dt.days * 0.2
        )

        self.user_item_matrix = df.pivot_table(
            index='user_id',
            columns='content_id',
            values='weighted_rating',
            fill_value=0,
        )

    def build_deep_learning_model(self, num_users, num_contents, embedding_size=50):
        user_input = Input(shape=(1,), name='user_input')
        content_input = Input(shape=(1,), name='content_input')

        user_embedding = Embedding(num_users, embedding_size, name='user_embedding')(user_input)
        content_embedding = Embedding(num_contents, embedding_size, name='content_embedding')(content_input)

        user_vec = Flatten()(user_embedding)
        content_vec = Flatten()(content_embedding)


        concat = Concatenate()([user_vec, content_vec])
        dense1 = Dense(128, activation='relu')(concat)
        dense2 = Dense(64, activation='relu')(dense1)
        output = Dense(1, activation='sigmoid')(dense2)

        self.deep_model = Model(inputs=[user_input, content_input], outputs=output)
        self.deep_model.compile(optimizer=Adam(0.001), loss='mse')



    def train_deep_model(self, epochs=10, batch_size=64):
        if (self.user_item_matrix is None or
            self.user_item_matrix.empty or
            self.content_features is None):
            raise ValueError("user_item_matrix - пуст или content_features - пуст")

        user_ids = []
        content_ids = []
        ratings = []

        for user_idx, user_id in enumerate(self.user_item_matrix.index):
            for content_idx, content_id in enumerate(self.user_item_matrix.columns):
                rating = self.user_item_matrix.iloc[user_idx, content_idx]
                if rating > 0:
                    user_ids.append(user_idx)
                    content_ids.append(content_idx)
                    ratings.append(rating)

        if not user_ids:
            raise ValueError("НЕТУ ДАННЫХ")

        ratings = np.array(ratings) / 10


        user_ids = np.array(user_ids)
        content_ids = np.array(content_ids)

        self.build_deep_learning_model(
            num_users=len(self.user_item_matrix.index),
            num_contents=len(self.user_item_matrix.columns),
        )

        history = self.deep_model.fit(
            x=[user_ids, content_ids],
            y=ratings,
            batch_size=batch_size,
            epochs=epochs,
            validation_split=0.2,
            verbose=1,
        )

        return history

    def recommend_for_user(self, user_id, top_n=10):
        if (self.deep_model is None
            or self.user_item_matrix is None
            or self.content_similarity_matrix is None):
            raise ValueError("Модель не тренировалась или нету данных")

        try:
            user_idx = list(self.user_item_matrix.index).index(user_id)
        except ValueError:
            return self.get_population_content(top_n)

        all_content_ids = list(self.user_item_matrix.columns)

        user_indices = np.array([user_idx] * len(all_content_ids))
        content_indices = np.array([list(self.user_item_matrix.columns).index(cid) for cid in all_content_ids])

        predicted_ratings = self.deep_model.predict([user_indices, content_indices]).flatten()

        recommended_indices = np.argsort(predicted_ratings)[::-1][:top_n]
        recommended_content_ids = [all_content_ids[i] for i in recommended_indices]

        recommended_content = ContentsService.rec_content(recommended_content_ids)

        return recommended_content


    def get_population_content(self, top_n=10):
        population_content = ContentsService.popular_content(top_n)

        return population_content


    def get_simular_content(self, content_id, top_n=10):
        if self.content_similarity_matrix is None or self.content_similarity_matrix.size == 0:
            raise ValueError("НЕТУ ДАННЫХ")

        content_ids = list(self.content_features.keys())
        try:
            content_idx = content_ids.index(content_id)
        except ValueError:
            return []

        sim_scores = list(enumerate(self.content_similarity_matrix[content_idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

        sim_scores = sim_scores[1:top_n + 1]
        similar_content_ids = [content_ids[i[0]] for i in sim_scores]
        similar_content = ContentsService.rec_content(similar_content_ids)

        return similar_content


if __name__ == "__main__":
    # Создаем экземпляр движка
    engine = RecommendationEngine()

    print("=" * 50)
    print("ТЕСТИРОВАНИЕ РЕКОМЕНДАТЕЛЬНОЙ СИСТЕМЫ")
    print("=" * 50)

    try:
        # Тест 1: Подготовка контентных фич
        print("\n1. Подготовка контентных фич...")
        engine.get_default_recommendations()
        print("✅ Контентные фичи подготовлены успешно")
        print(f"   Размер матрицы схожести: {engine.content_similarity_matrix.shape}")
        print(f"   Количество контентов: {len(engine.content_features)}")

        # Тест 2: Подготовка user-item матрицы
        print("\n2. Подготовка user-item матрицы...")
        engine.prepare_user_item_matrix()
        print("✅ User-item матрица подготовлена успешно")
        if engine.user_item_matrix is not None:
            print(f"   Пользователей: {len(engine.user_item_matrix.index)}")
            print(f"   Контентов: {len(engine.user_item_matrix.columns)}")
            print(f"   Размер матрицы: {engine.user_item_matrix.shape}")
        else:
            print("   ⚠️ User-item матрица пустая")

        # Тест 3: Получение популярного контента
        print("\n3. Тест популярного контента...")
        popular_content = engine.get_population_content(5)
        print(f"✅ Популярный контент: {len(popular_content)} элементов")
        for i, content in enumerate(popular_content, 1):
            print(f"   {i}. {content.title}")

        # Тест 4: Поиск похожего контента (если есть контент)
        if engine.content_features:
            print("\n4. Тест похожего контента...")
            first_content_id = list(engine.content_features.keys())[0]
            similar_content = engine.get_simular_content(first_content_id, 3)
            print(f"✅ Похожий контент для ID {first_content_id}: {len(similar_content)} элементов")
            for i, content in enumerate(similar_content, 1):
                print(f"   {i}. {content.title}")

        # Тест 5: Обучение модели (если есть данные)
        if (engine.user_item_matrix is not None and
                len(engine.user_item_matrix.index) > 0 and
                len(engine.user_item_matrix.columns) > 0):

            print("\n5. Обучение нейросети...")
            try:
                history = engine.train_deep_model(epochs=5, batch_size=32)
                print("✅ Модель успешно обучена")
                print(f"   Final loss: {history.history['loss'][-1]:.4f}")

                # Тест 6: Рекомендации для пользователя
                print("\n6. Тест рекомендаций...")
                first_user_id = engine.user_item_matrix.index[0]
                recommendations = engine.recommend_for_user(first_user_id, 5)
                print(f"✅ Рекомендации для пользователя {first_user_id}: {len(recommendations)} элементов")
                for i, content in enumerate(recommendations, 1):
                    print(f"   {i}. {content.title}")

            except Exception as e:
                print(f"❌ Ошибка при обучении модели: {e}")
                # Пропускаем следующие тесты если обучение не удалось
                print("⚠️ Пропускаем тесты рекомендаций из-за ошибки обучения")
        else:
            print("\n⚠️ Недостаточно данных для обучения модели")

        # Тест 7: Рекомендации для несуществующего пользователя (только если модель обучена)
        if engine.deep_model is not None:
            print("\n7. Тест для нового пользователя...")
            try:
                new_user_recommendations = engine.recommend_for_user(99999, 3)
                print(f"✅ Рекомендации для нового пользователя: {len(new_user_recommendations)} элементов")
                for i, content in enumerate(new_user_recommendations, 1):
                    print(f"   {i}. {content.title}")
            except Exception as e:
                print(f"❌ Ошибка при рекомендациях для нового пользователя: {e}")
        else:
            print("\n⚠️ Пропускаем тест для нового пользователя - модель не обучена")

    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 50)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 50)

    print(engine.deep_model, "deep_model")
    print(engine.user_item_matrix, "user_item_matryx")
    print(engine.content_similarity_matrix, "content_similarity_matrix")