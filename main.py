# This is a sample Python script.
import json
import os
import re
import subprocess

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
android_device = ''
list_data = []
device_info = {}


def download_split_apks():
    for data in list_data:
        result = os.popen('adb -s {0} shell "pm path {1}" '.format(android_device, data['package'])).read()
        results = result.split('\n')
        split_apks = []
        for r in results:
            if len(r) > 0 and not r.__contains__('base.apk') and r.__contains__(
                    "/data/app/"):  # base apk already copied
                path = r.split('package:')[1]
                temp = path.split('/')
                name = temp[len(temp) - 1]
                split_apks.append({'path': path, 'name': name})
                if not os.path.exists('apks-{0}/{1}-{2}'.format(android_device, data['package'], name)):
                    split_result = os.popen(
                        'adb -s {0} pull \"{1}\" \"apks-{0}/{2}-{3}\"'.format(android_device, path, data['package'],
                                                                              name)).read()
                    print(split_result)
        data['split'] = split_apks


def download_apks():
    if not os.path.exists('apks-{0}'.format(android_device)):
        os.mkdir('apks-{0}'.format(android_device))
    for data in list_data:
        if not os.path.exists('apks-{0}/{1}-{2}'.format(android_device, data['package'], data['name'])):
            command = 'adb -s {0} pull \"{1}\" \"apks-{0}/{2}-{3}\"'.format(android_device, data['path'],
                                                                            data['package'],
                                                                            data['name'])
            try:
                result = subprocess.check_output(command, encoding='UTF-8')
                print(result)
            except:
                print('copy apk failed!', data)


def get_all_apks():
    result = subprocess.check_output(
        'adb -s {0} shell "pm list packages -f --show-versioncode" '.format(android_device),
        encoding='UTF-8')
    results = result.split('\n')
    for r in results:
        if len(r) > 0:
            package = r.split('apk=')[1]
            version = package.split(':')[1]
            package = package.split(' ')[0]
            path = r.split('={0}'.format(package))[0].split('package:')[1]
            name = path.split('/')
            name = name[len(name) - 1]
            list_data.append({'package': package, 'path': path, 'name': name, 'version_code': version})


def restore_apks():
    json_data = open(r"list_data_{0}.json".format(android_device), 'r', encoding='UTF-8').read()
    global device_info
    global list_data
    device_info = json.loads(json_data)
    list_data = device_info['data']
    for data in list_data:
        exists_app = os.popen(
            'adb -s {0} shell "pm list packages -f --show-versioncode | grep {1}"'.format(android_device,
                                                                                       data['package'])).read()
        if exists_app.__contains__('apk='):
            package = exists_app.split('apk=')[1]
            version = package.split(':')[1]
            package = package.split(' ')[0]
            print('exist app, package : {0} , version : {1}'.format(package, version))
        else:
            package = data['package']
            version = '0'
            print('not exist app,package : {0}'.format(package))
        if not package.__eq__(data['package']) or int(data['version_code']) > int(version):
            if len(data['split']) > 0:
                apk_paths = '"apks-{0}/{1}-{2}"'.format(android_device, data['package'], data['name'])
                for s in data['split']:
                    apk_paths += ' "apks-{0}/{1}-{2}"'.format(android_device, data['package'], s['name'])
                result = os.popen(
                    'adb -s {0} install-multiple  -r -d --user 0 {1}'.format(android_device, apk_paths)).read()
                print(result)
            else:
                result = os.popen(
                    'adb -s {0} install  -r -d --user 0 apks-{0}/{1}-{2}'.format(android_device, data['package'],
                                                                                 data['name'])).read()
                print(result)


def wait_connect():
    result = os.popen('adb devices').read()
    while not result.__contains__("\tdevice"):
        result = os.popen('adb devices').read()
        print(result)
    results = result.split('\n')
    devices = ''
    index = 1
    for r in results:
        if r.__contains__('\tdevice'):
            devices += '{0}. {1}\n'.format(index, r.split('\t')[0])
            index += 1
    position = input('Please select device:\n{0}'.format(devices))
    global android_device
    android_device = results[int(position)].split('\t')[0]
    result = subprocess.check_output('adb -s {0} shell getprop'.format(android_device), encoding='UTF-8')
    results = result.split('\n')
    for r in results:
        if len(r) > 0:
            match_group = re.match('\\[(.*?)\\]: \\[(.*?)\\]', r)
            if match_group is None:
                print('skip')
            elif len(match_group.group(1)) > 0 and len(match_group.group(2)) > 0:
                device_info[match_group.group(1)] = match_group.group(2)


def save_list_data():
    device_info['data'] = list_data
    with open(r"list_data_{0}.json".format(android_device), "w", encoding="UTF-8") as file:
        # ensure_ascii=False，用于确保写入json的中文不发生乱码
        json.dump(device_info, file, ensure_ascii=False)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print('Welcome use backup android apk!')
    print('Please connect android device! and open usb debug.')
    wait_connect()
    prompt = input('You need to backup apk? Please input Y/N\n')
    if prompt.__eq__('Y'):
        get_all_apks()
        download_apks()
        download_split_apks()
        save_list_data()
    prompt = input('You need to restore apk? Please input Y/N\n')
    if prompt.__eq__('Y'):
        restore_apks()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
