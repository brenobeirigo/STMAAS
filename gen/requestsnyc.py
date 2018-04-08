source = 'E:/yellow_tripdata_2015-02.csv'

"""
### ALL HEADERS FROM NYC ##############################
    headers_requests = ['VendorID',
                    'tpep_pickup_datetime',
                    'tpep_dropoff_datetime',
                    'passenger_count',
                    'trip_distance',
                    'pickup_longitude',
                    'pickup_latitude',
                    'RatecodeID',
                    'store_and_fwd_flag',
                    'dropoff_longitude',
                    'dropoff_latitude',
                    'payment_type',
                    'fare_amount',
                    'extra',
                    'mta_tax',
                    'tip_amount',
                    'tolls_amount',
                    'improvement_surcharge',
                    'total_amount']
#######################################################
"""

headers_requests = ['tpep_pickup_datetime',
                    'pickup_longitude',
                    'pickup_latitude',
                    'dropoff_longitude',
                    'dropoff_latitude',
                    'passenger_count',
                    'trip_distance']

headers_vehicles = ['pickup_longitude',
                    'pickup_latitude']

def getRowNYC(row):
    # Dictionary of data
    info = {}

    index = 0
    info['VendorID'] = row[index]
    index += 1

    info['tpep_pickup_datetime'] = datetime.strptime(
        row[index], '%Y-%m-%d %H:%M:%S')

    index += 1
    info['tpep_dropoff_datetime'] = datetime.strptime(
        row[index], '%Y-%m-%d %H:%M:%S')

    index += 1
    info['passenger_count'] = int(row[index])

    index += 1
    info['trip_distance'] = float(row[index])

    index += 1
    info['pickup_longitude'] = row[index]

    index += 1
    info['pickup_latitude'] = row[index]

    index += 1
    info['ratecode_id'] = row[index]

    index += 1
    info['store_and_fwd_flag'] = row[index]

    index += 1
    info['dropoff_longitude'] = row[index]

    index += 1
    info['dropoff_latitude'] = row[index]

    index += 1
    info['payment_type'] = row[index]

    index += 1
    info['fare_amount'] = row[index]

    index += 1
    info['extra'] = row[index]

    index += 1
    info['mta_tax'] = row[index]

    index += 1
    info['tip_amount'] = float(row[index])

    index += 1
    info['tolls_amount'] = row[index]

    index += 1
    info['improvement_surcharge'] = row[index]

    index += 1
    info['total_amount'] = row[index]

    return info

def isValidRow(info, min_distance, max_distance):
    if float(info['pickup_longitude']) == 0 \
            or float(info['pickup_latitude']) == 0 \
            or float(info['dropoff_longitude']) == 0 \
            or float(info['dropoff_latitude']) == 0 \
            or info['trip_distance'] <= 0 \
            or info['trip_distance'] < min_distance \
            or info['trip_distance'] > max_distance:
        return False
    else:
        return True


def extract_data_nyc(origin_file_path,
                        window,
                        min_distance,
                        max_distance,
                        max_amount):

    list_of_requests = list()

    # Data dictionary
    # http://www.nyc.gov/html/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf

    try:
        # Try opening csv file
        with open(origin_file_path) as f:
            reader = csv.reader(f)

            # Get header in first line
            header = next(reader)

            dict_time_windows = {}

            from_datetime = datetime.strptime(
                window[0], '%Y-%m-%d %H:%M:%S')
            to_datetime = datetime.strptime(window[1], '%Y-%m-%d %H:%M:%S')

            # Create viable paths for files
            dateA = from_datetime.strftime('%Y_%m_%d_%Hh%Mm%Ss')
            dateB = to_datetime.strftime('%Y_%m_%d_%Hh%Mm%Ss')

            amount = 0

            for row in reader:

                # Separate row in dictionary
                info = GenTestCase.getRowNYC(row)

                # If data in row is valid (not zero, correct distances)
                if not GenTestCase.isValidRow(info, min_distance, max_distance):
                    continue

                # If amount of lines saved for window surpasses
                # allowed amount, window is completely processed
                if amount >= max_amount:
                    break

                # If demand line is inside the time window
                if info['tpep_pickup_datetime'] >= from_datetime \
                        and info['tpep_pickup_datetime'] <= to_datetime:

                    # Increment amount of lines in window
                    amount += 1

                    req = {'pickup_longitude': info['pickup_longitude'],
                            'pickup_latitude': info['pickup_latitude'],
                            'dropoff_longitude': info['dropoff_longitude'],
                            'dropoff_latitude': info['dropoff_latitude'],
                            'trip_distance': info['trip_distance']}

                    list_of_requests.append(req)

            return list_of_requests

    except IOError as e:
        # Does not exist OR no read permissions
        print("Unable to open file + " + str(e))
        return {}

    