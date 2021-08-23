import pytest
from pathlib import Path
from .operationtest import OperationTest

class TestCovidCheckup(OperationTest):
    prefix = "/covid-checkups"

    @pytest.mark.asyncio
    async def test_create_user(self,async_client):
        # create user admin
        await self.create_user(role='admin',**self.account_admin)
        # create user doctor 1
        await self.create_user(role='doctor',signature='signature_test.png',**self.account_1)

    @pytest.mark.asyncio
    async def test_create_institution(self,async_client):
        # user admin login
        response = await async_client.post('/users/login',json={
            'email': self.account_admin['email'],
            'password': self.account_admin['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        # create institution one
        with open(self.test_image_dir + 'image.jpeg','rb') as tmp, \
                open(self.test_image_dir + 'image.jpeg','rb') as tmp2:

            response = await async_client.post('/institutions/create',
                data={'name': self.name},
                files={'stamp': tmp, 'antigen': tmp2},
                headers={'X-CSRF-TOKEN': csrf_access_token}
            )
            assert response.status_code == 201
            assert response.json() == {"detail": "Successfully add a new institution."}

        # check image exists in directory
        image = await self.get_institution_image(self.name)
        assert Path(self.institution_dir + image['stamp']).is_file() is True
        assert Path(self.institution_dir + image['antigen']).is_file() is True

    @pytest.mark.asyncio
    async def test_create_client(self,async_client):
        institution_id = await self.get_institution_id(self.name)

        response = await async_client.post('/clients/create',json={
            "nik": "5103051905990006",
            "name": "nyoman pradipta dewantara",
            "birth_place": "balikpapan",
            "birth_date": "22-08-2021",
            "gender": "LAKI-LAKI",
            "phone": "+62 87862265363",
            "address": "purigading",
            "checking_type": "antigen",
            "institution_id": str(institution_id)
        })
        assert response.status_code == 201
        assert response.json() == {"detail": "Successfully registration."}
        # check all data is uppercase
        client_data = await self.get_client_data("5103051905990006")
        assert client_data['name'].isupper() is True
        assert client_data['birth_place'].isupper() is True
        assert client_data['gender'].isupper() is True
        assert client_data['address'].isupper() is True

    def test_validation_update_covid_checkup(self,client):
        url = self.prefix + '/update/'
        # field required
        response = client.put(url + '0',json={})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'check_date': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'check_result': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'doctor_id': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'institution_id': assert x['msg'] == 'field required'
        # all field blank
        response = client.put(url + '0',json={
            'check_date': '',
            'check_result': '',
            'doctor_id': '',
            'guardian_id': '',
            'location_service_id': '',
            'institution_id': ''
        })
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'covid_checkup_id': assert x['msg'] == 'ensure this value is greater than 0'
            if x['loc'][-1] == 'doctor_id': assert x['msg'] == 'ensure this value has at least 1 characters'
            if x['loc'][-1] == 'guardian_id': assert x['msg'] == 'ensure this value has at least 1 characters'
            if x['loc'][-1] == 'location_service_id': assert x['msg'] == 'ensure this value has at least 1 characters'
            if x['loc'][-1] == 'institution_id': assert x['msg'] == 'ensure this value has at least 1 characters'
        # check all field type data
        response = client.put(url + 'a',json={
            'check_date': 123,
            'check_result': 123,
            'doctor_id': 123,
            'guardian_id': 123,
            'location_service_id': 123,
            'institution_id': 123
        })
        for x in response.json()['detail']:
            if x['loc'][-1] == 'covid_checkup_id': assert x['msg'] == 'value is not a valid integer'
            if x['loc'][-1] == 'check_date': assert x['msg'] == 'strptime() argument 1 must be str, not int'
            if x['loc'][-1] == 'check_result': assert x['msg'] == "unexpected value; permitted: 'positive', 'negative'"
            if x['loc'][-1] == 'doctor_id': assert x['msg'] == 'str type expected'
            if x['loc'][-1] == 'guardian_id': assert x['msg'] == 'str type expected'
            if x['loc'][-1] == 'location_service_id': assert x['msg'] == 'str type expected'
            if x['loc'][-1] == 'institution_id': assert x['msg'] == 'str type expected'
        # check check_date format
        response = client.put(url + '1',json={'check_date': 'asd'})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'check_date': assert x['msg'] == "time data 'asd' does not match format '%d-%m-%Y %H:%M'"
        # invalid format
        response = client.put(url + '1',
            json={'doctor_id': '11A','guardian_id': '11A','location_service_id': '11A','institution_id': '11A'}
        )
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'doctor_id': assert x['msg'] == 'string does not match regex \"^[0-9]*$\"'
            if x['loc'][-1] == 'guardian_id': assert x['msg'] == 'string does not match regex \"^[0-9]*$\"'
            if x['loc'][-1] == 'location_service_id': assert x['msg'] == 'string does not match regex \"^[0-9]*$\"'
            if x['loc'][-1] == 'institution_id': assert x['msg'] == 'string does not match regex \"^[0-9]*$\"'

    @pytest.mark.asyncio
    async def test_update_covid_checkup(self,async_client):
        response = await async_client.post('/users/login',json={
            'email': self.account_admin['email'],
            'password': self.account_admin['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/update/'
        client_id = await self.get_client_id('5103051905990006')
        covid_checkup_id = await self.get_covid_checkup_id(client_id)
        doctor_id = await self.get_user_id(self.account_1['email'])
        admin_id = await self.get_user_id(self.account_admin['email'])
        institution_id = await self.get_institution_id(self.name)
        # check user is doctor
        response = await async_client.put(url + str(covid_checkup_id),json={
            "check_date": "23-08-2021 05:53",
            "check_result": "positive",
            "doctor_id": str(doctor_id),
            "institution_id": str(institution_id)
        },headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 401
        assert response.json() == {"detail": "Only users with doctor privileges can do this action."}
        # user doctor login
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')
        # covid-checup not found
        response = await async_client.put(url + '9' * 8,json={
            "check_date": "23-08-2021 05:53",
            "check_result": "positive",
            "doctor_id": str(doctor_id),
            "institution_id": str(institution_id)
        },headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 404
        assert response.json() == {"detail": "Covid-checkup not found!"}
        # doctor not found
        response = await async_client.put(url + str(covid_checkup_id),json={
            "check_date": "23-08-2021 05:53",
            "check_result": "positive",
            "doctor_id": '9' * 8,
            "institution_id": str(institution_id)
        },headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 404
        assert response.json() == {"detail": "Doctor not found!"}
        # check role account is doctor
        response = await async_client.put(url + str(covid_checkup_id),json={
            "check_date": "23-08-2021 05:53",
            "check_result": "positive",
            "doctor_id": str(admin_id),
            "institution_id": str(institution_id)
        },headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 404
        assert response.json() == {"detail": "Doctor not found!"}
        # institution not found
        response = await async_client.put(url + str(covid_checkup_id),json={
            "check_date": "23-08-2021 05:53",
            "check_result": "positive",
            "doctor_id": str(doctor_id),
            "institution_id": '9' * 8
        },headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 404
        assert response.json() == {"detail": "Institution not found!"}
        # guardian not found
        response = await async_client.put(url + str(covid_checkup_id),json={
            "check_date": "23-08-2021 05:53",
            "check_result": "positive",
            "doctor_id": str(doctor_id),
            "guardian_id": '9' * 8,
            "institution_id": str(institution_id)
        },headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 404
        assert response.json() == {"detail": "Guardian not found!"}
        # location-service not found
        response = await async_client.put(url + str(covid_checkup_id),json={
            "check_date": "23-08-2021 05:53",
            "check_result": "positive",
            "doctor_id": str(doctor_id),
            "location_service_id": '9' * 8,
            "institution_id": str(institution_id)
        },headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 404
        assert response.json() == {"detail": "Location-service not found!"}

        response = await async_client.put(url + str(covid_checkup_id),json={
            "check_date": "23-08-2021 05:53",
            "check_result": "positive",
            "doctor_id": str(doctor_id),
            "institution_id": str(institution_id)
        },headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully update the covid-checkup."}
        # check qrcode has been generate
        covid_checkup_data = await self.get_covid_checkup_data(client_id)
        assert Path(self.qrcode_dir + covid_checkup_data['check_hash'] + '.png').is_file() is True
        # delete qrcode
        Path(self.qrcode_dir + covid_checkup_data['check_hash'] + '.png').unlink()
        assert Path(self.qrcode_dir + covid_checkup_data['check_hash'] + '.png').is_file() is False
        # check qrcode has been generate again
        response = await async_client.put(url + str(covid_checkup_id),json={
            "check_date": "23-08-2021 05:53",
            "check_result": "positive",
            "doctor_id": str(doctor_id),
            "institution_id": str(institution_id)
        },headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully update the covid-checkup."}

        covid_checkup_data = await self.get_covid_checkup_data(client_id)
        assert Path(self.qrcode_dir + covid_checkup_data['check_hash'] + '.png').is_file() is True

    def test_validation_get_covid_checkup_by_id(self,client):
        url = self.prefix + '/get-covid-checkup/'
        # all field blank
        response = client.get(url + '0')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'covid_checkup_id': assert x['msg'] == 'ensure this value is greater than 0'
        # check all field type data
        response = client.get(url + 'a')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'covid_checkup_id': assert x['msg'] == 'value is not a valid integer'

    @pytest.mark.asyncio
    async def test_get_covid_checkup_by_id(self,async_client):
        response = await async_client.post('/users/login',json={
            'email': self.account_admin['email'],
            'password': self.account_admin['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/get-covid-checkup/'

        client_id = await self.get_client_id('5103051905990006')
        covid_checkup_id = await self.get_covid_checkup_id(client_id)
        # covid_checkup not found
        response = await async_client.get(url + '9' * 8,headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 404
        assert response.json() == {"detail": "Covid-checkup not found!"}

        response = await async_client.get(url + str(covid_checkup_id),headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 200
        assert 'covid_checkups_id' in response.json()
        assert 'covid_checkups_checking_type' in response.json()
        assert 'covid_checkups_check_date' in response.json()
        assert 'covid_checkups_check_result' in response.json()
        assert 'covid_checkups_doctor_id' in response.json()
        assert 'covid_checkups_doctor_username' in response.json()
        assert 'covid_checkups_doctor_email' in response.json()
        assert 'covid_checkups_guardian_id' in response.json()
        assert 'covid_checkups_guardian_name' in response.json()
        assert 'covid_checkups_location_service_id' in response.json()
        assert 'covid_checkups_location_service_name' in response.json()
        assert 'covid_checkups_institution_id' in response.json()
        assert 'covid_checkups_institution_name' in response.json()
        assert 'covid_checkups_created_at' in response.json()
        assert 'covid_checkups_updated_at' in response.json()

    def test_validation_preview_document_covid_checkup(self,client):
        url = self.prefix + '/preview-document/'
        # field required
        response = client.get(url + '0')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'checking_type': assert x['msg'] == 'field required'
        # all field blank
        response = client.get(url + '0?checking_type=')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'institution_id': assert x['msg'] == 'ensure this value is greater than 0'
        # check all field type data
        response = client.get(url + 'a?checking_type=asd')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'institution_id': assert x['msg'] == 'value is not a valid integer'
            if x['loc'][-1] == 'checking_type': assert x['msg'] == "unexpected value; permitted: 'antigen', 'genose', 'pcr'"

    @pytest.mark.asyncio
    async def test_preview_document_covid_checkup(self,async_client):
        await async_client.post('/users/login',json={
            'email': self.account_admin['email'],
            'password': self.account_admin['password']
        })

        url = self.prefix + '/preview-document/'

        institution_id = await self.get_institution_id(self.name)
        # institution not found
        response = await async_client.get(url + '9' * 8 + '?checking_type=antigen')
        assert response.status_code == 404
        assert response.json() == {"detail": "Institution not found!"}
        # check letterhead in institution exists in db
        response = await async_client.get(url + str(institution_id) + '?checking_type=pcr')
        assert response.status_code == 400
        assert response.json() == {"detail": "The institution doesn't have letterhead please fill the image letterhead pcr."}

        response = await async_client.get(url + str(institution_id) + '?checking_type=antigen')
        assert response.status_code == 200
        assert 'clients_nik' in response.json()
        assert 'clients_name' in response.json()
        assert 'clients_phone' in response.json()
        assert 'clients_birth_place' in response.json()
        assert 'clients_birth_date' in response.json()
        assert 'clients_gender' in response.json()
        assert 'clients_address' in response.json()
        assert 'clients_age' in response.json()
        assert 'covid_checkups_report_number' in response.json()
        assert 'covid_checkups_checking_type' in response.json()
        assert 'covid_checkups_check_date' in response.json()
        assert 'covid_checkups_check_result' in response.json()
        assert 'covid_checkups_doctor_username' in response.json()
        assert 'covid_checkups_doctor_email' in response.json()
        assert 'covid_checkups_institution_name' in response.json()
        assert 'covid_checkups_institution_letterhead' in response.json()
        assert 'covid_checkups_institution_stamp' in response.json()
        assert 'covid_checkups_doctor_signature' in response.json()
        assert 'covid_checkups_check_qrcode' in response.json()

    def test_validation_see_document_covid_checkup(self,client):
        url = self.prefix + '/see-document/'
        # all field blank
        response = client.get(url + '0')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'covid_checkup_id': assert x['msg'] == 'ensure this value is greater than 0'
        # check all field type data
        response = client.get(url + 'a')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'covid_checkup_id': assert x['msg'] == 'value is not a valid integer'

    @pytest.mark.asyncio
    async def test_see_document_covid_checkup(self,async_client):
        await async_client.post('/users/login',json={
            'email': self.account_admin['email'],
            'password': self.account_admin['password']
        })

        url = self.prefix + '/see-document/'

        client_id = await self.get_client_id('5103051905990006')
        covid_checkup_id = await self.get_covid_checkup_id(client_id)
        # covid_checkup doesn't have required data
        response = await async_client.get(url + '9' * 8)
        assert response.status_code == 400
        assert response.json() == {"detail": "The covid-checkup doesn't have all the required data."}
        # check letterhead in institution exists in db
        await self.update_covid_checkup(covid_checkup_id,**{'checking_type': 'pcr'})
        response = await async_client.get(url + str(covid_checkup_id))
        assert response.status_code == 400
        assert response.json() == {"detail": "The institution doesn't have letterhead please fill the image letterhead pcr."}

        await self.update_covid_checkup(covid_checkup_id,**{'checking_type': 'antigen'})
        response = await async_client.get(url + str(covid_checkup_id))
        assert response.status_code == 200
        assert 'clients_nik' in response.json()
        assert 'clients_name' in response.json()
        assert 'clients_phone' in response.json()
        assert 'clients_birth_place' in response.json()
        assert 'clients_birth_date' in response.json()
        assert 'clients_gender' in response.json()
        assert 'clients_address' in response.json()
        assert 'clients_age' in response.json()
        assert 'covid_checkups_report_number' in response.json()
        assert 'covid_checkups_checking_type' in response.json()
        assert 'covid_checkups_check_date' in response.json()
        assert 'covid_checkups_check_result' in response.json()
        assert 'covid_checkups_doctor_username' in response.json()
        assert 'covid_checkups_doctor_email' in response.json()
        assert 'covid_checkups_institution_name' in response.json()
        assert 'covid_checkups_institution_letterhead' in response.json()
        assert 'covid_checkups_institution_stamp' in response.json()
        assert 'covid_checkups_doctor_signature' in response.json()
        assert 'covid_checkups_check_qrcode' in response.json()

        # qrcode has been removed
        covid_checkup_data = await self.get_covid_checkup_data(client_id)
        Path(self.qrcode_dir + covid_checkup_data['check_hash'] + '.png').unlink()

        response = await async_client.get(url + str(covid_checkup_id))
        assert response.status_code == 200
        assert 'clients_nik' in response.json()
        assert 'clients_name' in response.json()
        assert 'clients_phone' in response.json()
        assert 'clients_birth_place' in response.json()
        assert 'clients_birth_date' in response.json()
        assert 'clients_gender' in response.json()
        assert 'clients_address' in response.json()
        assert 'clients_age' in response.json()
        assert 'covid_checkups_report_number' in response.json()
        assert 'covid_checkups_checking_type' in response.json()
        assert 'covid_checkups_check_date' in response.json()
        assert 'covid_checkups_check_result' in response.json()
        assert 'covid_checkups_doctor_username' in response.json()
        assert 'covid_checkups_doctor_email' in response.json()
        assert 'covid_checkups_institution_name' in response.json()
        assert 'covid_checkups_institution_letterhead' in response.json()
        assert 'covid_checkups_institution_stamp' in response.json()
        assert 'covid_checkups_doctor_signature' in response.json()
        assert 'covid_checkups_check_qrcode' in response.json()

    @pytest.mark.asyncio
    async def test_validate_document_covid_checkup(self,async_client):
        url = self.prefix + '/validate-document/'

        client_id = await self.get_client_id('5103051905990006')
        covid_checkup_data = await self.get_covid_checkup_data(client_id)
        # covid_checkup empty
        response = await async_client.get(url + 'a')
        assert response.status_code == 200
        assert response.json() is None

        response = await async_client.get(url + covid_checkup_data['check_hash'])
        assert response.status_code == 200
        assert 'clients_nik' in response.json()
        assert 'clients_name' in response.json()
        assert 'clients_phone' in response.json()
        assert 'clients_birth_place' in response.json()
        assert 'clients_birth_date' in response.json()
        assert 'clients_gender' in response.json()
        assert 'clients_address' in response.json()
        assert 'covid_checkups_checking_type' in response.json()
        assert 'covid_checkups_check_hash' in response.json()
        assert 'covid_checkups_check_date' in response.json()
        assert 'covid_checkups_check_result' in response.json()
        assert 'covid_checkups_institution_name' in response.json()

    def test_validation_delete_covid_checkup(self,client):
        url = self.prefix + '/delete/'
        # all field blank
        response = client.delete(url + '0')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'covid_checkup_id': assert x['msg'] == 'ensure this value is greater than 0'
        # check all field type data
        response = client.delete(url + 'a')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'covid_checkup_id': assert x['msg'] == 'value is not a valid integer'

    @pytest.mark.asyncio
    async def test_delete_covid_checkup(self,async_client):
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        # generate qrcode again
        url = self.prefix + '/update/'
        client_id = await self.get_client_id('5103051905990006')
        covid_checkup_id = await self.get_covid_checkup_id(client_id)
        doctor_id = await self.get_user_id(self.account_1['email'])
        institution_id = await self.get_institution_id(self.name)

        response = await async_client.put(url + str(covid_checkup_id),json={
            "check_date": "23-08-2021 05:53",
            "check_result": "positive",
            "doctor_id": str(doctor_id),
            "institution_id": str(institution_id)
        },headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully update the covid-checkup."}
        # check qrcode has been generate
        covid_checkup_data = await self.get_covid_checkup_data(client_id)
        assert Path(self.qrcode_dir + covid_checkup_data['check_hash'] + '.png').is_file() is True

        url = self.prefix + '/delete/'

        # covid_checkup not found
        response = await async_client.delete(url + '9' * 8,headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 404
        assert response.json() == {"detail": "Covid-checkup not found!"}
        # delete covid_checkup
        response = await async_client.delete(url + str(covid_checkup_id),headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully delete the covid-checkup."}
        # check qrcode hasbeen delete
        assert Path(self.qrcode_dir + covid_checkup_data['check_hash'] + '.png').is_file() is False

    @pytest.mark.asyncio
    async def test_delete_client(self,async_client):
        response = await async_client.post('/users/login',json={
            'email': self.account_admin['email'],
            'password': self.account_admin['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        client_id = await self.get_client_id('5103051905990006')
        # delete client one
        response = await async_client.delete('/clients/delete/' + str(client_id),headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully delete the client."}

    @pytest.mark.asyncio
    async def test_delete_institution(self,async_client):
        # user admin login
        response = await async_client.post('/users/login',json={
            'email': self.account_admin['email'],
            'password': self.account_admin['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        # delete institution one
        institution_id = await self.get_institution_id(self.name)
        image = await self.get_institution_image(self.name)

        response = await async_client.delete(
            '/institutions/delete/' + str(institution_id),
            headers={'X-CSRF-TOKEN': csrf_access_token}
        )
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully delete the institution."}
        # check image has been delete in directory
        assert Path(self.institution_dir + image['stamp']).is_file() is False
        assert Path(self.institution_dir + image['antigen']).is_file() is False

    @pytest.mark.asyncio
    async def test_delete_user_from_db(self,async_client):
        await self.delete_user_from_db()
