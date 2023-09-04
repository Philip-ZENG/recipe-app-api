"""
Tests for the ingredients API endpoint.
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


def detail_url(ingredient_id):
    """Create and return an ingredient detail URL."""
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


def create_user(email='user@example.com', password='test123'):
    """Create and return a new user."""
    return get_user_model().objects.create_user(email, password)


class PublicIngredientsApiTests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test authentication is required for retrieving ingredients."""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        """Test retrieving a list of ingredients."""
        # Create some sample ingredients
        Ingredient.objects.create(user=self.user, name='Kale')
        Ingredient.objects.create(user=self.user, name='Salt')

        # Make a request to retrieve ingredient lists
        res = self.client.get(INGREDIENTS_URL)

        # Get all ingredients from the database
        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        # Check that the response is correct
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # API response data == serializer data
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Test list of ingredients is limited to authenticated user."""
        # Create a new unauthenticated user
        user2 = create_user(email='user2@example.com')
        # Create some sample ingredients
        Ingredient.objects.create(user=user2, name='Vinegar')
        ingredient = Ingredient.objects.create(user=self.user, name='Tumeric')

        # Make a request to retrieve ingredient lists
        res = self.client.get(INGREDIENTS_URL)

        # Check that the response is correct
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Check that the response contains only the ingredient created by the
        # authenticated user
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)

    def test_update_ingredient(self):
        """Test updating an ingredient."""
        # Create a sample ingredient
        ingredient = Ingredient.objects.create(user=self.user, name='Vinegar')

        payload = {'name': 'Apple Cider Vinegar'}
        url = detail_url(ingredient.id)
        # Make a request to update the ingredient
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Refresh the ingredient from the database
        ingredient.refresh_from_db()
        # Check that the ingredient was updated
        self.assertEqual(ingredient.name, payload['name'])

    def test_delete_ingredients(self):
        """Tsst deleting an ingredient."""
        # Create a sample ingredient
        ingredient = Ingredient.objects.create(user=self.user, name='Vinegar')

        url = detail_url(ingredient.id)
        # Make a request to delete the ingredient
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        # Check that the ingredient was deleted
        self.assertFalse(Ingredient.objects.filter(user=self.user).exists())
