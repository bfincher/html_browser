from annoying.functions import get_object_or_None
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.urls import reverse

from html_browser.models import Group

from .test_admin_view import BaseAdminTest
from .test_base_view import contextCheck


class UserTest(BaseAdminTest):
    def testUserAdminView(self):
        self.login(self.user4)
        response = self.client.get(reverse('userAdmin'))
        self.assertEqual(200, response.status_code)
        context = response.context[0]
        contextCheck(self, context)
        self.assertEqual('admin/user_admin.html', response.templates[0].name)

        self.assertEqual(len(self.users), len(context['users']))

        contextUsernames = [user.username for user in context['users']]
        for user in self.users:
            self.assertTrue(user in contextUsernames)

        self.logout()
        self.login(self.user1)
        response = self.client.get(reverse('userAdmin'))
        self.assertEqual(302, response.status_code)
        self.assertEqual('/?next=/userAdmin/', response.url)

    def testEditUser(self):
        # test unauthorized user
        self.login(self.user1)
        response = self.client.get(reverse('editUser', args=[self.user1.username]))
        self.assertEqual(302, response.status_code)
        self.assertEqual('/?next=/editUser/user1/', response.url)

        self.login(self.user4)
        response = self.client.get(reverse('editUser', args=[self.user1.username]))
        self.assertEqual(200, response.status_code)
        context = response.context[0]
        contextCheck(self, context)
        self.assertEqual(self.user4.username, context['user'].username)
        self.assertEqual("admin/add_edit_user.html", response.templates[0].name)

        data = {'username': self.user1.username,
                'first_name': 'firstname',
                'last_name': 'lastname',
                'email': 'nobody@whocares.com',
                'userPk': self.user1.pk,
                'is_superuser': True,
                'is_active': False
                }

        response = self.client.post(reverse('editUser', args=[self.user1.username]), data)
        self.assertEqual(302, response.status_code)
        self.assertEqual('/userAdmin/', response.url)
        newUser1 = User.objects.get(username=self.user1.username)
        self.assertEqual('firstname', newUser1.first_name)
        self.assertEqual('lastname', newUser1.last_name)
        self.assertEqual('nobody@whocares.com', newUser1.email)
        self.assertTrue(newUser1.is_superuser)
        self.assertFalse(newUser1.is_active)
        
    def testDeleteUser(self):
        # test unauthorized user
        self.login(self.user1)
        response = self.client.post(reverse('deleteUser', args=[self.user2.username]))
        self.assertEqual(302, response.status_code)
        self.assertEqual('/?next=/deleteUser/user2', response.url)
        self.assertEqual(self.user2, User.objects.get(username=self.user2.username))
        
        self.login(self.user4)
        # test deleting current user
        response = self.client.post(reverse('deleteUser', args=[self.user4.username]))
        self.assertEqual('/userAdmin/', response.url)
        self.assertEqual(self.user4, User.objects.get(username=self.user4.username))
        
        response = self.client.post(reverse('deleteUser', args=[self.user1.username]))
        self.assertEqual(302, response.status_code)
        self.assertEqual('/userAdmin/', response.url)
        self.assertIsNone(get_object_or_None(User, username=self.user1.username))

    def testEditPassword(self):
        self.login(self.user4)
        response = self.client.get(reverse('editUser', args=[self.user1.username]))
        self.assertEqual(200, response.status_code)
        context = response.context[0]
        contextCheck(self, context)
        self.assertEqual(self.user4.username, context['user'].username)
        self.assertEqual("admin/add_edit_user.html", response.templates[0].name)

        data = {'username': self.user1.username,
                'userPk': self.user1.pk,
                'password': 'newPassword',
                'verifyPassword': 'newPassword',
                'is_active': True
                }

        response = self.client.post(reverse('editUser', args=[self.user1.username]), data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual("admin/user_admin.html", response.templates[0].name)
        self.assert_message_count(response, 0)
        self.assertTrue(authenticate(username=self.user1.username, password='newPassword'))
        self.logout()
        response = self.login(self.user1, 'newPassword', follow=True)
        self.assert_message_count(response, 0)

    def testSetGroup(self):
        self.login(self.user4)
        response = self.client.get(reverse('editUser', args=[self.user1.username]))
        self.assertEqual(200, response.status_code)
        context = response.context[0]
        contextCheck(self, context)
        self.assertEqual(self.user4.username, context['user'].username)
        self.assertEqual("admin/add_edit_user.html", response.templates[0].name)

        groupPk = str(Group.objects.get(name=self.group1.name).pk)

        data = {'username': self.user1.username,
                'first_name': 'firstname',
                'last_name': 'lastname',
                'email': 'nobody@whocares.com',
                'userPk': self.user1.pk,
                'is_superuser': True,
                'is_active': False,
                'groups': groupPk
                }

        response = self.client.post(reverse('editUser', args=[self.user1.username]), data)
        self.assertEqual(302, response.status_code)
        self.assertEqual('/userAdmin/', response.url)
        newUser1 = User.objects.get(username=self.user1.username)
        self.assertEqual('firstname', newUser1.first_name)
        self.assertEqual('lastname', newUser1.last_name)
        self.assertEqual('nobody@whocares.com', newUser1.email)
        self.assertTrue(newUser1.is_superuser)
        self.assertFalse(newUser1.is_active)
        self.assertEqual(1, newUser1.groups.count())
        self.assertTrue(self.group1 in newUser1.groups.all())
