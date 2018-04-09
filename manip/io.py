import os.path
import json
import io


try:
    to_unicode = unicode
except NameError:
    to_unicode = str

def save_json(data, file_name):
    # Write JSON file
    print("Saving data at \"",file_name,"\"...")
    with io.open(file_name, 'w', encoding='utf8') as outfile:
        str_ = json.dumps(data,
                          indent=4,
                          sort_keys=True,
                          separators=(',', ': '),
                          ensure_ascii=False)
        outfile.write(to_unicode(str_))

def load_json(path):
    # Add .json to the end of file if needed
    if path.find(".json") < 0:
        path = path + ".json"

    # Read JSON file
    with open(path) as data_file:
        data_loaded = json.load(data_file)

    return data_loaded


def log(logging, logger_obj, file, m):
    hdlr = logging.FileHandler(file, mode=m)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    hdlr.setFormatter(formatter)
    logger_obj.addHandler(hdlr)


def close_logs(logger):
    x = list(logger.handlers)
    for i in x:
        logger.removeHandler(i)
        i.flush()
        i.close()