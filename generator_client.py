import requests
import pathlib
import os
import json
import jsonpickle

GENERATOR_CLIENT_LOG = 'Client Log : '


def log(value):
    print('{} {}'.format(GENERATOR_CLIENT_LOG, value))


def obj_dict(obj):
    return obj.to_dict()


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


class TargetModel(object):

    def __init__(self):
        self.id = 0
        self.model_str = ''
        self.directory = ''
        self.result = None
        self.app_dir = ''
        self.template_dir = ''

    def get_app_name(self) -> str:
        return self.result['name'].lower()

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

    def to_dict(self):
        return {
            'model_str': self.model_str,
            'directory': self.directory,
            'result' : self.result,
            'app_dir': self.app_dir,
            'template_dir' : self.template_dir
        }


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
        id = 0
        list_target_models = list()
        root_path = pathlib.Path.cwd() / self.root_path
        if os.path.isdir(root_path):
            for (dirpath, dirnames, filenames) in os.walk(root_path):
                if 'models.py' in filenames:
                    log('current directory {}'.format(dirpath))
                    model_str = read_file('models.py', dirpath)
                    if 'IGNORE-GENERATE' not in model_str:
                        target_model = TargetModel()
                        target_model.id = id
                        target_model.model_str = model_str
                        target_model.directory = dirpath
                        target_model.set_app_dir(dirpath)
                        list_target_models.append(target_model)
                        id += 1
            return list_target_models
        else:
            log('Exception : directory {} not found'.format(self.root_path))

    def write_target_model(self, target_model: TargetModel):

        for file_item in target_model.result['result_files']:
            write_string(target_model.directory, '{}.py'.format(file_item['name']), file_item['value'])

        target_model.make_template_dir()

        for file_item in target_model.result['template_files']:
            write_string(target_model.get_full_template_dir(),
                         '{}_{}.html'.format(target_model.result['name'].lower(), file_item['name']), file_item['value'])

    def write_model(self):
        for target_model in self.target_models:
            log(target_model.directory)
            self.write_target_model(target_model)

    def generate_model(self):
        self.generate_model_v2()

    def generate_model_v2(self):
        self.target_models = self.read_model()
        list_model_str = [{
            'id' : tm.id,
            'model_str' : tm.model_str
        } for tm in self.target_models]
        response = requests.post(self.url,
                                 data= {
                                     'username': self.username,
                                     'password': self.password,
                                     'models': json.dumps(list_model_str)
                                 })
        for data_model in jsonpickle.loads(response.text):
            for target_model in self.target_models:
                if target_model.id == data_model['id']:
                    target_model.result = data_model['model_code']
        self.write_model()


    def generate_model_v1(self):
        self.target_models = self.read_model()
        for target_model in self.target_models:
            response = requests.post(self.url, data={'username': self.username, 'password': self.password,
                                                     'models': target_model.model_str})
            log(response.text)
            target_model.result = json.loads(response.text)
        self.write_model()


def test():
    generator_client: GeneratorClient = GeneratorClient()
    generator_client.initial_configuration()
    # generator_client.read_model()
    generator_client.generate_model()


if __name__ == '__main__':
    test()
