from django.test import TestCase, Client
from django.contrib.auth import get_user_model


User = get_user_model()


class CoreUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create(username='testuser')
        self.auth_client = Client()
        self.auth_client.force_login(self.user)

    def test_non_existent_url(self):
        non_existent_url = '/asdlghlasdhgl/'
        response = self.guest_client.get(non_existent_url)
        self.assertTemplateUsed(response, 'core/404.html')
        response = self.auth_client.get(non_existent_url)
        self.assertTemplateUsed(response, 'core/404.html')
