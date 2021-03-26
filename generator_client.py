import requests
import pathlib
import os
import json

GENERATOR_CLIENT_LOG = 'Client Log : '


# FILE_LIST = ['admin', 'apps', 'forms', 'tables', 'urls', 'views', ]
#
# HTML_FILE_LIST = ['confirm_delete', 'detail', 'form', 'list']

def log(value):
    print('{} {}'.format(GENERATOR_CLIENT_LOG, value))


def read_file(file_name, parent_path: str = None):
    with open(os.path.join(parent_path if parent_path else os.path.dirname(os.path.abspath(__file__)), file_name),
              "r") as f:
        template_string = ''
        for line in f.readlines():
            template_string += line
        f.close()
    return template_string


def write_string(path, file_name, value):
    print(os.path.join(path, file_name))
    py_file = open(os.path.join(path, file_name), 'wt')
    py_file.write(value)
    py_file.close()


class TargetModel:

    def __init__(self):
        self.model_str = ''
        self.directory = ''
        self.result = None
        self.app_dir = ''
        self.template_dir = ''

    def set_app_dir(self, directory):
        split_result = directory.split('/')
        self.app_dir = split_result[-1]
        self.template_dir = pathlib.Path(directory) / 'templates'

    def make_template_dir(self):
        template_dir = pathlib.Path(self.template_dir)
        if not template_dir.exists():
            template_dir.mkdir()

        template_app_dir = template_dir / self.app_dir
        if not template_app_dir.exists():
            template_app_dir.mkdir()

    def get_full_template_dir(self):
        return pathlib.Path(self.template_dir) / self.app_dir


class GeneratorClient:

    def __init__(self):
        self.username = ''
        self.password = ''
        self.url = ''
        self.root_path = ''
        self.target_models = list()

    def initial_configuration(self):
        log('initial configuration client')
        config_dict = json.loads(self.read_configuration())
        self.username = config_dict['username']
        self.password = config_dict['password']
        self.url = config_dict['url']
        self.root_path = config_dict['root_path']

    def read_configuration(self) -> str:
        log('read configuration')
        root_path = read_file('configuration.json')
        log(root_path)
        return root_path

    def read_model(self):
        list_target_models = list()
        root_path = pathlib.Path.cwd() / self.root_path
        if os.path.isdir(root_path):
            for (dirpath, dirnames, filenames) in os.walk(root_path):
                if 'models.py' in filenames:
                    log('current directory {}'.format(dirpath))
                    model_str = read_file('models.py', dirpath)
                    if 'IGNORE-GENERATE' not in model_str:
                        target_model = TargetModel()
                        target_model.model_str = model_str
                        target_model.directory = dirpath
                        target_model.set_app_dir(dirpath)
                        list_target_models.append(target_model)
            return list_target_models
        else:
            log('Exception : directory {} not found'.format(self.root_path))

    def write_target_model(self, target_model: TargetModel):
        for file_item in target_model.result['result_files']:
            write_string(target_model.directory, '{}.py'.format(file_item['name']), file_item['value'])

        target_model.make_template_dir()

        for file_item in target_model.result['template_files']:
            write_string(target_model.get_full_template_dir(),
                         '{}_{}.html'.format(target_model.app_dir, file_item['name']), file_item['value'])

    def write_model(self):
        for target_model in self.target_models:
            log(target_model.directory)
            self.write_target_model(target_model)

    def generate_model(self):
        self.target_models = self.read_model()
        for target_model in self.target_models:
            response = requests.post(self.url, data={'username': self.username, 'password': self.password,
                                                     'models': target_model.model_str})
            log(response.text)
            target_model.result = json.loads(response.text)
        self.write_model()


def test():
    # target_model = TargetModel()
    # target_model.set_app_dir("/Users/fahmi/Documents/Pycharm/generator_client/project/todo")
    # print(target_model.app_dir)
    # print(target_model.template_dir)

    generator_client: GeneratorClient = GeneratorClient()
    generator_client.initial_configuration()
    # generator_client.read_model()
    generator_client.generate_model()


if __name__ == '__main__':
    test()
