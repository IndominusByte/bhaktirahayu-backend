import pytest
from pathlib import Path
from .operationtest import OperationTest

class TestClient(OperationTest):
    prefix = "/clients"

    @pytest.mark.asyncio
    async def test_create_user(self,async_client):
        # create user admin
        await self.create_user(role='admin',**self.account_admin)

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
        # create institution two
        with open(self.test_image_dir + 'image.jpeg','rb') as tmp, \
                open(self.test_image_dir + 'image.jpeg','rb') as tmp2:

            response = await async_client.post('/institutions/create',
                data={'name': self.name2},
                files={'stamp': tmp, 'antigen': tmp2},
                headers={'X-CSRF-TOKEN': csrf_access_token}
            )
            assert response.status_code == 201
            assert response.json() == {"detail": "Successfully add a new institution."}

        # check image exists in directory
        image = await self.get_institution_image(self.name2)
        assert Path(self.institution_dir + image['stamp']).is_file() is True
        assert Path(self.institution_dir + image['antigen']).is_file() is True

    def test_validation_identity_card_ocr(self,client):
        url = self.prefix + '/identity-card-ocr'

        # field required
        response = client.post(url,data={})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'kind': assert x['msg'] == 'field required'
        # check all field type data
        response = client.post(url,data={'kind': 'asd'})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'kind': assert x['msg'] == "unexpected value; permitted: 'ktp', 'kis'"

        # image required
        response = client.post(url,files={})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'image': assert x['msg'] == 'field required'
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

    def test_identity_card_ocr(self,client):
        url = self.prefix + '/identity-card-ocr'
        # ktp laki-laki
        with open(self.test_image_dir + 'ktp1.jpg','rb') as tmp:
            response = client.post(url,data={'kind': 'ktp'}, files={'image': tmp})
            assert response.status_code == 200
            assert response.json() == {
                'nik': '510305190599000006',
                'name': 'NYOMAN PRADIPTA DEWANTARA',
                'birth_date': '1999-05-19T00:00:00',
                'birth_place': 'BALIKPAPAN',
                'gender': 'LAKI-LAKI',
                'address': 'JL MERAK C4/34 PURI GADING, AINGK. BHUANA GUBUG'
            }
        # ktp perempuan
        with open(self.test_image_dir + 'ktp2.jpg','rb') as tmp:
            response = client.post(url,data={'kind': 'ktp'}, files={'image': tmp})
            assert response.status_code == 200
            assert response.json() == {
                'nik': '5103056309510001',
                'name': 'DESAK PUTU SUTRISNI',
                'birth_date': '1961-09-23T00:00:00',
                'birth_place': 'BANJAR',
                'gender': 'PEREMPUAN',
                'address': 'JL. MERAK C 4/34 PURI GADING, LINGK. BHUANA GUB'
            }
        # wrong ktp
        with open(self.test_image_dir + 'image.jpeg','rb') as tmp:
            response = client.post(url,data={'kind': 'ktp'}, files={'image': tmp})
            assert response.status_code == 200
            assert response.json() == {
                'nik': None,
                'name': None,
                'birth_date': None,
                'birth_place': None,
                'gender': None,
                'address': None
            }
        # kis laki-laki
        with open(self.test_image_dir + 'kis1.jpeg','rb') as tmp:
            response = client.post(url,data={'kind': 'kis'}, files={'image': tmp})
            assert response.status_code == 200
            assert response.json() == {
                'nik': '5103051905990006',
                'name': 'NYOMAN PRADIPTA DEWANTARA',
                'birth_date': '1999-05-19T00:00:00',
                'birth_place': None,
                'gender': None,
                'address': '.JL. MERAK C 4/34 PURI GADING, LINGK. BHUANA GUBUG JIMBARAN, KUTA SELATAN, KAB. BADUNG'
            }
        # kis perempuan
        with open(self.test_image_dir + 'kis2.jpeg','rb') as tmp:
            response = client.post(url,data={'kind': 'kis'}, files={'image': tmp})
            assert response.status_code == 200
            assert response.json() == {
                'nik': '5103056309610001',
                'name': 'DESAK PUTU SUTRISNI',
                'birth_date': '1961-09-23T00:00:00',
                'birth_place': None,
                'gender': None,
                'address': 'JL. MERAK C 4/34 PURI GADING, LINGK. BHUANA GUBUG JIMBARAN, KUTA SELATAN, KAB. BADUNG'
            }
        # wrong kis
        with open(self.test_image_dir + 'image.jpeg','rb') as tmp:
            response = client.post(url,data={'kind': 'kis'}, files={'image': tmp})
            assert response.status_code == 200
            assert response.json() == {
                'nik': None,
                'name': None,
                'birth_date': None,
                'birth_place': None,
                'gender': None,
                'address': None
            }

    def test_validation_create_client(self,client):
        url = self.prefix + "/create"
        # field required
        response = client.post(url,json={})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'nik': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'name': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'birth_place': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'birth_date': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'gender': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'phone': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'address': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'checking_type': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'institution_id': assert x['msg'] == 'field required'
        # all field blank
        response = client.post(url,json={
            "nik": "",
            "name": "",
            "birth_place": "",
            "birth_date": "",
            "gender": "",
            "phone": "",
            "address": "",
            "checking_type": "",
            "institution_id": ""
        })
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'nik': assert x['msg'] == 'ensure this value has at least 3 characters'
            if x['loc'][-1] == 'name': assert x['msg'] == 'ensure this value has at least 3 characters'
            if x['loc'][-1] == 'birth_place': assert x['msg'] == 'ensure this value has at least 3 characters'
            if x['loc'][-1] == 'phone': assert x['msg'] == 'ensure this value has at least 1 characters'
            if x['loc'][-1] == 'address': assert x['msg'] == 'ensure this value has at least 5 characters'
            if x['loc'][-1] == 'institution_id': assert x['msg'] == 'ensure this value has at least 1 characters'
        # test limit value
        response = client.post(url,json={
            "nik": "a" * 200,
            "name": "a" * 200,
            "birth_place": "a" * 200,
            "birth_date": "a" * 200,
            "gender": "a" * 200,
            "phone": "a" * 200,
            "address": "a" * 200,
            "checking_type": "a" * 200,
            "institution_id": "a" * 200
        })
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'nik': assert x['msg'] == 'ensure this value has at most 100 characters'
            if x['loc'][-1] == 'name': assert x['msg'] == 'ensure this value has at most 100 characters'
            if x['loc'][-1] == 'birth_place': assert x['msg'] == 'ensure this value has at most 100 characters'
            if x['loc'][-1] == 'phone': assert x['msg'] == 'ensure this value has at most 20 characters'
        # check all field type data
        response = client.post(url,json={
            "nik": 123,
            "name": 123,
            "birth_place": 123,
            "birth_date": 123,
            "gender": 123,
            "phone": 123,
            "address": 123,
            "checking_type": 123,
            "institution_id": 123
        })
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'nik': assert x['msg'] == 'str type expected'
            if x['loc'][-1] == 'name': assert x['msg'] == 'str type expected'
            if x['loc'][-1] == 'birth_place': assert x['msg'] == 'str type expected'
            if x['loc'][-1] == 'birth_date': assert x['msg'] == 'strptime() argument 1 must be str, not int'
            if x['loc'][-1] == 'gender': assert x['msg'] == "unexpected value; permitted: 'LAKI-LAKI', 'PEREMPUAN'"
            if x['loc'][-1] == 'phone': assert x['msg'] == 'str type expected'
            if x['loc'][-1] == 'address': assert x['msg'] == 'str type expected'
            if x['loc'][-1] == 'checking_type': assert x['msg'] == "unexpected value; permitted: 'antigen', 'genose', 'pcr'"
            if x['loc'][-1] == 'institution_id': assert x['msg'] == 'str type expected'
        # check birth_date format
        response = client.post(url,json={'birth_date': 'asd'})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'birth_date': assert x['msg'] == "time data 'asd' does not match format '%d-%m-%Y'"
        # invalid format
        response = client.post(url,json={'nik': '11A', 'institution_id': '1A'})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'nik': assert x['msg'] == 'string does not match regex \"^[0-9]*$\"'
            if x['loc'][-1] == 'institution_id': assert x['msg'] == 'string does not match regex \"^[0-9]*$\"'
        # invalid phone number
        response = client.post(url,json={'phone': 'asdasd'})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'phone': assert x['msg'] == "value is not a valid mobile phone number"

        response = client.post(url,json={'phone': '8762732'})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'phone': assert x['msg'] == "value is not a valid mobile phone number"
        # invalid nik
        response = client.post(url,json={'nik': '123123'})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'nik': assert x['msg'] == 'invalid nik format'

        response = client.post(url,json={'nik': '5103051234560006'})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'nik': assert x['msg'] == 'invalid nik format'

    @pytest.mark.asyncio
    async def test_create_client(self,async_client):
        url = self.prefix + '/create'

        institution_id = await self.get_institution_id(self.name)
        # institution not found
        response = await async_client.post(url,json={
            "nik": "5103051905990006",
            "name": "NYOMAN PRADIPTA DEWANTARA",
            "birth_place": "BALIKPAPAN",
            "birth_date": "22-08-2021",
            "gender": "LAKI-LAKI",
            "phone": "+62 87862265363",
            "address": "PURIGADING",
            "checking_type": "antigen",
            "institution_id": "9" * 8
        })
        assert response.status_code == 404
        assert response.json() == {"detail": "Institution not found!"}
        # institution doesn't have antigen, genose or pcr
        response = await async_client.post(url,json={
            "nik": "5103051905990006",
            "name": "NYOMAN PRADIPTA DEWANTARA",
            "birth_place": "BALIKPAPAN",
            "birth_date": "22-08-2021",
            "gender": "LAKI-LAKI",
            "phone": "+62 87862265363",
            "address": "PURIGADING",
            "checking_type": "pcr",
            "institution_id": str(institution_id)
        })
        assert response.status_code == 404
        assert response.json() == {"detail": "The institution does not have pcr checking."}

        response = await async_client.post(url,json={
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

        # check register many times
        response = await async_client.post(url,json={
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
        assert response.status_code == 400
        assert response.json() == \
            {"detail": "You cannot register many times at the same institute, please try again after 1 hour."}

        # edit data if client exists in db
        institution_id = await self.get_institution_id(self.name2)
        response = await async_client.post(url,json={
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
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully registration."}

    @pytest.mark.asyncio
    async def test_phone_duplicate_create_client(self,async_client):
        url = self.prefix + '/create'

        institution_id = await self.get_institution_id(self.name)
        response = await async_client.post(url,json={
            "nik": "5171010609990002",
            "name": "paulus bonatua simanjuntak",
            "birth_place": "denpasar",
            "birth_date": "22-08-2021",
            "gender": "LAKI-LAKI",
            "phone": "+62 87862265363",
            "address": "denpasar",
            "checking_type": "antigen",
            "institution_id": str(institution_id)
        })
        assert response.status_code == 400
        assert response.json() == {"detail": "The phone number has already been taken."}

        # create another client
        institution_id = await self.get_institution_id(self.name)
        response = await async_client.post(url,json={
            "nik": "5171010609990002",
            "name": "paulus bonatua simanjuntak",
            "birth_place": "denpasar",
            "birth_date": "22-08-2021",
            "gender": "LAKI-LAKI",
            "phone": "+62 87862265362",
            "address": "denpasar",
            "checking_type": "antigen",
            "institution_id": str(institution_id)
        })
        assert response.status_code == 201
        assert response.json() == {"detail": "Successfully registration."}

    def test_validation_get_client_data_by_nik(self,client):
        url = self.prefix + '/get-data-by-nik'
        # field required
        response = client.get(url)
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'nik': assert x['msg'] == 'field required'
        # all field blank
        response = client.get(url + '?nik=')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'nik': assert x['msg'] == 'ensure this value has at least 1 characters'
        # check all field type data
        response = client.get(url + '?nik=1A')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'nik': assert x['msg'] == 'string does not match regex \"^[0-9]*$\"'

    def test_get_client_data_by_nik(self,client):
        url = self.prefix + '/get-data-by-nik'

        # nik empty
        response = client.get(url + '?nik=0000000000000000')
        assert response.status_code == 200
        assert response.json() is None

        response = client.get(url + '?nik=5103051905990006')
        assert response.status_code == 200
        # check data exists and type data
        assert type(response.json()['nik']) == str
        assert type(response.json()['name']) == str
        assert type(response.json()['phone']) == str
        assert type(response.json()['birth_place']) == str
        assert type(response.json()['birth_date']) == str
        assert type(response.json()['gender']) == str
        assert type(response.json()['address']) == str

    def test_validation_get_client_info_by_nik(self,client):
        url = self.prefix + '/get-info-by-nik'
        # field required
        response = client.get(url)
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'nik': assert x['msg'] == 'field required'
        # all field blank
        response = client.get(url + '?nik=')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'nik': assert x['msg'] == 'ensure this value has at least 1 characters'
        # check all field type data
        response = client.get(url + '?nik=1A')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'nik': assert x['msg'] == 'string does not match regex \"^[0-9]*$\"'

    def test_get_client_info_by_nik(self,client):
        url = self.prefix + '/get-info-by-nik'

        response = client.get(url + '?nik=5103051905990006')
        assert response.status_code == 200
        # check data exists and type data
        assert type(response.json()['nik']) == str
        assert type(response.json()['valid']) == bool
        assert type(response.json()['area_code']) == str
        assert type(response.json()['location_valid']) == bool
        assert type(response.json()['province']) == str
        assert type(response.json()['district']) == str
        assert type(response.json()['subdistrict']) == str
        assert type(response.json()['gender']) == str
        assert type(response.json()['birth_date']) == str

    def test_validation_get_all_clients(self,client):
        url = self.prefix + '/all-clients'
        # field required
        response = client.get(url)
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'page': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'per_page': assert x['msg'] == 'field required'
        # all field blank
        response = client.get(
            url + '?page=0&per_page=0&q=&gender=&checking_type=&check_result=&doctor_id=' +
            '&guardian_id=&location_service_id=&institution_id=&register_start_date=' +
            '&register_end_date=&check_start_date=&check_end_date='
        )
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'page': assert x['msg'] == 'ensure this value is greater than 0'
            if x['loc'][-1] == 'per_page': assert x['msg'] == 'ensure this value is greater than 0'
            if x['loc'][-1] == 'q': assert x['msg'] == 'ensure this value has at least 1 characters'
            if x['loc'][-1] == 'doctor_id': assert x['msg'] == 'ensure this value has at least 1 characters'
            if x['loc'][-1] == 'guardian_id': assert x['msg'] == 'ensure this value has at least 1 characters'
            if x['loc'][-1] == 'location_service_id': assert x['msg'] == 'ensure this value has at least 1 characters'
            if x['loc'][-1] == 'institution_id': assert x['msg'] == 'ensure this value has at least 1 characters'
            if x['loc'][-1] == 'register_start_date': assert x['msg'] == 'ensure this value has at least 1 characters'
            if x['loc'][-1] == 'register_end_date': assert x['msg'] == 'ensure this value has at least 1 characters'
            if x['loc'][-1] == 'check_start_date': assert x['msg'] == 'ensure this value has at least 1 characters'
            if x['loc'][-1] == 'check_end_date': assert x['msg'] == 'ensure this value has at least 1 characters'
        # check all field type data
        response = client.get(
            url + '?page=a&per_page=a&q=123&gender=123&checking_type=123&check_result=123&doctor_id=123' +
            '&guardian_id=123&location_service_id=123&institution_id=123&register_start_date=123' +
            '&register_end_date=123&check_start_date=123&check_end_date=123'
        )
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'page': assert x['msg'] == 'value is not a valid integer'
            if x['loc'][-1] == 'per_page': assert x['msg'] == 'value is not a valid integer'
            if x['loc'][-1] == 'gender': assert x['msg'] == "unexpected value; permitted: 'LAKI-LAKI', 'PEREMPUAN'"
            if x['loc'][-1] == 'checking_type': assert x['msg'] == "unexpected value; permitted: 'antigen', 'genose', 'pcr'"
            if x['loc'][-1] == 'check_result': assert x['msg'] == \
                "unexpected value; permitted: 'positive', 'negative', 'empty'"
            if x['loc'][-1] == 'register_start_date': assert x['msg'] == \
                'string does not match regex \"(\\d{2}-\\d{2}-\\d{4})\"'
            if x['loc'][-1] == 'register_end_date': assert x['msg'] == \
                'string does not match regex \"(\\d{2}-\\d{2}-\\d{4})\"'
            if x['loc'][-1] == 'check_start_date': assert x['msg'] == \
                'string does not match regex \"(\\d{2}-\\d{2}-\\d{4} \\d{2}:\\d{2})\"'
            if x['loc'][-1] == 'check_end_date': assert x['msg'] == \
                'string does not match regex \"(\\d{2}-\\d{2}-\\d{4} \\d{2}:\\d{2})\"'
        # invalid format date and validate date
        response = client.get(url + '?page=1&per_page=1&register_start_date=22-08-2021')
        assert response.status_code == 422
        assert response.json() == {"detail": "register_end_date is required"}

        response = client.get(url + '?page=1&per_page=1&register_end_date=22-08-2021')
        assert response.status_code == 422
        assert response.json() == {"detail": "register_start_date is required"}

        response = client.get(url + '?page=1&per_page=1&register_start_date=22-08-2021&register_end_date=21-08-2021')
        assert response.status_code == 422
        assert response.json() == {"detail": "the start time must be after the end time"}

        response = client.get(url + '?page=1&per_page=1&check_start_date=22-08-2021 15:55')
        assert response.status_code == 422
        assert response.json() == {"detail": "check_end_date is required"}

        response = client.get(url + '?page=1&per_page=1&check_end_date=22-08-2021 15:55')
        assert response.status_code == 422
        assert response.json() == {"detail": "check_start_date is required"}

        response = client.get(url + '?page=1&per_page=1&check_start_date=22-08-2021 15:55&check_end_date=22-08-2021 14:55')
        assert response.status_code == 422
        assert response.json() == {"detail": "the start time must be after the end time"}

    def test_get_all_clients(self,client):
        client.post('/users/login',json={
            'email': self.account_admin['email'],
            'password': self.account_admin['password']
        })

        url = self.prefix + '/all-clients'

        response = client.get(url + '?page=1&per_page=1&q=5103051905990006')
        assert response.status_code == 200
        assert 'data' in response.json()
        assert 'total' in response.json()
        assert 'next_num' in response.json()
        assert 'prev_num' in response.json()
        assert 'page' in response.json()
        assert 'iter_pages' in response.json()

        # check data exists and type data
        assert type(response.json()['data'][0]['clients_id']) == str
        assert type(response.json()['data'][0]['clients_nik']) == str
        assert type(response.json()['data'][0]['clients_name']) == str
        assert type(response.json()['data'][0]['clients_phone']) == str
        assert type(response.json()['data'][0]['clients_birth_place']) == str
        assert type(response.json()['data'][0]['clients_birth_date']) == str
        assert type(response.json()['data'][0]['clients_gender']) == str
        assert type(response.json()['data'][0]['clients_address']) == str
        assert type(response.json()['data'][0]['clients_created_at']) == str
        assert type(response.json()['data'][0]['clients_updated_at']) == str
        assert type(response.json()['data'][0]['covid_checkups']) == list
        assert len(response.json()['data'][0]['covid_checkups']) != 0

    def test_validation_get_all_clients_export(self,client):
        url = self.prefix + '/all-clients-export'
        # all field blank
        response = client.get(
            url + '?q=&gender=&checking_type=&check_result=&doctor_id=' +
            '&guardian_id=&location_service_id=&institution_id=&register_start_date=' +
            '&register_end_date=&check_start_date=&check_end_date='
        )
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'q': assert x['msg'] == 'ensure this value has at least 1 characters'
            if x['loc'][-1] == 'doctor_id': assert x['msg'] == 'ensure this value has at least 1 characters'
            if x['loc'][-1] == 'guardian_id': assert x['msg'] == 'ensure this value has at least 1 characters'
            if x['loc'][-1] == 'location_service_id': assert x['msg'] == 'ensure this value has at least 1 characters'
            if x['loc'][-1] == 'institution_id': assert x['msg'] == 'ensure this value has at least 1 characters'
            if x['loc'][-1] == 'register_start_date': assert x['msg'] == 'ensure this value has at least 1 characters'
            if x['loc'][-1] == 'register_end_date': assert x['msg'] == 'ensure this value has at least 1 characters'
            if x['loc'][-1] == 'check_start_date': assert x['msg'] == 'ensure this value has at least 1 characters'
            if x['loc'][-1] == 'check_end_date': assert x['msg'] == 'ensure this value has at least 1 characters'
        # check all field type data
        response = client.get(
            url + '?q=123&gender=123&checking_type=123&check_result=123&doctor_id=123' +
            '&guardian_id=123&location_service_id=123&institution_id=123&register_start_date=123' +
            '&register_end_date=123&check_start_date=123&check_end_date=123'
        )
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'gender': assert x['msg'] == "unexpected value; permitted: 'LAKI-LAKI', 'PEREMPUAN'"
            if x['loc'][-1] == 'checking_type': assert x['msg'] == "unexpected value; permitted: 'antigen', 'genose', 'pcr'"
            if x['loc'][-1] == 'check_result': assert x['msg'] == \
                "unexpected value; permitted: 'positive', 'negative', 'empty'"
            if x['loc'][-1] == 'register_start_date': assert x['msg'] == \
                'string does not match regex \"(\\d{2}-\\d{2}-\\d{4})\"'
            if x['loc'][-1] == 'register_end_date': assert x['msg'] == \
                'string does not match regex \"(\\d{2}-\\d{2}-\\d{4})\"'
            if x['loc'][-1] == 'check_start_date': assert x['msg'] == \
                'string does not match regex \"(\\d{2}-\\d{2}-\\d{4} \\d{2}:\\d{2})\"'
            if x['loc'][-1] == 'check_end_date': assert x['msg'] == \
                'string does not match regex \"(\\d{2}-\\d{2}-\\d{4} \\d{2}:\\d{2})\"'
        # invalid format date and validate date
        response = client.get(url + '?register_start_date=22-08-2021')
        assert response.status_code == 422
        assert response.json() == {"detail": "register_end_date is required"}

        response = client.get(url + '?register_end_date=22-08-2021')
        assert response.status_code == 422
        assert response.json() == {"detail": "register_start_date is required"}

        response = client.get(url + '?register_start_date=22-08-2021&register_end_date=21-08-2021')
        assert response.status_code == 422
        assert response.json() == {"detail": "the start time must be after the end time"}

        response = client.get(url + '?check_start_date=22-08-2021 15:55')
        assert response.status_code == 422
        assert response.json() == {"detail": "check_end_date is required"}

        response = client.get(url + '?check_end_date=22-08-2021 15:55')
        assert response.status_code == 422
        assert response.json() == {"detail": "check_start_date is required"}

        response = client.get(url + '?check_start_date=22-08-2021 15:55&check_end_date=22-08-2021 14:55')
        assert response.status_code == 422
        assert response.json() == {"detail": "the start time must be after the end time"}

    def test_get_all_clients_export(self,client):
        client.post('/users/login',json={
            'email': self.account_admin['email'],
            'password': self.account_admin['password']
        })

        url = self.prefix + '/all-clients-export'

        response = client.get(url + '?q=5103051905990006')
        assert response.status_code == 200
        # check data exists and type data
        assert type(response.json()[0]['clients_no']) == str
        assert type(response.json()[0]['clients_nik']) == str
        assert type(response.json()[0]['clients_name']) == str
        assert type(response.json()[0]['clients_phone']) == str
        assert type(response.json()[0]['clients_birth_place']) == str
        assert type(response.json()[0]['clients_birth_date']) == str
        assert type(response.json()[0]['clients_gender']) == str
        assert type(response.json()[0]['clients_address']) == str
        assert type(response.json()[0]['covid_checkups_checking_type']) == str
        assert response.json()[0]['covid_checkups_check_date'] is None
        assert response.json()[0]['covid_checkups_check_result'] is None
        assert response.json()[0]['covid_checkups_doctor_username'] is None
        assert response.json()[0]['covid_checkups_doctor_email'] is None
        assert response.json()[0]['covid_checkups_guardian_name'] is None
        assert response.json()[0]['covid_checkups_location_service_name'] is None
        assert type(response.json()[0]['covid_checkups_institution_name']) == str

    def test_validation_update_client(self,client):
        url = self.prefix + '/update/'
        # field required
        response = client.put(url + '0',json={})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'nik': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'name': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'birth_place': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'birth_date': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'gender': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'phone': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'address': assert x['msg'] == 'field required'
        # all field blank
        response = client.put(url + '0',json={
            "nik": "",
            "name": "",
            "birth_place": "",
            "birth_date": "",
            "gender": "",
            "phone": "",
            "address": "",
        })
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'client_id': assert x['msg'] == 'ensure this value is greater than 0'
            if x['loc'][-1] == 'nik': assert x['msg'] == 'ensure this value has at least 3 characters'
            if x['loc'][-1] == 'name': assert x['msg'] == 'ensure this value has at least 3 characters'
            if x['loc'][-1] == 'birth_place': assert x['msg'] == 'ensure this value has at least 3 characters'
            if x['loc'][-1] == 'phone': assert x['msg'] == 'ensure this value has at least 1 characters'
            if x['loc'][-1] == 'address': assert x['msg'] == 'ensure this value has at least 5 characters'
        # test limit value
        response = client.put(url + '1',json={
            "nik": "a" * 200,
            "name": "a" * 200,
            "birth_place": "a" * 200,
            "birth_date": "a" * 200,
            "gender": "a" * 200,
            "phone": "a" * 200,
            "address": "a" * 200,
        })
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'nik': assert x['msg'] == 'ensure this value has at most 100 characters'
            if x['loc'][-1] == 'name': assert x['msg'] == 'ensure this value has at most 100 characters'
            if x['loc'][-1] == 'birth_place': assert x['msg'] == 'ensure this value has at most 100 characters'
            if x['loc'][-1] == 'phone': assert x['msg'] == 'ensure this value has at most 20 characters'
        # check all field type data
        response = client.put(url + 'a',json={
            "nik": 123,
            "name": 123,
            "birth_place": 123,
            "birth_date": 123,
            "gender": 123,
            "phone": 123,
            "address": 123,
        })
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'client_id': assert x['msg'] == 'value is not a valid integer'
            if x['loc'][-1] == 'nik': assert x['msg'] == 'str type expected'
            if x['loc'][-1] == 'name': assert x['msg'] == 'str type expected'
            if x['loc'][-1] == 'birth_place': assert x['msg'] == 'str type expected'
            if x['loc'][-1] == 'birth_date': assert x['msg'] == 'strptime() argument 1 must be str, not int'
            if x['loc'][-1] == 'gender': assert x['msg'] == "unexpected value; permitted: 'LAKI-LAKI', 'PEREMPUAN'"
            if x['loc'][-1] == 'phone': assert x['msg'] == 'str type expected'
            if x['loc'][-1] == 'address': assert x['msg'] == 'str type expected'
        # check birth_date format
        response = client.put(url + '1',json={'birth_date': 'asd'})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'birth_date': assert x['msg'] == "time data 'asd' does not match format '%d-%m-%Y'"
        # invalid format
        response = client.put(url + '1',json={'nik': '11A'})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'nik': assert x['msg'] == 'string does not match regex \"^[0-9]*$\"'
        # invalid phone number
        response = client.put(url + '1',json={'phone': 'asdasd'})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'phone': assert x['msg'] == "value is not a valid mobile phone number"

        response = client.put(url + '1',json={'phone': '8762732'})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'phone': assert x['msg'] == "value is not a valid mobile phone number"
        # invalid nik
        response = client.put(url + '1',json={'nik': '123123'})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'nik': assert x['msg'] == 'invalid nik format'

        response = client.put(url + '1',json={'nik': '5103051234560006'})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'nik': assert x['msg'] == 'invalid nik format'

    @pytest.mark.asyncio
    async def test_update_client(self,async_client):
        response = await async_client.post('/users/login',json={
            'email': self.account_admin['email'],
            'password': self.account_admin['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/update/'
        client_id = await self.get_client_id('5103051905990006')
        # client not found
        response = await async_client.put(url + '9' * 8,json={
            "nik": "5103051905990006",
            "name": "NYOMAN PRADIPTA DEWANTARA",
            "birth_place": "BALIKPAPAN",
            "birth_date": "22-08-2021",
            "gender": "LAKI-LAKI",
            "phone": "+62 87862265363",
            "address": "PURIGADING"
        },headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 404
        assert response.json() == {"detail": "Client not found!"}
        # nik already taken
        response = await async_client.put(url + str(client_id),json={
            "nik": "5171010609990002",
            "name": "NYOMAN PRADIPTA DEWANTARA",
            "birth_place": "BALIKPAPAN",
            "birth_date": "22-08-2021",
            "gender": "LAKI-LAKI",
            "phone": "+62 87862265363",
            "address": "PURIGADING"
        },headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 400
        assert response.json() == {"detail": "The nik has already been taken."}
        # phone already taken
        response = await async_client.put(url + str(client_id),json={
            "nik": "5103051905990006",
            "name": "NYOMAN PRADIPTA DEWANTARA",
            "birth_place": "BALIKPAPAN",
            "birth_date": "22-08-2021",
            "gender": "LAKI-LAKI",
            "phone": "+62 87862265362",
            "address": "PURIGADING"
        },headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 400
        assert response.json() == {"detail": "The phone has already been taken."}

        response = await async_client.put(url + str(client_id),json={
            "nik": "5103051905990006",
            "name": "dewantara pradipta nyoman",
            "birth_place": "tejakula",
            "birth_date": "22-08-2021",
            "gender": "LAKI-LAKI",
            "phone": "+62 87862265363",
            "address": "kuta selatan"
        },headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully update the client."}
        # check all data is uppercase
        client_data = await self.get_client_data("5103051905990006")
        assert client_data['name'].isupper() is True
        assert client_data['birth_place'].isupper() is True
        assert client_data['gender'].isupper() is True
        assert client_data['address'].isupper() is True

    def test_validation_delete_client(self,client):
        url = self.prefix + '/delete/'
        # all field blank
        response = client.delete(url + '0')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'client_id': assert x['msg'] == 'ensure this value is greater than 0'
        # check all field type data
        response = client.delete(url + 'a')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'client_id': assert x['msg'] == 'value is not a valid integer'

    @pytest.mark.asyncio
    async def test_delete_client(self,async_client):
        response = await async_client.post('/users/login',json={
            'email': self.account_admin['email'],
            'password': self.account_admin['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/delete/'
        client_id = await self.get_client_id('5103051905990006')
        # client not found
        response = await async_client.delete(url + '9' * 8,headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 404
        assert response.json() == {"detail": "Client not found!"}
        # delete client one
        response = await async_client.delete(url + str(client_id),headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully delete the client."}
        # delete client two
        client_id = await self.get_client_id('5171010609990002')
        response = await async_client.delete(url + str(client_id),headers={'X-CSRF-TOKEN': csrf_access_token})
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
        # delete institution two
        institution_id = await self.get_institution_id(self.name2)
        image = await self.get_institution_image(self.name2)

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
