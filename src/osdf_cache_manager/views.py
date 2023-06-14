from flask import Blueprint, request, redirect, Response, Flask, make_response
import htcondor

from get_ads import get_cache_ads_from_namespace, get_namespace_ad
from geosort import sort_proxies

views = Blueprint(__name__, "views")
from app import namespace_ads, cache_ads, namespaces # Careful, playing with something close to a circular dependency here... app.py also imports views 
@views.route("<path:path>", methods=["GET","HEAD","PROPFIND", "PUT"])
def redirect_to_cache(path):
    # Get the client IP
    ip_addr = request.headers.get('X-Real-Ip')

    # Parse the path and requested file
    path = "/"+path
    namespace = ""
    for _namespace in namespaces:
        #if _namespace in path:
        if path.startswith(_namespace):
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
                if authenticated:
                    link_header += "<{}>; rel=\"duplicate\"; pri={} ".format(cache["AuthContactURL"], priority_counter)
                else:
                    link_header += "<{}>; rel=\"duplicate\"; pri={} ".format(cache["ContactURL"], priority_counter)
            else:
                if authenticated:
                    link_header += "<{}>; rel=\"duplicate\"; pri={}, ".format(cache["AuthContactURL"], priority_counter)
                else:
                    link_header += "<{}>; rel=\"duplicate\"; pri={}, ".format(cache["ContactURL"], priority_counter)
        response.headers['Link'] = link_header

        # Get the token for auth
        auth_token = None
        if request.headers.get("Authorization"):
            auth_token = request.headers.get("Authorization")

        # Create the X-OSDF-Authorization header
        namespace_ad = get_namespace_ad(namespace, namespace_ads)
        X_OSDF_Authorization_hdr = ""
        if "Issuer" in namespace_ad: # If there is an issuer, then other fields will also be present
            X_OSDF_Authorization_hdr = "issuer={}".format(namespace_ad["Issuer"])
            if auth_token:
                X_OSDF_Authorization_hdr += ", authorization={}".format(auth_token)
        response.headers["X-OSDF-Authorization"] = X_OSDF_Authorization_hdr

        # Create the X-OSDF-Token-Generation header
        X_OSDF_Token_Generation_hdr = ""
        if "Issuer" in namespace_ad: # If there is an issuer, then other fields will also be present  
            X_OSDF_Token_Generation_hdr = "issuer={}, max-scope-depth={}, strategy={}, base-path={}".format(namespace_ad["Issuer"], namespace_ad["MaxScopeDepth"], namespace_ad["Strategy"], namespace_ad["BasePath"])
            if "VaultServer" in namespace_ad:
                X_OSDF_Token_Generation_hdr += ", vault-server={}".format(namespace_ad["VaultServer"])
            # if "BasePath" in namespace_ad:
            #     X_OSDF_Authorization_hdr += ", base-path={}".format(namespace_ad["BasePath"])
        response.headers["X-OSDF-Token-Generation"] = X_OSDF_Token_Generation_hdr

        response.headers["X-OSDF-Namespace"] = "namespace={}, readhttps={}, use-token-on-read={}".format(namespace, namespace_ad["ReadHTTPS"], namespace_ad["UseTokenOnRead"])

        # Headers are all set up, send them back
        return response
    else:
        # Indicate error
        return 'Bad namespace, or failure to advertise to collector!', 404



