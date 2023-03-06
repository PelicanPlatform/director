def get_cache_ads_from_namespace(all_namespace_ads, all_cache_ads, namespace, operation):
    namespace_ads = []
    if "PUT" in operation:
        namespace_ads = [ad for ad in all_namespace_ads if ad["Operations"]=="GET,HEAD,PROPFIND,PUT" and ad["Path"]==namespace]

    else:
        namespace_ads = [ad for ad in all_namespace_ads if ad["Operations"]=="GET,HEAD,PROPFIND" and ad["Path"]==namespace]

    caches = [ad["ServerName"] for ad in namespace_ads]
    cache_ads = []
    for cache in caches:
        for cache_ad in all_cache_ads:
            if cache_ad["Name"] == cache:
                cache_ads.append(cache_ad)

    
    authenticated = namespace_ads[0]["Authentication"]
    return [cache_ads, authenticated]