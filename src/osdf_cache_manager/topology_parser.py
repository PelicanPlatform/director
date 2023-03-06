import json
import requests
import tldextract
import htcondor
import classad

def get_topo_data(topo_JSON_src):
    topology_data = json.loads(requests.get(topo_JSON_src).text)
    return topology_data

def create_cache_class_ads_list(topo_data):
    cache_class_ads_list = [cache_class_ad_from_topo(cache) for cache in topo_data["caches"]]
    #flatten (go from [[[classad]],[[classad]]] --> [[classad],[classad]])
    #cache_class_ads_list = [classad for sublist in cache_class_ads_list for classad in sublist]
    return cache_class_ads_list

def create_namespace_class_ads_list(topo_data):
    namespace_class_ads_list = [namespace_class_ad_from_topo(namespace, cache) for namespace in topo_data["namespaces"] for cache in namespace["caches"]]
    #namespace_class_ads_list = [classad for sublist in namespace_class_ads_list for classad in sublist]
    return namespace_class_ads_list

def cache_class_ad_from_topo(cache):
    class_ad_dict = {"MyType":"OSDFServer", "Name":cache["resource"], "AuthContactURL":cache["auth_endpoint"], "ContactURL":cache["endpoint"]}
    ad_from_dict = classad.ClassAd(class_ad_dict)   
    return ad_from_dict

def namespace_class_ad_from_topo(namespace, cache):
    class_ad_dict = {"MyType":"OSDFNamespace", "ServerName":cache["resource"], "Path":namespace["path"], "Authentication":namespace["readhttps"],"Operations":None}
    
    operations_str = "GET,HEAD,PROPFIND"
    if namespace["writebackhost"] != None:
        writebackhost_domain = tldextract.extract(namespace["writebackhost"]).domain
        cache_domain = tldextract.extract(cache["endpoint"]).domain
        if cache_domain == writebackhost_domain:
            operations_str += ",PUT"

    class_ad_dict["Operations"] = operations_str
    name = namespace["path"] + ":" + cache["resource"]
    class_ad_dict["Name"] = name
    ad_from_dict = classad.ClassAd(class_ad_dict)
    return ad_from_dict
