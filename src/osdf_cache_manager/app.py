import htcondor
import os

from flask import Flask
from flask_apscheduler import APScheduler
from views import views
from get_ads import get_cache_ads_from_namespace
from topology_parser import *
from classads import get_namespace_ads, get_cache_ads, get_namespaces
from advertise import advertise_to_coll
import requests

#############################
# Flask app & scheduler setup
#############################

app = Flask(__name__)
app.register_blueprint(views, url_prefix="/")

scheduler = APScheduler()
scheduler.init_app(app)

#############################
# Initializations
#############################

# Create classads and advertise
collector = htcondor.Collector()
topology_data_src = "https://topology.opensciencegrid.org/osdf/namespaces"
advertise_to_coll(topology_data_src, collector)

# Store the ads in memory
namespace_ads = get_namespace_ads(collector)
cache_ads = get_cache_ads(collector)
namespaces = get_namespaces(namespace_ads)

#############################
# Schedule Jobs
#############################
@scheduler.task('cron', id='advertise_topo_classads', minute='*/10')
def advertise_topo_classads():    
    collector = htcondor.Collector()
    advertise_to_coll(topology_data_src, collector)
    
@scheduler.task('cron', id='generate_classads_list', minute='*/10')
def generate_classads_list():
    collector = htcondor.Collector()
    global namespace_ads
    namespace_ads = get_namespace_ads(collector)
    global cache_ads
    cache_ads = get_cache_ads(collector)
    
# Update local maxmind db every Tue and Thurs at 23:00. Upstream is updated every Tue/Thurs earlier in the day
@scheduler.task('cron', id='get_maxmind_db', day_of_week='tue,thu', hour='23')
def update_local_maxminddb():
    if 'MAXMIND_LICENSE_KEY' in os.environ:
        license_key = os.environ['MAXMIND_LICENSE_KEY']
    elif 'MAXMIND_LICENSE_KEY_FILE' in os.environ:
        with open(os.environ['MAXMIND_LICENSE_KEY_FILE']) as fp:
            license_key = fp.read()

    maxminddb_URL = "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key={}&suffix=tar.gz".format(license_key)
    with open ("/app/GeoLite2-City.mmdb", 'wb') as f:
        f.write(requests.get(maxminddb_URL).content)

#############################
# Start the scheduler and run
# the app
#############################
scheduler.start()
if __name__ == '__main__':
    app.run(host="localhost", port=8000)

