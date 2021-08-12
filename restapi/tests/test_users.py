# import pytest
from app import app
from .operationtest import OperationTest

class TestUser(OperationTest):
    prefix = "/users"

    def test_validation_login_user(self,client):
        url = self.prefix + '/login'
        # field required
        response = client.post(url,json={})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'email': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'password': assert x['msg'] == 'field required'
        # email & password blank
        response = client.post(url,json={'email':'','password':''})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'email': assert x['msg'] == 'value is not a valid email address'
            if x['loc'][-1] == 'password': assert x['msg'] == 'ensure this value has at least 6 characters'
        # test limit value
        response = client.post(url,json={'email': 'a' * 200 + '@example.com', 'password': 'a' * 200})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'email': assert x['msg'] == 'value is not a valid email address'
            if x['loc'][-1] == 'password': assert x['msg'] == 'ensure this value has at most 100 characters'
        # check all field type data
        response = client.post(url,json={'email':123,'password':123})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'email': assert x['msg'] == 'value is not a valid email address'
            if x['loc'][-1] == 'password': assert x['msg'] == 'str type expected'
        # invalid email format
        response = client.post(url,json={'email':'asdd@gmasd','password':'asdasd'})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'email': assert x['msg'] == 'value is not a valid email address'
        # invalid credential
        response = client.post(url,json={'email': self.account_admin['email'],'password':'asdasd'})
        assert response.status_code == 422
        assert response.json() == {"detail":"Invalid credential."}

    def test_login_user(self,client):
        url = self.prefix + '/login'

        response = client.post(url,json={'email': self.account_admin['email'], 'password': self.account_admin['password']})
        assert response.status_code == 200
        assert response.json() == {"detail":"Successfully login."}
        # check cookies exists
        assert response.cookies.get('access_token_cookie') is not None
        assert response.cookies.get('csrf_access_token') is not None

        assert response.cookies.get('refresh_token_cookie') is not None
        assert response.cookies.get('csrf_refresh_token') is not None

    def test_validation_fresh_token(self,client):
        url = self.prefix + '/fresh-token'
        # field required
        response = client.post(url,json={})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'password': assert x['msg'] == 'field required'
        # all field blank
        response = client.post(url,json={'password':''})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'password': assert x['msg'] == 'ensure this value has at least 6 characters'
        # test limit value
        response = client.post(url,json={'password':'a' * 200})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'password': assert x['msg'] == 'ensure this value has at most 100 characters'
        # check all type data
        response = client.post(url,json={'password': 123})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'password': assert x['msg'] == 'str type expected'
        # user login
        response = client.post(self.prefix + '/login',json={
            'email': self.account_admin['email'],
            'password': self.account_admin['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')
        # password not same as database
        response = client.post(url,headers={'X-CSRF-TOKEN': csrf_access_token},json={'password': 'asdasd'})
        assert response.status_code == 422
        assert response.json() == {"detail":"Password does not match with our records."}

    def test_fresh_token(self,client):
        # user login
        response = client.post(self.prefix + '/login',json={
            'email': self.account_admin['email'],
            'password': self.account_admin['password']
        })
        access_token_cookie = response.cookies.get('access_token_cookie')
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/fresh-token'

        response = client.post(url,
            headers={'X-CSRF-TOKEN': csrf_access_token},
            json={'password': self.account_admin['password']}
        )
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully make a fresh token."}
        # access token not same anymore
        assert access_token_cookie != response.cookies.get('access_token_cookie')
        assert csrf_access_token != response.cookies.get('csrf_access_token')

    def test_refresh_token(self,client):
        url = self.prefix + '/login'
        # login to get token from cookie
        response = client.post(url,json={'email': self.account_admin['email'], 'password': self.account_admin['password']})
        # set cookie to variable
        access_token_cookie = response.cookies.get('access_token_cookie')
        csrf_access_token = response.cookies.get('csrf_access_token')
        csrf_refresh_token = response.cookies.get('csrf_refresh_token')

        # refresh the token
        url = self.prefix + '/refresh-token'
        response = client.post(url,headers={"X-CSRF-TOKEN": csrf_refresh_token})
        assert response.status_code == 200
        assert response.json() == {'detail': 'The token has been refreshed.'}

        # check access cookie not same again
        assert access_token_cookie != response.cookies.get('access_token_cookie')
        assert csrf_access_token != response.cookies.get('csrf_access_token')

    def test_revoke_access_token(self,client,authorize):
        # login to get token from cookie
        url = self.prefix + '/login'
        response = client.post(url,json={'email': self.account_admin['email'], 'password': self.account_admin['password']})
        # set token and csrf to variable
        access_token_cookie = response.cookies.get('access_token_cookie')
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/access-revoke'
        response = client.delete(url,headers={"X-CSRF-TOKEN": csrf_access_token})
        assert response.status_code == 200
        assert response.json() == {'detail': 'An access token has revoked.'}
        # check token has been revoked
        response = client.delete(url,headers={"X-CSRF-TOKEN": csrf_access_token})
        assert response.status_code == 401
        assert response.json() == {"detail": "Token has been revoked"}
        # check jti store in redis
        jti = authorize.get_raw_jwt(access_token_cookie)['jti']
        assert app.state.redis.get(jti) == "true"

    def test_revoke_refresh_token(self,client,authorize):
        # login to get token from cookie
        url = self.prefix + '/login'
        response = client.post(url,json={'email': self.account_admin['email'], 'password': self.account_admin['password']})
        # set token and csrf to variable
        refresh_token_cookie = response.cookies.get('refresh_token_cookie')
        csrf_refresh_token = response.cookies.get('csrf_refresh_token')

        url = self.prefix + '/refresh-revoke'
        response = client.delete(url,headers={"X-CSRF-TOKEN": csrf_refresh_token})
        assert response.status_code == 200
        assert response.json() == {"detail": "An refresh token has revoked."}
        # check token has been revoked
        response = client.delete(url,headers={"X-CSRF-TOKEN": csrf_refresh_token})
        assert response.status_code == 401
        assert response.json() == {"detail": "Token has been revoked"}
        # check jti store in redis
        jti = authorize.get_raw_jwt(refresh_token_cookie)['jti']
        assert app.state.redis.get(jti) == "true"

    def test_delete_all_cookies(self,client):
        url = self.prefix + '/login'

        response = client.post(url,json={'email': self.account_admin['email'], 'password': self.account_admin['password']})
        assert response.status_code == 200
        assert response.json() == {"detail":"Successfully login."}
        # check cookies exists
        assert response.cookies.get('access_token_cookie') is not None
        assert response.cookies.get('csrf_access_token') is not None

        assert response.cookies.get('refresh_token_cookie') is not None
        assert response.cookies.get('csrf_refresh_token') is not None

        url = self.prefix + '/delete-cookies'

        response = client.delete(url)
        assert response.status_code == 200
        assert response.json() == {"detail":"All cookies have been deleted."}
        # check cookies doesn't exists
        assert response.cookies.get('access_token_cookie') is None
        assert response.cookies.get('csrf_access_token') is None

        assert response.cookies.get('refresh_token_cookie') is None
        assert response.cookies.get('csrf_refresh_token') is None

    def test_validation_update_password(self,client):
        url = self.prefix + '/update-password'
        # field required
        response = client.put(url,json={})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'old_password': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'password': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'confirm_password': assert x['msg'] == 'field required'
        # all field blank
        response = client.put(url,json={'old_password':'','password':'','confirm_password':''})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'old_password': assert x['msg'] == 'ensure this value has at least 6 characters'
            if x['loc'][-1] == 'password': assert x['msg'] == 'ensure this value has at least 6 characters'
            if x['loc'][-1] == 'confirm_password': assert x['msg'] == 'ensure this value has at least 6 characters'
        # test limit value
        response = client.put(url,json={
            'old_password': 'a' * 200,
            'password': 'a' * 200,
            'confirm_password': 'a' * 200
        })
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'old_password': assert x['msg'] == 'ensure this value has at most 100 characters'
            if x['loc'][-1] == 'password': assert x['msg'] == 'ensure this value has at most 100 characters'
            if x['loc'][-1] == 'confirm_password': assert x['msg'] == 'ensure this value has at most 100 characters'
        # check all field type data
        response = client.put(url,json={'old_password':123,'password':123,'confirm_password':123})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'old_password': assert x['msg'] == 'str type expected'
            if x['loc'][-1] == 'password': assert x['msg'] == 'str type expected'
            if x['loc'][-1] == 'confirm_password': assert x['msg'] == 'str type expected'
        # check password same as confirm_password
        response = client.put(url,json={'password':'asdasd','confirm_password':'asdasdasd'})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'password': assert x['msg'] == 'password must match with password confirmation'
        # user login
        response = client.post(self.prefix + '/login',json={
            'email': self.account_admin['email'],
            'password': self.account_admin['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')
        # old password not same as database
        response = client.put(url,
            headers={"X-CSRF-TOKEN": csrf_access_token},
            json={
                'old_password': 'asdasd',
                'password': self.account_admin['password'],
                'confirm_password': self.account_admin['password']
            }
        )
        assert response.status_code == 422
        assert response.json() == {"detail": "Password does not match with our records."}

    def test_update_password(self,client):
        url = self.prefix + '/update-password'
        # user login
        response = client.post(self.prefix + '/login',json={
            'email': self.account_admin['email'],
            'password': self.account_admin['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        response = client.put(url,
            headers={"X-CSRF-TOKEN": csrf_access_token},
            json={'old_password': self.account_admin['password'],'password':'asdasd','confirm_password':'asdasd'}
        )
        assert response.status_code == 200
        assert response.json() == {"detail": "Success update your password."}
