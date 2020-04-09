import functools, itertools, types, builtins, operator, six
import ptypes, pecoff
import ptypes.bitmap as bitmap

import sys, logging, array

if sys.version_info.major < 3:
    import collections
    MutableMapping = collections.MutableMapping
else:
    import collections.abc
    MutableMapping = collections.abc.MutableMapping

def get(object, attribute):
    return getattr(object, "_LinkerInternal__{:s}".format(attribute))

class DictionaryBase(MutableMapping):
    def __init__(self, *args, **kwargs):
        self.__mapping__ = {}
        self.update(*args, **kwargs)

    def __iter__(self):
        return iter(self.__mapping__)
    def __getitem__(self, key):
        return self.__mapping__[key]
    def __setitem__(self, key, value):
        self.__mapping__[key] = value
    def __delitem__(self, key):
        del self.__mapping__[key]
    def __len__(self):
        res = [ key for key in self ]
        return len(res)
    def viewkeys(self):
        return { key for key in self }
    def viewvalues(self):
        return { self[key] for key in self }
    def viewitems(self):
        return { (key, self[key]) for key in self }
    def __repr__(self):
        res = { key : self[key] for key in self }
        return "{!s}".format(res)

class LinkerInternal(DictionaryBase):
    '''
    manage all of the symbols required to apply relocations to a section
    '''
    def __init__(self):
        super(LinkerInternal, self).__init__()

        self.__relocations = {}
        self.__symbols = {}

        self.__cache = {}
        self.__undefined = {}
        self.__names = {}

        self.__defined = {}

    @classmethod
    def apply(cls, segment, segmentbase, relocation, symbolbase, symbolvalue):
        offset, type = relocation['VirtualAddress'].int(), relocation['Type']
        if type['REL32']:
            res = reduce(lambda agg, by: agg * 0x100 + by, reversed(segment[offset : offset + 4]))
            res += (symbolbase + symbolvalue) - (segmentbase + offset + 4)
            data = [(res & (0x100 ** octet * 0xff)) // 0x100 ** octet for octet in range(4)]
        elif type['ADDR32NB']:
            res = reduce(lambda agg, by: agg * 0x100 + by, reversed(segment[offset : offset + 4]))
            res += (symbolbase + symbolvalue)
            data = [(res & (0x100 ** octet * 0xff)) // 0x100 ** octet for octet in range(4)]
        elif type['ADDR32']:
            raise TypeError(type)   # This would make the code non-relocatable
        elif type['DIR32NB']:
            raise TypeError(type)   # Untested..
            res = reduce(lambda agg, by: agg * 0x100 + by, reversed(segment[offset : offset + 4]))
            res += symbolvalue
        elif type['DIR32']:
            raise TypeError(type)   # This would make the code non-relocatable
        else:
            raise TypeError(type)
        segment[offset : offset + len(data)] = array.array('B', data)
        return segment

    @classmethod
    def location(cls, section, value=None):

        if section is None:
            fmt = "<external>{:s}".format
        else:
            filename = section.source.file.name
            fmt = functools.partial("{:s}#{:s}{:s}".format, filename, section.name())
        return fmt('') if value is None else fmt("{:+#x}".format(value))

    def __iter__(self):
        for name in reduce(operator.or_, map(six.viewkeys, (self.__undefined, self.__defined))):
            yield name
        return

    def __getitem__(self, name):
        if name in self.__defined:
            return self.__defined[name]
        return super(LinkerInternal, self).__getitem__(name)

    def __setitem__(self, name, value):
        if name in self.__undefined:
            return super(LinkerInternal, self).__setitem__(name, value)
        raise KeyError(name)

    def __cache_symbol(self, section, symbol):
        '''cache the symbol associated with the specified section'''
        name, undefined = symbol.Name(), symbol['SectionNumber']['UNDEFINED']

        # If the symbol was already cached, then determine whether we're updating
        # it or not
        if symbol in self.__cache:
            res, value = self.__cache[symbol]

            # If the symbol has some undefined references, then figure out what
            # method we'll need to use in order to update all of them
            if name in self.__undefined:

                # Our symbol is in the undefined list, but is defined somewhere
                if symbol in self.__undefined[name] and name in self.__names:
                    if value is not None:
                        raise AssertionError
                    logging.info("copying value ({:s}) to {:s} symbol {:s}".format(self.location(*self.__cache[self.__names[name]]), symbol['storageclass'].str(), name))
                    self.__cache[symbol] = self.__cache[self.__names[name]]
                    for item in self.__undefined.pop(name):
                        self.__cache[item] = self.__cache[symbol]

                # There actually are no defined values anywhere, so forget it
                elif symbol in self.__undefined[name]:
                    logging.debug("skipping still undefined {:s} symbol {:s}".format(symbol['storageclass'].str(), name))

                # We have a value, so simply do it
                elif not undefined:
                    logging.info("undefined {:s} symbol {:s} is being redefined to {:s}".format(symbol['storageclass'].str(), name, self.location(section, value)))
                    for item in self.__undefined.pop(name):
                        self.__cache[item] = section, value
                    pass

            # If the sections are different, then something here is up...
            if section and res is not section:
                raise ValueError("refusing to re-map {:s} symbol {:s} from {:s} to {:s}".format(symbol['storageclass'].str(), name, self.location(res, value), self.location(section, symbol['value'].int())))

            # If the value is undefined, then we can simply update it
            elif value is None:
                if undefined:
                    logging.debug("skipping already undefined {:s} symbol {:s}".format(symbol['storageclass'].str(), name))

                else:
                    logging.info("updating cached {:s} symbol {:s} with {:s}".format(symbol['storageclass'].str(), name, self.location(section, symbol['value'].int())))
                    self.__cache[symbol] = section, symbol['value'].int()
                    self.__names[name] = symbol

            # Just a catch-all for logs
            else:
                if undefined:
                    logging.debug("skipping {:s} symbol {:s} already cached as ({:s})".format(symbol['storageclass'].str(), name, self.location(res, value)))

                elif value != symbol['value'].int():
                    logging.fatal("refusing to assign value ({:s}) to cache for {:s} symbol {:s} with value ({:s})".format(self.location(section, symbol['value'].int()), symbol['storageclass'].str(), name, self.location(res, value)))

        # If it's undefined, then allow the user to modify it if they want
        elif undefined:
            if name in self.__undefined:
                logging.debug("adding duplicate undefined {:s} symbol {:s}".format(symbol['storageclass'].str(), name))
            else:
                logging.debug("adding new undefined {:s} symbol {:s}".format(symbol['storageclass'].str(), name))
            self.__cache[symbol] = (section, None)
            self.__undefined.setdefault(name, set()).add(symbol)
            self.setdefault(name, None)

        # If the symbol has been cached, but is undefined then fix all their references
        elif name in self.__undefined:
            logging.info("assigning {:s} symbol with value ({:s}) over undefined symbol {:s}".format(symbol['storageclass'].str(), self.location(section, symbol['value'].int()), name))
            self.__cache[symbol] = (section, symbol['value'].int())
            for item in self.__undefined.pop(name):
                self.__cache[item] = self.__cache[symbol]
            self.__names[name] = symbol

        # Otherwise, this is just a symbol being added so treat it as such
        else:
            if name in self.__names and symbol['storageclass']['EXTERNAL']:
                if self.__cache[self.__names[name]] == (None, None):
                    logging.info("overriding {:s} symbol {:s} with value {:s}".format(symbol['storageclass'].str(), name, self.location(section, symbol['value'].int())))
                else:
                    logging.warn("overriding duplicate {:s} symbol {:s} having value {:s} with value {:s}".format(symbol['storageclass'].str(), name, self.location(*self.__cache[self.__names[name]]), self.location(section, symbol['value'].int())))
            else:
                logging.debug("creating {:s} symbol {:s} with value {:s}".format(symbol['storageclass'].str(), name, self.location(section, symbol['value'].int())))
            self.__cache[symbol] = (section, symbol['value'].int())
            self.__names[name] = symbol
        return

    def add_symbol(self, section, symbol):
        '''add symbol defined by the specified section'''
        res = self.__symbols.setdefault(section, [])
        res.append(symbol)
        self.__cache_symbol(section, symbol)

    def add_relocation(self, section, relocation, symbol):
        '''add relocation contained by the specified section'''
        res = self.__relocations.setdefault(section, [])
        res.append((relocation, symbol))

    def required(self, section):
        '''return symbols required by the specified section'''
        results = []
        for relocation, symbol in self.__relocations.get(section, []):
            results.append(symbol)
        return results

    def symbols(self, section):
        '''return symbols defined by the specified section'''
        results = []
        for symbol in self.__symbols.get(section, []):
            results.append(symbol)
        return results

    def collect(self, symbol):
        '''collect all sections required for symbol to be rendered properly'''
        def gather(symbol, state):
            section = self.section(symbol)

            if section is None:
                logging.warn("Required {:s} symbol {:s} is undefined".format(symbol['storageclass'].str(), symbol.Name()))
                return
            elif section in state:
                return

            state.add(section)
            results.append(section)

            for symbol in self.required(section):
                gather(symbol, state)
            return
        results = []
        gather(symbol, set())
        return results

    def missing(self, section):
        '''return any symbols that are required to apply relocations to the section'''
        results = []
        for relocation, symbol in self.__relocations.get(section, []):
            res, value = self.__cache[symbol]
            if (res, value) == (None, None) and self[symbol.Name()] is None:
                logging.debug("user value for symbol {!s} is currently undefined: {:s}".format(symbol.Name(), symbol.summary()))
                results.append(symbol)
            elif res is not None and value is None:
                logging.warn("cache is missing a value ({!s}) for symbol {:s} belonging to relocation ({!r}): {:s}".format(value, symbol.Name(), relocation, symbol.summary()))
                results.append(symbol)
            continue
        return results

    def rebase(self, section, base):
        """rebase the symbols in the given section to the specified address

        this doesn't actually change anything but lets a user query the address
        of any symbols in a rebased section.
        """
        for symbol in self.missing(section):
            if symbol.Name() not in self.__defined:
                self.__defined[symbol.Name()] = None
            continue

        for symbol in self.__symbols[section]:
            _, offset = self.__cache[symbol]
            self.__defined[symbol.Name()] = base + offset
        return

    def relocate(self, section, data, segmentbases):
        '''apply relocations for the section to the given data using segmentbases to lookup the address of each segment'''
        if not isinstance(data, (bytes, array.array)):
            raise TypeError(data)

        segment = array.array('B', data)
        for relocation, symbol in self.__relocations.get(section, []):
            symbol_section, value = self.__cache[symbol]
            if symbol_section is None:
                base, res = 0x0, self[symbol.Name()]
            else:
                base, res = segmentbases[symbol_section], value
            segment = self.apply(segment, segmentbases[section], relocation, base, res)
        return segment

    def section(self, symbol):
        '''return the section containing the specified symbol'''
        res, _ = self.__cache[symbol]
        return res

    def symbol(self, name):
        """return the symbol for the specified name

        if the symbol is a duplicate (due to being local), then return the latest symbol
        """
        return self.__names[name]

    def dump(self):
        cls = self.__class__
        res = ["{!s}".format(cls)]
        for symbol in self.__cache:
            section, value = self.__cache[symbol]
            res.append("({:s}) {:s} {!s}".format(section and section['Name'].str(), symbol.Name(), None if value is None else "{:#x}".format(value)))
        return '\n'.join(res)

class Linker(object):
    def __init__(self):
        res = {'__iter__', '__getitem__', '__setitem__', '__len__'}
        self.__forwarded__ = res | { name for name in dict.__dict__.keys() if not name.startswith('__') }
        self.__state__ = LinkerInternal()

        self.__segments = []

    @property
    def state(self):
        return self.__state__

    def __add_segment(self, section, segment):
        '''add segment data belonging to the specified section'''
        if not isinstance(segment, bytes):
            raise TypeError(segment)
        res = array.array('B', segment)
        self.__segments.append((section, res))

    def __process_relocations(self, section, sections, symbols):
        for relocation in section['pointertorelocations'].d.li:
            symbol = symbols[relocation['SymbolTableIndex'].int()]
            self.state.add_symbol(None if symbol.SectionIndex() is None else sections[symbol.SectionIndex()], symbol)
            self.state.add_relocation(section, relocation, symbol)
        return

    def __process_symbols(self, section, symbols):
        for symbol in symbols:
            self.state.add_symbol(section, symbol)
        return 

    def __process_section(self, object, section):
        res = object['header']['pointertosymboltable'].d.li
        symbols = { index : symbol for index, symbol in res['symbols'].enumerate() }
        sections = [ item for item in object['sections'] ]
        if section not in sections:
            raise ValueError
        iterable = (symbol for symbol in six.itervalues(symbols) if symbol.SectionIndex() is not None and section is sections[symbol.SectionIndex()] )
        self.__process_symbols(section, iterable)
        self.__process_relocations(section, sections, symbols)

    def __process_externals(self, object):
        res = object['header']['pointertosymboltable'].d.li
        iterable = (symbol for symbol, _ in res['symbols'].iterate() if symbol.SectionIndex() is None)
        for symbol in iterable:
            self.state.add_symbol(None, symbol)
        return

    def add(self, object):
        self.__process_externals(object)
        for section in object['sections']:
            self.__process_section(object, section)
        return

    def segment(self, section, align=''):
        res = section['pointertorawdata'].d
        data = '\0' * section['sizeofrawdata'].int() if section['characteristics']['CNT_UNINITIALIZED_DATA'] else res.li.serialize()
        alignment = 2 ** (section['characteristics']['ALIGN'] if align else 0)
        padding = (alignment - len(data) % alignment) & (alignment - 1)
        self.__add_segment(section, data + align * padding)

    def lookup(self, name):
        return self.state.symbol(name)

    def collect(self, symbols):
        sections = set()
        for symbol in symbols:
            sections.update(self.state.collect(symbol))
        return [ section for section in sections ]

    def render(self, address=0):
        available = [ section for section, _ in self.__segments ]
        return self.render_only(available, address)

    def render_only(self, sections, address=0):
        '''render all the specified segments linked together at the specified base address'''
        available = { section for section in sections }
        sections = [ (section, segment) for section, segment in self.__segments if section in available ] 

        segmentbases = {}
        for section, segment in sections:
            missing = self.state.missing(section)
            if missing:
                for symbol in missing:
                    logging.warn("Linking section {!s} requires the symbol {:s} to be defined!".format(section.name(), symbol.Name()))
                raise ValueError("unable to link due to undefined symbols")
            segmentbases[section] = address
            address += len(segment)

        result = array.array('B')
        for section, segment in sections:
            segment = self.state.relocate(section, segment, segmentbases)
            result.extend(segment)

        for section, _ in sections:
            self.state.rebase(section, segmentbases[section])
        return result

    def simulate(self, address=0):
        available = { section for section, _ in self.__segments }
        return self.simulate_only(available, address)

    def simulate_only(self, sections, address=0):
        '''return a dictionary containing all symbols and their addresses as if all segments were linked'''
        available = { section for section in sections }
        sections = [ (section, segment) for section, segment in self.__segments if section in available ] 

        segmentbases = {}
        for section, segment in sections:
            segmentbases[section] = address
            address += len(segment)

        for section, _ in sections:
            self.state.rebase(section, segmentbases[section])
        return

    def __getattr__(self, name):
        if name in self.__forwarded__:
            return object.__getattribute__(self.state, name)
        raise AttributeError(name)

    def __iter__(self):
        for item in self.state:
            yield item
        return
    def __len__(self):
        return len(self.state)
    def __getitem__(self, key):
        return self.state[key]
    def __setitem__(self, key, value):
        self.state[key] = value

if __name__ == '__main__':
    import sys, os, argparse

    def integral(arg):
        if arg.startswith('0x'):
            return int(arg, 16)
        elif arg.startswith('0o'):
            return int(arg, 8)
        elif any(arg.startswith(prefix) for prefix in ['0y', '0b']):
            return int(arg[2:], 2)
        return int(arg, 10)

    def symbol(arg):
        if arg.count('=') != 1:
            raise RuntimeError("Invalid format for symbol: {!s}".format(arg))
        name, value = arg.split('=', 2)
        return name, integral(value)

    parser = argparse.ArgumentParser(description='link some pecoff objects together whilst allowing duplicate symbols (order preserved)')
    parser.add_argument('infile', metavar='COFF', nargs='+', type=argparse.FileType('rb'), help='a PECOFF object file')
    parser.add_argument('-o', '--outfile', metavar='FILENAME', type=argparse.FileType('wb'), default='-', help='a filename to emit the linked result to')
    parser.add_argument('-n', '--no-link', dest='link', action='store_false', default=True, help='simulate linking instead of writing the file')
    parser.add_argument('-u', '--dump-undefined', dest='dump', action='store_const', default=0, const=1, help='dump all undefined symbols required to be linked')
    parser.add_argument('-d', '--dump-all', dest='dump', action='store_const', const=2, help='dump all resolved symbols after being linked')
    parser.add_argument('-D', '--define', dest='symbols', type=symbol, action='append', default=[], help='define the specified symbol')
    parser.add_argument('-s', '--only', dest='only', type=str, action='append', default=[], help='only use the specified symbols and the symbols they depend on')
    parser.add_argument('-f', '--force', action='store_true', help='force linking despite symbols being undefined')
    parser.add_argument('--base-address', dest='address', metavar='ADDRESS', type=lambda arg: int(arg, 16), default=0x0, help='the base address for the entire result')
    Args = parser.parse_args()

    logging.root.setLevel(logging.INFO)

    if sys.platform in {'win32'}:
        import msvcrt
        [ msvcrt.setmode(f.fileno(), os.O_BINARY) for f in Args.infile if f.isatty() ]

    self = Linker()
    cache = self.state._LinkerInternal__cache

    for infile in Args.infile:
        source = ptypes.prov.fileobj(infile)
        store = pecoff.Object.File(source=source).l
        self.add(store)

        discardable = {'LNK_REMOVE','MEM_DISCARDABLE'}
        for section in store['sections']:
            if any(section['characteristics'][characteristic] for characteristic in discardable):
                continue
            self.segment(section)
        source.close()

    for name, value in Args.symbols:
        self[name] = value

    undefined = { key for key in self if self[key] is None }

    if Args.link:
        if len(undefined) > 0:
            logging.warn("The following symbols are currently {:s}...".format('being redefined' if Args.force else 'undefined'))
            print('\n'.join("[{:d}] {:s}".format(1 + index, symbol) for index, symbol in enumerate(undefined)))
        else:
            logging.info('No undefined symbols were found!')

    if Args.force:
        for index, key in enumerate(undefined):
            self[key] = 0xffff0000 | (index << 4)

    if Args.only:
        symbols = []
        for name in Args.only:
            symbols.append(self.lookup(name))
        sections = self.collect(symbols)
        command = functools.partial(self.render_only, sections) if Args.link else functools.partial(self.simulate_only, sections)

    else:
        command = self.render if Args.link else self.simulate

    if Args.link:
        data = command(Args.address)
        logging.info("Writing {:d} bytes".format(len(data)))
        data.tofile(Args.outfile)
        Args.outfile.close()

    else:
        data = command(Args.address)

    if Args.dump:
        res = sorted(self.items(), key=operator.itemgetter(1)) if Args.dump >= 2 else sorted([(key, value) for key, value in self.iteritems() if key in undefined], key=operator.itemgetter(1))
        if res:
            for index, (key, value) in enumerate(res):
                print("[{:d}] {:s} {!s}".format(1 + index, key, '<undefined>' if value is None else "{:#x}".format(value)))
        else:
            logging.fatal('No symbols were found!')

    if not Args.link and not Args.dump:
        logging.fatal('Nothing to do!')

    sys.exit(0)
