import argparse
from csv import reader
import json
#from pprint import pprint # useful for debugging
import sys

# Parse command line params
# usage = """Usage: verticalAdjacencyTranslator.py -f "roomsAdjacency.txt" [-o "roomsAdjacency.json" [-r]]
# Options:
#   -f  Name of the (main) input TXT file with information about adjacency of individual rooms.
#   -o  Name of the output file which will be created. If none is provided, the input file name will be used.
#   -r  Rewrite the output file instead of updating it
# """
parser = argparse.ArgumentParser(description = 'Creates adjacency file feasible for the Heat Transfer Simulation')
parser.add_argument('-f', "--filename", action = "store", dest = 'adjacencyFileName', required = True, help = 'Name of the (main) input CSV file with information about adjacency of individual rooms.')
parser.add_argument('-o', "--outputfilename", action = "store", dest = 'outputFileName', help = 'Name of the output file which will be created. If none is provided, the input file name will be used.')
parser.add_argument('-r', "--rewrite", action = 'store_true', default = False, dest = 'rw', help = 'Rewrite the output file instead of updating it')
args = vars(parser.parse_args())
adjacencyFileName = args['adjacencyFileName'] if args['adjacencyFileName'] else "CeilingsAdjacency.csv"
outputFileName = args['outputFileName'] if args['outputFileName'] else ""
rw = args['rw'] if args['rw'] else False

# Search for a room by its ID. Returns room object or None
def getRoomById(id):
    for room in data['rooms']:
        if room['id'] == id:
            return room
    return None

# If there is already a file with adjacencies and the flag is not set to rewrite it, read it
if len(outputFileName) > 0 and not rw:
    with open(outputFileName, 'r', encoding="utf-8") as fh:
        data = json.load(fh)
else:
    data = {}

#Adding individual rooms/zones
if not 'rooms' in data:
    data['rooms'] = []

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
with open(adjacencyFileName, 'r', encoding="utf-8") as fh:
    csvReader = reader(fh)
    next(csvReader) #skip heading
    for row in csvReader:
        id1 = row[0]
        id2 = row[1]
        if id1 == id2: #room which spans through multiple levels
            continue
        wallId += 1
        data['walls'].append({
            'id': wallId,
            'area': float(row[2]), # area in metres
            'leftID': id1, #left and right are really arbitrary here
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
