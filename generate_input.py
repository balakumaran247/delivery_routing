import csv, json, os

class generate_json:
    '''
    Converts the input csv files to json files
    origins.csv and destinations.csv from data directory
    '''

    def convert(self, csvFilePath, jsonFilePath):
        data = {}
        with open(csvFilePath, encoding='utf-8') as csvf:
            csvReader = csv.DictReader(csvf)
            for rows in csvReader:
                key = rows['\ufeffuno']
                data[key] = rows
        with open(jsonFilePath, 'w', encoding='utf-8') as jsonf:
            jsonf.write(json.dumps(data, indent=4))

def main():
    origins_csv = os.path.join('.', 'data', 'origins.csv')
    destinations_csv = os.path.join('.', 'data', 'destinations.csv')
    origins_json = os.path.join('.', 'data', 'origins.json')
    destinations_json = os.path.join('.', 'data', 'destinations.json')
    conv = generate_json()
    conv.convert(origins_csv, origins_json)
    conv.convert(destinations_csv, destinations_json)
    print('\ncorresponding json files are generated\n')

if __name__ == '__main__':
    main()