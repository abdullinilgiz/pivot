import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.cache import cache
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post, Group, Comment, Follow

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='testuser')
        cls.post = Post.objects.create(
            text='This is text #1.',
            author=cls.user,
            pk=0,
        )
        cls.group = Group.objects.create(
            title='This is title',
            slug='testgroup',
            description='test desctription',
        )
        cls.group2 = Group.objects.create(
            title='Second',
            slug='testgroup2',
            description='desctription2',
        )

        cls.stranger_user = User.objects.create(username='testuser2')
        cls.stranger_post = Post.objects.create(
            text='This is text #2.',
            author=cls.stranger_user,
            group=cls.group2,
        )
        for id in range(1, 14):
            Post.objects.create(
                text=f'Post number {id + 2}',
                author=cls.user,
                group=cls.group,
            )

        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='for_context.gif',
            content=cls.small_gif,
            content_type='image/gif',
        )
        cls.post_with_image = Post.objects.create(
            text='Post number 16',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.auth_client = Client()
        self.auth_client.force_login(self.user)
        self.stranger_client = Client()
        self.stranger_client.force_login(self.stranger_user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        post_id = str(self.post.pk)
        urlnames_pagename = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.user.get_username()}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': post_id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': post_id}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in urlnames_pagename.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.auth_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_posts_lists_pages_uses_correct_context(self):
        urlnames_testcase = {
            reverse('posts:index'): {},
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ): {'group': self.group},
            reverse(
                'posts:profile',
                kwargs={'username': self.user.get_username()}
            ): {'author': self.user,
                'posts_number': 15},
        }
        for url, specific_context in urlnames_testcase.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                page_obj = response.context['page_obj']
                post_0 = page_obj[0]
                self.assertEqual(
                    post_0.text,
                    'Post number 16',
                    'Order of the posts is not correct'
                )
                self.assertEqual(
                    post_0.author,
                    self.user,
                    'Author of the post is not correct'
                )
                self.assertEqual(
                    post_0.group,
                    self.group,
                    'Group of the post is not correct'
                )
                for item, value in specific_context.items():
                    self.assertEqual(response.context[item], value)

    def test_posts_lists_pages_show_correct_pagination(self):
        urlnames_testcase = {
            reverse('posts:index'): {'number_of_posts_page1': 10,
                                     'number_of_posts_page2': 6},
            reverse(
                'posts:group_list',
                kwargs={'slug': 'testgroup'}
            ): {'number_of_posts_page1': 10,
                'number_of_posts_page2': 4},
            reverse(
                'posts:profile',
                kwargs={'username': 'testuser'}
            ): {'number_of_posts_page1': 10,
                'number_of_posts_page2': 5},
        }
        for url, testcase in urlnames_testcase.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                page_obj = response.context['page_obj']
                self.assertEqual(
                    len(page_obj),
                    testcase['number_of_posts_page1'],
                    'Paginator do not show correct first page'
                )
                response = self.guest_client.get(url + '?page=2')
                page_obj = response.context['page_obj']
                self.assertEqual(
                    len(page_obj),
                    testcase['number_of_posts_page2'],
                    'Paginator do not show correct last page'
                )

        response = self.guest_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group2.slug}
            )
        )
        page_obj = response.context['page_obj']
        self.assertEqual(
            len(page_obj),
            1,
            'Paginator do not show correct last page'
        )

    def test_post_detail_context(self):
        post_id = str(self.post.pk)
        response = self.guest_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': post_id}
            )
        )
        post = response.context['post']
        author = response.context['author']
        group = response.context['group']
        author_posts_number = response.context['author_posts_number']
        self.assertEqual(
            post.text,
            'This is text #1.',
            'Detailed post pages do not show correct text'
        )
        self.assertEqual(
            post.author,
            self.user,
            'Detailed post pages do not show correct author'
        )
        self.assertIsNone(
            post.group,
            'Detailed post pages do not correct group'
        )
        self.assertEqual(
            author_posts_number,
            15,
            'The number of posts of the author is wrong'
        )

        post_id = str(self.stranger_post.pk)
        response = self.auth_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': post_id}
            )
        )
        post = response.context['post']
        author = response.context['author']
        group = response.context['group']
        author_posts_number = response.context['author_posts_number']
        self.assertEqual(
            post.text,
            'This is text #2.',
            'Detailed post pages do not show correct text'
        )
        self.assertEqual(
            author,
            self.stranger_user,
            'Detailed post pages do not show correct author'
        )
        self.assertEqual(
            group,
            self.group2,
            'Detailed post pages do not correct group'
        )
        self.assertEqual(
            author_posts_number,
            1,
            'The number of posts of the author is wrong'
        )

    def test_post_create_uses_correct_context(self):
        response = self.auth_client.get(reverse('posts:post_create'))
        form = response.context['form']
        formfileds_types = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for field, form_type in formfileds_types.items():
            with self.subTest(field=field):
                self.assertIsInstance(
                    form.fields[field],
                    form_type,
                    'Post creation page has wrong form types'
                )

    def test_post_edit_uses_correct_context(self):
        post_id = self.post.pk
        response = self.auth_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': post_id}
            )
        )
        self.assertEqual(response.context['is_edit'], True)
        self.assertEqual(post_id, response.context['post_id'])
        form = response.context['form']
        formfields_content = {
            'text': 'This is text #1.',
            'group': None,
        }
        for field, content in formfields_content.items():
            with self.subTest(field=field):
                self.assertEqual(form.initial[field], content)

        post = Post.objects.all()[0]
        post_id = post.pk
        response = self.auth_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': post_id}
            )
        )
        self.assertEqual(response.context['is_edit'], True)
        self.assertEqual(post_id, response.context['post_id'])
        form = response.context['form']
        formfields_content = {
            'text': 'Post number 16',
            'group': post.group.pk,
        }
        for field, content in formfields_content.items():
            with self.subTest(field=field):
                self.assertEqual(form[field].value(), content)

    def test_posts_lists_uses_correct_context_for_images(self):
        urls = {
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.user.get_username()}),
        }
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                context = response.context
                first_post = context['page_obj'][0]
                self.assertEqual(first_post.image.name,
                                 'posts/for_context.gif',
                                 'posts:index uses wrong images')

    def test_post_detail_uses_correct_context_for_images(self):
        post_id = self.post_with_image.pk
        response = self.guest_client.get(reverse('posts:post_detail',
                                                 kwargs={'post_id': post_id}))
        context = response.context
        post = context['post']
        self.assertEqual(post.image.name,
                         'posts/for_context.gif',
                         'posts:index uses wrong images')

    def test_post_detail_shows_comments(self):
        post_id = self.post.pk
        form_data = {
            'text': 'Comment by stranger',
        }
        self.stranger_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post_id}),
            data=form_data,
        )
        form_data = {
            'text': 'Comment by auth user',
        }
        self.auth_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post_id}),
            data=form_data,
        )

        response = self.guest_client.get(reverse('posts:post_detail',
                                                 kwargs={'post_id': post_id}))
        comments = response.context['comments']
        self.assertEqual(len(comments),
                         2,
                         'Post detail uses incorrect number of comments')

    def test_post_detail_shows_correct_ordering(self):
        post_id = self.post.pk
        form_data = {
            'text': 'Comment by stranger',
        }
        self.stranger_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post_id}),
            data=form_data,
        )
        form_data = {
            'text': 'Comment by auth user',
        }
        self.auth_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post_id}),
            data=form_data,
        )

        response = self.guest_client.get(reverse('posts:post_detail',
                                                 kwargs={'post_id': post_id}))
        comments = response.context['comments']
        self.assertEqual(comments[0],
                         Comment.objects.all()[0],
                         'This comment should not be first')
        self.assertEqual(comments[1],
                         Comment.objects.all()[1],
                         'This comment should not be second')

    def test_index_cache(self):
        form_data = {
            'text': 'Post that would be deleted',
            'group': self.group.pk,
        }
        self.auth_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        post = Post.objects.filter(text=form_data['text'])[0]
        response_before_delete = self.auth_client.get(reverse('posts:index'))
        post.delete()
        response_after_delete = self.auth_client.get(reverse('posts:index'))
        self.assertEqual(response_after_delete.content,
                         response_before_delete.content)
        cache.clear()
        response_after_clear = self.auth_client.get(reverse('posts:index'))
        self.assertNotEqual(response_after_delete, response_after_clear)

    def test_auth_client_follow(self):
        self.auth_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.stranger_user.get_username()}
        ))
        self.assertTrue(
            Follow.objects.filter(
                user=self.user, author=self.stranger_user
            ).exists(),
            'view do not create create follow object',
        )

    def test_auth_client_unfollow(self):
        Follow.objects.create(user=self.user, author=self.stranger_user)
        self.auth_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.stranger_user.get_username()}
        ))
        self.assertFalse(
            Follow.objects.filter(
                user=self.user, author=self.stranger_user
            ).exists(),
            'view do not delete follow object',
        )

    def test_follow_index_uses_correct_context(self):
        self.auth_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.stranger_user.get_username()}
        ))
        response = self.auth_client.get(reverse('posts:follow_index'))
        page_obj = response.context['page_obj']
        self.assertEqual(
            Post.objects.filter(author=self.stranger_user).count(),
            len(page_obj),
            'following show wrong posts number'
        )
        self.assertEqual(page_obj[0], self.stranger_post)

        response = self.stranger_client.get(reverse('posts:follow_index'))
        page_obj = response.context['page_obj']
        self.assertEqual(
            0,
            len(page_obj),
            'following show wrong posts number'
        )
