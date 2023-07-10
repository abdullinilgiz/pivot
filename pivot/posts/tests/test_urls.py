from http import HTTPStatus

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.cache import cache

from posts.models import Post, Group

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='testuser')
        cls.post = Post.objects.create(
            text='This is text. And another symbols for lenth.',
            author=cls.user,
        )

        cls.stranger_user = User.objects.create(username='testuser2')
        cls.stranger_post = Post.objects.create(
            text='This is text. And another symbols for lenth.',
            author=cls.stranger_user,
        )

        cls.group = Group.objects.create(
            title='This is title',
            slug='testgroup',
            description='test desctription',
        )

    def setUp(self):
        self.guest_client = Client()
        self.auth_client = Client()
        self.auth_client.force_login(self.user)
        self.stranger_client = Client()
        self.stranger_client.force_login(self.stranger_user)
        cache.clear()

    def test_access_right_for_guest(self):
        post_id = str(self.stranger_post.pk)
        url_names = [
            '/',
            '/group/' + self.group.slug + '/',
            '/profile/' + self.user.get_username() + '/',
            '/posts/' + post_id + '/',
        ]
        for url in url_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_access_right_for_authen_user(self):
        post_id = str(self.stranger_post.pk)
        url_names = [
            '/',
            '/group/' + self.group.slug + '/',
            '/profile/' + self.user.get_username() + '/',
            '/posts/' + post_id + '/',
            '/create/',
        ]
        for url in url_names:
            with self.subTest(url=url):
                response = self.auth_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_access_right_for_author_user(self):
        post_id = str(self.post.pk)
        url_names = [
            '/',
            '/group/' + self.group.slug + '/',
            '/profile/' + self.user.get_username() + '/',
            '/posts/' + post_id + '/',
            '/posts/' + post_id + '/edit/',
            '/create/',
        ]
        for url in url_names:
            with self.subTest(url=url):
                response = self.auth_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template_auth_user(self):
        post_id = str(self.post.pk)
        urlnames_templates = {
            '/': 'posts/index.html',
            '/group/' + self.group.slug + '/': 'posts/group_list.html',
            '/profile/' + self.user.get_username() + '/': 'posts/profile.html',
            '/posts/' + post_id + '/': 'posts/post_detail.html',
            '/posts/' + post_id + '/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for url, template in urlnames_templates.items():
            with self.subTest(url=url):
                response = self.auth_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_guest_user(self):
        post_id = str(self.post.pk)
        urlnames_templates = {
            '/': 'posts/index.html',
            '/group/' + self.group.slug + '/': 'posts/group_list.html',
            '/profile/' + self.user.get_username() + '/': 'posts/profile.html',
            '/posts/' + post_id + '/': 'posts/post_detail.html',
        }
        for url, template in urlnames_templates.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_urls_redirect_guest_user(self):
        post_id1 = str(self.post.pk)
        post_id2 = str(self.stranger_post.pk)
        targetUrl_redirectUrl = {
            '/posts/' + post_id1 + '/edit/': '/auth/login/?next=/posts/'
            + post_id1 + '/edit/',
            '/create/': '/auth/login/?next=/create/',
            '/posts/' + post_id2 + '/edit/': '/auth/login/?next=/posts/'
            + post_id2 + '/edit/',
            '/create/': '/auth/login/?next=/create/',
        }
        for target_url, redirect_url in targetUrl_redirectUrl.items():
            with self.subTest(url=target_url):
                response = self.guest_client.get(target_url, follow=True)
                self.assertRedirects(response, redirect_url)

    def test_edit_redirect_for_stranger(self):
        post_id1 = str(self.post.pk)
        targetUrl_redirectUrl = {
            '/posts/' + post_id1 + '/edit/': '/posts/' + post_id1
            + '/',
        }
        for target_url, redirect_url in targetUrl_redirectUrl.items():
            with self.subTest(url=target_url):
                response = self.stranger_client.get(target_url, follow=True)
                self.assertRedirects(response, redirect_url)
