import htcondor
import os
import tarfile
from flask_cors import CORS

from flask import Flask
from flask_apscheduler import APScheduler
from get_ads import get_cache_ads_from_namespace
from topology_parser import *
from classads import get_namespace_ads, get_cache_ads, get_namespaces
from advertise import advertise_to_coll
from update_db import update_db
import requests

#############################
# Globals
#############################
# Set up collector + debugging
htcondor.param['TOOL_DEBUG'] = 'D_SECURITY:2'
htcondor.param['TOOL_LOG'] = '/home/debug-log'
htcondor.enable_debug()
htcondor.enable_log()
collector = htcondor.Collector() # The collector to be used should exist as an env var "_condor_COLLECTOR_HOST"

# Data source used to create classads
topology_data_src = "https://topology.opensciencegrid.org/osdf/namespaces"


#############################
# Initializations
#############################
# Get the geosort database
update_db() # Won't update if the database is already there. Use True as an argument to override

# Create classads and advertise
print("Performing initial advertisements to collector...")
advertise_to_coll(topology_data_src, collector)
print("Done")

# Store the ads in memory
namespace_ads = get_namespace_ads(collector)
cache_ads = get_cache_ads(collector)
namespaces = get_namespaces(namespace_ads)


#############################
# Set up/start the scheduler and run
# the app
#############################

if __name__ == '__main__':
    from waitress import serve

    #############################
    # Flask app
    #############################
    def create_app():
        app = Flask(__name__)
        with app.app_context():
            from views import views
            app.register_blueprint(views, url_prefix="/")
        return app

    app = create_app()

    #############################
    # Enable CORS on all endpoints
    #############################
    CORS(app)

    #############################
    # Set up the scheduler
    #############################
    scheduler = APScheduler()
    scheduler.max_instances = 1
    scheduler.init_app(app)

    #############################
    # Schedule Jobs
    #############################
    @scheduler.task('cron', id='advertise_topo_classads', minute='*/10')
    def advertise_topo_classads():
        print("advertising to collector...") 
        advertise_to_coll(topology_data_src, collector)
        print("advertising done")
        
    @scheduler.task('cron', id='generate_classads_list', minute='*/10')
    def generate_classads_list():
        global namespace_ads
        print("Performing scheduled namespace ad generation...")
        namespace_ads = get_namespace_ads(collector)
        print("Done")
        global cache_ads
        print("Performing scheduled cache ad generation...")
        cache_ads = get_cache_ads(collector)
        print("Done")
        
    # Update local maxmind db every Tue and Thurs at 23:00. Upstream is updated every Tue/Thurs earlier in the day
    @scheduler.task('cron', id='get_maxmind_db', day_of_week='tue,thu', hour='23')
    def update_local_maxminddb():
        print("Performing scheduled maxmind db update...")
        update_db(True) # True tells update_db that it should pull the database and update.
        print("Done")

    scheduler.start()

    #############################
    # Dinner is served!
    #############################
    serve(app, host='0.0.0.0', port=8443) # use for prod
    #app.run(host='0.0.0.0', port=8443, debug=True) # For debugging, not a production server
    # Note that when run in debug mode, Flask will create duplicate instances of the app,
    # which will result in scheduled tasks being run twice. This isn't an issue for debugging,
    # but it's something to be aware of.
