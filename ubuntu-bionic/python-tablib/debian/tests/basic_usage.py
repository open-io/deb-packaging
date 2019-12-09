'''
Script used to test that tablib is loading properly and able to use the basic
export functions without failing.
'''
import tablib

headers = ('first_name', 'last_name')
data = [('John', 'Adams'), ('George', 'Washington')]
data = tablib.Dataset(*data, headers=headers)
export_json = data.export('json')
if export_json != '[{"first_name": "John", "last_name": "Adams"}, {"first_name": "George", "last_name": "Washington"}]':
    print('The json export returned an unexpected value:\n{}'.format(export_json))
    exit(1)

export_yaml = data.export('yaml')
if export_yaml != '- {first_name: John, last_name: Adams}\n- {first_name: George, last_name: Washington}\n':
    print('The yaml export returned an unexpected value:\n{}'.format(export_yaml))
    exit(2)

export_csv = data.export('csv')
if export_csv != 'first_name,last_name\r\nJohn,Adams\r\nGeorge,Washington\r\n':
    print('The csv export returned an unexpected value:\n{}'.format(export_csv))
    exit(3)
