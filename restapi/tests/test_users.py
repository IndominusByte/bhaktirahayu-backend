import pytest
from app import app
from pathlib import Path
from .operationtest import OperationTest

class TestUser(OperationTest):
    prefix = "/users"

    @pytest.mark.asyncio
    async def test_create_user(self,async_client):
        # create user admin
        await self.create_user(role='admin',**self.account_admin)
        # create user doctor 1
        await self.create_user(role='doctor',signature='signature_test.png',**self.account_1)

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
            json={
                'old_password': self.account_admin['password'],
                'password': self.account_admin['password'],
                'confirm_password': self.account_admin['password']
            }
        )
        assert response.status_code == 200
        assert response.json() == {"detail": "Success update your password."}

    def test_validation_update_account(self,client):
        url = self.prefix + '/update-account'
        # field required
        response = client.put(url,data={})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'email': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'username': assert x['msg'] == 'field required'
        # all field blank
        response = client.put(url,data={'email': ' ', 'username': ' '})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'email': assert x['msg'] == 'value is not a valid email address'
            if x['loc'][-1] == 'username': assert x['msg'] == 'ensure this value has at least 3 characters'
        # test limit value
        response = client.put(url,data={'email': 'a' * 200 + '@example.com', 'username': 'a' * 200})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'email': assert x['msg'] == 'value is not a valid email address'
            if x['loc'][-1] == 'username': assert x['msg'] == 'ensure this value has at most 100 characters'
        # check valid email
        response = client.put(url,data={'email':'asdsd@asd'})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'email': assert x['msg'] == 'value is not a valid email address'

        # danger file extension
        with open(self.test_image_dir + 'test.txt','rb') as tmp:
            response = client.put(url,files={'image': tmp})
            assert response.status_code == 422
            assert response.json() == {'detail': 'Cannot identify the image.'}
        # not valid file extension
        with open(self.test_image_dir + 'test.gif','rb') as tmp:
            response = client.put(url,files={'image': tmp})
            assert response.status_code == 422
            assert response.json() == {'detail': 'Image must be between jpg, png, jpeg.'}
        # file cannot grater than 5 Mb
        with open(self.test_image_dir + 'size.jpeg','rb') as tmp:
            response = client.put(url,files={'image': tmp})
            assert response.status_code == 413
            assert response.json() == {'detail':'An image cannot greater than 5 Mb.'}

    @pytest.mark.asyncio
    async def test_update_account(self,async_client):
        # user admin login
        response = await async_client.post('/users/login',json={
            'email': self.account_admin['email'],
            'password': self.account_admin['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/update-account'

        # only doctor can upload signature
        with open(self.test_image_dir + 'image.jpeg','rb') as tmp:
            response = await async_client.put(url,
                data={'email': self.account_admin['email'], 'username': self.account_admin['username']},
                files={'image': tmp},
                headers={'X-CSRF-TOKEN': csrf_access_token}
            )
            assert response.status_code == 400
            assert response.json() == {"detail": "The only a doctor can change signature."}

        # check email duplicate
        response = await async_client.put(url,
            data={'email': self.account_1['email'], 'username': self.account_1['username']},
            headers={'X-CSRF-TOKEN': csrf_access_token}
        )
        assert response.status_code == 400
        assert response.json() == {"detail": "The email has already been taken."}

        response = await async_client.put(url,
            data={'email': self.account_admin['email'], 'username': self.account_admin['username']},
            headers={'X-CSRF-TOKEN': csrf_access_token}
        )
        assert response.status_code == 200
        assert response.json() == {"detail": "Success updated your account."}

        # user doctor login
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        # doctor update signature
        with open(self.test_image_dir + 'image.jpeg','rb') as tmp:
            response = await async_client.put(url,
                data={'email': self.account_1['email'], 'username': self.account_1['username']},
                files={'image': tmp},
                headers={'X-CSRF-TOKEN': csrf_access_token}
            )
            assert response.status_code == 200
            assert response.json() == {"detail": "Success updated your account."}

        # check file signature exists in directory
        signature = await self.get_user_signature(self.account_1['email'])
        assert Path(self.signature_dir + signature).is_file() is True
        # detele signature in directory
        Path(self.signature_dir + signature).unlink()

    def test_my_user(self,client):
        url = self.prefix + '/my-user'

        # user login
        client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })

        response = client.get(url)
        assert response.status_code == 200
        assert 'id' in response.json()
        assert 'username' in response.json()
        assert 'email' in response.json()
        assert 'role' in response.json()
        assert 'signature' in response.json()
        assert 'created_at' in response.json()
        assert 'updated_at' in response.json()

    def test_validation_create_doctor(self,client):
        url = self.prefix + '/create-doctor'
        # field required
        response = client.post(url,data={})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'image': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'email': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'username': assert x['msg'] == 'field required'
        # all field blank
        response = client.post(url,data={'email': ' ', 'username': ' '})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'email': assert x['msg'] == 'value is not a valid email address'
            if x['loc'][-1] == 'username': assert x['msg'] == 'ensure this value has at least 3 characters'
        # test limit value
        response = client.post(url,data={'email': 'a' * 200 + '@example.com', 'username': 'a' * 200})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'email': assert x['msg'] == 'value is not a valid email address'
            if x['loc'][-1] == 'username': assert x['msg'] == 'ensure this value has at most 100 characters'
        # check valid email
        response = client.post(url,data={'email':'asdsd@asd'})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'email': assert x['msg'] == 'value is not a valid email address'

        # danger file extension
        with open(self.test_image_dir + 'test.txt','rb') as tmp:
            response = client.post(url,files={'image': tmp})
            assert response.status_code == 422
            assert response.json() == {'detail': 'Cannot identify the image.'}
        # not valid file extension
        with open(self.test_image_dir + 'test.gif','rb') as tmp:
            response = client.post(url,files={'image': tmp})
            assert response.status_code == 422
            assert response.json() == {'detail': 'Image must be between jpg, png, jpeg.'}
        # file cannot grater than 5 Mb
        with open(self.test_image_dir + 'size.jpeg','rb') as tmp:
            response = client.post(url,files={'image': tmp})
            assert response.status_code == 413
            assert response.json() == {'detail':'An image cannot greater than 5 Mb.'}

    @pytest.mark.asyncio
    async def test_create_doctor(self,async_client):
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/create-doctor'
        # check user is admin
        with open(self.test_image_dir + 'image.jpeg','rb') as tmp:
            response = await async_client.post(url,
                data={'email': self.account_2['email'], 'username': self.account_2['username']},
                files={'image': tmp},
                headers={'X-CSRF-TOKEN': csrf_access_token}
            )
            assert response.status_code == 401
            assert response.json() == {"detail": "Only users with admin privileges can do this action."}

        # user admin login
        response = await async_client.post('/users/login',json={
            'email': self.account_admin['email'],
            'password': self.account_admin['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        # check email duplicate
        with open(self.test_image_dir + 'image.jpeg','rb') as tmp:
            response = await async_client.post(url,
                data={'email': self.account_1['email'], 'username': self.account_1['username']},
                files={'image': tmp},
                headers={'X-CSRF-TOKEN': csrf_access_token}
            )
            assert response.status_code == 400
            assert response.json() == {"detail": "The email has already been taken."}

        with open(self.test_image_dir + 'image.jpeg','rb') as tmp:
            response = await async_client.post(url,
                data={'email': self.account_2['email'], 'username': self.account_2['username']},
                files={'image': tmp},
                headers={'X-CSRF-TOKEN': csrf_access_token}
            )
            assert response.status_code == 201
            assert response.json() == {"detail": "Successfully add a new doctor."}

        # check file signature exists in directory
        signature = await self.get_user_signature(self.account_2['email'])
        assert Path(self.signature_dir + signature).is_file() is True
        # detele signature in directory
        Path(self.signature_dir + signature).unlink()

    def test_validation_get_all_doctors(self,client):
        url = self.prefix + '/all-doctors'
        # field required
        response = client.get(url)
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'page': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'per_page': assert x['msg'] == 'field required'
        # all field blank
        response = client.get(url + '?page=0&per_page=0&q=')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'page': assert x['msg'] == 'ensure this value is greater than 0'
            if x['loc'][-1] == 'per_page': assert x['msg'] == 'ensure this value is greater than 0'
            if x['loc'][-1] == 'q': assert x['msg'] == 'ensure this value has at least 1 characters'
        # check all field type data
        response = client.get(url + '?page=a&per_page=a&q=123')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'page': assert x['msg'] == 'value is not a valid integer'
            if x['loc'][-1] == 'per_page': assert x['msg'] == 'value is not a valid integer'

    def test_get_all_doctors(self,client):
        client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })

        url = self.prefix + '/all-doctors'

        response = client.get(url + '?page=1&per_page=1&q=' + self.account_1['email'])
        assert response.status_code == 200
        assert 'data' in response.json()
        assert 'total' in response.json()
        assert 'next_num' in response.json()
        assert 'prev_num' in response.json()
        assert 'page' in response.json()
        assert 'iter_pages' in response.json()

        # check data exists and type data
        assert type(response.json()['data'][0]['users_id']) == str
        assert type(response.json()['data'][0]['users_username']) == str
        assert type(response.json()['data'][0]['users_email']) == str
        assert type(response.json()['data'][0]['users_signature']) == str

    def test_validation_get_multiple_doctors(self,client):
        url = self.prefix + '/get-multiple-doctors'
        # field required
        response = client.post(url,json={})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'list_id': assert x['msg'] == 'field required'
        # all field blank
        response = client.post(url,json={'list_id': []})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'list_id': assert x['msg'] == 'ensure this value has at least 1 items'

        response = client.post(url,json={'list_id': ['']})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 0: assert x['msg'] == 'ensure this value has at least 1 characters'
        # check all field type data
        response = client.post(url,json={'list_id': '123'})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'list_id': assert x['msg'] == 'value is not a valid list'

        response = client.post(url,json={'list_id': [1]})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 0: assert x['msg'] == 'str type expected'
        # invalid format
        response = client.post(url,json={'list_id': ['1A']})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 0: assert x['msg'] == 'string does not match regex \"^[0-9]*$\"'

    @pytest.mark.asyncio
    async def test_get_multiple_doctors(self,async_client):
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/get-multiple-doctors'

        user_id = await self.get_user_id(self.account_1['email'])
        # user not found
        response = await async_client.post(url,json={'list_id': ['9' * 8]},headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 200
        assert response.json() == []

        response = await async_client.post(url,json={'list_id': [str(user_id)]},headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 200
        # check data exists and type data
        assert type(response.json()[0]['users_id']) == str
        assert type(response.json()[0]['users_username']) == str

    @pytest.mark.asyncio
    async def test_reset_password_doctor(self,async_client):
        url = self.prefix + '/reset-password-doctor/'
        # all field blank
        response = await async_client.put(url + '0')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'doctor_id': assert x['msg'] == 'ensure this value is greater than 0'
        # check all field type data
        response = await async_client.put(url + 'a')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'doctor_id': assert x['msg'] == 'value is not a valid integer'

        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        user_id = await self.get_user_id(self.account_admin['email'])
        # check user is admin
        response = await async_client.put(url + str(user_id),headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 401
        assert response.json() == {"detail": "Only users with admin privileges can do this action."}
        # user admin login
        response = await async_client.post('/users/login',json={
            'email': self.account_admin['email'],
            'password': self.account_admin['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')
        # doctor not found
        response = await async_client.put(url + '9' * 8,headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 404
        assert response.json() == {"detail": "Doctor not found!"}
        # check user is not admin
        response = await async_client.put(url + str(user_id),headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 400
        assert response.json() == {"detail": "You can only reset the password of a doctor account."}

        user_id = await self.get_user_id(self.account_1['email'])

        response = await async_client.put(url + str(user_id),headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully reset the password of the doctor."}

    def test_validation_update_doctor(self,client):
        url = self.prefix + '/update-doctor/'
        # field required
        response = client.put(url + '0',data={})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'email': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'username': assert x['msg'] == 'field required'
        # all field blank
        response = client.put(url + '0',data={'email': ' ', 'username': ' '})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'doctor_id': assert x['msg'] == 'ensure this value is greater than 0'
            if x['loc'][-1] == 'email': assert x['msg'] == 'value is not a valid email address'
            if x['loc'][-1] == 'username': assert x['msg'] == 'ensure this value has at least 3 characters'
        # test limit value
        response = client.put(url + '1',data={'email': 'a' * 200 + '@example.com', 'username': 'a' * 200})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'email': assert x['msg'] == 'value is not a valid email address'
            if x['loc'][-1] == 'username': assert x['msg'] == 'ensure this value has at most 100 characters'
        # check all field type data
        response = client.put(url + 'a')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'doctor_id': assert x['msg'] == 'value is not a valid integer'
        # check valid email
        response = client.put(url + '1',data={'email':'asdsd@asd'})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'email': assert x['msg'] == 'value is not a valid email address'

        # danger file extension
        with open(self.test_image_dir + 'test.txt','rb') as tmp:
            response = client.put(url + '1',files={'image': tmp})
            assert response.status_code == 422
            assert response.json() == {'detail': 'Cannot identify the image.'}
        # not valid file extension
        with open(self.test_image_dir + 'test.gif','rb') as tmp:
            response = client.put(url + '1',files={'image': tmp})
            assert response.status_code == 422
            assert response.json() == {'detail': 'Image must be between jpg, png, jpeg.'}
        # file cannot grater than 5 Mb
        with open(self.test_image_dir + 'size.jpeg','rb') as tmp:
            response = client.put(url + '1',files={'image': tmp})
            assert response.status_code == 413
            assert response.json() == {'detail':'An image cannot greater than 5 Mb.'}

    @pytest.mark.asyncio
    async def test_update_doctor(self,async_client):
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': 'bhaktirahayu'
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/update-doctor/'
        user_id = await self.get_user_id(self.account_admin['email'])

        # check user is admin
        response = await async_client.put(url + str(user_id),
            data={'email': self.account_1['email'], 'username': self.account_1['username']},
            headers={'X-CSRF-TOKEN': csrf_access_token}
        )
        assert response.status_code == 401
        assert response.json() == {"detail": "Only users with admin privileges can do this action."}
        # user admin login
        response = await async_client.post('/users/login',json={
            'email': self.account_admin['email'],
            'password': self.account_admin['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')
        # doctor not found
        response = await async_client.put(url + '9' * 8,
            data={'email': self.account_1['email'], 'username': self.account_1['username']},
            headers={'X-CSRF-TOKEN': csrf_access_token}
        )
        assert response.status_code == 404
        assert response.json() == {"detail": "Doctor not found!"}
        # check account is doctor
        response = await async_client.put(url + str(user_id),
            data={'email': self.account_1['email'], 'username': self.account_1['username']},
            headers={'X-CSRF-TOKEN': csrf_access_token}
        )
        assert response.status_code == 400
        assert response.json() == {"detail": "You can only edit a doctor account."}
        # check email duplicate
        user_id = await self.get_user_id(self.account_2['email'])

        response = await async_client.put(url + str(user_id),
            data={'email': self.account_1['email'], 'username': self.account_1['username']},
            headers={'X-CSRF-TOKEN': csrf_access_token}
        )
        assert response.status_code == 400
        assert response.json() == {"detail": "The email has already been taken."}

        response = await async_client.put(url + str(user_id),
            data={'email': self.account_2['email'], 'username': self.account_2['username']},
            headers={'X-CSRF-TOKEN': csrf_access_token}
        )
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully update the doctor."}

        with open(self.test_image_dir + 'image.jpeg','rb') as tmp:
            response = await async_client.put(url + str(user_id),
                data={'email': self.account_2['email'], 'username': self.account_2['username']},
                files={'image': tmp},
                headers={'X-CSRF-TOKEN': csrf_access_token},
            )
            assert response.status_code == 200
            assert response.json() == {"detail": "Successfully update the doctor."}

        # check file signature exists in directory
        signature = await self.get_user_signature(self.account_2['email'])
        assert Path(self.signature_dir + signature).is_file() is True
        # detele signature in directory
        Path(self.signature_dir + signature).unlink()

    def test_validation_delete_doctor(self,client):
        url = self.prefix + '/delete-doctor/'
        # all field blank
        response = client.delete(url + '0')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'doctor_id': assert x['msg'] == 'ensure this value is greater than 0'
        # check all field type data
        response = client.delete(url + 'a')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'doctor_id': assert x['msg'] == 'value is not a valid integer'

    @pytest.mark.asyncio
    async def test_delete_doctor(self,async_client):
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': 'bhaktirahayu'
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/delete-doctor/'
        user_id = await self.get_user_id(self.account_admin['email'])

        # check user is admin
        response = await async_client.delete(url + str(user_id),headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 401
        assert response.json() == {"detail": "Only users with admin privileges can do this action."}
        # user admin login
        response = await async_client.post('/users/login',json={
            'email': self.account_admin['email'],
            'password': self.account_admin['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')
        # doctor not found
        response = await async_client.delete(url + '9' * 8,headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 404
        assert response.json() == {"detail": "Doctor not found!"}
        # check account is doctor
        response = await async_client.delete(url + str(user_id),headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 400
        assert response.json() == {"detail": "You can't delete an admin account."}

        user_id = await self.get_user_id(self.account_1['email'])
        signature = await self.get_user_signature(self.account_1['email'])
        # delete doctor one
        response = await async_client.delete(url + str(user_id),headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully delete the doctor."}
        # check image has been delete in directory
        assert Path(self.signature_dir + signature).is_file() is False
        # delete doctor two
        user_id = await self.get_user_id(self.account_2['email'])
        signature = await self.get_user_signature(self.account_2['email'])

        response = await async_client.delete(url + str(user_id),headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully delete the doctor."}
        # check image has been delete in directory
        assert Path(self.signature_dir + signature).is_file() is False

    @pytest.mark.asyncio
    async def test_delete_user_from_db(self,async_client):
        await self.delete_user_from_db()
