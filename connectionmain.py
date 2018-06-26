import argparse
from src.main.python.ConnectionUtils.DatabaseConnector import DatabaseConnector
from src.main.python.ConnectionUtils.Table import Table

def getParser():
    desc = 'Tools for database interaction'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('configpath', type=str, help='Path to config.ini file')
    parser.add_argument('table', type=str, default='', help='Target table name')
    parser.add_argument('-p', '--datapath', type=str, default='', help='Filepath to data, if needed')
    parser.add_argument('-b', '--build', action='store_true', help='Build table from filepath')
    parser.add_argument('-s', '--spatial', action='store_true', help='Make table spatial')
    parser.add_argument('-oc', '--longitudecol', type=str, default='Longitude', help='Longitude column name')
    parser.add_argument('-ac', '--latitudecol', type=str, default='Latitude', help='Latitude column name')
    parser.add_argument('-gc', '--geometrycol', type=str, default='geom', help='Geometry column name')
    parser.add_argument('-u', '--update', action='store_true', help='Update existing table from filepath')
    parser.add_argument('-cc', '--countrycol', type=str, default='Country', help='Country column name')
    parser.add_argument('-lc', '--locationcol', type=str, default='Location', help='Location column name')
    parser.add_argument('-cq', '--customquery', action='store_true', help='Run custom query.')
    parser.add_argument('-l', '--limit', type=int, default=0, help='Set limit for number of values returned.')
    parser.add_argument('-gt', '--gettable', action='store_true', help='Print table entries.')
    parser.add_argument('-ccl', '--checkcountryloc', action='store_true', help='Find entires by country and location')
    parser.add_argument('-cll', '--checklatlon', action='store_true', help='Find entries by latitude and longitude')
    parser.add_argument('-ov', '--lngval', type=float, default=0.0, help='Longitude value')
    parser.add_argument('-av', '--latval', type=float, default=0.0, help='Latitude value')
    parser.add_argument('-r', '--radius', type=float, default=300000, help='Search radius')
    parser.add_argument('-cv', '--countryname', type=str, default='', help='Country name')
    parser.add_argument('-lv', '--locname', type=str, default='', help='Location name')

    return parser

if __name__ == '__main__':
    parser = getParser()
    args = parser.parse_args()

    connector = DatabaseConnector()
    connector.getConnectFromConfig(filePath=args.configpath)
    table = Table(args.table, connector)

    if args.build is True:
        table.buildTableFromFile(args.datapath)
    if args.spatial is True:
        table.makeTableSpatial(lngColName=args.longitudecol, latColName=args.latitudecol, geomColName=args.geometrycol)
    if args.update is True:
        table.updateEntries(lngColName=args.longitudecol, latColName=args.latitudecol, countryColName=args.countrycol,
                            locationColName=args.locationcol, filePath=args.datapath)
    if args.customquery is True:
        table.customQuery()
    if args.gettable is True:
        print(*table.getTable(limit=args.limit), sep='\n')
    if args.checklatlon is True:
        print(*table.checkForEntryByLatLon(lat=args.latval, lon=args.lngval, searchRadius=args.radius, geomColName=args.geometrycol)[1], sep='\n')
    if args.checkcountryloc is True:
        print(*table.checkForEntryByCountryLoc(locationName=args.locname, countryName=args.countryname,
                                               locationColName=args.locationcol, countryColName=args.countrycol)[1], sep='\n')

    connector.closeConnection()