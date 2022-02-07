import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создали юзера
        cls.user = User.objects.create_user(
            username='TestArt'
        )
        # Создали первую группу
        cls.group_1 = Group.objects.create(
            title='Название группы для теста_1',
            slug='test-slug_1',
            description='Описание группы для теста_1'
        )
        # Создали вторую группу
        cls.group_2 = Group.objects.create(
            title='Название группы для теста_2',
            slug='test-slug_2',
            description='Описание группы для теста_2'
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        # Создали пост
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст поста для теста',
            group=cls.group_1,
            image=cls.uploaded,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            text='Отлично',
            author=cls.user
        )
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    # Проверяем используемые шаблоны
    def test_pages_posts_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group_1.slug}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}):
                'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}):
                'posts/post_create.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    # Проверяем контекст
    def test_index_page_show_correct_context(self):
        """Шаблон index список постов."""
        response = self.guest_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        post_image = first_object.image
        self.assertEqual(post_image, self.post.image)
        self.assertEqual(post_group_0, self.group_1)
        self.assertEqual(post_author_0, self.user)
        self.assertEqual(post_text, self.post.text)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list список постов, отфильтрованных по группе."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group_1.slug})
        )
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_group_0 = first_object.group
        post_image = first_object.image
        self.assertEqual(post_image, self.post.image)
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_group_0, self.group_1)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile список постов, отфильтрованных по пользователю."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_image = first_object.image
        self.assertEqual(post_image, self.post.image)
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_author_0, self.user)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail один пост отфильтрованный по id."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_image = first_object.image
        self.assertEqual(post_image, self.post.image)
        self.assertEqual(post_text_0, self.post.text)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit, форма редактирования поста,
        отфильтрованного по id ."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        )
        first_object = response.context['post']
        post_text_0 = first_object.text
        post_group_0 = first_object.group
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_group_0, self.group_1)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create, форма создания поста."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_fields = response.context['form'].fields[value]
                self.assertIsInstance(form_fields, expected)

    def test_post_on_index(self):
        """Пост появляется на главной странице сайта."""
        response = self.guest_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        group_title = first_object.group.title
        self.assertEqual(group_title, self.group_1.title)

    def test_post_on_group(self):
        """Пост появляется на странице выбранной группы."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group_1.slug})
        )
        first_object = response.context['page_obj'][0]
        group_title = first_object.group.title
        self.assertEqual(group_title, self.group_1.title)

    def test_post_on_profile(self):
        """Пост появляется в профайле пользователя."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        first_object = response.context['page_obj'][0]
        group_title = first_object.group.title
        self.assertEqual(group_title, self.group_1.title)

    def test_add_comment(self):
        """Комментировать посты может только авторизованный пользователь"""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        self.assertEqual(
            response.context['comments'][0].text,
            self.comment.text
        )

    def test_add_comment2(self):
        """После успешной отправки комментарий появляется на странице поста"""
        comment_form_field = {'text': forms.fields.CharField}
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        comment_form = response.context.get('form').fields.get('text')
        self.assertIsInstance(comment_form, comment_form_field['text'])

    def test_cache_correct_index_page(self):
        """Проверка работы кэширования на главной странице"""
        response_0 = self.authorized_client.get(reverse('posts:index'))

        post = Post.objects.create(text='Test', author=self.user,
                                   group=self.group_1)
        response_1 = self.authorized_client.get(reverse('posts:index'))
        Post.objects.filter(id=post.id).delete()

        response_2 = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response_1.content, response_2.content)

        cache.clear()
        response_3 = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response_0.content, response_3.content)


class FollowViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создали юзера
        cls.user = User.objects.create_user(
            username='TestArt'
        )
        cls.user_2 = User.objects.create_user(
            username='TestArtov'
        )
        cls.follow = Follow.objects.create(
            author=cls.user,
            user=cls.user_2
        )
        # Создали первую группу
        cls.group_1 = Group.objects.create(
            title='Название группы для теста_1',
            slug='test-slug_1',
            description='Описание группы для теста_1'
        )
        # Создали вторую группу
        cls.group_2 = Group.objects.create(
            title='Название группы для теста_2',
            slug='test-slug_2',
            description='Описание группы для теста_2'
        )
        # Создали пост
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст поста для теста',
            group=cls.group_1,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            text='Отлично',
            author=cls.user
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_follow_another_user(self):
        """Авторизованный пользователь,
        может подписываться на других пользователей"""
        follow_count = Follow.objects.count()
        self.authorized_client.get(reverse('posts:profile_follow',
                                           kwargs={'username': self.user_2}))
        self.assertTrue(Follow.objects.filter(user=self.user,
                                              author=self.user_2).exists())
        self.assertEqual(Follow.objects.count(), follow_count + 1)

    def test_unfollow_another_user(self):
        """Авторизованный пользователь,
        может удалять других пользователей из подписок"""
        Follow.objects.create(user=self.user, author=self.user_2)
        follow_count = Follow.objects.count()
        self.assertTrue(Follow.objects.filter(user=self.user,
                                              author=self.user_2).exists())
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.user_2}
            )
        )
        print(follow_count)
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.user_2
            ).exists()
        )
        self.assertEqual(Follow.objects.count(), follow_count - 1)

    def test_new_post_follow(self):
        """ Новая запись пользователя будет в ленте у тех кто на него
            подписан.
        """
        following = User.objects.create(username='following')
        Follow.objects.create(user=self.user, author=following)
        post = Post.objects.create(author=following, text=self.post.text)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertIn(post, response.context['page_obj'].object_list)

    def test_new_post_unfollow(self):
        """ Новая запись пользователя не будет у тех кто не подписан на него.
        """
        self.client.logout()
        User.objects.create_user(
            username='somobody_temp',
            password='pass'
        )
        self.client.login(username='somobody_temp')
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotIn(
            self.post.text,
            response.context['page_obj'].object_list
        )


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='TestArt'
        )
        cls.group_1 = Group.objects.create(
            title='Название группы для теста_1',
            slug='test-slug_1',
            description='Описание группы для теста_1'
        )
        objs = (
            Post(
                author=cls.user,
                text='Тестовый текст',
                group=cls.group_1
            )
            for i in range(13)
        )
        Post.objects.bulk_create(objs)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index_page_paginator(self):
        """Шаблон index список постов."""
        posts_count = Post.objects.count()
        posts_count_2_pages = posts_count % settings.DEFAULT_POSTS_PER_PAGE
        response = self.guest_client.get(reverse('posts:index'))
        response_2 = self.authorized_client.get(
            reverse('posts:index') + '?page=2'
        )
        self.assertEqual(
            len(response.context['page_obj']),
            settings.DEFAULT_POSTS_PER_PAGE
        )
        self.assertEqual(
            len(response_2.context['page_obj']),
            posts_count_2_pages
        )

    def test_group_list_page_paginator(self):
        """Шаблон group_list список постов, отфильтрованных по группе."""
        posts_count = Post.objects.count()
        posts_count_2_pages = posts_count % settings.DEFAULT_POSTS_PER_PAGE
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group_1.slug})
        )
        response_2 = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group_1.slug}
            ) + '?page=2'
        )
        self.assertEqual(
            len(response.context['page_obj']),
            settings.DEFAULT_POSTS_PER_PAGE
        )
        self.assertEqual(
            len(response_2.context['page_obj']),
            posts_count_2_pages
        )

    def test_profile_page_paginator(self):
        """Шаблон profile список постов, отфильтрованных по пользователю."""
        posts_count = Post.objects.count()
        posts_count_2_pages = posts_count - settings.DEFAULT_POSTS_PER_PAGE
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        response_2 = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.user}
            ) + '?page=2'
        )
        self.assertEqual(
            len(response.context['page_obj']),
            settings.DEFAULT_POSTS_PER_PAGE
        )
        self.assertEqual(
            len(response_2.context['page_obj']),
            posts_count_2_pages
        )
