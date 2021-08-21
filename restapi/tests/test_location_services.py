import pytest
from .operationtest import OperationTest

class TestLocationService(OperationTest):
    prefix = "/location-services"

    @pytest.mark.asyncio
    async def test_create_user(self,async_client):
        # create user admin
        await self.create_user(role='admin',**self.account_admin)
        # create user doctor 1
        await self.create_user(role='doctor',signature='signature_test.png',**self.account_1)

    def test_validation_create_location_service(self,client):
        url = self.prefix + '/create'
        # field required
        response = client.post(url,json={})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'name': assert x['msg'] == 'field required'
        # all field blank
        response = client.post(url,json={'name': ''})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'name': assert x['msg'] == 'ensure this value has at least 3 characters'
        # test limit value
        response = client.post(url,json={'name': 'a' * 200})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'name': assert x['msg'] == 'ensure this value has at most 100 characters'
        # check all field type data
        response = client.post(url,json={'name': 123})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'name': assert x['msg'] == 'str type expected'

    def test_create_location_service(self,client):
        response = client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/create'
        # check user is admin
        response = client.post(url,json={'name': self.name},headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 401
        assert response.json() == {"detail": "Only users with admin privileges can do this action."}
        # user admin login
        response = client.post('/users/login',json={
            'email': self.account_admin['email'],
            'password': self.account_admin['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        response = client.post(url,json={'name': self.name},headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 201
        assert response.json() == {"detail": "Successfully add a new location-service."}

    def test_name_duplicate_create_location_service(self,client):
        response = client.post('/users/login',json={
            'email': self.account_admin['email'],
            'password': self.account_admin['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/create'

        response = client.post(url,json={'name': self.name},headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 400
        assert response.json() == {"detail": "The name has already been taken."}

    def test_validation_get_all_location_services(self,client):
        url = self.prefix + '/all-location-services'
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

    def test_get_all_location_services(self,client):
        url = self.prefix + '/all-location-services'

        response = client.get(url + '?page=1&per_page=1&q=' + self.name)
        assert response.status_code == 200
        assert 'data' in response.json()
        assert 'total' in response.json()
        assert 'next_num' in response.json()
        assert 'prev_num' in response.json()
        assert 'page' in response.json()
        assert 'iter_pages' in response.json()

        # check data exists and type data
        assert type(response.json()['data'][0]['location_services_id']) == str
        assert type(response.json()['data'][0]['location_services_name']) == str

    def test_validation_get_multiple_location_services(self,client):
        url = self.prefix + '/get-multiple-location-services'
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
    async def test_get_multiple_location_services(self,async_client):
        response = await async_client.post('/users/login',json={
            'email': self.account_admin['email'],
            'password': self.account_admin['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/get-multiple-location-services'

        location_service_id = await self.get_location_service_id(self.name)
        # location-service empty
        response = await async_client.post(url,json={'list_id': ['9' * 8]},headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 200
        assert response.json() == []

        response = await async_client.post(url,
            json={'list_id': [str(location_service_id)]},
            headers={'X-CSRF-TOKEN': csrf_access_token}
        )
        assert response.status_code == 200
        # check data exists and type data
        assert type(response.json()[0]['location_services_id']) == str
        assert type(response.json()[0]['location_services_name']) == str

    def test_validation_update_location_service(self,client):
        url = self.prefix + '/update/'
        # field required
        response = client.put(url + '0',json={})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'name': assert x['msg'] == 'field required'
        # all field blank
        response = client.put(url + '0',json={'name': ''})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'location_service_id': assert x['msg'] == 'ensure this value is greater than 0'
            if x['loc'][-1] == 'name': assert x['msg'] == 'ensure this value has at least 3 characters'
        # check all field type data
        response = client.put(url + 'a',json={'name': 123})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'location_service_id': assert x['msg'] == 'value is not a valid integer'
            if x['loc'][-1] == 'name': assert x['msg'] == 'str type expected'
        # test limit value
        response = client.put(url + '1',json={'name': 'a' * 200})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'name': assert x['msg'] == 'ensure this value has at most 100 characters'

    @pytest.mark.asyncio
    async def test_update_location_service(self,async_client):
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/update/'
        location_service_id = await self.get_location_service_id(self.name)
        # check user is admin
        response = await async_client.put(url + str(location_service_id),
            json={'name': self.name},
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
        # location-service not found
        response = await async_client.put(url + '9' * 8,
            json={'name': self.name},
            headers={'X-CSRF-TOKEN': csrf_access_token}
        )
        assert response.status_code == 404
        assert response.json() == {"detail": "Location-service not found!"}

        response = await async_client.put(url + str(location_service_id),
            json={'name': self.name},
            headers={'X-CSRF-TOKEN': csrf_access_token}
        )
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully update the location-service."}

    @pytest.mark.asyncio
    async def test_name_duplicate_update_location_service(self,async_client):
        # user admin login
        response = await async_client.post('/users/login',json={
            'email': self.account_admin['email'],
            'password': self.account_admin['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/create'
        # create another location-service
        response = await async_client.post(url,
            json={'name': self.name2},
            headers={'X-CSRF-TOKEN': csrf_access_token}
        )
        assert response.status_code == 201
        assert response.json() == {"detail": "Successfully add a new location-service."}

        url = self.prefix + '/update/'
        location_service_id = await self.get_location_service_id(self.name2)
        # name already taken
        response = await async_client.put(url + str(location_service_id),
            json={'name': self.name},
            headers={'X-CSRF-TOKEN': csrf_access_token}
        )
        assert response.status_code == 400
        assert response.json() == {"detail": "The name has already been taken."}

    def test_validation_delete_location_service(self,client):
        url = self.prefix + '/delete/'
        # all field blank
        response = client.delete(url + '0')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'location_service_id': assert x['msg'] == 'ensure this value is greater than 0'
        # check all field type data
        response = client.delete(url + 'a')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'location_service_id': assert x['msg'] == 'value is not a valid integer'

    @pytest.mark.asyncio
    async def test_delete_location_service(self,async_client):
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/delete/'
        location_services_id = await self.get_location_service_id(self.name)
        # check user is admin
        response = await async_client.delete(url + str(location_services_id),headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 401
        assert response.json() == {"detail": "Only users with admin privileges can do this action."}
        # user admin login
        response = await async_client.post('/users/login',json={
            'email': self.account_admin['email'],
            'password': self.account_admin['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')
        # location-service not found
        response = await async_client.delete(url + '9' * 8,headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 404
        assert response.json() == {"detail": "Location-service not found!"}
        # delete location-service one
        response = await async_client.delete(url + str(location_services_id),headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully delete the location-service."}

        # delete location-service two
        location_services_id = await self.get_location_service_id(self.name2)
        response = await async_client.delete(url + str(location_services_id),headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully delete the location-service."}

    @pytest.mark.asyncio
    async def test_delete_user_from_db(self,async_client):
        await self.delete_user_from_db()
