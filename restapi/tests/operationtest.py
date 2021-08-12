import os

class OperationTest:
    name = 'testtesttttttt'
    name2 = 'testtesttttttt2'
    account_1 = {'email':'testtesting@gmail.com','username':'testtesting','password':'testtesting'}
    account_2 = {'email':'testtesting2@gmail.com','username':'testtesting2','password':'testtesting2'}
    base_dir = os.path.join(os.path.dirname(__file__),'../static/')
    test_image_dir = base_dir + 'test_image/'
