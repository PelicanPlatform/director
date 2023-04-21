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
    authenticated = namespace["readhttps"] or namespace["usetokenonread"]
    class_ad_dict = {"MyType":"OSDFNamespace", "ServerName":cache["resource"], "Path":namespace["path"], "Authentication":authenticated,"Operations":None, "ReadHTTPS":namespace["readhttps"], "UseTokenOnRead":namespace["usetokenonread"], "DirListHost":namespace["dirlisthost"]}
    
    # Set up supported authorizations
    # THIS SECTION NEEDS REVIEW, IS PROBABLY WRONG
    operations_str = "GET,HEAD,PROPFIND"
    if namespace["writebackhost"] is not None:
        writebackhost_domain = tldextract.extract(namespace["writebackhost"]).domain
        cache_domain = tldextract.extract(cache["endpoint"]).domain
        if cache_domain == writebackhost_domain:
            operations_str += ",PUT"

    class_ad_dict["Operations"] = operations_str
    name = namespace["path"] + ":" + cache["resource"]
    class_ad_dict["Name"] = name

    # Determine which credential generation fields to create
    if namespace["credential_generation"] is not None: # A method for providing credentials is present
        class_ad_dict["Strategy"] = namespace["credential_generation"]["strategy"]
        class_ad_dict["Issuer"] = namespace["credential_generation"]["issuer"]
        class_ad_dict["MaxScopeDepth"] = namespace["credential_generation"]["max_scope_depth"]
        if namespace["credential_generation"]["strategy"] == "Vault":
            class_ad_dict["VaultServer"] = namespace["credential_generation"]["vault_server"]

    ad_from_dict = classad.ClassAd(class_ad_dict)
    return ad_from_dict
