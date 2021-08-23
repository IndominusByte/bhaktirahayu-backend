import pytest
from .operationtest import OperationTest

class TestUtil(OperationTest):
    prefix = "/utils"

    @pytest.mark.asyncio
    async def test_create_user(self,async_client):
        # create user admin
        await self.create_user(role='admin',**self.account_admin)

    def test_validation_encoding_image_base64(self,client):
        url = self.prefix + '/encoding-image-base64'
        # field required
        response = client.post(url,json={})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'path_file': assert x['msg'] == 'field required'
        # all field blank
        response = client.post(url,json={'path_file': ''})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'path_file': assert x['msg'] == 'path \".\" does not point to a file'
        # check all field type data
        response = client.post(url,json={'path_file': 123})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'path_file': assert x['msg'] == 'value is not a valid path'

        # file not exists in folder static
        response = client.post(url,json={'path_file': 'static/signature/signaturee.png'})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'path_file': assert x['msg'] == \
                'file or directory at path \"static/signature/signaturee.png\" does not exist'

        # file exists but not in folder static
        response = client.post(url,json={'path_file': 'routers/Clients.py'})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'path_file': assert x['msg'] == 'value is not a valid path'

    def test_encoding_image_base64(self,client):
        response = client.post('/users/login',json={
            'email': self.account_admin['email'],
            'password': self.account_admin['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/encoding-image-base64'

        response = client.post(url,
            json={'path_file': 'static/signature/signature.png'},
            headers={'X-CSRF-TOKEN': csrf_access_token}
        )
        assert response.status_code == 200
        assert type(response.json()) == str

    @pytest.mark.asyncio
    async def test_delete_user_from_db(self,async_client):
        await self.delete_user_from_db()
