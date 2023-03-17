import os
import requests
import tarfile
import shutil
from os.path import exists




def update_db(update=False):


    db_exists = exists("/app/maxminddb/GeoLite2-City.mmdb")
    if (update or not db_exists):
        # Get MaxMind License Key from env var or file
        if 'MAXMIND_LICENSE_KEY' in os.environ:
                license_key = os.environ['MAXMIND_LICENSE_KEY']
        elif 'MAXMIND_LICENSE_KEY_FILE' in os.environ:
            with open(os.environ['MAXMIND_LICENSE_KEY_FILE']) as fp:
                license_key = fp.read()

        # Create MaxMindDB Update URL
        maxminddb_URL = "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key={}&suffix=tar.gz".format(license_key)

        print("Download/writing db tarfile")
        with open ("/app/maxminddb/GeoLite2-City.tar.gz", 'wb') as f:
            f.write(requests.get(maxminddb_URL).content)

        print("Extracting tarfile")
        with tarfile.open("/app/maxminddb/GeoLite2-City.tar.gz", 'r:gz') as tar:
            member_names = tar.getnames()
            common_prefix = os.path.commonprefix(member_names)
            tar.extractall(path="/app/maxminddb/")

        db_file_name = "GeoLite2-City.mmdb"
        print("Moving db.mmdb")
        shutil.move(os.path.join("/app/maxminddb", common_prefix, db_file_name), "/app/maxminddb/GeoLite2-City.mmdb")
        print("Deleting tar directory")
        shutil.rmtree(os.path.join("/app/maxminddb", common_prefix)) 
        print("Deleting tarfile")
        os.remove("/app/maxminddb/GeoLite2-City.tar.gz")


