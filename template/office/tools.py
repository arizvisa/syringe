import logging, contextlib, itertools

import ptypes, office.storage
from ptypes import ptype

logger = logging.getLogger(__name__)

@contextlib.contextmanager
def ModifyDirectoryEntryData(store, directory, type=None):
    """A context manager that allows one to modify the contents of a directory entry.

    A tuple containing two ptypes are yielded. The first is the original data decoded
    from the stream. The second is an uninitialized block that is intended to be
    initialized by the caller with the new contents. The directory entry and its chain
    will be updated with the size of the initialized type.
    """
    logger.info("Processing stream: {:s}".format(directory['Name'].str()))
    oldstream = directory.Data(None, clamp=False) if type is None else directory.Data(type)
    newstream = ptype.block(source=oldstream.source) if type is None else type(source=oldstream.source)

    try:
        abort = None
        yield oldstream, newstream
    except StopIteration:
        logger.info("Aborting overwrite of stream ({:d} byte{:s}) due to user request.".format(oldstream.size(), '' if oldstream.size() == 1 else 's'))
        return
    except Exception as exception:
        logger.error("Aborting overwrite of stream ({:d} byte{:s}) due to exception...".format(oldstream.size(), '' if oldstream.size() == 1 else 's'))
        abort = exception
    finally:
        if abort:
            raise abort
        if not newstream.initializedQ():
            raise ValueError("Refusing to overwrite contents of stream with uninitialized data {:s}.".format(newstream.instance()))

    logger.info("Ready to commit {:s} to stream: {:s}".format(newstream.instance(), directory['Name'].str()))
    logger.debug('')
    logger.debug(newstream)
    logger.debug('')

    logger.info("Overwriting stream ({:d} byte{:s}) with {:s} ({:d} byte{:s})...".format(oldstream.size(), '' if oldstream.size() == 1 else 's', newstream.instance(), newstream.size(), '' if newstream.size() == 1 else 's'))

    # figure out which allocation table to use.
    which, newtable = ('mini', store.MiniFat()) if newstream.size() < store['MiniFat']['ulMiniSectorCutoff'].int() else ('', store.Fat())
    oldwhich, oldtable = ('mini', store.MiniFat()) if oldstream.size() < store['MiniFat']['ulMiniSectorCutoff'].int() else ('', store.Fat())

    # clear out contents of old stream
    #global mallet, nail
    #count = oldtable.entries(directory['qwSize'].int())
    #nail = directory.Data(None, clamp=False)
    #mallet = ptype.block().set(bytearray(map(functools.partial(state.randint, 0x00), [0xff] * oldtable.sectorSize() * count)))
    #mallet = ptype.block().set(bytearray(map(functools.partial(state.randint, 0x00), [0xff] * nail.size())))
    #mallet.commit(offset=0, source=nail.source)

    # update its chain in the respective allocation table.
    if oldtable is newtable:
        chain, count = directory.chain(), newtable.entries(newstream.size())
        logger.info("Resizing {:d} {:s}sector{:s} for \"{:s}\" to {:d} {:s}sector{:s}.".format(len(chain), which, '' if len(chain) == 1 else 's', directory['Name'].str(), count, which, '' if count == 1 else 's'))
        res = newtable.resizeChain(chain, count)
        logger.info("Resized {:s}chain into {:s}sector{:s} {:s}.".format(which, which, '' if len(res) == 1 else 's', ', '.join(itertools.chain(map("{:d}".format, res[:-1]), ["and {:d}".format(*res[-1:])])) if len(res) > 2 else ' and '.join(map("{:d}".format, res))))
        newtable.c
        difference = len(res) - len(chain)
        difference and logger.info("Committed changes for {:s} will require {:d}{:s} sector{:s}.".format(newtable.instance(), abs(difference), ' additional' if difference > 0 else ' unlinked' if difference < 0 else '', '' if abs(difference) == 1 else 's'))
        logger.info("Committed changes for {:s} will remain in {:s}fat.".format(newtable.instance(), which))

        directory['sectLocation'].set(res[0] if res else 'ENDOFCHAIN').c
        directory['qwSize'].set(newtable.used(res)).c

    # otherwise if the table changed, then we can release the previous table's
    # sectors and set things up so that we allocate out of the new table.
    else:
        oldchain = directory.chain()
        chain_description = ', '.join(itertools.chain(map("{:d}".format, oldchain[:-1]), ["and {:d}".format(*oldchain[-1:])])) if len(oldchain) > 2 else ' and '.join(map("{:d}".format, oldchain))
        logger.info("Discovered {:d} {:s}sector{:s} for \"{:s}\" that will be unlinked ({:s}).".format(len(oldchain), oldwhich, '' if len(oldchain) == 1 else 's', directory['Name'].str(), chain_description))
        unlinked = oldtable.unlink(oldchain)
        logger.info("Unlinked {:d} {:s}sector{:s} for \"{:s}\" ({:s}).".format(len(oldchain), oldwhich, '' if len(oldchain) == 1 else 's', directory['Name'].str(), chain_description))
        oldtable.c
        logger.info("Committed {:s} as {:s}fat due to {:d} unlinked sector{:s}.".format(oldtable.instance(), oldwhich, len(unlinked), '' if len(unlinked) == 1 else 's'))
        chain, count = [], newtable.entries(newstream.size())
        res = newtable.growChain(chain, count)
        logger.info("Created new {:s}chain for {:s}sector{:s} {:s}.".format(which, which, '' if len(res) == 1 else 's', ', '.join(itertools.chain(map("{:d}".format, res[:-1]), ["and {:d}".format(*res[-1:])])) if len(res) > 2 else ' and '.join(map("{:d}".format, res))))
        newtable.c
        logger.info("Committed changes for {:s} as {:s}fat due to {:d} additional sector{:s}.".format(newtable.instance(), which, len(res), '' if len(res) == 1 else 's'))
        directory['sectLocation'].set(res[0] if res else 'ENDOFCHAIN').c
        directory['qwSize'].set(newtable.used(res)).c

    # if there aren't enough sectors within the file, then add whatever's needed.
    needed, size = (size * newtable.required(res) for size in [1, newtable.sectorSize()])
    if not which and len(store['Data']) < needed:
        iterable = (store['Data'].append(store.FileSector) for item in range(needed - len(store['Data'])))
        newsectors = [item.c for item in iterable]
        logger.info("Added {:d} file sector{:s} to {:s}...".format(len(newsectors), '' if len(newsectors) == 1 else 's', store.instance()))

    # if there's not enough space in the ministream, then add sectors to it.
    elif which and store.Directory().root['qwSize'].int() < size:
        root = store.Directory().root
        chain = store.chain(root['sectLocation'].int())
        fat, size = store.Fat(), needed * newtable.sectorSize()

        iterable = (store['Data'].append(store.FileSector) for item in range(fat.entries(size) - len(chain)))
        newsectors = [item.c for item in iterable]
        logger.info("Added {:d} file sectors to ministream...".format(len(newsectors)))

        newchain = fat.link(chain + [item.index() for item in newsectors])
        oldsize, newsize = fat.used(chain), fat.used(newchain)
        logger.info("Ministream was grown from {:d} byte{:s} to {:d} byte{:s}.".format(oldsize, '' if oldsize == 1 else 's', newsize, '' if newsize == 1 else 's'))
        logger.info("Committing changes to {:s}...".format(fat.instance()))
        fat.c
        logger.info("Updating {:s} containing ministream from {:d} byte{:s} to {:d} byte{:s}: {:s}".format(root.instance(), root['qwSize'], '' if root['qwSize'].int() == 1 else 's', newsize, '' if newsize == 1 else 's', root['Name'].str()))
        root['qwSize'].set(newsize).c
        root['sectLocation'].set(newchain[0] if newchain else 'ENDOFCHAIN')
        store.value = [item for item in store.value]

    ## get the new chain and use it to write the new stream
    newdata = directory.Data(None, clamped=False)
    #mallet = ptype.block(length=newdata.size()).set(bytearray(map(functools.partial(state.randint, 0x00), [0xff] * newtable.sectorSize() * count)))
    #mallet.commit(offset=0, source=newdata.source)

    count = newtable.entries(newstream.size())
    expected = newtable.sectorSize() * count
    logger.info("Stream takes up {:d} byte{:s} and will result in total allocated space of {:d} byte{:s}.".format(newstream.size(), '' if newstream.size() == 1 else 's', expected, '' if expected == 1 else 's'))
    newstream.commit(offset=0, source=newdata.source) if newdata.size() else newstream
    logger.info("Committed {:s} into {:d} {:s}sector{:s}.".format(newstream.instance(), count, which, '' if count == 1 else 's'))

    ## update the entry size.
    logger.info("Updating entry {:s}: {}".format(directory.instance(), directory['qwSize']))
    directory['sectLocation'] if count else directory['sectLocation'].set('ENDOFCHAIN')
    directory['qwSize'].set(newstream.size()).c
    logger.info("Committed {:s} as {:#x}.".format(directory['qwSize'].instance(), directory['qwSize']))

def ModifyDirectoryEntryChain(store, entry):
    """A context manager that allows one to modify the sectors that are used by the specified directory entry.

    A tuple containing two lists is yielded. The first list is the original chain of sectors for the entry.
    The second list is intended to be modified with the desired sectors that the entry should be moved to.
    """
    modify = ModifyFatChain if entry.streamQ() else ModifyMiniFatChain
    return modify(store, entry['sectLocation'].int())

@contextlib.contextmanager
def ModifyDirectory(store):
    """A context manager that allows one to modify the sectors that are used by directory.

    A tuple containing two lists is yielded. The first list is the original chain of sectors
    containing the directory. The second list is intended to be modified with the desired
    sectors that the directory should be moved to.
    """
    header, fat, world = store['Fat'], store.Fat(), store['Data']

    # figure out the sectors that we'll be exchanging using the list returned to the caller.
    iterable = fat.chain(header['sectDirectory'].int())
    oldchain, newchain = [index for index in iterable], []
    try:
        abort = None
        yield oldchain, newchain
    except StopIteration:
        logger.info("Aborting modification of directory stream ({:d} sector{:s}) due to user request.".format(len(oldchain), '' if len(oldchain) == 1 else 's'))
        return
    except Exception as exception:
        logger.error("Aborting modification of directory stream ({:d} sector{:s}) due to exception...".format(len(oldchain), '' if len(oldchain) == 1 else 's'))
        abort = exception
    finally:
        if abort:
            raise abort
        if newchain and len(fat) < max(newchain):
            raise IOError("Refusing to modify {:d} sector{:s} of directory stream due to the {:s} not being large enough (required {:d}).".format(len(oldchain), '' if len(oldchain) == 1 else 's', fat.instance(), max(newchain)))
        #elif oldchain == newchain:
        #    logger.warning("No need to modify directory stream ({:d} sector{:s}) as old chain ({:s}) is the same as new chain ({:s}).".format(len(oldchain), '' if len(oldchain) == 1 else 's', ', '.join(map("{:d}".format, oldchain)), ', '.join(map("{:d}".format, newchain))))
        #    return

    logger.info("Ready to exchange {:d} sector{:s} of directory stream with {:d} sector{:s}.".format(len(oldchain), '' if len(oldchain) == 1 else 's', len(newchain), '' if len(newchain) == 1 else 's'))
    logger.debug("Old sector{:s}: {:s}".format('' if len(oldchain) == 1 else 's', ', '.join(map("{:d}".format, oldchain))))
    logger.debug("New sector{:s}: {:s}".format('' if len(newchain) == 1 else 's', ', '.join(map("{:d}".format, newchain))))

    # record both the old and new sectors (if available)
    olditems, newitems = {oidx : (world[oidx].copy() if 0 <= oidx < len(world) else store.new(store.FileSector, offset=fat[oidx].d.getoffset()).l) for oidx in oldchain}, {}
    for oidx, nidx in zip(oldchain, newchain):
        old = olditems[oidx]
        if nidx in olditems:
            new = olditems[nidx].copy()
        elif 0 <= nidx < len(world):
            new = world[nidx]
        else:
            new = store.new(store.FileSector, offset=fat[nidx].d.getoffset()).a
        newitems[nidx] = new

    # copy any of the old directory sectors into the new ones.
    for oidx, nidx in zip(oldchain, newchain):
        old, new = olditems[oidx], newitems[nidx]
        logger.debug("Exchanging sector {:d} at {:s} with sector {:d} at {:s}.".format(oidx, old.instance(), nidx, new.instance()))
        new.commit(offset=old.getoffset()), old.commit(offset=new.getoffset())
    newdir = [newitems[nidx] for nidx in newchain[:len(oldchain)]] if oldchain else []

    # gather any additional sectors for the new directory chain.
    additional = []
    if len(newchain) != len(newdir):
        logger.info("Growing {:s} from {:d} sector{:s} to {:d} sector{:s}.".format(fat.instance(), len(oldchain), '' if len(oldchain) == 1 else 's', len(newchain), '' if len(newchain) == 1 else 's'))
        locations = {nidx : fat[nidx].d.getoffset() if 0 <= nidx < len(fat) else store._uHeaderSize + store._uSectorSize * nidx for nidx in newchain}
        iterable = ((world[nidx].li if 0 <= nidx < len(world) else store.new(store.FileSector, offset=locations[nidx])) for nidx in newchain[len(oldchain):])
        additional.extend(iterable)

    # then we can initialize those additional sectors.
    if additional:
        logger.info("Adding {:d} sector{:s} to {:s}".format(len(additional), '' if len(additional) == 1 else 's', fat.instance()))

    iterable = (new.a.asDirectory() for new in additional if not new.initializedQ())
    [ new.a.c for new in iterable ]

    # now we can unlink the previous chain and link the new one.
    [fat[oidx].c for oidx in fat.unlink(oldchain)]
    [fat[nidx].c for nidx in fat.link(newchain)]

    # and then finally update the header and commit it.
    header['sectDirectory'].set(newchain[0] if newchain else 'ENDOFCHAIN')
    store['Header']['uMajorVersion'].int() > 3 and header['csectDirectory'].set(len(newchain))
    header.c

@contextlib.contextmanager
def ModifyFatChain(store, chain):
    """A context manager that allows one to modify the sectors that are used by the specified fat chain.

    A tuple containing two lists is yielded. The first list is the original chain of file sectors by
    index. The second list is intended to be modified with the new indices of the desired file sectors.
    The contents of the entire chain is preserved and the number of file-sectors cannot be modified.
    """
    fat, world = store.Fat(), store['Data']

    # figure out the sectors that we'll be exchanging using the list returned to the caller.
    iterable = (index for index in chain) if hasattr(chain, '__iter__') else fat.chain(chain)
    oldchain, newchain = [index for index in iterable], []
    try:
        abort = None
        yield oldchain, newchain
    except StopIteration:
        logger.info("Aborting modification of stream ({:d} sector{:s}) due to user request.".format(len(oldchain), '' if len(oldchain) == 1 else 's'))
        return
    except Exception as exception:
        logger.error("Aborting modification of stream ({:d} sector{:s}) due to exception...".format(len(oldchain), '' if len(oldchain) == 1 else 's'))
        abort = exception
    finally:
        if abort:
            raise abort
        if len(oldchain) != len(newchain):
            raise ValueError("Refusing to modify {:d} sector{:s} of stream with different number of sectors ({:d}).".format(len(oldchain), '' if len(oldchain) == 1 else 's', len(newchain)))
        #elif oldchain == newchain:
        #    logger.warning("No need to modify stream ({:d} sector{:s}) as old chain ({:s}) is the same as new chain ({:s}).".format(len(oldchain), '' if len(oldchain) == 1 else 's', ', '.join(map("{:d}".format, oldchain)), ', '.join(map("{:d}".format, newchain))))
        #    return

    logger.info("Ready to exchange {:d} sector{:s} of stream with {:d} sector{:s}.".format(len(oldchain), '' if len(oldchain) == 1 else 's', len(newchain), '' if len(newchain) == 1 else 's'))
    logger.debug("Old sector{:s}: {:s}".format('' if len(oldchain) == 1 else 's', ', '.join(map("{:d}".format, oldchain))))
    logger.debug("New sector{:s}: {:s}".format('' if len(newchain) == 1 else 's', ', '.join(map("{:d}".format, newchain))))

    # exchange the sectors from the old chain with the new one.
    olditems = {oidx : world[oidx].copy() for oidx in oldchain}
    for oidx, nidx in zip(oldchain, newchain):
        new = olditems[nidx].copy() if nidx in olditems else world[nidx]
        logger.debug("Writing sector {:d} at {:s} to sector {:d} at {:s}.".format(nidx, new.instance(), oidx, olditems[oidx].instance()))
        new.commit(offset=olditems[oidx].getoffset())

    for oidx, nidx in zip(oldchain, newchain):
        new = olditems[nidx] if nidx in olditems else world[nidx]
        logger.debug("Writing sector {:d} at {:s} to sector {:d} at {:s}.".format(oidx, olditems[oidx].instance(), nidx, new.instance()))
        olditems[oidx].commit(offset=new.getoffset())

    # verify that we didn't damage the streams in any way.
    oldstream = b''.join([olditems[oidx].serialize() for oidx in oldchain])
    newstream = b''.join([world[nidx].l.serialize() for nidx in newchain])
    assert(oldstream == newstream)

    # now we can unlink the previous chain and link the new one.
    [fat[oidx].c for oidx in fat.unlink(oldchain)]
    [fat[nidx].c for nidx in fat.link(newchain)]

    # reload the fat in case we just modified the ministream
    store.value = [item for item in store.value]

@contextlib.contextmanager
def ModifyMiniFatChain(store, chain):
    """A context manager that allows one to modify the minisectors that are used by the specified minichain.

    A tuple containing two lists is yielded. The first list is the original chain of minisectors by
    index. The second list is intended to be modified with the new indices for the desired minisectors.
    The contents of the entire chain is preserved and the number of mini-sectors cannot be modified.
    """
    directory = store.Directory()
    mfat, root = store.MiniFat(), directory.RootEntry()
    smallworld = root.Data(None, clamp=False)

    # figure out the sectors that we'll be exchanging using the list returned to the caller.
    iterable = (index for index in chain) if hasattr(chain, '__iter__') else mfat.chain(chain)
    oldchain, newchain = [index for index in iterable], []
    try:
        abort = None
        yield oldchain, newchain
    except StopIteration:
        logger.info("Aborting modification of stream ({:d} minisector{:s}) due to user request.".format(len(oldchain), '' if len(oldchain) == 1 else 's'))
        return
    except Exception as exception:
        logger.error("Aborting modification of stream ({:d} minisector{:s}) due to exception...".format(len(oldchain), '' if len(oldchain) == 1 else 's'))
        abort = exception
    finally:
        if abort:
            raise abort
        if len(oldchain) != len(newchain):
            raise ValueError("Refusing to modify {:d} minisector{:s} of stream with different number of minisectors ({:d}).".format(len(oldchain), '' if len(oldchain) == 1 else 's', len(newchain)))
        elif newchain and len(smallworld) < max(newchain):
            raise IOError("Refusing to replace {:d} minisector{:s} of stream with chain referencing minisector {:d} when only {:d} minisector{:s} are available.".format(len(oldchain), '' if len(oldchain) == 1 else 's', max(newchain), len(smallworld), '' if len(smallworld) == 1 else 's'))
        #elif oldchain == newchain:
        #    logger.warning("No need to modify stream ({:d} minisector{:s}) as old chain ({:s}) is the same as new chain ({:s}).".format(len(oldchain), '' if len(oldchain) == 1 else 's', ', '.join(map("{:d}".format, oldchain)), ', '.join(map("{:d}".format, newchain))))
        #    return

    logger.info("Ready to exchange {:d} minisector{:s} of stream with {:d} minisector{:s}.".format(len(oldchain), '' if len(oldchain) == 1 else 's', len(newchain), '' if len(newchain) == 1 else 's'))
    logger.debug("Old minisector{:s}: {:s}".format('' if len(oldchain) == 1 else 's', ', '.join(map("{:d}".format, oldchain))))
    logger.debug("New minisector{:s}: {:s}".format('' if len(newchain) == 1 else 's', ', '.join(map("{:d}".format, newchain))))

    # exchange the sectors from the old chain with the new one.
    olditems = {oidx : smallworld[oidx].copy() for oidx in oldchain}
    for oidx, nidx in zip(oldchain, newchain):
        new = olditems[nidx].copy() if nidx in olditems else smallworld[nidx]
        logger.debug("Writing minisector {:d} at {:s} to minisector {:d} at {:s}.".format(nidx, new.instance(), oidx, olditems[oidx].instance()))
        new.commit(offset=olditems[oidx].getoffset())

    for oidx, nidx in zip(oldchain, newchain):
        new = olditems[nidx] if nidx in olditems else smallworld[nidx]
        logger.debug("Writing minisector {:d} at {:s} to minisector {:d} at {:s}.".format(oidx, olditems[oidx].instance(), nidx, new.instance()))
        olditems[oidx].commit(offset=new.getoffset())

    # verify that we didn't damage the streams in any way.
    oldstream = b''.join([olditems[oidx].serialize() for oidx in oldchain])
    newstream = b''.join([smallworld[nidx].l.serialize() for nidx in newchain])
    assert(oldstream == newstream)

    # now we can unlink the previous chain and link the new one.
    [mfat[oidx].c for oidx in mfat.unlink(oldchain)]
    [mfat[nidx].c for nidx in mfat.link(newchain)]

@contextlib.contextmanager
def ModifyFat(store):
    """A context manager that allows one to modify the file sectors that are used by the FAT.

    A tuple containing two lists is yielded. The first list is the original list of file sector
    indices. The second list is intended to be modified with the desired new file sector indices.
    """
    difat, world = store.DiFat(), store['Data']
    fat, sectors = store.Fat(), [sector.int() for index, sector in difat.enumerate()]
    if not all(fat[idx].object['FATSECT'] for idx in sectors if 0 <= idx < len(fat)):
        wrong = [idx for idx in sectors if not fat[idx].object['FATSECT']]
        logger.error("{:d} sector{:s} for the {:s} are not specified as {:s} ({:s}).".format(len(wrong), '' if len(wrong) == 1 else 's', fat.instance(), 'FATSECT', ', '.join(map("{:d}".format, wrong))))

    oldchain, newchain = sectors[:], []
    try:
        abort = None
        yield oldchain, newchain
    except StopIteration:
        logger.info("Aborting modification of {:s} ({:d} sector{:s}) due to user request.".format(fat.instance(), len(oldchain), '' if len(oldchain) == 1 else 's'))
        return
    except Exception as exception:
        logger.error("Aborting modification of {:s} ({:d} sector{:s}) due to exception...".format(fat.instance(), len(oldchain), '' if len(oldchain) == 1 else 's'))
        abort = exception
    finally:
        if abort:
            raise abort
        if len(difat) < len(newchain):
            raise IOError("Not enough available elements in {:s} ({:d}) to store {:d} sector{:s} for {:s}.".format(difat.instance(), len(difat), len(newchain), '' if len(newchain) == 1 else 's', fat.instance()))
        #elif oldchain == newchain:
        #    logger.warning("No need to modify {:s} ({:d} sector{:s}) as old chain ({:s}) is the same as new chain ({:s}).".format(fat.instance(), len(oldchain), '' if len(oldchain) == 1 else 's', ', '.join(map("{:d}".format, oldchain)), ', '.join(map("{:d}".format, newchain))))
        #    return

    logger.info("Ready to exchange {:d} sector{:s} of {:s} with {:d} sector{:s}.".format(len(oldchain), '' if len(oldchain) == 1 else 's', fat.instance(), len(newchain), '' if len(newchain) == 1 else 's'))

    # record both the old and new sectors (if available)
    olditems, newitems = {oidx : (world[oidx].copy() if 0 <= oidx < len(world) else store.new(store.FileSector, offset=fat[oidx].d.getoffset()).l) for oidx in oldchain}, {}
    for oidx, nidx in zip(oldchain, newchain):
        old = olditems[oidx]
        if nidx in olditems:
            new = olditems[nidx].copy()
        elif 0 <= nidx < len(world):
            new = world[nidx]
        else:
            new = store.new(store.FileSector, offset=fat[nidx].d.getoffset()).a
        newitems[nidx] = new

    # start out by clearing the old entries in the old cache and emptying the difat.
    [ fat[oidx].set('FREESECT').c for oidx in oldchain ]
    oldchain and logger.info("Cleared {:d} sector{:s} in {:s} to {:s}.".format(len(oldchain), '' if len(oldchain) == 1 else 's', fat.instance(), 'FREESECT'))
    removed = [(index, sector.set('FREESECT').c) for index, sector in difat.enumerate() if sector.int() in olditems]
    oldchain and logger.info("Removed {:d} entr{:s} from {:s}.".format(len(removed), 'y' if len(oldchain) == 1 else 'ies', difat.instance()))
    [ fat[oidx].set('FREESECT').c for oidx, _ in removed ]

    # copy any of the old sectors into the new ones.
    for oidx, nidx in zip(oldchain, newchain):
        old, new = olditems[oidx], newitems[nidx]
        logger.debug("Exchanging sector {:d} at {:s} with sector {:d} at {:s}.".format(oidx, old.instance(), nidx, new.instance()))
        new.commit(offset=old.getoffset()), old.commit(offset=new.getoffset())
    newfat = [newitems[nidx] for nidx in newchain[:len(oldchain)]] if oldchain else []

    # add any missing sectors to the newfat.
    additional = []
    if len(newchain) != len(newfat):
        logger.info("Growing {:s} from {:d} sector{:s} to {:d} sector{:s}.".format(fat.instance(), len(oldchain), '' if len(oldchain) == 1 else 's', len(newchain), '' if len(newchain) == 1 else 's'))
        locations = {nidx : fat[nidx].d.getoffset() if 0 <= nidx < len(fat) else store._uHeaderSize + store._uSectorSize * nidx for nidx in newchain}
        iterable = ((world[nidx].li if 0 <= nidx < len(world) else store.new(store.FileSector, offset=locations[nidx])) for nidx in newchain[len(oldchain):])
        additional.extend(iterable)

    # now we'll need to initialize any of the additional sectors.
    if additional:
        logger.info("Adding {:d} sector{:s} to {:s}".format(len(additional), '' if len(additional) == 1 else 's', fat.instance()))
    [ new.a.asTable(office.storage.FAT).a.c for new in additional if not new.initializedQ() ]

    # then we can update the difat with each entry for the file allocation table.
    logger.info("Updating {:s} with {:d} sector{:s} for {:s}".format(difat.instance(), len(newchain), '' if len(newchain) == 1 else 's', fat.instance()))
    for nidx, ptr in zip(newchain, difat):
        logger.debug("Assigning index {:s} at {:s} of {:s} with sector {:d} for {:s}.".format(ptr.name(), ptr.instance(), difat.instance(), nidx, fat.instance()))
        ptr.set(nidx).c

    # update the number of fat sectors declared in the header
    header = store['Fat']
    header['csectFat'].set(len(newchain))
    header.c

    # reset the fat for the entire document so we can update it with the sectors that are used.
    store.value = [item for item in store.value]

    logger.info("Reloading {:s} with {:d} sector{:s} from {:s} ({:s}).".format(fat.instance(), len(newchain), '' if len(newchain) == 1 else 's', difat.instance(), ', '.join(map("{:d}".format, newchain))))
    newdfat, newfat = store.DiFat(), store.Fat()

    [ newfat[oidx].set('FREESECT').c for oidx in oldchain ]
    [ newfat[nidx].set('FATSECT').c for nidx in newchain ]
    newchain and logger.info("Updated {:d} sector{:s} in {:s} to {:s}.".format(len(newchain), '' if len(newchain) == 1 else 's', newfat.instance(), 'FATSECT'))

@contextlib.contextmanager
def ModifyDiFat(store):
    """A context manager that allows one to modify the file sectors that are used by the DIFAT.

    A tuple containing two lists is yielded. The first list is the original list of file sector
    indices. The second list is intended to be modified with the desired new file sector indices.
    """
    difat, world, dfchain = store.DiFat(), store['Data'], store.difatchain()

    # first verify that the fat is correct.
    fat, sectors = store.Fat(), [sector.int() for index, sector in difat.enumerate()]
    if not all(fat[idx].object['FATSECT'] for idx in sectors):
        wrong = [idx for idx in sectors if not fat[idx].object['FATSECT']]
        logger.warning("{:d} sector{:s} in the {:s} are not specified as {:s} ({:s}).".format(len(wrong), '' if len(wrong) == 1 else 's', fat.instance(), 'FATSECT', ', '.join(map("{:d}".format, wrong))))

    # now we can check the difat is properly assigned in the fat
    if not all(fat[idx].object['DIFSECT'] for idx in dfchain):
        wrong = [idx for idx in sectors if not fat[idx].object['DIFSECT']]
        logger.warning("{:d} sector{:s} in the {:s} for {:s} are not specified as {:s} ({:s}).".format(len(wrong), '' if len(wrong) == 1 else 's', fat.instance(), difat.instance(), 'DIFSECT', ', '.join(map("{:d}".format, wrong))))

    oldchain, newchain = dfchain[:], []
    try:
        abort = None
        yield oldchain, newchain
    except StopIteration:
        logger.info("Aborting modification of {:s} ({:d} sector{:s}) due to user request.".format(difat.instance(), len(oldchain), '' if len(oldchain) == 1 else 's'))
        return
    except Exception as exception:
        logger.error("Aborting modification of {:s} ({:d} sector{:s}) due to exception...".format(difat.instance(), len(oldchain), '' if len(oldchain) == 1 else 's'))
        abort = exception
    finally:
        if abort:
            raise abort
        #elif oldchain == newchain:
        #    logger.warning("No need to modify {:s} ({:d} sector{:s}) as old chain ({:s}) is the same as new chain ({:s}).".format(difat.instance(), len(oldchain), '' if len(oldchain) == 1 else 's', ', '.join(map("{:d}".format, oldchain)), ', '.join(map("{:d}".format, newchain))))
        #    return

    logger.info("Ready to exchange {:d} sector{:s} of {:s} with {:d} sector{:s}.".format(len(oldchain), '' if len(oldchain) == 1 else 's', fat.instance(), len(newchain), '' if len(newchain) == 1 else 's'))

    # record both the old and new sectors (if available)
    olditems, newitems = {oidx : (world[oidx].copy() if 0 <= oidx < len(world) else store.new(store.FileSector, offset=fat[oidx].d.getoffset()).l) for oidx in oldchain}, {}
    for oidx, nidx in zip(oldchain, newchain):
        old = olditems[oidx]
        if nidx in olditems:
            new = olditems[nidx].copy()
        elif 0 <= nidx < len(world):
            new = world[nidx]
        else:
            new = store.new(store.FileSector, offset=fat[nidx].d.getoffset()).a
        newitems[nidx] = new

    # copy any of the old sectors into the new ones.
    for oidx, nidx in zip(oldchain, newchain):
        old, new = olditems[oidx], newitems[nidx]
        logger.debug("Exchanging sector {:d} at {:s} with sector {:d} at {:s}.".format(oidx, old.instance(), nidx, new.instance()))
        new.commit(offset=old.getoffset()), old.commit(offset=new.getoffset())
    newdfat = [newitems[nidx] for nidx in newchain[:len(oldchain)]] if oldchain else []

    # add any missing sectors to the new difat.
    additional = []
    if len(newchain) != len(newdfat):
        logger.info("Growing {:s} from {:d} sector{:s} to {:d} sector{:s}.".format(difat.instance(), len(oldchain), '' if len(oldchain) == 1 else 's', len(newchain), '' if len(newchain) == 1 else 's'))
        locations = {nidx : fat[nidx].d.getoffset() if 0 <= nidx < len(fat) else store._uHeaderSize + store._uSectorSize * nidx for nidx in newchain}
        iterable = ((world[nidx].li if 0 <= nidx < len(world) else store.new(store.FileSector, offset=locations[nidx])) for nidx in newchain[len(oldchain):])
        additional.extend(iterable)

    # then we'll remove the old entries from the current fat.
    [ fat[oidx].set('FREESECT').c for oidx in oldchain ]
    oldchain and logger.info("Cleared {:d} sector{:s} in {:s} to {:s}.".format(len(oldchain), '' if len(oldchain) == 1 else 's', fat.instance(), 'FREESECT'))

    # now we can update the file header with the new difat sectors.
    header = store['DiFat']
    if newchain:
        start = newchain[0]
        logger.info("Updating {:s} to reference {:d} sector{:s} of {:s} starting at sector {:d}.".format(header.instance(), len(newchain), '' if len(newchain) == 1 else 's', difat.instance(), start))
        header.set(sectDiFat=start, csectDifat=len(newchain))
    else:
        header.set(sectDiFat='ENDOFCHAIN', csectDifat=len(newchain))
    header.c

    # then we link the entire DiFat together.
    newdfat.extend(additional)
    for index, nidx in enumerate(newchain[1:]):
        sector = newdfat[index]
        new = sector.asTable(office.storage.DIFAT) if sector.initializedQ() else sector.a.asTable(office.storage.DIFAT).a
        logger.info("Updating {:s} to reference sector {:d} containing {:s}.".format(new[-1].instance(), nidx, difat.instance()))
        new[-1].set(nidx)
        new.c

    if newdfat:
        last = newdfat[-1].a.asTable(office.storage.DIFAT).a
        last[-1].set('ENDOFCHAIN').c
        last.c

    # reset the fat for the entire document, and update it with the new difat entries.
    store.value = [item for item in store.value]

    logger.info("Reloading {:s} using {:d} sector{:s} from {:s} ({:s}).".format(fat.instance(), len(newchain), '' if len(newchain) == 1 else 's', difat.instance(), ', '.join(map("{:d}".format, newchain))))
    newfat = store.Fat()

    # now we can update the new fat with the sectors containing our modified difat.
    [ newfat[nidx].set('DIFSECT').c for nidx in newchain ]
    newchain and logger.info("Updated {:d} sector{:s} in {:s} to {:s}.".format(len(newchain), '' if len(newchain) == 1 else 's', newfat.instance(), 'DIFSECT'))

@contextlib.contextmanager
def ModifyMiniFat(store):
    """A context manager that allows one to modify the file sectors that are used by the MINIFAT.

    A tuple containing two lists is yielded. The first list is the original list of file sector
    indices. The second list is intended to be modified with the desired new file sector indices.
    """
    header, fat, world = store['MiniFat'], store.Fat(), store['Data']
    mfat, oldchain, newchain = store.MiniFat(), [index for index in fat.chain(header['sectMiniFat'].int())], []

    if len(oldchain) != header['csectMiniFat'].int():
        count = header['csectMiniFat'].int()
        logger.error("Number of sectors in header ({:d}) to not correspond to length of chain ({:d}) containing the {:s}.".format(count, len(oldchain), mfat.instance()))

    try:
        abort = None
        yield oldchain, newchain
    except StopIteration:
        logger.info("Aborting modification of {:s} ({:d} sector{:s}) due to user request.".format(mfat.instance(), len(oldchain), '' if len(oldchain) == 1 else 's'))
        return
    except Exception as exception:
        logger.error("Aborting modification of {:s} ({:d} sector{:s}) due to exception...".format(mfat.instance(), len(oldchain), '' if len(oldchain) == 1 else 's'))
        abort = exception
    finally:
        if abort:
            raise abort
        if len(fat) < len(newchain):
            raise IOError("Not enough available elements in {:s} ({:d}) to store {:d} sector{:s} for {:s}.".format(fat.instance(), len(fat), len(newchain), '' if len(newchain) == 1 else 's', mfat.instance()))
        #elif oldchain == newchain:
        #    logger.warning("No need to modify {:s} for {:s} ({:d} sector{:s}) as old chain ({:s}) is the same as new chain ({:s}).".format(fat.instance(), mfat.instance(), len(oldchain), '' if len(oldchain) == 1 else 's', ', '.join(map("{:d}".format, oldchain)), ', '.join(map("{:d}".format, newchain))))
        #    return

    logger.info("Ready to exchange {:d} sector{:s} of {:s} with {:d} sector{:s}.".format(len(oldchain), '' if len(oldchain) == 1 else 's', fat.instance(), len(newchain), '' if len(newchain) == 1 else 's'))
    logger.debug("Old sector{:s}: {:s}".format('' if len(oldchain) == 1 else 's', ', '.join(map("{:d}".format, oldchain))))
    logger.debug("New sector{:s}: {:s}".format('' if len(newchain) == 1 else 's', ', '.join(map("{:d}".format, newchain))))

    # record both the old and new sectors (if available)
    olditems, newitems = {oidx : world[oidx].copy() for oidx in oldchain}, {}
    for oidx, nidx in zip(oldchain, newchain):
        old = olditems[oidx]
        if nidx in olditems:
            new = olditems[nidx].copy()
        elif 0 <= nidx < len(world):
            new = world[nidx]
        else:
            new = store.new(store.FileSector, offset=fat[nidx].d.getoffset()).a
        newitems[nidx] = new

    # copy any of the old sectors into the new ones.
    for oidx, nidx in zip(oldchain, newchain):
        old, new = olditems[oidx], newitems[nidx]
        logger.debug("Exchanging sector {:d} at {:s} with sector {:d} at {:s}.".format(oidx, old.instance(), nidx, new.instance()))
        new.commit(offset=old.getoffset()), old.commit(offset=new.getoffset())
    newmfat = [newitems[nidx] for nidx in newchain[:len(oldchain)]] if oldchain else []

    # add any missing sectors to the newfat.
    additional = []
    if len(newchain) != len(newmfat):
        logger.info("Growing {:s} from {:d} sector{:s} to {:d} sector{:s}.".format(mfat.instance(), len(oldchain), '' if len(oldchain) == 1 else 's', len(newchain), '' if len(newchain) == 1 else 's'))
        iterable = ((world[nidx] if 0 <= nidx < len(world) else store.new(store.FileSector, offset=fat[nidx].d.getoffset()).a) for nidx in newchain[len(oldchain):])
        additional.extend(iterable)

    # now we'll need to initialize any of the additional sectors.
    if additional:
        logger.info("Adding {:d} sector{:s} to {:s}".format(len(additional), '' if len(additional) == 1 else 's', mfat.instance()))

    for new in additional:
        table = new.asTable(office.storage.MINIFAT).a
        table.c

    # exchange the sectors from the old chain with the new one.
    for oidx, nidx in zip(oldchain, newchain):
        old, new = world[oidx].copy(), world[nidx].copy()
        old.l, new.l
        old.commit(offset=new.getoffset()), new.commit(offset=old.getoffset())

    # then we can update the fat with each entry for the mfat.. unlink
    # the old chain and then relink the new one that we received.
    logger.info("Updating {:s} with {:d} sector{:s} for {:s}".format(fat.instance(), len(newchain), '' if len(newchain) == 1 else 's', mfat.instance()))

    [fat[oidx].c for oidx in fat.unlink(oldchain)]
    [fat[nidx].c for nidx in fat.link(newchain)]

    # then we just need to update the header with the new minifat.
    if newchain:
        header.set(sectMiniFat=newchain[0], csectMiniFat=len(newchain))
    else:
        header.set(sectMiniFat='ENDOFCHAIN', csectMiniFat=len(newchain))
    header.c

    # reload the fat so that the ministream is refreshed
    store.value = [item for item in store.value]

if __name__ == '__main__':
    import sys, logging
    import ptypes, office.storage
    from ptypes import *

    handler = logging.StreamHandler()
    formatter = logging.Formatter(">>> %(message)s")
    handler.setFormatter(formatter)

    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    rp, __name__ = sys.argv[1:] if len(sys.argv) == 3 else itertools.islice(itertools.chain(sys.argv[1:], [''] * 2), 2)

    source = ptypes.provider.file(rp, 'rw')
    source = ptypes.setsource(source)

    ## file
    store = office.storage.File()
    store = store.l

    ## directory and sectors
    directory = store.Directory()
    world = [sector for sector in store['Data']]
    locations = {index : sector.getoffset() for index, sector in enumerate(world)}
    difat, fat, mfat, mstream = store.DiFat(), store.Fat(), store.MiniFat(), directory.root.Data()

if __name__.upper() == 'DEFRAG':
    ministream = directory.root.Data()

    # start by figuring out the sizes of absolutely everything
    with ModifyDiFat(store) as (old, new): raise StopIteration
    difatsectors = old
    with ModifyFat(store) as (old, new): raise StopIteration
    fatsectors = old
    with ModifyMiniFat(store) as (old, new): raise StopIteration
    minifatsectors = old
    with ModifyDirectory(store) as (old, new): raise StopIteration
    dirsectors = old

    # grab the difat, fat, minifat, and directories
    difat = store.DiFat()
    fat = store.Fat()
    mfat = store.MiniFat()
    directory = store.Directory()

    # now we snag all of the known directory entries
    directoryentries_fat, directoryentries_mfat = {}, {}
    for index, entry in enumerate(directory):
        if entry['Type']['Unknown']:
            continue
        directoryentries = directoryentries_fat if entry.streamQ() else directoryentries_mfat
        directoryentries[index] = entry.chain()

    # first grab the ministream and its fat sectors.
    ministream = directory.root.Data(None, clamp=False)

    [root_index] = (index for index, entry in enumerate(directory) if entry['Type']['Root'])
    ministream_chain = directoryentries_fat.pop(root_index)

    # now we need to calculate the required length of the minifat, and
    # determine how many sectors the minifat should take up along with
    # the number of sectors that should be occupied by the ministream.
    minisectors_used = sum(map(len, directoryentries_mfat.values()))
    new_minifat_length = mfat.entries(mfat.sectorSize() * minisectors_used)
    new_minifat_size, new_ministream_size = mfat.tableSize(new_minifat_length), mfat.streamSize(new_minifat_length)
    new_minifat_sectors, new_ministream_sectors = fat.entries(new_minifat_size), fat.entries(new_ministream_size)

    # figure out how many directory entries we actually need to store
    # everything, and use it to calculate the required size.
    entries_used = sum(1 for entry in directory if entry.used())
    new_directory_size = store.new(office.storage.Directory).alloc(length=entries_used).size()
    new_directory_sectors = fat.entries(new_directory_size)

    # calculate the required number of fat sectors, and then use them
    # to figure out how many entries are required so that we can use
    # it to calculate the number of sectors that the fat should take up.
    fatsectors_used = sum(map(len, itertools.chain([dirsectors, minifatsectors, ministream_chain], directoryentries_fat.values())))
    fatsectors_required = new_directory_sectors + new_minifat_sectors + new_ministream_sectors + sum(map(len, directoryentries_fat.values()))

    required_fat_size = fat.tableSize(fatsectors_required)
    required_fat_sectors = fat.entries(required_fat_size)

    # now we can calculate how many entries are required for the difat.
    extra_difat_entries = max(0, required_fat_sectors - len(store['Table']))
    required_difat_size = difat.tableSize(extra_difat_entries)
    required_difat_sectors = fat.entries(required_difat_size)

    # and now we can use the total size to calculate the _actual_ size of the fat and difat.
    new_fat_size = fat.tableSize(fatsectors_required + required_difat_sectors)
    new_fat_sectors = fat.entries(new_fat_size)

    extra_difat_entries = max(0, new_fat_sectors - len(store['Table']))
    new_difat_size = difat.tableSize(extra_difat_entries)
    new_difat_sectors = fat.entries(new_difat_size)

    # grab all of the sectors containing all the things
    iterable = itertools.chain(*(chain for sidx, chain in directoryentries_fat.items()))
    world = {sidx : store['Data'][sidx].copy() for sidx in itertools.chain(iterable, difatsectors, fatsectors, minifatsectors, dirsectors)}
    total = sum(sector.size() for sidx, sector in world.items())

    # start by emitting our statistics.
    logger.info("DiFat sectors: {:d}".format(len(difatsectors)))
    logger.info("DiFat entries: {:d}/{:d}".format(sum(1 for _, item in difat.enumerate() if not item.object['FREESECT']), len(difat)))
    logger.info("Fat sectors: {:d}".format(len(fatsectors)))
    logger.info("Fat entries: {:d}/{:d}/{:d}".format(sum(1 for _, item in fat.enumerate() if not item.object['FREESECT']), fat.required(), len(fat)))
    logger.info("MiniFat sectors: {:d}".format(len(minifatsectors)))
    logger.info("MiniFat entries: {:d}/{:d}/{:d}".format(sum(1 for _, item in mfat.enumerate() if not item.object['FREESECT']), mfat.required(), len(mfat)))
    logger.info("Directory sectors: {:d}".format(len(dirsectors)))
    logger.info("Directory entries: {:d}/{:d}".format(sum(1 for item in directory if item.used()), len(directory)))
    logger.info("Total sectors: {:d}/{:d} ({:+#x} byte{:s})".format(len(world), len(store['Data']), total, '' if total == 1 else 's'))

    # start by creating the DIFAT that will contain the FAT.
    sidx = 0
    with ModifyDiFat(store) as (old, new):
        [ new.append(sidx + counter) for counter in range(new_difat_sectors) ]
        sidx += len(new)
    updated_difat_sectors = new

    # now we can create the FAT using the entries from the DIFAT.
    with ModifyFat(store) as (old, new):
        [ new.append(sidx + counter) for counter in range(new_fat_sectors) ]
        sidx += len(new)
    updated_fat_sectors = new

    # grab the fat, so we can initialize it with what we've done so far.
    newfat = store.Fat().a
    [ newfat[idx].set('DIFSECT').c for idx in updated_difat_sectors ]
    [ newfat[idx].set('FATSECT').c for idx in updated_fat_sectors ]

    # now we can create the Directory using the next set of entries.
    with ModifyDirectory(store) as (old, new):
        [ new.append(sidx + counter) for counter in range(new_directory_sectors) ]
        sidx += len(new)
    updated_directory_sectors = new

    # we need to copy the directory into the new sectors, but we also need to preserve
    # the tree that the directory is sorted by. this is done by just building an index
    # of the original tree, building a new one, and then joining everything together.
    old_directory_table = {index : (entry['iLeftSibling'], entry['iChild'], entry['iRightSibling']) for index, entry in enumerate(directory) if entry.used()}
    busted = {index for index, iTreeNode in old_directory_table.items() if any(i.int() not in old_directory_table or i.int() == index for i in iTreeNode if not i['NOSTREAM'])}
    if busted:
        for index in sorted(busted):
            iTreeNode = left, child, right = old_directory_table.pop(index)
            logger.warning("Directory entry {:d} will be removed as it is potentially corrupt and references an unused or unavailable entry ({:s}).".format(index, ', '.join("{:d}".format(i) for i in iTreeNode if i not in old_directory_table)))
        logger.warning("Discarded {:d} directory entr{:s} from directory.".format(len(busted), 'y' if len(busted) == 1 else 'ies'))

    old_directory_entries = {directory[index].getoffset() : index for index in old_directory_table}

    iterable = ((directory[index], (iLeftSibling, iChild, iRightSibling)) for index, (iLeftSibling, iChild, iRightSibling) in old_directory_table.items())
    filtered = ((entry.getoffset(), [(None if i['NOSTREAM'] else directory[i.int()].getoffset()) for i in iTreeNodes]) for entry, iTreeNodes in iterable)
    new_directory_table = {offset : (iLeftSibling, iChild, iRightSibling) for offset, (iLeftSibling, iChild, iRightSibling) in filtered}

    # build the directory, line them up, pack them together into an index.
    new_directory_layout = [directory[index].copy() for index in sorted(old_directory_table)]
    new_directory_entries = {entry.getoffset() : index for index, entry in enumerate(new_directory_layout)}

    iterable = (directory[index] for index in old_directory_table)
    new_directory_index = {new_directory_entries[entry.getoffset()] : old_directory_entries[entry.getoffset()] for entry in iterable}

    # now we can go through and update each entry in the index.
    for offset, iTreeNodeOffsets in new_directory_table.items():
        entry_index = new_directory_entries[offset]
        entry = new_directory_layout[entry_index]
        [iLeft, iChild, iRight] = (None if iOffset is None else new_directory_entries[iOffset] for iOffset in iTreeNodeOffsets)
        entry['iLeftSibling'].set('NOSTREAM' if iLeft is None else iLeft)
        entry['iChild'].set('NOSTREAM' if iChild is None else iChild)
        entry['iRightSibling'].set('NOSTREAM' if iRight is None else iRight)

    # that should've setup the new_directory list and we only need to save it to the document.
    new_directory = store.Directory()
    for index, entry in enumerate(new_directory):
        entry.a
        original = new_directory_layout[index] if index < len(new_directory_layout) else entry
        [ entry[field].set(original[field].get()) for field in original ]
        entry.c
    new_directory.c

    # now we can iterate through all of the fat directory entries.
    for nindex, entry in enumerate(new_directory):
        oindex = new_directory_index[nindex] if nindex in new_directory_index else 'badindex'
        if oindex in directoryentries_fat:
            logger.warning("Processing entry {:d} ({:d}): {}".format(nindex, oindex, entry))
            oldchain = directoryentries_fat[oindex]
            newchain = [sidx + counter for counter, _ in enumerate(oldchain)]
            sidx += len(newchain)

            logger.warning("Linking {:d} sector{:s} ({:s})...".format(len(newchain), '' if len(newchain) == 1 else 's', ', '.join(map("{:d}".format, newchain))))
            [newfat[idx].c for idx in newfat.link(newchain)]
            #[world[oidx].commit(offset=store['Data'][nidx].getoffset(), source=store['Data'].source) for oidx, nidx in zip(oldchain, newchain)]
            [store['Data'][nidx].set(world[oidx].get()).c for oidx, nidx in zip(oldchain, newchain)]

            entry['sectLocation'].set(newchain[0] if newchain else 'ENDOFCHAIN').c
        continue

    # next we need to deal with the minifat and the ministream.
    with ModifyMiniFat(store) as (old, new):
        while old: old.pop()
        [ new.append(sidx + counter) for counter in range(new_minifat_sectors) ]
        sidx += len(new)

    oldchain = ministream_chain
    newchain = [sidx + counter for counter in range(new_ministream_sectors)]
    sidx += len(newchain)

    [newfat[idx].c for idx in newfat.link(newchain)]
    new_directory.root['sectLocation'].set(newchain[0] if newchain else 'ENDOFCHAIN').c
    new_directory.root['qwSize'].set(len(newchain) * newfat.sectorSize())
    updated_minifat_sectors = newchain

    # now we can fetch both of them so that they can be populated.
    newminifat = store.MiniFat().a
    newministream = new_directory.root.Data(None, clamp=False)

    # now we can iterate through all of the minifat directory entries.
    midx = 0
    for nindex, entry in enumerate(new_directory):
        oindex = new_directory_index[nindex] if nindex in new_directory_index else 'badindex'
        if oindex in directoryentries_mfat:
            logger.warning("Processing entry {:d} ({:d}): {}".format(nindex, oindex, entry))
            oldchain = directoryentries_mfat[oindex]
            newchain = [midx + counter for counter, _ in enumerate(oldchain)]
            midx += len(newchain)

            logger.warning("Linking {:d} minisector{:s} ({:s})...".format(len(newchain), '' if len(newchain) == 1 else 's', ', '.join(map("{:d}".format, newchain))))
            [newminifat[idx].c for idx in newminifat.link(newchain)]
            #[ministream[oidx].commit(offset=newministream[nidx].getoffset(), source=newministream.source) for oidx, nidx in zip(oldchain, newchain)]
            [newministream[nidx].set(ministream[oidx].get()).c for oidx, nidx in zip(oldchain, newchain)]

            entry['sectLocation'].set(newchain[0] if newchain else 'ENDOFCHAIN').c
        continue

    # write the entire directory that we messed with.
    new_directory.c

    # now we can zero the rest of the ministream sectors and the file sectors.
    indices = [idx for idx in range(midx, len(newministream))]
    logger.warning("Clearing {:d} minisector{:s} ({:s})...".format(len(indices), '' if len(indices) == 1 else 's', ', '.join(map("{:d}".format, indices))))
    [ newministream[index].a.c for index in range(midx, len(newministream)) ]

    indices = [idx for idx in range(sidx, len(store['Data']))]
    logger.warning("Clearing {:d} filesector{:s} ({:s})...".format(len(indices), '' if len(indices) == 1 else 's', ', '.join(map("{:d}".format, indices))))
    [ store['Data'][index].a.c for index in range(sidx, len(store['Data'])) ]

    logger.info('')

    # now we just need to reload all of our sectors, reset the document,
    # compare the contents for all of the streams that we just modified.
    count = sum(map(len, [updated_directory_sectors, updated_fat_sectors, updated_minifat_sectors, updated_difat_sectors])) + sum(map(len, directoryentries_fat.values()))
    logger.warning("Reloading all sectors ({:d}) that have been modified prior to verifying {:d} stream{:s} from {:s}.".format(count, len(new_directory_index), '' if len(new_directory_index) == 1 else 's', new_directory.instance()))
    [ store['Data'][nidx].l for nidx in itertools.chain(updated_directory_sectors, updated_fat_sectors, updated_minifat_sectors, updated_difat_sectors, *directoryentries_fat.values()) ]
    store.value = [item for item in store.value]

    for nindex, newentry in enumerate(new_directory):
        if nindex not in new_directory_index:
            continue
        oindex = new_directory_index[nindex]
        oldentry = directory[oindex]

        new = newentry.Data(None, clamp=False)
        if oindex in directoryentries_fat:
            old = [world[sidx] for sidx in directoryentries_fat[oindex]]
        elif oindex in directoryentries_mfat:
            old = [ministream[midx] for midx in directoryentries_mfat[oindex]]
        else:
            newentry['Type']['Root'] and logger.warning("Skipping directory entry {:d} due to being of type {:s}.".format(nindex, newentry['Type']))
            not newentry['Type']['Root'] and logger.warning("Unable to compare new directory entry {:d} with old directory entry {:d} of type {:s}.".format(nindex, oindex, newentry['Type']))
            continue
        osize, nsize = (entry['qwSize'].int() for entry in [oldentry, newentry])

        old_clamped, new_clamped = b''.join(item.serialize() for item in old)[:osize], new.serialize()[:nsize]
        if old_clamped == new_clamped:
            logger.info("Directory entry {:d} ({:d} byte{:s}) matches old directory entry {:d} ({:d} byte{:s}) of type {:s} : {:#s}".format(nindex, len(new_clamped), '' if len(new_clamped) == 1 else 's', oindex, len(old_clamped), '' if len(old_clamped) == 1 else 's', newentry['Type'], newentry['Name']))
        else:
            logger.warning("Directory entry {:d} ({:d} byte{:s}) does not match old directory entry {:d} ({:d} byte{:s}) of type : {:#s}".format(nindex, len(new_clamped), '' if len(new_clamped) == 1 else 's', oindex, len(old_clamped), '' if len(old_clamped) == 1 else 's', newentry['Type'], newentry['Name']))
        continue

    logger.info('')
    logger.info("Defragmentation complete!")
    logger.info("Original number of filesectors was {:d} sector{:s} ({:d} byte{:s}).".format(len(store['Data']), '' if len(store['Data']) == 1 else 's', store['Data'].size(), '' if store['Data'].size() == 1 else 's'))
    logger.info("Original number of minisectors was {:d} minisector{:s} ({:d} byte{:s}).".format(len(ministream), '' if len(ministream) == 1 else 's', ministream.size(), '' if ministream.size() == 1 else 's'))
    logger.info('')
    logger.info('Original file allocation tables:')
    logger.info("{}".format(fat))
    logger.info("{}".format(mfat))

    logger.info('')
    logger.info("Defragmented number of filesectors is {:d} sector{:s} ({:d} byte{:s}).".format(sidx, '' if sidx == 1 else 's', newfat.streamSize(sidx), '' if newfat.streamSize(sidx) == 1 else 's'))
    logger.info("Defragmented number of minisectors is {:d} minisector{:s} ({:d} byte{:s}).".format(len(newministream), '' if len(newministream) == 1 else 's', newministream.size(), '' if newministream.size() == 1 else 's'))
    logger.info('')
    logger.info('Defragmented file allocation tables:')
    logger.info("{}".format(newfat))
    logger.info("{}".format(newminifat))

elif __name__.upper() == 'TELEFRAG':
    import random
    state = random.Random()

    # find the sectors we shouldn't modify
    ignore = {sector.int() for sector in difat.iterate()}

    # build a table that we can consume sectors from.
    table = {index for index in range(len(world))} - ignore
    shuffled = sorted(table)
    state.shuffle(shuffled)
    take = lambda count, table=shuffled: [item.pop() for item in [table] * count]

    # grab the sectors for the directory, minifat, and directory entries (fat).
    dirsectors = store.chain(store['fat']['sectDirectory'].int())
    mfsectors = store.chain(store['minifat']['sectMiniFat'].int())

    directoryentries = {}
    for index, entry in enumerate(directory):
        if entry['Type']['Unknown']: continue
        if entry.streamQ():
            directoryentries[index] = store.chain(entry['sectLocation'].int())
        continue

    # now we collect all the sectors that we're going to use.
    newdirsectors = take(len(dirsectors))
    newmfsectors = take(len(mfsectors))
    newdirectoryentries = {index : take(len(sectors)) for index, sectors in directoryentries.items()}
    unused = take(len(shuffled))

    # then we'll write contents from the original sector to the new location.
    for old, new in zip(dirsectors, newdirsectors):
        world[old].commit(offset=locations[new])

    for old, new in zip(mfsectors, newmfsectors):
        world[old].commit(offset=locations[new])

    for index in directoryentries:
        oldchain, newchain = directoryentries[index], newdirectoryentries[index]
        for old, new in zip(oldchain, newchain):
            world[old].commit(offset=locations[new])
        continue

    # check that sectors have been committed in their shuffled order
    for old, new in zip(dirsectors, newdirsectors):
        item = world[old].copy(offset=locations[new])
        assert(world[old].serialize() == item.serialize() == item.l.serialize())

    for old, new in zip(mfsectors, newmfsectors):
        item = world[old].copy(offset=locations[new])
        assert(world[old].serialize() == item.serialize() == item.l.serialize())

    for index in directoryentries:
        oldchain, newchain = directoryentries[index], newdirectoryentries[index]
        for old, new in zip(oldchain, newchain):
            item = world[old].copy(offset=locations[new])
            assert(world[old].serialize() == item.serialize() == item.l.serialize())
        continue

    # now we need to update the fat and update their entrypoints.
    uncommitted = fat.link(newdirsectors)
    store['fat']['sectDirectory'].set(uncommitted[0] if uncommitted else 'FREESECT').c
    assert([index for index in fat.chain(store['fat']['sectDirectory'].int())] == uncommitted)
    assert(all(index not in unused for index in uncommitted))
    [fat[index].c for index in uncommitted]

    directory.source = ptypes.provider.disorderly([world[index].copy().l for index in uncommitted], autocommit={})

    uncommitted = fat.link(newmfsectors)
    store['minifat']['sectMiniFat'].set(uncommitted[0] if uncommitted else 'FREESECT').c
    assert([index for index in fat.chain(store['minifat']['sectMiniFat'].int())] == uncommitted)
    assert(all(index not in unused for index in uncommitted))
    [fat[index].c for index in uncommitted]

    for index in directoryentries:
        entry, newchain = directory[index], newdirectoryentries[index]
        uncommitted = fat.link(newchain)
        entry['sectLocation'].set(uncommitted[0] if uncommitted else 'FREESECT').c
        assert([index for index in fat.chain(entry['sectLocation'].int())] == uncommitted)
        assert(all(index not in unused for index in uncommitted))
        [fat[index].c for index in uncommitted]

    # last step is to clear the free sectors.
    [fat[index].set('FREESECT').c for index in unused]

    # and also overwrite them with garbage.
    size = store['SectorShift'].SectorSize()
    for index in unused:
        samples = map(state.getrandbits, [8] * size)
        block = ptype.block().set(bytearray(samples))
        block.commit(source=source, offset=locations[index])

    # reload the directory and the minifat using the data we fixed up.
    store = store.l
    mfat = store.MiniFat()
    directory = store.Directory()
    assert(item.serialize() == world[index].serialize() for index, item in zip(newdirsectors, directory.source.contiguous))

    # now we can do a good job screwing up the minifat.
    tinystream = directory.RootEntry().Data(None)
    smallworld = [sector for sector in tinystream]
    locations = {index : sector.getoffset() for index, sector in enumerate(smallworld)}

    directoryentries = {}
    for index, entry in enumerate(directory):
        if entry['Type']['Unknown']: continue
        if entry.ministreamQ():
            directoryentries[index] = store.minichain(entry['sectLocation'].int())
        continue

    # build a (tiny) table that we can consume sectors from.
    table = {index for index in range(len(smallworld))}
    tinyshuffle = sorted(table)
    state.shuffle(tinyshuffle)
    take = lambda count, table=tinyshuffle: [item.pop() for item in [table] * count]

    # collect the new sector indices for each directory entry.
    newdirectoryentries = {index : take(len(sectors)) for index, sectors in directoryentries.items()}
    unused = take(len(tinyshuffle))

    # move the old minisectors to their new location.
    for index in directoryentries:
        oldchain, newchain = directoryentries[index], newdirectoryentries[index]
        for old, new in zip(oldchain, newchain):
            smallworld[old].commit(offset=locations[new])
        continue

    # verify that the minisectors have the expected data.
    for index in directoryentries:
        oldchain, newchain = directoryentries[index], newdirectoryentries[index]
        for old, new in zip(oldchain, newchain):
            item = smallworld[old].copy(offset=locations[new])
            assert(smallworld[old].serialize() == item.serialize() == item.l.serialize())
        continue

    # final thing to do is to update the minifat and fix the directory entrypoints.
    for index in directoryentries:
        entry, newchain = directory[index], newdirectoryentries[index]
        uncommitted = mfat.link(newchain)
        entry['sectLocation'].set(uncommitted[0] if uncommitted else 'FREESECT').c
        assert([index for index in mfat.chain(entry['sectLocation'].int())] == uncommitted)
        assert(all(index not in unused for index in uncommitted))
        [mfat[index].c for index in uncommitted]

    # then we clean up for clearing the free sectors and overwriting them w/ garbage.
    [mfat[index].set('FREESECT').c for index in unused]

    size = store['SectorShift'].MiniSectorSize()
    for index in unused:
        samples = map(state.getrandbits, [8] * size)
        block = ptype.block().set(bytearray(samples))
        block.commit(source=tinystream.source, offset=locations[index])

    # we're done, so we just close everything and let the i/o cache do its thing.
    source.close()

elif __name__.split('.')[0] != __package__:
    import sys
    print("Usage: {:s} FILE [defrag|telefrag]".format(sys.argv[0] if sys.argv else __file__))
