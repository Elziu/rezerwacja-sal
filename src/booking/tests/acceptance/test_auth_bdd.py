import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from django.contrib.auth import get_user_model, authenticate

User = get_user_model()

pytestmark = pytest.mark.django_db

scenarios('features/auth.feature')

@pytest.fixture
def context():
    return {}

@given(parsers.parse('istnieje użytkownik "{username}" z hasłem "{password}"'))
def create_regular_user(username, password):
    User.objects.create_user(username=username, password=password)

@given(parsers.parse('istnieje administrator "{username}" z hasłem "{password}"'))
def create_admin_user(username, password):
    User.objects.create_superuser(username=username, password=password)

@when(parsers.parse('użytkownik loguje się używając loginu "{username}" i hasła "{password}"'))
def attempt_login(context, username, password):
    # Since we are testing at Service/Model layer, simple authenticate check implies logic works.
    # For full integration, we'd use client.login() or selenium, but pytest-bdd often used for business logic.
    # We will simulate authentication check.
    user = authenticate(username=username, password=password)
    context['authenticated_user'] = user

@then('logowanie powinno się powieść')
def check_login_success(context):
    assert context['authenticated_user'] is not None

@then('użytkownik powinien mieć uprawnienia zwykłego pracownika')
def check_regular_permissions(context):
    user = context['authenticated_user']
    assert not user.is_staff
    assert not user.is_superuser

@then('użytkownik powinien mieć uprawnienia administratora')
def check_admin_permissions(context):
    user = context['authenticated_user']
    assert user.is_superuser

@then('logowanie powinno się nie udać')
def check_login_failed(context):
    assert context['authenticated_user'] is None
