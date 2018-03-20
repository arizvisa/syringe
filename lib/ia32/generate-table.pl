#!/usr/bin/perl
use XML::Simple;
use Data::Dumper;
use Getopt::ArgParse;

use strict; use warnings;

local $/=undef;

## parse out command line arguments using damian conway's genius..
my $ap = Getopt::ArgParse->new_parser(
    description => "Generate an opcode table for determining instruction lengths.",
    print_usage_if_help => 1,
);
$ap->add_arg("--input", "-f",
    dest=>'infile',
    metavar=>'INFILE',
    default=>'-',
    help=>"the file containing the operand table .xml file.",
);
$ap->add_arg("--output", "-o",
    dest=>'outfile',
    metavar=>'OUTFILE',
    default=>'-',
    help=>"the file to write the generated contents.",
);
$ap->add_arg("--format",
    dest=>'format',
    choices_i=>['perl', 'python', 'javascript', 'c', 'shell'],
    default=>'python',
    required=>1,
    help=>"the format to output the table in.",
);
$ap->add_arg("--name", "-n",
    dest=>'name',
    metavar=>'NAME',
    help=>"the name of the table to output if the requsted format needs it.",
);

die $ap->print_usage() if !@ARGV;
my $args = $ap->parse_args(@ARGV);

## Figure out which file to read from
my $infile;
if ($args->infile eq "-") {
    print STDERR "Reading from standard input...\n";
    $infile = *STDIN;
} else {
    open($infile, '<', $args->infile) ||
        die sprintf("Unable to open file %s for reading: %s", $args->infile, $!);
    print STDERR sprintf("Reading from %s...\n", $args->infile);
}

## Figure out which file to write to
my $outfile;
if ($args->outfile eq "-") {
    $outfile = *STDOUT;
} else {
    open($outfile, '>', $args->outfile) ||
        die sprintf("Unable to open file %s for writing: %s", $args->outfile, $!);
    print STDERR sprintf("Writing to %s...\n", $args->outfile);
}

## parse xml file
my $prefixes = "\x26\x2e\x36\x3e\x64\x65\x66\x67\xf0\xf2\xf3";
my $ref = XMLin(<$infile>, ForceArray => ['operand'])->{instruction};

## create opcode list
my @opcodes = map {undef} 0..0x1ff;

## assign to opcode list
foreach my $rec (@{$ref}) {
    my $value = $rec->{value};

    if (defined $opcodes[$value]) {
        print STDERR sprintf("[%x] %s previously defined as %s\n", $value, $rec->{mnemonic}, $opcodes[$value]->{mnemonic});
        next;
    }
    $opcodes[$value] = $rec;
}

## convert operand-size to a single byte representation
sub makeSize {
    my ($value) = @_;

    my %lookup = (
        ops_2opword => 0x40-1,
        ops_opbyte => 0x40-2,
        ops_opword => 0x40-3,
        ops_opdword => 0x40-4,
        ops_opqword => 0x40-5,
        ops_opfarpointer => 0x40-6,
        ops_ropdword => 0x40-7,
    );

    local $_;

    # check for inconsistencies     (this code being written whilst also being
    #     logically flawed, but i can't think of how to solve this right now...)
    my $match = $value;
#    foreach $_ (@value) {
#        if ($_ ne $match) {
#            die "$_ != $match";
#        }
#    }
    return $lookup{$value} || int($value);
}

## convert operand-type to a single byte
sub makeType {
    my ($type) = @_;
    my $res = 0;

    my %lookup = (
        IMM => 1,
        MODRM => 2
    );

    $res |= $lookup{$type} || 0;
    return $res;
}

## XXX: build the final operand given a list of operands
sub makeOperand {
    my ($operand) = @_;
    my $result;
    my %operand = %{$operand};

    my %lookup = (
        IMM => 1,
        MODRM => 2
    );

    my ($size, $type) = (0, 0);

    ## collect flags and size
    # XXX: might be best to check to see if a size is defined twice
    foreach my $k (keys %operand) {
        if ($k eq 'IMM') {
            $type |= $lookup{IMM};
            $size = makeSize($operand{IMM});

        } elsif ($k eq 'MODRM') {
            $type |= $lookup{MODRM};
            $size = makeSize($operand{MODRM}) if ($size == 0);
        }
    }

    $size &= 0x3f;
    $type &= 0x03;

    return ($type << 6) | $size;
}

## hexdump
sub hdump {
    my $offset = 0;
    my(@array,$format);
    foreach my $data (unpack("a16"x(length($_[0])/16)."a*",$_[0])) {
        my($len)=length($data);
        if ($len == 16) {
            @array = unpack('N4', $data);
            $format="0x%08x (%05d)   %08x %08x %08x %08x   %s\n";
        } else {
            @array = unpack('C*', $data);
            $_ = sprintf "%2.2x", $_ for @array;
            push(@array, '  ') while $len++ < 16;
            $format="0x%08x (%05d)" .
               "   %s%s%s%s %s%s%s%s %s%s%s%s %s%s%s%s   %s\n";
        }
        $data =~ tr/\0-\37\177-\377/./;
        printf $format,$offset,$offset,@array,$data;
        $offset += 16;
    }
}

## shift some arbitrary number of elements out of an array reference
sub shiftout {
    my ($size, $refarray) = @_;
    local $_ = shift @{$refarray};
    if ($size > 1 && @{$refarray}) {
        my @result = shiftout($size - 1, $refarray);
        return ($_, @result);
    }
    return $_;
}

## group $size elements of an array
sub chunkArray {
    my ($size, @array) = @_;
    my (@result);

    while (@array) {
        local @_ = shiftout($size, \@array);
        push @result, [@_];
    }
    return @result;
}

## return an array of all operands merged together (MODRM+IMM should be merged)
sub mergeOperand {
    my (@operands) = @_;
    local $_;

    my %result;
    foreach $_ (@operands) {
        my ($type,$size) = ($_->{type}, $_->{size});
        next if (ref($type) eq 'HASH');

        if (($type ne 'IMM') && ($type ne 'MODRM')) {
            die "Unknown operand type: $type";
        }
        $result{$type} = $size;
    }
    return (\%result);
}

## check if opcode is a prefix, and if an opcode is undefined, display an error
for (my $index=0; $index < @opcodes; $index++) {
    my $value = $opcodes[$index]->{value};
    if ( index($prefixes, chr($index)) == -1 and !defined $value) {
        #print STDERR sprintf("[%x] is undefined\n", $index);
    }
}

## generate table
# XXX: somehow, this table isn't being generated properly
my @result;
for (my $op=0; $op < @opcodes; $op++) {
    $result[$op] = 0;

    my $instruction = $opcodes[$op];

    my $operand = mergeOperand(@{$instruction->{operand}});
    $operand = makeOperand($operand);
#    print hex($op) . "\n" . sprintf('%2x', $operand) . "\n";
#    exit;
    $result[$op] = $operand;
}

## XXX: hardcode specific opcodes because they're not defined in the xml ref
$opcodes[0x10f] = "\xc1";       # 3dNow! -> \x0f\x0f modrm imm1

############################
if (0) {
    my $string = join("", map{chr}@result);
    print "$string";
}

############################
my $name = $args->name || "OperandLookupTable";
if (lc $args->format eq "python") {
    my $string = join("", map{chr}@result);
    print $outfile "$name = ''.join([\n";

    for (my $i=0; $i<length($string); $i+=0x10) {
        my $s = substr($string, $i, 0x10);

        print $outfile "    \"";
        for (my $n = 0; $n < length($s); $n++) {
            my $c = substr($s, $n, 1);
            printf $outfile ("\\x%02x",ord($c) & 0xff);
        }
        print $outfile "\"\n";
    }
    print $outfile "])\n";

} elsif (lc $args->format eq "c") {
    my $group=0x10;
    @_ = map { sprintf("0x%02x", $_) } @result;
    @_ = chunkArray($group, @_);
    my $row=0;
    @_ = map { sprintf("/*%02X*/ %s", ($row++)*$group, join(",", @{$_})); } @_;
    my $array = join(",\n", @_);

    print $outfile "#include <stdint.h>\n\n";
    print $outfile "const uint8_t $name\[] = {\n";
    print $outfile "$array\n";
    print $outfile "};";
} elsif (lc $args->format eq "perl") {
    my $string = join("", map{chr}@result);
    print $outfile "package $name;\n";
    print $outfile "use strict; use warnings;\n";
    print $outfile "\n";
    print $outfile 'use vars qw(@EXPORT_OK @Table);'."\n";
    print $outfile "\n";
    print $outfile 'our @EXPORT_OK = (@Table);'."\n";
    

    print $outfile 'my @Table = ('."\n";
    for (my $i=0; $i<length($string); $i+=0x10) {
        my $s = substr($string, $i, 0x10);

        print $outfile "    ";
        for (my $n = 0; $n < length($s); $n++) {
            my $c = substr($s, $n, 1);
            printf $outfile ("0x%02x, ",ord($c) & 0xff);
        }
        print $outfile "\n";
    }
    print $outfile ");\n";
} elsif (lc $args->format eq "shell") {
    for (my $i=0; $i<@result; $i++) {
        print $outfile "$result[$i]\n";
    }
} elsif (lc $args->format eq "javascript" || lc $args eq "js") {
    print $outfile "module.exports['$name'] = [\n";
    for (my $i=0; $i<@result; $i+=0x10) {
        my @slice = @result[$i..$i+0x10];
        print $outfile "    ";
        for (my $j=0; $j<scalar(@slice)-1; $j++) {
            printf $outfile ("0x%02x, ", $slice[$j] & 0xff);
        }
        print $outfile "\n";
    }
    print $outfile "];\n";
    print $outfile "module.exports[null] = module.exports['$name'];\n";
} else {
    die sprintf("Unknown format: %s", $args->format);
}

