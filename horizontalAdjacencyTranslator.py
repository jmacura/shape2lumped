import argparse
from csv import reader
import json
#from pprint import pprint # useful when debugging
import sys

# Parse command line params
# usage = """Usage: horizontalAdjacencyTranslator.py  -p "roomsAreas.csv"  [-m "mappings.txt"] -f "roomsAdjacency.txt" [-o "roomsAdjacency.json" [-r]]
# Options:
#   -p  Name of the CSV file with properties about each room.
#   -m  Name of the TXT file with mappings between IDs used in the adjacency file and th IDs which should be used in the output. If none is provided, IDs from the input file will be used.
#   -f  Name of the (main) input TXT file with information about adjacency of individual rooms.
#   -o  Name of the output file which will be created. If none is provided, the input file name will be used.
#   -r  Rewrite the output file instead of updating it
# """
parser = argparse.ArgumentParser(description = 'Creates adjacency file feasible for the Heat Transfer Simulation')
parser.add_argument('-p', "--properties", action = "store", dest = 'propertyFileName', required = True, help = 'Name of the CSV file with properties (area, height) about each room.')
parser.add_argument('-m', "--mappings", action = "store", dest = 'mappingFileName', required = True, help = 'Name of the TXT file with mappings between IDs used in the adjacency file and th IDs which should be used in the output.')
parser.add_argument('-f', "--filename", action = "store", dest = 'adjacencyFileName', required = True, help = 'Name of the (main) input TXT file with information about adjacency of individual rooms.')
parser.add_argument('-o', "--outputfilename", action = "store", dest = 'outputFileName', help = 'Name of the output file which will be created. If none is provided, the input file name will be used.')
parser.add_argument('-r', "--rewrite", action = 'store_true', default = False, dest = 'rw', help = 'Rewrite the output file instead of updating it')
args = vars(parser.parse_args())
mappingFileName = args['mappingFileName'] if args['mappingFileName'] else "ID_FID_pxID.txt"
propertyFileName = args['propertyFileName'] if args['propertyFileName'] else "RoomsAreas.csv"
adjacencyFileName = args['adjacencyFileName'] if args['adjacencyFileName'] else "RoomsAdjacency.txt"
outputFileName = args['outputFileName'] if args['outputFileName'] else ""
rw = args['rw'] if args['rw'] else False

# Search for a room by its ID. Returns room object or None
def getRoomById(id):
    for room in data['rooms']:
        if room['id'] == id:
            return room
    return None

# FAV-specific function to rename numerical IDs back to their normal string form
def renameToAlfa(value):
    UX = value[0]
    val = None
    if int(UX) == 1:
        val = 'UC'
    elif int(UX) == 2:
        val = 'UN'
    elif int(UX) == 3:
        val = 'US'
    elif int(UX) == 4:
        val = 'UNW'
    else:
        print("Unknown type of room: {}!!".format(UX))
    if len(value) == 6:
        return "".join([val, value[1:4], chr(int(value[4:]))])
    elif len(value) > 6:
        return "".join([val, value[1:4], chr(int(value[4:6])), value[6:]])
    else:
        return "".join([val, value[1:]])

# Recode IDs by using a hash-table
idTable = {}
idTable['-1'] = '-1' # outdoor/ambient
with open(mappingFileName, "r", encoding="utf-8") as fh:
    csvReader = reader(fh, delimiter=";")
    next(csvReader) #skip heading
    for row in csvReader:
        idTable[row[0]] = renameToAlfa(row[1])

# If there is already a file with adjacencies and the flag is not set to rewrite it, read it
if len(outputFileName) > 0 and not rw:
    with open(outputFileName, 'r', encoding="utf-8") as fh:
        data = json.load(fh)
else:
    data = {}

#Adding individual rooms/zones
if not 'rooms' in data:
    data['rooms'] = []
with open(propertyFileName, 'r', encoding="utf-8") as fh:
    csvReader = reader(fh)
    next(csvReader)
    for row in csvReader:
        if not getRoomById(row[0]):
            data['rooms'].append({
                'id': row[0],
                'volume': round(float(row[1]) * float(row[2]), 2),
                'height': round(float(row[2]), 2),
                'walls': []
            })

#Adding outdoor/ambient zone
if not 'ambient' in data:
    data['ambient'] = {
        'constant': True,
        'walls': []
    }

if not 'walls' in data:
    data['walls'] = []

#Set auto-counter of walls
wallId = max(wall['id'] for wall in data['walls']) if len(data['walls']) > 0 else 0

#Adding walls and connecting zones with walls
#Currently, the inforamtion is being held duplicitly in general "walls" array and in "walls" array by each room
with open(adjacencyFileName, 'r', encoding="utf-8") as fh:
    csvReader = reader(fh, delimiter=";")
    next(csvReader) #skip heading
    for row in csvReader:
        id1 = idTable[row[1]]
        id2 = idTable[row[2]]
        roomHeight = getRoomById(id1)['height'] if id1 != "-1" else getRoomById(id2)['height']
        wallId += 1
        data['walls'].append({
            'id': wallId,
            'area': float(row[3].replace(',', "."))*float(roomHeight), #'length': float(row[3].replace(',', "."))
            'leftID': id1,
            'rightID': id2
        })
        if getRoomById(id1):
            rm1 = getRoomById(id1)
            rm1['walls'].append(wallId)
        elif id1 == "-1": # beacause of "-1" ambient room
            data['ambient']['walls'].append(wallId)
        else:
            print("Unknown room ID {} cannot be linked with {}".format(id1, id2))
        if getRoomById(id2):
            rm2 = getRoomById(id2)
            rm2['walls'].append(wallId)
        elif id2 == "-1": # beacause of "-1" ambient room
            data['ambient']['walls'].append(wallId)
        else:
            print("Unknown room ID {} cannot be linked with {}".format(id2, id1))

if len(outputFileName) == 0:
    outputFileName = ".".join( (adjacencyFileName.split('.')[0], "json") )
with open(outputFileName, 'w', encoding="utf-8") as out:
    json.dump(data, out)
print("File \"{}\" succesfully created".format(outputFileName))
