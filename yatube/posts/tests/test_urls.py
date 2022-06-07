from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Название группы для теста',
            slug='test-slug',
            description='Описание группы для теста',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.user,
        )

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.user)
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент
        self.user = User.objects.create_user(username='StasBasov')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_guest_client(self):
        """Страницы доступны любому пользователю."""
        templates_url_names = {
            reverse('posts:index'): HTTPStatus.OK,
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
                HTTPStatus.OK,
            reverse('posts:profile', kwargs={'username': self.user.username}):
                HTTPStatus.OK,
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}):
                HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for page, code in templates_url_names.items():
            with self.subTest(page=page, code=code):
                response = self.guest_client.get(page)
                self.assertEqual(response.status_code, code)

    def test_create_url_exists_at_desired_location(self):
        """Страница create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_redirect_guest_on_login(self):
        """Страница /create/ перенаправит анонимного
        пользователя на страницу логина."""
        response = self.guest_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_edit_url_exists_at_desired_location(self):
        """Страница /posts/1/edit/ доступна автору."""
        response = self.author_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_url_redirect_guest_on_login(self):
        """Страница /posts/1/edit/ перенаправит анонимного
        пользователя на страницу логина."""
        response = self.guest_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user.username}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}):
                'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}):
                'posts/post_create.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_wrong_url_returns_404(self):
        """Страница /fail/ возвращает код 404 пользователю."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
