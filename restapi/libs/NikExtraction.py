from datetime import datetime
from config import settings

class NikExtraction:
    def validator(self, nik: str) -> bool:
        return len(nik) == 16

    def locator(self, kodewilayah: str) -> tuple:
        try:
            df_tmp = next(filter(lambda data: data['kodewilayah'] == kodewilayah, settings.nik_area_code_data))
            valid = True
            province = df_tmp['provinsi'].upper()
            district = df_tmp['kabupatenkota'].upper()
            subdistrict = df_tmp['kecamatan'].upper()
        except Exception:
            valid = False
            province = None
            district = None
            subdistrict = None
        finally:
            return (valid, province, district, subdistrict)

    def gender_checker(self, gender_num: int) -> str:
        if gender_num in [0, 1, 2, 3]:
            return 'LAKI-LAKI'
        if gender_num in [4, 5, 6, 7]:
            return 'PEREMPUAN'
        return None

    def dob_checker(self, dob: int) -> datetime:
        if dob > 400000: dob = dob - 400000

        dob = str(dob)

        try:
            dateformat_dob = datetime.strptime(dob, '%d%m%y')
        except Exception:
            dateformat_dob = None

        return dateformat_dob

    def nik_extract(self, nik_number: str) -> dict:
        """
        Required to assume nik is valid

        valid -> true
        location_valid -> true/false
        gender -> not null
        birth_date -> not null
        """
        try:
            valid = self.validator(nik_number)
            area_code = nik_number[:6]
            location_valid, province, district, subdistrict = self.locator(area_code)
            gender = self.gender_checker(int(nik_number[6:7]))
            birth_date = self.dob_checker(int(nik_number[6:12]))
        except Exception:
            valid, area_code, location_valid = False, None, False
            province, district, subdistrict = None, None, None
            gender, birth_date = None, None

        valid = valid is True and location_valid is True and birth_date is not None

        return {
            'nik': nik_number,
            'valid': valid,
            'area_code': area_code,
            'location_valid': location_valid,
            'province': province,
            'district': district,
            'subdistrict': subdistrict,
            'gender': gender,
            'birth_date': birth_date
        }
