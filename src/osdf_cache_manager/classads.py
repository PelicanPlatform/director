import htcondor


def get_all_OSDF_ads(collector):
    all_ads = collector.query(constraint='MyType=="OSDFNamespace" || MyType=="OSDFServer"')
    return all_ads

def get_namespace_ads(collector):
    namespace_ads = collector.query(constraint='MyType=="OSDFNamespace"')
    return namespace_ads

def get_cache_ads(collector):
    cache_ads = collector.query(constraint='MyType=="OSDFServer"')
    return cache_ads
    
def get_namespaces(namespace_ads):
    namespaces = []
    for namespace_ad in namespace_ads:
        if namespace_ad["Path"] not in namespaces:
            namespaces.append(namespace_ad["Path"])
    return namespaces
    
