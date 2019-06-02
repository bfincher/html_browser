from .test_admin_view import BaseAdminTest
from .test_base_view import contextCheck
from django.urls import reverse
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

class UserTest(BaseAdminTest):
    def testUserAdminView(self):
        self.login(self.user4)
        response = self.client.get(reverse('userAdmin'))
        self.assertEquals(200, response.status_code)
        context = response.context[0]
        contextCheck(self, context)
        self.assertEquals('admin/user_admin.html', response.templates[0].name)

        self.assertEquals(len(self.users), len(context['users']))
        
        contextUsernames = [user.username for user in context['users']]
        for user in self.users:
            self.assertTrue(user in contextUsernames)

        self.logout()
        self.login(self.user1)
        response = self.client.get(reverse('userAdmin'))
        self.assertEquals(302, response.status_code)
        self.assertEquals('/?next=/userAdmin/', response.url)

    def testEditUser(self):
        #test unauthorized user
        self.login(self.user1)
        response = self.client.get(reverse('editUser', args=[self.user1.username]))
        self.assertEquals(302, response.status_code)
        self.assertEquals('/?next=/editUser/user1/', response.url)
        
        self.login(self.user4)
        response = self.client.get(reverse('editUser', args=[self.user1.username]))
        self.assertEquals(200, response.status_code)
        context = response.context[0]
        contextCheck(self, context)
        self.assertEquals(self.user4.username, context['user'].username)
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
        self.assertEquals(302, response.status_code)
        self.assertEqual('/userAdmin/', response.url)
        newUser1 = User.objects.get(username = self.user1.username)
        self.assertEqual('firstname', newUser1.first_name)
        self.assertEqual('lastname', newUser1.last_name)
        self.assertEqual('nobody@whocares.com', newUser1.email)
        self.assertTrue(newUser1.is_superuser)
        self.assertFalse(newUser1.is_active)

    def testEditPassword(self):
        self.login(self.user4)
        response = self.client.get(reverse('editUser', args=[self.user1.username]))
        self.assertEquals(200, response.status_code)
        context = response.context[0]
        contextCheck(self, context)
        self.assertEquals(self.user4.username, context['user'].username)
        self.assertEqual("admin/add_edit_user.html", response.templates[0].name)

        data = {'username': self.user1.username,
                'userPk': self.user1.pk,
                'password': 'newPassword', 
                'verifyPassword': 'newPassword',
                'is_active': True
            }

        response = self.client.post(reverse('editUser', args=[self.user1.username]), data, follow=True)
        self.assertEquals(200, response.status_code)
        self.assertEqual("admin/user_admin.html", response.templates[0].name)
        self.assert_message_count(response, 0)
        self.assertTrue(authenticate(username=self.user1.username, password='newPassword'))
        self.logout()
        response = self.login(self.user1, 'newPassword', follow=True)
        self.assert_message_count(response, 0)
        
    def testSetGroup(self):
        self.login(self.user4)
        response = self.client.get(reverse('editUser', args=[self.user1.username]))
        self.assertEquals(200, response.status_code)
        context = response.context[0]
        contextCheck(self, context)
        self.assertEquals(self.user4.username, context['user'].username)
        self.assertEqual("admin/add_edit_user.html", response.templates[0].name)
        
        data = {'username': self.user1.username,
                'first_name': 'firstname', 
                'last_name': 'lastname', 
                'email': 'nobody@whocares.com',
                'userPk': self.user1.pk,
                'is_superuser': True, 
                'is_active': False,
                'groups': '1'
        }

        response = self.client.post(reverse('editUser', args=[self.user1.username]), data)
        self.assertEquals(302, response.status_code)
        self.assertEqual('/userAdmin/', response.url)
        newUser1 = User.objects.get(username = self.user1.username)
        self.assertEqual('firstname', newUser1.first_name)
        self.assertEqual('lastname', newUser1.last_name)
        self.assertEqual('nobody@whocares.com', newUser1.email)
        self.assertTrue(newUser1.is_superuser)
        self.assertFalse(newUser1.is_active)