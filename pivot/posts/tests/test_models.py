from django.contrib.auth import get_user_model
from django.test import TestCase
from posts.models import Post, Group

User = get_user_model()


class PostsModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='This is title',
            slug='test_group',
            description='test desctription',
        )
        cls.user = User.objects.create(username='testuser')
        cls.post = Post.objects.create(
            text='This is text. And another symbols for lenth.',
            author=cls.user,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = self.group
        self.assertEqual(
            group.__str__(),
            'This is title',
            '__str__ method for Group do not woirk correct'
        )

        post = self.post
        self.assertEqual(
            post.__str__(),
            'This is text. And another symbols for lenth.'[:15],
            '__str__ method for Post do not woirk correct'
        )
