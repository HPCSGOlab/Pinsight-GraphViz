import bt2

for msg in bt2.TraceCollectionMessageIterator('../testtraces'):
    if type(msg) is bt2._EventMessageConst:
        event = msg.event

        if event.name == 'cupti_pinsight_lttng_ust:cudaMemcpyAsync_begin':
            vpid = event['src']
            print(msg.event.name)
            print(vpid)
            
    