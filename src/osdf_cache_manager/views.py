from flask import Blueprint, request, redirect, Response, Flask, make_response
import htcondor

from get_ads import get_cache_ads_from_namespace
from geosort import sort_proxies

views = Blueprint(__name__, "views")


from app import namespace_ads, cache_ads, namespaces
@views.route("<path:path>", methods=["GET","HEAD","PROPFIND", "PUT"])
def redirect_to_cache(path):
    # Get the client IP
    ip_addr = request.headers.get('X-Real-Ip')

    # Parse the path and requested file
    path = "/"+path
    namespace = ""
    for _namespace in namespaces:
        if _namespace in path:
            namespace = _namespace
            break
        
    if namespace != "":
        obj = path[len(namespace):]
        # Get caches
        operation = request.method
        cache_list, authenticated = get_cache_ads_from_namespace(namespace_ads, cache_ads, namespace, operation)
        
        # Order caches
        sorted_caches, rc = sort_proxies(ip_addr, cache_list)
        if rc == None:
            cache_list = sorted_caches
        
        # Use ordered caches to formulate redirect with Metalink/HTTP response headers
        if authenticated:
            redirect_url = "http://{}{}{}".format(cache_list[0]["AuthContactURL"], namespace, obj)
        else:
            redirect_url = "http://{}{}{}".format(cache_list[0]["ContactURL"], namespace, obj)
        response = make_response(redirect(redirect_url), 307)

        # Make Link header persuant to Metalink/HTTP RFC to provide ordered list of other caches
        link_header = ""
        priority_counter = 0
        for cache in cache_list:
            priority_counter +=1
            if priority_counter == len(cache_list):
                link_header += "<{}>; rel=\"duplicate\"; pri={} ".format(cache["ContactURL"], priority_counter)
            else:
                link_header += "<{}>; rel=\"duplicate\"; pri={}, ".format(cache["ContactURL"], priority_counter)
        response.headers['Link'] = link_header
        return response

    else:
        # Indicate error
        return 'Bad namespace, or failure to advertise to collector!', 404
