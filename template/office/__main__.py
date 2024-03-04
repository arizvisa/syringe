import ptypes, office.storage as storage, office.propertyset as propertyset
import office.excel as excel, office.powerpoint as powerpoint, office.art as art, office.graph as graph

if __name__ == '__main__':
    import os, sys
    filename = sys.argv[1]

    try:
        ptypes.setsource(ptypes.prov.file(filename, mode='rw'))
    except ptypes.error.ProviderError as E:
        print("{!s}: Unable to open file in r/w, trying as r/o instead...".format(E))
        ptypes.setsource(ptypes.prov.file(filename, mode='rb'))

    store = storage.File()
    print('>>> Loading File...')
    store = store.l
    print(store['Header'])
    print()

    print('>>> Loading DiFat...')
    print(store['DiFat'])
    difat = store.DiFat()
    print()

    print('>>> Loading Fat...')
    print(store['Fat'])
    fat = store.Fat()
    print()

    print('>>> Loading MiniFat...')
    print(store['MiniFat'])
    minifat = mfat = store.MiniFat()
    print(store['MiniFat'])
    print()

    print('>>> Loading Directory...')
    directory = store.Directory()
    print(directory)
