from .operationtest import OperationTest

class TestClient(OperationTest):
    prefix = "/clients"

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
