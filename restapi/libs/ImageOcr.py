import numpy as np
import re, os, cv2, pytesseract
from datetime import datetime
from typing import Optional

class BaseImageOcr:
    base_dir: str = os.path.join(os.path.dirname(__file__),'../static/identity_ocr/')

    def levenshtein(self, source: str, target: str) -> int:
        if len(source) < len(target):
            return self.levenshtein(target, source)

        # So now we have len(source) >= len(target).
        if len(target) == 0:
            return len(source)

        # We call tuple() to force strings to be used as sequences
        # ('c', 'a', 't', 's') - numpy uses them as values by default.
        source = np.array(tuple(source))
        target = np.array(tuple(target))

        # We use a dynamic programming algorithm, but with the
        # added optimization that we only need the last two rows
        # of the matrix.
        previous_row = np.arange(target.size + 1)
        for s in source:
            # Insertion (target grows longer than source):
            current_row = previous_row + 1

            # Substitution or matching:
            # Target and source items are aligned, and either
            # are different (cost of 1), or are the same (cost of 0).
            current_row[1:] = np.minimum(
                current_row[1:],
                np.add(previous_row[:-1], target != s)
            )

            # Deletion (target grows shorter than source):
            current_row[1:] = np.minimum(
                current_row[1:],
                current_row[0:-1] + 1
            )

            previous_row = current_row

        return previous_row[-1]

    def get_percentage_contain_text(self, regex: str, data_string: str) -> float:
        upper_char = len(" ".join(re.findall(regex, data_string)))
        total_char = len(data_string)
        return (upper_char / total_char) * 100

class ImageOcrKTP(BaseImageOcr):
    def change_wrong_digit_nik(self, character: str) -> str:
        character = character.replace("NIK","")
        character = character.replace("U","0")
        character = character.replace("O","0")
        character = character.replace("D","0")
        character = character.replace("N","0")

        character = character.replace("L","1")
        character = character.replace(")","1")
        character = character.replace("C","2")

        character = character.replace("Y","4")
        character = character.replace("H","4")
        character = character.replace("S","5")
        character = character.replace("b","6")
        character = character.replace("?","7")
        character = character.replace("A","8")
        character = character.replace("I","9")

        return character

    def change_wrong_digit_date(self, character: str) -> str:
        character = character.replace("/","7")
        return character

    def get_nik_entity(self, data: list) -> tuple:
        data_filter = list()
        for index, text in enumerate(data):
            # change wrong digit
            text = "".join(re.findall(r"[0-9]{2,}.*", self.change_wrong_digit_nik(text)))

            is_digit = len([x for x in text if x.isdigit()])
            is_char = len([x for x in text if not x.isdigit()])

            if is_digit > 10 and is_digit < 25:
                data_filter.append((is_digit,is_char,text,index))

        if len(data_filter) < 1:
            return (None, None)

        data_filter.sort(key=lambda tup: tup[0],reverse=True)
        data_filter.sort(key=lambda tup: tup[1])

        result = data_filter[0]

        if result[0] < 14:
            return (None, None)

        return (re.sub('[^0-9]','', result[-2]), result[-1])

    def get_gender_entity(self, data: list, date_index: int) -> tuple:
        for index, value in enumerate(data):
            if 'laki' in value.lower():
                return ('LAKI-LAKI', index)
            if 'perempuan' in value.lower() or 'wanita' in value.lower():
                return ('PEREMPUAN', index)

        if date_index is None: return (None, None)

        try:
            list_gender = ['laki-laki','laki','perempuan','wanita']
            contain_gender = re.findall(r"\b[A-Z]{3,}\b", data[date_index + 1])

            guest_gender = [
                (self.levenshtein(gender, x.lower()), gender) for x in contain_gender for gender in list_gender
            ]
            guest_gender.sort(key=lambda tup: tup[0])
            guest_gender = guest_gender[0]

            if guest_gender[-1] == 'laki-laki' or guest_gender[-1] == 'laki':
                return ('LAKI-LAKI', date_index + 1)
            if guest_gender[-1] == 'perempuan' or guest_gender[-1] == 'wanita':
                return ('PEREMPUAN', date_index + 1)
        except Exception:
            pass

        return (None, None)

    def get_address_entity(self, data: list, gender_index: int) -> tuple:
        index_one = gender_index + 1 if gender_index else None
        for x in ['Gol','Darah','Alamat']:
            for i,v in enumerate(data):
                if x in v and len(v.split()) > 1: index_one = i if x == 'Alamat' else i + 1

        if index_one is not None:
            result, index_two = None, index_one + 1

            try:
                percentage_char = self.get_percentage_contain_text("[A-Z/.,]+",data[index_one])
                percentage_num = self.get_percentage_contain_text("[0-9]+",data[index_one])
                found_word = re.findall(r"(\b(RT|RW|RTRW|KAWIN|BELUM|CERAI|HIDUP|MATI)\b)", data[index_one])
                if percentage_char >= percentage_num and len(found_word) == 0:
                    result = data[index_one]
            except Exception:
                return (None, None)

            # get address below
            try:
                percentage_char = self.get_percentage_contain_text("[A-Z/.,]+",data[index_two])
                percentage_num = self.get_percentage_contain_text("[0-9]+",data[index_two])
                found_word = re.findall(r"(\b(RT|RW|RTRW|KAWIN|BELUM|CERAI|HIDUP|MATI)\b)", data[index_two])
                if percentage_char >= percentage_num and len(found_word) == 0:
                    result = "{} {}".format(result,data[index_two])
            except Exception:
                pass

            if result:
                result = " ".join(re.findall(r"([A-Z0-9/.,]{2,}.*)", result))
                return (" ".join(re.findall("[A-Z0-9/.,]+", result)), index_one)

        return (None, None)

    def get_birth_place_entity(self, data: list, gender_index: int, date_index: int) -> tuple:
        index = gender_index or date_index
        if index and index == gender_index: index = index - 1

        try:
            if len(re.findall(r"([A-Z]{2,})", data[index])) == 0: index = index - 1
            if len(re.findall(r"([A-Z]{2,})", data[index])) == 0: return (None, None)

            result = " ".join(re.findall(r"[A-Z]{1,}[^a-z].*", data[index]))
            return (" ".join(re.findall("[A-Z]+", result)), index)
        except Exception:
            pass

        return (None, None)

    def get_name_entity(self, data: list, nik_index: int, birth_place_index: int) -> tuple:
        index_one, index_two, found_in = None, None, None

        if result := [i for i,v in enumerate(data) if len(re.findall(r"([A-Z]{2,})", v)) != 0 and 'nama' in v.lower()]:
            index_one = result[0]
            found_in = 'nama'

        try:
            if (
                index_one is None and
                birth_place_index is not None and
                len(re.findall(r"([A-Z]{2,})", data[birth_place_index - 1])) != 0 and
                len(re.findall(r"(\b(PROVINSI|KOTA|KABUPATEN)\b)", data[birth_place_index - 1])) == 0
            ):
                index_one = birth_place_index - 1
                found_in = 'birth_place'
        except Exception:
            pass

        try:
            if (
                index_one is None and
                nik_index is not None and
                len(re.findall(r"([A-Z]{2,})", data[nik_index + 1])) != 0 and
                len(re.findall(r"(\b(PROVINSI|KOTA|KABUPATEN)\b)", data[nik_index + 1])) == 0
            ):
                index_one = nik_index + 1
                found_in = 'nik'
        except Exception:
            pass

        if index_one is None: return (None, None)

        try:
            if (
                found_in in ['nama','nik'] and
                index_one + 1 != birth_place_index and
                self.get_percentage_contain_text("[A-Z]+",data[index_one + 1]) > 60 and
                len(re.findall(r"([A-Z]{2,})", data[index_one + 1])) != 0 and
                len(re.findall(r"(\b(PROVINSI|KOTA|KABUPATEN)\b)", data[index_one + 1])) == 0
            ):
                index_two = index_one + 1
        except Exception:
            pass

        try:
            if (
                found_in == 'birth_place' and
                index_one - 1 != nik_index and
                self.get_percentage_contain_text("[A-Z]+",data[index_one - 1]) > 60 and
                len(re.findall(r"([A-Z]{2,})", data[index_one - 1])) != 0 and
                len(re.findall(r"(\b(PROVINSI|KOTA|KABUPATEN)\b)", data[index_one - 1])) == 0
            ):
                index_two = index_one - 1
        except Exception:
            pass

        try:
            result = data[index_one]

            if found_in == 'birth_place' and index_two is not None:
                result = "{} {}".format(data[index_two],data[index_one])

            if found_in in ['nama','nik'] and index_two is not None:
                result = "{} {}".format(data[index_one],data[index_two])

            if result:
                result = " ".join(re.findall(r"[A-Z]{1,}[^a-z].*", result))
                return (" ".join(re.findall("[A-Z]+", result)), index_one)
        except Exception:
            pass

        return (None, None)

    def extract_valid_date(self, date_string: str) -> str:
        for i in range(len(date_string)):
            guest_date = date_string[i:i + 8]
            if len(guest_date) >= 6:
                day, month, year = None, None, None

                for i in reversed(range(1,3)):
                    try:
                        day = datetime.strptime(guest_date[0:i],'%d')
                        guest_date = guest_date[i:]
                        break
                    except Exception:
                        pass

                if day is None:
                    continue

                day = day.strftime('%d')

                for i in reversed(range(1,3)):
                    try:
                        month = datetime.strptime(guest_date[0:i],'%m')
                        guest_date = guest_date[i:]
                        break
                    except Exception:
                        pass

                if month is None:
                    continue

                month = month.strftime('%m')

                try:
                    year = datetime.strptime(guest_date,'%Y')
                except Exception:
                    continue

                year = year.strftime('%Y')

                if int(year) > 1910 and int(year) < 2100:
                    return f"{day}-{month}-{year}"

        return None

    def extract_date(self, data: list) -> tuple:
        contain_digit = [
            (re.sub("[^0-9]", "", value), index) for index, value
            in enumerate([self.change_wrong_digit_date(x) for x in data])
            if len(re.sub("[^0-9]", "", value)) > 5
        ]

        if len(contain_digit) < 1:
            return (None, None)

        valid_format_date = [
            (self.extract_valid_date(guest[0]),guest[1])
            for guest in contain_digit if self.extract_valid_date(guest[0])
        ]

        if len(valid_format_date) < 1:
            return (None, None)

        valid_format_date.sort(key=lambda tup: datetime.strptime(tup[0],'%d-%m-%Y').year)

        return valid_format_date[0]

    def extract_image_to_text(self, image: str, debug: Optional[bool] = None) -> dict:
        path = os.path.join(self.base_dir,'ktp',image)

        # read img
        img = cv2.imread(path)

        # convert the image to grayscale and blur sligthly
        blur = cv2.medianBlur(img, 3)
        gray = cv2.cvtColor(blur, cv2.COLOR_BGR2GRAY)

        # threshold image
        _, threshed = cv2.threshold(gray, 127, 255, cv2.THRESH_TRUNC)

        # (3) Detect
        result = pytesseract.image_to_string((threshed), lang="ind")
        result = [x for x in [i.strip() for i in result.split('\n')] if len(x) > 2]

        date, date_index = self.extract_date(result)
        nik, nik_index = self.get_nik_entity(result)
        gender, gender_index = self.get_gender_entity(result,date_index)
        address, address_index = self.get_address_entity(result,gender_index)
        birth_place, birth_place_index = self.get_birth_place_entity(result,gender_index,date_index)
        name, name_index = self.get_name_entity(result,nik_index,birth_place_index)

        if debug:
            print("=" * 20)
            print(result)
            print("=" * 20)

            print("NAMA -> ",(name,name_index))
            print("TGL LAHIR -> ",(date, date_index))
            print("TEMPAT LAHIR -> ",(birth_place,birth_place_index))
            print("NIK -> ",(nik,nik_index))
            print("JENIS KELAMIN -> ",(gender,gender_index))
            print("ADDRESS -> ",(address,address_index))

        return {
            'nik': nik if nik and len(nik) > 1 else None,
            'name': name if name and len(name) > 1 else None,
            'birth_date': date if date and len(date) > 1 else None,
            'birth_place': birth_place if birth_place and len(birth_place) > 1 else None,
            'gender': gender if gender and len(gender) > 1 else None,
            'address': address if address and len(address) > 1 else None
        }

class ImageOcrKIS(BaseImageOcr):
    def change_wrong_character_name(self, character: str) -> str:
        character = character.replace("|","I")
        return character

    def get_no_card_entity(self, data: list) -> tuple:
        if result := [(v,i,len(re.sub("[^0-9]", "", v))) for i,v in enumerate(data) if len(re.sub("[^0-9]", "", v)) > 10]:
            result.sort(key=lambda tup: tup[-1])
            return (re.sub('[^0-9]','', result[0][0]), result[0][1])
        return (None, None)

    def get_nik_entity(self, data: list, no_card: str) -> tuple:
        if result := [(v,i,len(re.sub("[^0-9]", "", v))) for i,v in enumerate(data) if len(re.sub("[^0-9]", "", v)) > 10]:
            result.sort(key=lambda tup: tup[-1],reverse=True)
            if re.sub('[^0-9]','', result[0][0]) != no_card:
                return (re.sub('[^0-9]','', result[0][0]), result[0][1])
        return (None, None)

    def get_name_entity(self, data: list, no_card_index: int) -> tuple:
        try:
            name = self.change_wrong_character_name(data[no_card_index + 1])
            result = " ".join(re.findall(r"[A-Z,.]{1,}[^a-z].*", name))
            percentage = self.get_percentage_contain_text("[A-Z,.]+", name)
            if result and percentage > 60:
                return (" ".join(re.findall("[A-Z,.]+", result)), no_card_index + 1)
        except Exception:
            pass

        return (None, None)

    def get_address_entity(self, data: list, name_index: int, no_card_index: int, date_index: int) -> tuple:
        index_one = name_index or no_card_index
        if index_one and index_one == name_index: index_one = index_one + 1
        if index_one and index_one == no_card_index: index_one = index_one + 2
        if found := [i for i,v in enumerate(data) if len(re.findall(r"([A-Z/.,]{2,})", v)) != 0 and 'Alamat' in v]:
            index_one = found[0]

        result = None

        try:
            if self.get_percentage_contain_text("[A-Z0-9/.,]+",data[index_one]) >= 75:
                result = data[index_one]
        except Exception:
            pass

        try:
            if (
                result is not None and
                index_one + 1 != date_index and
                self.get_percentage_contain_text("[A-Z0-9/.,]+",data[index_one + 1]) >= 75
            ):
                result = "{} {}".format(data[index_one], data[index_one + 1])
        except Exception:
            pass

        if result:
            result = " ".join(re.findall(r"([A-Z0-9/.,]{2,}.*)", result))
            return (" ".join(re.findall("[A-Z0-9/.,]+", result)), index_one)

        return (None, None)

    def get_birth_date_entity(self, data: list) -> tuple:
        if not data: return (None, None)

        months = [
            ('01','januari'), ('02','februari'),
            ('03','maret'), ('04','april'),
            ('05','mei'), ('06','juni'),
            ('07','juli'), ('08','agustus'),
            ('09','september'), ('10','oktober'),
            ('11','november'), ('12','desember')
        ]

        guest_date = list()
        for month in months:
            date = [
                (word[0], min([self.levenshtein(month[-1], x.lower()) for x in word[-1]]))
                for word in [(i,v.split()) for i,v in enumerate(data)]
            ]
            date.sort(key=lambda tup: tup[-1])
            guest_date.append((date[0][1],date[0][0],month))

        guest_date.sort(key=lambda tup: tup[0])
        guest_date = guest_date[0]

        # get word and replace month to number
        replace_word = [(self.levenshtein(guest_date[-1][-1], x.lower()), x) for x in data[guest_date[1]].split()]
        replace_word.sort(key=lambda tup: tup[0])
        data[guest_date[1]] = data[guest_date[1]].replace(replace_word[0][-1],guest_date[-1][0])

        try:
            tgl = re.findall(r"(\d{1,2} \d{1,2} \d{4})",data[guest_date[1]])[0]
            tgl = re.sub('[^0-9]','', tgl)
            if len(tgl) == 7: tgl = "0{}".format(tgl)

            date = datetime.strptime(tgl[0:2] + '-' + tgl[2:4] + '-' + tgl[4:], '%d-%m-%Y')
            if((date.year > 1910) and (date.year < 2100)):
                return (date.strftime('%d-%m-%Y'), guest_date[1])
        except Exception:
            pass

        return (None, None)

    def extract_image_to_text(self, image: str, debug: Optional[bool] = None) -> dict:
        path = os.path.join(self.base_dir,'kis',image)

        # read img
        img = cv2.imread(path)

        # convert the image to grayscale and blur sligthly
        blur = cv2.medianBlur(img, 3)
        gray = cv2.cvtColor(blur, cv2.COLOR_BGR2GRAY)

        # threshold image
        _, threshed = cv2.threshold(gray, 127, 255, cv2.THRESH_TRUNC)

        # (3) Detect
        result = pytesseract.image_to_string((threshed), lang="ind")
        result = [x for x in [i.strip() for i in result.split('\n')] if len(x) > 2]

        no_card, no_card_index = self.get_no_card_entity(result)
        nik, nik_index = self.get_nik_entity(result, no_card)
        date, date_index = self.get_birth_date_entity(result)
        name, name_index = self.get_name_entity(result, no_card_index)
        address, address_index = self.get_address_entity(result, name_index, no_card_index, date_index)

        if debug:
            print("=" * 20)
            print(result)
            print("=" * 20)

            print("NOMOR KARTU -> ",(no_card,no_card_index))
            print("NAMA -> ",(name,name_index))
            print("NIK -> ",(nik,nik_index))
            print("TGL LAHIR -> ",(date,date_index))
            print("ADDRESS -> ",(address, address_index))

        return {
            'no_card': no_card if no_card and len(no_card) > 1 else None,
            'nik': nik if nik and len(nik) > 1 else None,
            'name': name if name and len(name) > 1 else None,
            'birth_date': date if date and len(date) > 1 else None,
            'address': address if address and len(address) > 1 else None
        }
