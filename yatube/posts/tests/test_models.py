from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
        )

    def test_urls_guest_client(self):
        """Страницы доступны любому пользователю."""
        templates_url_names = {
            PostModelTest.group: PostModelTest.group.title,
            PostModelTest.post: PostModelTest.post.text[:15],
        }
        for task, object_name in templates_url_names.items():
            with self.subTest(task=task, object_name=object_name):
                self.assertEqual(object_name, str(task))
