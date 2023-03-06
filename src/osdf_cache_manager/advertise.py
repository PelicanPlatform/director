from topology_parser import create_cache_class_ads_list, create_namespace_class_ads_list, get_topo_data
import os
import htcondor

def advertise_to_coll(topo_data_src, collector):
    topo_JSON = get_topo_data(topo_data_src)
    cache_class_ads_list = create_cache_class_ads_list(topo_JSON)
    namespace_class_ads_list = create_namespace_class_ads_list(topo_JSON)

    # Handle HTCondor security and advertise ads to collector
    with htcondor.SecMan() as sm:
        if 'BEARER_TOKEN' in os.environ:
            sm.setToken(htcondor.Token(os.environ['BEARER_TOKEN']))
        elif 'BEARER_TOKEN_FILE' in os.environ:
            with open(os.environ['BEARER_TOKEN_FILE']) as fp:
                sm.setToken(htcondor.Token(fp.read().strip()))
        
        if cache_class_ads_list:
            try:
                collector.advertise(cache_class_ads_list)
            except Exception as exc:
                print("Exception occurred while trying to advertise cache class ads to the collector: {}".format(exc))
        if namespace_class_ads_list:
            try:
                collector.advertise(namespace_class_ads_list)
            except Exception as exc:
                print("Exception occurred while trying to advertise namespace class ads to the collector: {}".format(exc))

