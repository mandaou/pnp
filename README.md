# NDN Resolver
Is a tool to map publisher's NDN names to Autonomous System Numbers in NDN Format.

Example:

    /om/edu/squ     -- Resolves to -->      /AS1,/AS2,/AS20


## Dataset:
1. We chose the top 1 million sites from the Majestic database (put reference here).
2. We randomly distributed the producers among the 34 nodes in NDN testbed (we need to change /AS1 to /AFA as per the testbed db)



### Caching the datasets:
* datasets/DSManager is responsible for reading the datasets and creating a cache file
* The cache dict has 10 entries: few_utf, few_named, 1k_utf, 1k_named, 10k_utf, 10k_named, 100k_uft, 100k_named, 1m_utf, 1m_named
* The value for each of these 10 entries is a dict containing the dataset items. **These items are pickled**, i.e. you need to unpickle them before adding them to the algorithm database
* The ephemeral cache file is stored under /tmp/cache.pkl
* This changed loading the datasets into memory from 120 second to less than 4 seconds
* Writing to the cache file is as follows:
  * For NTv2 usage:
    * For each item tuple (k,v) in the majestic dataset:      
    
          ('/com/google/www', ['/AS1', '/AS2', '/AS3'])
    * NDN Encode k:
    
          [bytearray(b'\x08\x03com'), bytearray(b'\x08\x06google'), bytearray(b'\x08\x03www')]
    * NDN Encode each item in v: 
    
          [[bytearray(b'\x08\x03AS1')], [bytearray(b'\x08\x03AS2')], [bytearray(b'\x08\x03AS3')]]
    * Pickle the encoded k:  
      
          b'\x80\x04\x95I\x00\x00\x00\x00\x00\x00\x00]\x94(\x8c\x08builtins\x94\x8c\tbytearray\x94\x93\x94C\x05\x08\x03com\x94\x85\x94R\x94h\x03C\x08\x08\x06google\x94\x85\x94R\x94h\x03C\x05\x08\x03www\x94\x85\x94R\x94e.'
    * Pickly the encoded v list:   
      
          b'\x80\x04\x95O\x00\x00\x00\x00\x00\x00\x00]\x94(]\x94\x8c\x08builtins\x94\x8c\tbytearray\x94\x93\x94C\x05\x08\x03AS1\x94\x85\x94R\x94a]\x94h\x04C\x05\x08\x03AS2\x94\x85\x94R\x94a]\x94h\x04C\x05\x08\x03AS3\x94\x85\x94R\x94ae.'
    * Create a new dictionary and added the pickle_key and the pickled_value   
      
          {b'\x80\x04\x95I\x00\x00\x00\x00\x00\x00\x00]\x94(\x8c\x08builtins\x94\x8c\tbytearray\x94\x93\x94C\x05\x08\x03com\x94\x85\x94R\x94h\x03C\x08\x08\x06google\x94\x85\x94R\x94h\x03C\x05\x08\x03www\x94\x85\x94R\x94e.': b'\x80\x04\x95O\x00\x00\x00\x00\x00\x00\x00]\x94(]\x94\x8c\x08builtins\x94\x8c\tbytearray\x94\x93\x94C\x05\x08\x03AS1\x94\x85\x94R\x94a]\x94h\x04C\x05\x08\x03AS2\x94\x85\x94R\x94a]\x94h\x04C\x05\x08\x03AS3\x94\x85\x94R\x94ae.'}
    * After adding all the encoded/pickled tuples to the dictionary, save it as a dictionary value for a key that represent the dataset name, i.e. **1m**  
    * Dump the dictionary that caches all the datasets to **/tmp/cache.pkl**
  * For other algorithms, same as above while skipping the NDN encoding for k & v

### Presets Cache
Up to 15 minutes if not cached

# The experiment:
* Read datasets from disk into memory. Each dataset is stored twice in memory, one as text and one as NDN encoded names. In both format, the keys and the values are encoded using pickle.
* The experiment starts by choosing the proper dataset format for each type of algorithms. NTv2 for example expect to use the NDN enoded format, CTrie/STrie on the other hand are expected to use the text format
* The next step is to stream each entry in the dataset dictionary to the algorithm to add it to its backend, again, the data will arrive encoded with pickle, so the first step before adding it is to unpickle it.
* The timing for the "load" process starts now.
* The unpickle will result either a text key/value for non NDN algorithms, or a NDN encoded key/value for NDN named algorithms 
* The key/value with then be passed to Algo.add(k,v) method to add the entry to the algorithm's backend database.
* After adding all batch's key/values, the timing stop and the batch load time will be calculated and recorded.


# Freezing requirements
    pip3 freeze > requirements.txt