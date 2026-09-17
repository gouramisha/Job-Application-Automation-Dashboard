from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class AuthFlowTests(APITestCase):
    def test_register_creates_profile_settings_and_returns_tokens(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "email": "new@example.com",
                "first_name": "New",
                "last_name": "User",
                "password": "StrongPass123!",
                "password_confirm": "StrongPass123!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        user = User.objects.get(email="new@example.com")
        # The post_save signal must have built both one-to-ones, or every
        # profile/settings read would 500 on a fresh account.
        self.assertTrue(hasattr(user, "profile"))
        self.assertTrue(hasattr(user, "settings"))

    def test_register_rejects_mismatched_passwords(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "email": "mismatch@example.com",
                "password": "StrongPass123!",
                "password_confirm": "DifferentPass123!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password_confirm", response.data)

    def test_register_rejects_weak_password(self):
        response = self.client.post(
            "/api/auth/register/",
            {"email": "weak@example.com", "password": "12345678", "password_confirm": "12345678"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_login_returns_user_payload(self):
        User.objects.create_user(email="a@example.com", password="StrongPass123!", first_name="Ada")
        response = self.client.post(
            "/api/auth/login/",
            {"email": "a@example.com", "password": "StrongPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["email"], "a@example.com")
        self.assertEqual(response.data["user"]["full_name"], "Ada")

    def test_endpoints_require_authentication(self):
        for url in ["/api/auth/me/", "/api/jobs/", "/api/resumes/", "/api/analytics/dashboard/"]:
            with self.subTest(url=url):
                self.assertEqual(
                    self.client.get(url).status_code, status.HTTP_401_UNAUTHORIZED
                )


class ProfileTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="p@example.com", password="StrongPass123!", first_name="Pat"
        )
        self.client.force_authenticate(self.user)

    def test_profile_update_writes_through_to_user_names(self):
        response = self.client.patch(
            "/api/auth/profile/",
            {"first_name": "Patricia", "phone": "+1 555 0100", "skills": "Python, Django"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Patricia")
        self.assertEqual(self.user.profile.phone, "+1 555 0100")

    def test_as_form_values_flattens_profile_for_the_form_filler(self):
        profile = self.user.profile
        profile.phone = "+1 555 0100"
        profile.city, profile.country = "Austin", "USA"
        profile.requires_sponsorship = True
        profile.custom_answers = {"Why here?": "Great team"}
        profile.save()

        values = profile.as_form_values()
        self.assertEqual(values["email"], "p@example.com")
        self.assertEqual(values["phone"], "+1 555 0100")
        self.assertEqual(values["location"], "Austin, USA")
        self.assertEqual(values["requires_sponsorship"], "Yes")
        # Custom answers are merged in so the filler can answer free-text
        # screening questions it has seen before.
        self.assertEqual(values["Why here?"], "Great team")

    def test_change_password_rejects_wrong_current_password(self):
        response = self.client.post(
            "/api/auth/change-password/",
            {"current_password": "WrongPass123!", "new_password": "BrandNewPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
