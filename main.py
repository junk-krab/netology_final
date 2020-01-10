import requests
import json
import time
import sys

TOKEN = '73eaea320bdc0d3299faa475c196cfea1c4df9da4c6d291633f9fe8f83c08c4de2a3abf89fbc3ed8a44e1'
USERS_GET_URL = 'https://api.vk.com/method/users.get'
GROUPS_GET_URL = 'https://api.vk.com/method/groups.get'
GROUPS_GETMEMBERS_URL = 'https://api.vk.com/method/groups.getMembers'


def clean_request(URL, params):
    basic_params = {
        'v': '5.101',
        'access_token': TOKEN
    }
    params.update(basic_params)
    while True:
        try:
            response = requests.get(URL, params=params)
            if response.status_code == 200:
                response = response.json()
                if 'error' in response:
                    error = response['error']['error_code']
                    if error in (18, 30):
                        print('Пользователь удален, заблокирован или профиль приватный')
                        sys.exit()
                    elif error == 6:
                        time.sleep(0.4)
                        continue
                    elif error == 113:
                        print('Неверный ID')
                        sys.exit()
                    else:
                        print('Произошла одна из многочисленных ошибок')
                        sys.exit()
                else:
                    return response
            else:
                print('Ошибка сервера')
                sys.exit()
        except requests.ReadTimeout:
            print('Read Timeout')
            continue


class User:
    id = ''

    def __init__(self, id):
        # n кол-во друзей в какой либо группе
        self.n = 2
        self.list_without_friends = []
        self.list_with_friends = []
        self.id = id
        params = {
            'user_ids': self.id,
        }
        response = clean_request(USERS_GET_URL, params)
        print(f'Запрашиваем информацию о {id}')
        self.id = response['response'][0]['id']

    def take_groups(self):
        params = {
            'user_id': self.id,
            'count': '1000',
            'extended': '1',
            'fields': ['members_count']
        }
        response = clean_request(GROUPS_GET_URL, params)
        print('Запрашиваем информацию о группах')
        group_list = []
        for i in response['response']['items']:
            if 'deactivated' not in i:
                group_list.append(dict(gid=i['id'], name=i['name'], members_count=i['members_count']))
        return group_list

    def groups_without_friends(self, groups_list):
        print('Выбираем группы в которой нет друзей:')
        for ind, group in enumerate(groups_list):
            params = {
                'group_id': group['gid'],
                'filter': 'friends'
            }
            response_friend_in_group = clean_request(GROUPS_GETMEMBERS_URL, params)
            print('\r{} из {} групп пройдено'.format(ind + 1, len(groups_list)), end='')
            if 0 < response_friend_in_group['response']['count'] <= self.n:
                self.list_with_friends.append(groups_list[ind])
            if response_friend_in_group['response']['count'] == 0:
                self.list_without_friends.append(groups_list[ind])
        return self.list_without_friends

    def groups_with_friend(self):
        if len(self.list_with_friends) > 0:
            print(f'\nГруппы, в которых обнаружены общие друзья и их кол-во не больше {self.n}:')
            for count, iter in enumerate(self.list_with_friends):
                print('{}. Группа - {}'.format(count + 1, iter['name']))
        else:
            print(f'Групп, где кол-во не более {self.n} не обнаружено')


def write_to_json(group_list):
    with open('groups.json', mode='w', encoding='utf-8') as file:
        json.dump(group_list, file, ensure_ascii=False, indent=4)
    print()
    print()
    print('Список групп без друзей записан в файл groups.json')


def main():
    user_id = input('Введите id пользователя: ')
    user = User(user_id)
    groups_list = user.take_groups()
    write_to_json(user.groups_without_friends(groups_list))
    user.groups_with_friend()


if __name__ == '__main__':
    main()