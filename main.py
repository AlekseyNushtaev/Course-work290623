import requests
import json
import logging
import time

class VkPhotoLoad:
    url_vk = 'https://api.vk.com/method/photos.get'
    url_yadisk = 'https://cloud-api.yandex.net/v1/disk/resources'
    def __init__(self, id, token_vk, token_yadisk, photo_value=5, folder_name='VKupload'):
        self.params_vk = {
            'owner_id': id,
            'access_token': token_vk,
            'extended': '1',
            'v': '5.131'
        }
        self.params_album = {
            'owner_id': id,
            'access_token': token_vk,
            'v': '5.131'
        }
        self.headers_yadisk = {
            'Authorization': token_yadisk
        }
        self.token_yadisk = token_yadisk
        self.photo_value = photo_value
        self.path_folder = folder_name

    def album_choice(self):
        # Запрос альбомов через метод photos.getAlbums, возврат значения, которое вводит пользователь
        response_vk_albums = requests.get(self.url_vk + 'Albums', params=self.params_album)
        logging.info('Получен json-file из VK с данными по всем альбомам')
        time.sleep(0.1)
        album_dict = {'Профиль': 'profile', 'Стена': 'wall'}
        for item in response_vk_albums.json()['response']['items']:
            album_dict[item['title']] = item['id']
        print('****** АЛЬБОМЫ ПОЛЬЗОВАТЕЛЯ ******')
        for key in album_dict.keys():
            print(key)
        print('**********************************', end='\n\n')
        return album_dict[input('Введите имя альбома для выгрузки фотографий    ')]

    def vk_photo_get(self):
        # получение json файла при выполнении метода photos.get, преобразование в список необходимыми для загрузки фото
        # на диск и создания json файла параметры (name, type, url). Возвращаем требуемое кол-во фото.
        response_vk_json = requests.get(self.url_vk, params={**self.params_vk, **{'album_id': self.album_choice()}})
        logging.info('Получен json-file из VK с данными по фото')
        photo_list = []
        for img in response_vk_json.json()['response']['items']:
            type, url = img['sizes'][0]['type'], img['sizes'][0]['url']
            for img_uniq in img['sizes']:
                if img_uniq['type'] > type:                        # сравниваем тип размера в обратном алфавитном порядке
                    type, url = img_uniq['type'], img_uniq['url']
                elif img_uniq['type'] == 'w':                      # есть исключение из алфапвита - 'w' самый большое разрешение
                    type, url = img_uniq['type'], img_uniq['url']
                    break
            name = f'{str(img["likes"]["count"])}.jpg'
            for element in photo_list:
                if element[1] == name:
                    name = f'{str(img["likes"]["count"])}-{str(img["date"])}.jpg'
# бывает, что в альбоме фото размещены одной датой - соответственно фото с одинаковым кол-вом лайков будут с одинаковым
# именем и перезаписываться, для исключения этой ситуации  добавляем id фото
                if element[1] == f'{str(img["likes"]["count"])}-{str(img["date"])}.jpg':
                    name = f'{str(img["likes"]["count"])}-{str(img["date"])}-{str(img["id"])}.jpg'
            photo_list.append([type, name, url])
        photo_list.sort(reverse=True, key=lambda x: x[0] == 'w') # сортируем в обратном алфавитном порядке с исключение - 'w'
        logging.info(f'Сформирован список с данными по фото с наибольшими размерами - {self.photo_value} шт.')
        return photo_list[:self.photo_value]

    def json_file(self, photo_list):
        # формирование json-файла с праметрами загружаемых фотографий на диск
        json_list = []
        for photo in photo_list:
            json_list.append({'file name': photo[1], 'size': photo[0]})
        with open('photo_info.json', 'w', encoding='utf-8') as f:
            json.dump(json_list, f, indent=2)
        logging.info('Сформирован выходной json-файл с данными по фото')

    def yadisk_upload(self):
        # создание папки на YandexDisk и загрузка файлов
        photo_list = self.vk_photo_get()
        response_create_folder = requests.put(self.url_yadisk, params={'path': self.path_folder}, headers=self.headers_yadisk)
        logging.info(f'Создана папка {self.path_folder} на YandexDisk')
        cnt = 0
        for photo in photo_list:
            cnt += 1
            params = {
                'url': photo[2],
                'path': self.path_folder + '/' + photo[1]
            }
            response_upload_file = requests.post(self.url_yadisk+'/upload', params=params, headers=self.headers_yadisk)
            logging.info(f'Загружено {cnt} файлов из {self.photo_value}')
        self.json_file(photo_list)


if __name__ == '__main__':

    file_log = logging.FileHandler(filename='py_log.log', encoding='utf-8', mode='w')
    console_out = logging.StreamHandler()
    logging.basicConfig(handlers=(file_log, console_out),
                        format='[%(asctime)s | %(levelname)s]: %(message)s',
                        level=logging.INFO)

    with open('tokenVK.txt', 'r') as file:
        token_vk = file.read().strip()
        logging.info('Загрузка ВК токена из файла tokenVK.txt завершена')

    with open('tokenYadisk.txt', 'r') as file:
        token_yadisk = file.read().strip()
        logging.info('Загрузка YandexDisk токена из файла tokenYadisk.txt завершена')

    id = '1'
    id_load = VkPhotoLoad(id, token_vk, token_yadisk)
    id_load.yadisk_upload()
