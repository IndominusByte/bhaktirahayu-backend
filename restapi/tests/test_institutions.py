import pytest
from pathlib import Path
from .operationtest import OperationTest

class TestInstitution(OperationTest):
    prefix = "/institutions"

    @pytest.mark.asyncio
    async def test_create_user(self,async_client):
        # create user admin
        await self.create_user(role='admin',**self.account_admin)
        # create user doctor 1
        await self.create_user(role='doctor',signature='signature_test.png',**self.account_1)

    def test_validation_create_institution(self,client):
        url = self.prefix + '/create'
        # field required
        response = client.post(url,data={})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'name': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'stamp': assert x['msg'] == 'field required'
        # all field blank
        response = client.post(url,data={'name':' '})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'name': assert x['msg'] == 'ensure this value has at least 3 characters'
        # test limit value
        response = client.post(url,data={'name':'a' * 200})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'name': assert x['msg'] == 'ensure this value has at most 100 characters'

        # danger file extension
        with open(self.test_image_dir + 'test.txt','rb') as tmp:
            response = client.post(url,files={'stamp': tmp})
            assert response.status_code == 422
            assert response.json() == {'detail': 'Cannot identify the image.'}

        with open(self.test_image_dir + 'test.txt','rb') as tmp:
            response = client.post(url,files={'antigen': tmp})
            assert response.status_code == 422
            assert response.json() == {'detail': 'Cannot identify the image.'}

        with open(self.test_image_dir + 'test.txt','rb') as tmp:
            response = client.post(url,files={'genose': tmp})
            assert response.status_code == 422
            assert response.json() == {'detail': 'Cannot identify the image.'}

        with open(self.test_image_dir + 'test.txt','rb') as tmp:
            response = client.post(url,files={'pcr': tmp})
            assert response.status_code == 422
            assert response.json() == {'detail': 'Cannot identify the image.'}

        # not valid file extension
        with open(self.test_image_dir + 'test.gif','rb') as tmp:
            response = client.post(url,files={'stamp': tmp})
            assert response.status_code == 422
            assert response.json() == {'detail': 'Image must be between jpg, png, jpeg.'}

        with open(self.test_image_dir + 'test.gif','rb') as tmp:
            response = client.post(url,files={'antigen': tmp})
            assert response.status_code == 422
            assert response.json() == {'detail': 'Image must be between jpg, png, jpeg.'}

        with open(self.test_image_dir + 'test.gif','rb') as tmp:
            response = client.post(url,files={'genose': tmp})
            assert response.status_code == 422
            assert response.json() == {'detail': 'Image must be between jpg, png, jpeg.'}

        with open(self.test_image_dir + 'test.gif','rb') as tmp:
            response = client.post(url,files={'pcr': tmp})
            assert response.status_code == 422
            assert response.json() == {'detail': 'Image must be between jpg, png, jpeg.'}

        # file cannot grater than 5 Mb
        with open(self.test_image_dir + 'size.jpeg','rb') as tmp:
            response = client.post(url,files={'stamp': tmp})
            assert response.status_code == 413
            assert response.json() == {'detail':'An image cannot greater than 5 Mb.'}

        with open(self.test_image_dir + 'size.jpeg','rb') as tmp:
            response = client.post(url,files={'antigen': tmp})
            assert response.status_code == 413
            assert response.json() == {'detail':'An image cannot greater than 5 Mb.'}

        with open(self.test_image_dir + 'size.jpeg','rb') as tmp:
            response = client.post(url,files={'genose': tmp})
            assert response.status_code == 413
            assert response.json() == {'detail':'An image cannot greater than 5 Mb.'}

        with open(self.test_image_dir + 'size.jpeg','rb') as tmp:
            response = client.post(url,files={'pcr': tmp})
            assert response.status_code == 413
            assert response.json() == {'detail':'An image cannot greater than 5 Mb.'}

        # antigen, genose or pcr must be filled
        with open(self.test_image_dir + 'image.jpeg','rb') as tmp:
            response = client.post(url,data={'name': self.name},files={'stamp': tmp})
            assert response.status_code == 422
            assert response.json() == {'detail': 'Upps, at least upload one of antigen, genose or pcr.'}

    @pytest.mark.asyncio
    async def test_create_institution(self,async_client):
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/create'
        # check user is admin
        with open(self.test_image_dir + 'image.jpeg','rb') as tmp, open(self.test_image_dir + 'image.jpeg','rb') as tmp2:
            response = await async_client.post(url,
                data={'name': self.name},
                files={'stamp': tmp, 'antigen': tmp2},
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

        with open(self.test_image_dir + 'image.jpeg','rb') as tmp, \
                open(self.test_image_dir + 'image.jpeg','rb') as tmp2, \
                open(self.test_image_dir + 'image.jpeg','rb') as tmp3, \
                open(self.test_image_dir + 'image.jpeg','rb') as tmp4:

            response = await async_client.post(url,
                data={'name': self.name},
                files={'stamp': tmp, 'antigen': tmp2, 'genose': tmp3, 'pcr': tmp4},
                headers={'X-CSRF-TOKEN': csrf_access_token}
            )
            assert response.status_code == 201
            assert response.json() == {"detail": "Successfully add a new institution."}

        # check image exists in directory
        image = await self.get_institution_image(self.name)
        assert Path(self.institution_dir + image['stamp']).is_file() is True
        assert Path(self.institution_dir + image['antigen']).is_file() is True
        assert Path(self.institution_dir + image['genose']).is_file() is True
        assert Path(self.institution_dir + image['pcr']).is_file() is True

    def test_name_duplicate_create_institution(self,client):
        response = client.post('/users/login',json={
            'email': self.account_admin['email'],
            'password': self.account_admin['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/create'

        with open(self.test_image_dir + 'image.jpeg','rb') as tmp, open(self.test_image_dir + 'image.jpeg','rb') as tmp2:
            response = client.post(url,
                data={'name': self.name},
                files={'stamp': tmp, 'antigen': tmp2},
                headers={'X-CSRF-TOKEN': csrf_access_token}
            )
            assert response.status_code == 400
            assert response.json() == {"detail": "The name has already been taken."}

    def test_validation_get_all_institutions(self,client):
        url = self.prefix + '/all-institutions'
        # field required
        response = client.get(url)
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'page': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'per_page': assert x['msg'] == 'field required'
        # all field blank
        response = client.get(url + '?page=0&per_page=0&q=&checking_type')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'page': assert x['msg'] == 'ensure this value is greater than 0'
            if x['loc'][-1] == 'per_page': assert x['msg'] == 'ensure this value is greater than 0'
            if x['loc'][-1] == 'q': assert x['msg'] == 'ensure this value has at least 1 characters'
        # check all field type data
        response = client.get(url + '?page=a&per_page=a&q=123&checking_type=123')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'page': assert x['msg'] == 'value is not a valid integer'
            if x['loc'][-1] == 'per_page': assert x['msg'] == 'value is not a valid integer'
            if x['loc'][-1] == 'checking_type': assert x['msg'] == "unexpected value; permitted: 'genose', 'antigen', 'pcr'"

    def test_get_all_institutions(self,client):
        url = self.prefix + '/all-institutions'

        response = client.get(url + '?page=1&per_page=1&q=' + self.name)
        assert response.status_code == 200
        assert 'data' in response.json()
        assert 'total' in response.json()
        assert 'next_num' in response.json()
        assert 'prev_num' in response.json()
        assert 'page' in response.json()
        assert 'iter_pages' in response.json()

        # check data exists and type data
        assert type(response.json()['data'][0]['institutions_id']) == str
        assert type(response.json()['data'][0]['institutions_name']) == str
        assert type(response.json()['data'][0]['institutions_stamp']) == str
        assert type(response.json()['data'][0]['institutions_antigen']) == str
        assert type(response.json()['data'][0]['institutions_genose']) == str
        assert type(response.json()['data'][0]['institutions_pcr']) == str

    def test_validation_get_multiple_institutions(self,client):
        url = self.prefix + '/get-multiple-institutions'
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
    async def test_get_multiple_institutions(self,async_client):
        response = await async_client.post('/users/login',json={
            'email': self.account_admin['email'],
            'password': self.account_admin['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/get-multiple-institutions'

        institution_id = await self.get_institution_id(self.name)
        # institution empty
        response = await async_client.post(url,json={'list_id': ['9' * 8]},headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 200
        assert response.json() == []

        response = await async_client.post(url,
            json={'list_id': [str(institution_id)]},
            headers={'X-CSRF-TOKEN': csrf_access_token}
        )
        assert response.status_code == 200
        # check data exists and type data
        assert type(response.json()[0]['institutions_id']) == str
        assert type(response.json()[0]['institutions_name']) == str

    def test_validation_update_institution(self,client):
        url = self.prefix + '/update/'
        # field required
        response = client.put(url + '0',data={})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'name': assert x['msg'] == 'field required'
        # all field blank
        response = client.put(url + '0',data={'name': ' ', 'image_delete': ' '})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'institution_id': assert x['msg'] == 'ensure this value is greater than 0'
            if x['loc'][-1] == 'name': assert x['msg'] == 'ensure this value has at least 3 characters'
            if x['loc'][-1] == 'image_delete': assert x['msg'] == 'ensure this value has at least 2 characters'
        # check all field type data
        response = client.put(url + 'a')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'institution_id': assert x['msg'] == 'value is not a valid integer'
        # test limit value
        response = client.put(url + '1',data={'name': 'a' * 200})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'name': assert x['msg'] == 'ensure this value has at most 100 characters'

        # danger file extension
        with open(self.test_image_dir + 'test.txt','rb') as tmp:
            response = client.put(url + '1',files={'stamp': tmp})
            assert response.status_code == 422
            assert response.json() == {'detail': 'Cannot identify the image.'}

        with open(self.test_image_dir + 'test.txt','rb') as tmp:
            response = client.put(url + '1',files={'antigen': tmp})
            assert response.status_code == 422
            assert response.json() == {'detail': 'Cannot identify the image.'}

        with open(self.test_image_dir + 'test.txt','rb') as tmp:
            response = client.put(url + '1',files={'genose': tmp})
            assert response.status_code == 422
            assert response.json() == {'detail': 'Cannot identify the image.'}

        with open(self.test_image_dir + 'test.txt','rb') as tmp:
            response = client.put(url + '1',files={'pcr': tmp})
            assert response.status_code == 422
            assert response.json() == {'detail': 'Cannot identify the image.'}

        # not valid file extension
        with open(self.test_image_dir + 'test.gif','rb') as tmp:
            response = client.put(url + '1',files={'stamp': tmp})
            assert response.status_code == 422
            assert response.json() == {'detail': 'Image must be between jpg, png, jpeg.'}

        with open(self.test_image_dir + 'test.gif','rb') as tmp:
            response = client.put(url + '1',files={'antigen': tmp})
            assert response.status_code == 422
            assert response.json() == {'detail': 'Image must be between jpg, png, jpeg.'}

        with open(self.test_image_dir + 'test.gif','rb') as tmp:
            response = client.put(url + '1',files={'genose': tmp})
            assert response.status_code == 422
            assert response.json() == {'detail': 'Image must be between jpg, png, jpeg.'}

        with open(self.test_image_dir + 'test.gif','rb') as tmp:
            response = client.put(url + '1',files={'pcr': tmp})
            assert response.status_code == 422
            assert response.json() == {'detail': 'Image must be between jpg, png, jpeg.'}

        # file cannot grater than 5 Mb
        with open(self.test_image_dir + 'size.jpeg','rb') as tmp:
            response = client.put(url + '1',files={'stamp': tmp})
            assert response.status_code == 413
            assert response.json() == {'detail':'An image cannot greater than 5 Mb.'}

        with open(self.test_image_dir + 'size.jpeg','rb') as tmp:
            response = client.put(url + '1',files={'antigen': tmp})
            assert response.status_code == 413
            assert response.json() == {'detail':'An image cannot greater than 5 Mb.'}

        with open(self.test_image_dir + 'size.jpeg','rb') as tmp:
            response = client.put(url + '1',files={'genose': tmp})
            assert response.status_code == 413
            assert response.json() == {'detail':'An image cannot greater than 5 Mb.'}

        with open(self.test_image_dir + 'size.jpeg','rb') as tmp:
            response = client.put(url + '1',files={'pcr': tmp})
            assert response.status_code == 413
            assert response.json() == {'detail':'An image cannot greater than 5 Mb.'}

        # invalid image delete format
        response = client.put(url + '1',data={'name': 'a' * 4, 'image_delete': 'a' * 3})
        assert response.status_code == 422
        assert response.json() == {'detail': 'Invalid image format on image_delete'}

    @pytest.mark.asyncio
    async def test_update_institution(self,async_client):
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/update/'
        image = await self.get_institution_image(self.name)
        institution_id = await self.get_institution_id(self.name)
        # check user is admin
        response = await async_client.put(url + str(institution_id),
            data={'name': self.name},
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
        # stamp is required
        response = await async_client.put(url + str(institution_id),
            data={'name': self.name, 'image_delete': image['stamp']},
            headers={'X-CSRF-TOKEN': csrf_access_token}
        )
        assert response.status_code == 422
        assert response.json() == {"detail": "Image is required, make sure the institution has stamp."}
        # antigen, genose or pcr must be filled
        response = await async_client.put(url + str(institution_id),
            data={'name': self.name, 'image_delete': ','.join([image['antigen'],image['genose'],image['pcr']])},
            headers={'X-CSRF-TOKEN': csrf_access_token}
        )
        assert response.status_code == 422
        assert response.json() == {"detail": "Upps, at least upload one of antigen, genose or pcr."}
        # try to switch image without image delete
        with open(self.test_image_dir + 'image.jpeg','rb') as tmp, \
                open(self.test_image_dir + 'image.jpeg','rb') as tmp2, \
                open(self.test_image_dir + 'image.jpeg','rb') as tmp3, \
                open(self.test_image_dir + 'image.jpeg','rb') as tmp4:
            response = await async_client.put(url + str(institution_id),
                data={'name': self.name},
                files={'stamp': tmp,'antigen': tmp2, 'genose': tmp3, 'pcr': tmp4},
                headers={'X-CSRF-TOKEN': csrf_access_token}
            )
            assert response.status_code == 200
            assert response.json() == {"detail": "Successfully update the institution."}

        # check image is remove
        assert Path(self.institution_dir + image['stamp']).is_file() is False
        assert Path(self.institution_dir + image['antigen']).is_file() is False
        assert Path(self.institution_dir + image['genose']).is_file() is False
        assert Path(self.institution_dir + image['pcr']).is_file() is False

        # try to delete image and switch image
        image = await self.get_institution_image(self.name)

        with open(self.test_image_dir + 'image.jpeg','rb') as tmp, \
                open(self.test_image_dir + 'image.jpeg','rb') as tmp2:
            response = await async_client.put(url + str(institution_id),
                data={'name': self.name, 'image_delete': ','.join([image['antigen'],image['pcr']])},
                files={'stamp': tmp, 'genose': tmp2},
                headers={'X-CSRF-TOKEN': csrf_access_token}
            )
            assert response.status_code == 200
            assert response.json() == {"detail": "Successfully update the institution."}

        # check image is remove
        assert Path(self.institution_dir + image['stamp']).is_file() is False
        assert Path(self.institution_dir + image['antigen']).is_file() is False
        assert Path(self.institution_dir + image['genose']).is_file() is False
        assert Path(self.institution_dir + image['pcr']).is_file() is False
        # check image in db has been switch
        image = await self.get_institution_image(self.name)
        assert image['stamp'] is not None
        assert image['antigen'] is None
        assert image['genose'] is not None
        assert image['pcr'] is None

        # update to default
        with open(self.test_image_dir + 'image.jpeg','rb') as tmp, \
                open(self.test_image_dir + 'image.jpeg','rb') as tmp2, \
                open(self.test_image_dir + 'image.jpeg','rb') as tmp3, \
                open(self.test_image_dir + 'image.jpeg','rb') as tmp4:
            response = await async_client.put(url + str(institution_id),
                data={'name': self.name},
                files={'stamp': tmp,'antigen': tmp2, 'genose': tmp3, 'pcr': tmp4},
                headers={'X-CSRF-TOKEN': csrf_access_token}
            )
            assert response.status_code == 200
            assert response.json() == {"detail": "Successfully update the institution."}

    @pytest.mark.asyncio
    async def test_name_duplicate_update_institution(self,async_client):
        # user admin login
        response = await async_client.post('/users/login',json={
            'email': self.account_admin['email'],
            'password': self.account_admin['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/create'
        # create another institution
        with open(self.test_image_dir + 'image.jpeg','rb') as tmp, \
                open(self.test_image_dir + 'image.jpeg','rb') as tmp2, \
                open(self.test_image_dir + 'image.jpeg','rb') as tmp3, \
                open(self.test_image_dir + 'image.jpeg','rb') as tmp4:

            response = await async_client.post(url,
                data={'name': self.name2},
                files={'stamp': tmp, 'antigen': tmp2, 'genose': tmp3, 'pcr': tmp4},
                headers={'X-CSRF-TOKEN': csrf_access_token}
            )
            assert response.status_code == 201
            assert response.json() == {"detail": "Successfully add a new institution."}

        url = self.prefix + '/update/'
        institution_id = await self.get_institution_id(self.name2)
        # name already taken
        response = await async_client.put(url + str(institution_id),
            data={'name': self.name},
            headers={'X-CSRF-TOKEN': csrf_access_token}
        )
        assert response.status_code == 400
        assert response.json() == {"detail": "The name has already been taken."}

    def test_validation_delete_institution(self,client):
        url = self.prefix + '/delete/'
        # all field blank
        response = client.delete(url + '0')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'institution_id': assert x['msg'] == 'ensure this value is greater than 0'
        # check all field type data
        response = client.delete(url + 'a')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'institution_id': assert x['msg'] == 'value is not a valid integer'

    @pytest.mark.asyncio
    async def test_delete_institution(self,async_client):
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/delete/'
        institution_id = await self.get_institution_id(self.name)
        image = await self.get_institution_image(self.name)
        # check user is admin
        response = await async_client.delete(url + str(institution_id),headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 401
        assert response.json() == {"detail": "Only users with admin privileges can do this action."}
        # user admin login
        response = await async_client.post('/users/login',json={
            'email': self.account_admin['email'],
            'password': self.account_admin['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')
        # institution not found
        response = await async_client.delete(url + '9' * 8,headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 404
        assert response.json() == {"detail": "Institution not found!"}
        # delete institution one
        response = await async_client.delete(url + str(institution_id),headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully delete the institution."}
        # check image has been delete in directory
        assert Path(self.institution_dir + image['stamp']).is_file() is False
        assert Path(self.institution_dir + image['antigen']).is_file() is False
        assert Path(self.institution_dir + image['genose']).is_file() is False
        assert Path(self.institution_dir + image['pcr']).is_file() is False

        # delete institution two
        institution_id = await self.get_institution_id(self.name2)
        image = await self.get_institution_image(self.name2)

        response = await async_client.delete(url + str(institution_id),headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully delete the institution."}
        # check image has been delete in directory
        assert Path(self.institution_dir + image['stamp']).is_file() is False
        assert Path(self.institution_dir + image['antigen']).is_file() is False
        assert Path(self.institution_dir + image['genose']).is_file() is False
        assert Path(self.institution_dir + image['pcr']).is_file() is False

    @pytest.mark.asyncio
    async def test_delete_user_from_db(self,async_client):
        await self.delete_user_from_db()
