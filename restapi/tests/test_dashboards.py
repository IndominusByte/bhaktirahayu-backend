import pytest
from .operationtest import OperationTest

class TestDashboard(OperationTest):
    prefix = "/dashboards"

    @pytest.mark.asyncio
    async def test_create_user(self,async_client):
        # create user admin
        await self.create_user(role='admin',**self.account_admin)

    def test_total_data_dashboard(self,client):
        client.post('/users/login',json={
            'email': self.account_admin['email'],
            'password': self.account_admin['password']
        })

        url = self.prefix + '/total-data'

        response = client.get(url)
        assert response.status_code == 200
        assert 'total_institutions' in response.json()
        assert 'total_location_services' in response.json()
        assert 'total_guardians' in response.json()
        assert 'total_doctors' in response.json()
        assert 'total_male' in response.json()
        assert 'total_female' in response.json()

    def test_validation_chart_data_dashboard(self,client):
        url = self.prefix + '/chart-data'
        # field required
        response = client.get(url)
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'period': assert x['msg'] == 'field required'
        # all field blank
        response = client.get(url + '?period=&institution_id=0&location_service_id=0')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'institution_id': assert x['msg'] == 'ensure this value is greater than 0'
            if x['loc'][-1] == 'location_service_id': assert x['msg'] == 'ensure this value is greater than 0'
        # check all field type data
        response = client.get(url + '?period=123&institution_id=asd&location_service_id=asd')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'period': assert x['msg'] == "unexpected value; permitted: 'week', 'month', 'year'"
            if x['loc'][-1] == 'institution_id': assert x['msg'] == 'value is not a valid integer'
            if x['loc'][-1] == 'location_service_id': assert x['msg'] == 'value is not a valid integer'

    def test_chart_data_dashboard(self,client):
        client.post('/users/login',json={
            'email': self.account_admin['email'],
            'password': self.account_admin['password']
        })

        url = self.prefix + '/chart-data'

        response = client.get(url + '?period=week')
        assert response.status_code == 200
        assert 'done_waiting' in response.json()
        assert 'antigen_p_n' in response.json()
        assert 'genose_p_n' in response.json()
        assert 'pcr_p_n' in response.json()

    @pytest.mark.asyncio
    async def test_delete_user_from_db(self,async_client):
        await self.delete_user_from_db()
