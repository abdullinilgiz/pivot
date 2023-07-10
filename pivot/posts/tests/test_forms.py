import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.core.cache import cache
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post, Group, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='testuser')
        cls.group = Group.objects.create(
            title='This is title',
            slug='testgroup',
            description='test desctription',
        )
        cls.post = Post.objects.create(
            text='This is old text',
            author=cls.user,
        )
        cls.stranger_user = User.objects.create(username='testuser2')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(self.user)
        self.stranger_client = Client()
        self.stranger_client.force_login(self.stranger_user)
        self.guest_client = Client()
        cache.clear()

    def test_create_post(self):
        number_of_posts = Post.objects.count()
        form_data = {
            'text': 'Text',
            'group': self.group.pk
        }
        self.auth_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(
            Post.objects.count(),
            number_of_posts + 1,
            'Number of posts do not change after post form action')

        self.assertTrue(
            Post.objects.filter(
                group=self.group,
                text=form_data['text'],
                author=self.user
            ).exists(),
            'Number of posts do not change for group after creation'
        )

    def test_create_post_with_image(self):
        number_of_posts = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='test.gif',
            content=small_gif,
            content_type='image/gif',
        )
        form_data = {
            'text': 'Text',
            'group': self.group.pk,
            'image': uploaded,
        }
        self.auth_client.post(
            reverse('posts:post_create'),
            data=form_data,
        )
        self.assertEqual(
            Post.objects.count(),
            number_of_posts + 1,
            'Number of posts do not change after post form action')

        self.assertTrue(
            Post.objects.filter(
                group=self.group,
                text=form_data['text'],
                author=self.user,
                image='posts/test.gif',
            ).exists(),
            'Number of posts do not change for group after creation'
        )

    def test_edit_post(self):
        post_id = self.post.pk
        form_data = {
            'text': 'This is new text',
            'group': self.group.pk
        }
        self.auth_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': post_id}
            ),
            data=form_data,
        )
        edited_post = Post.objects.get(pk=post_id)
        self.assertEqual(edited_post.text, form_data['text'])
        self.assertEqual(edited_post.group, self.group)

    def test_edit_post_by_stranger(self):
        post_id = self.post.pk
        old_text = self.post.text
        old_group = self.post.group
        form_data = {
            'text': 'This is new text',
            'group': self.group.pk
        }
        self.stranger_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': post_id}
            ),
            data=form_data,
        )
        self.guest_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': post_id}
            ),
            data=form_data,
        )
        post = Post.objects.get(pk=post_id)
        self.assertEqual(post.text, old_text)
        self.assertEqual(post.group, old_group)

    def test_create_post_by_guest_client(self):
        number_of_posts = Post.objects.count()
        form_data = {
            'text': 'This post should not exist',
            'group': self.group.pk
        }
        self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(
            Post.objects.count(),
            number_of_posts,
            'Guest client can change number of posts')

        self.assertFalse(
            Post.objects.filter(
                group=self.group,
                text=form_data['text']
            ).exists(),
            'Number of posts do not change for group after creation'
        )

    def test_add_comment_by_guest_client(self):
        number_of_comments = Comment.objects.count()
        form_data = {
            'text': 'New comment',
        }
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
        )
        self.assertEqual(number_of_comments,
                         Comment.objects.count(),
                         'Guest should not be able to add comments')

    def test_add_comment_by_auth_client(self):
        number_of_comments = Comment.objects.count()
        form_data = {
            'text': 'New comment',
        }
        self.stranger_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
        )
        self.assertEqual(number_of_comments + 1,
                         Comment.objects.count(),
                         'Guest should not be able to add comments')
        self.assertTrue(Comment.objects.filter(
            text='New comment',
            author=self.stranger_user,
            post=self.post).exists(),
            'Comment with given fields do not exist',
        )
