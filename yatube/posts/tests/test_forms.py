import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, Comment
from posts.forms import PostForm

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='TestArt'
        )
        cls.author_client = Client()
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
        cls.group_old = Group.objects.create(
            title='test_group_old',
            slug='test-slug-old',
            description='test_description'
        )
        cls.group_new = Group.objects.create(
            title='test_group_new',
            slug='test-slug-new',
            description='test_description'
        )
        cls.post = Post.objects.create(
            text='test_post',
            group=cls.group_old,
            author=cls.user,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Проверка формы создания нового поста."""
        posts_count = Post.objects.count()
        group_field = self.group_old.id
        form_data = {
            'text': 'test_new_post',
            'group': group_field,
            'image': self.uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            )
        )
        first_post = Post.objects.first()
        post_text = first_post.text
        post_author_0 = first_post.author
        post_group_0 = first_post.group
        post_image = first_post.image
        self.assertEqual(post_image.name, f'posts/{self.uploaded.name}')
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(post_group_0, self.group_old)
        self.assertEqual(post_author_0, self.user)
        self.assertEqual(post_text, form_data['text'])

    def test_edit_post(self):
        """Проверка формы редактирования поста и изменение
        его в базе данных."""
        posts_count = Post.objects.count()
        group_field_new = self.group_new.id
        form_data = {
            'text': 'test_edit_post',
            'group': group_field_new,
        }
        self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk}
            )
        )
        first_post = Post.objects.first()
        post_text = first_post.text
        post_author_0 = first_post.author
        post_group_0 = first_post.group
        self.assertEqual(post_group_0, self.group_new)
        self.assertEqual(post_author_0, self.user)
        self.assertEqual(post_text, form_data['text'])

        self.assertFalse(
            Post.objects.filter(
                group=self.group_old.id,
                text='test_post',
            ).exists()
        )

    def test_edit_post_guest(self):
        """Проверка формы редактирования поста гостем."""
        group_field = self.group_old.id
        login_url = reverse('login')
        create_url = reverse(
            'posts:post_edit',
            kwargs={'post_id': self.post.pk}
        )
        expected_redirect = f'{login_url}?next={create_url}'
        form_data = {
            'text': 'test_edit_post',
            'group': group_field,
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, expected_redirect
        )

    def test_create_post_guest(self):
        """Проверка формы создания поста гостем."""
        group_field = self.group_old.id
        login_url = reverse('login')
        create_url = reverse('posts:post_create')
        expected_redirect = f'{login_url}?next={create_url}'
        form_data = {
            'text': 'test_edit_post',
            'group': group_field,
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, expected_redirect
        )

    def test_comment(self):
        """Авторизованный может комментировать"""
        comment_count = Comment.objects.count()
        post_id = self.post.pk
        form_data = {
            'text': 'Новый комментарий',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post_id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(Comment.objects.filter(
            text=form_data['text']).exists()
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': post_id}))

    def test_comment_guest(self):
        """Проверка создания коммента гостем."""
        post_id = self.post.pk
        login_url = reverse('login')
        create_url = reverse('posts:add_comment', kwargs={'post_id': post_id})
        expected_redirect = f'{login_url}?next={create_url}'
        form_data = {
            'text': 'test_comment',
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post_id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, expected_redirect
        )
