#!/usr/bin/perl
use XML::Simple;
use Data::Dumper;

use strict; use warnings;

my $prefixes = "\x26\x2e\x36\x3e\x64\x65\x66\x67\xf0\xf2\xf3";
local $/=undef;
my $xml = <STDIN>;
my $ref = XMLin($xml, ForceArray => ['operand'])->{instruction};

my @array;
foreach my $rec (@{$ref}) {
    my $value = int($rec->{value});

    if (defined $array[$value]) {
        print STDERR sprintf("[%x] %s previously defined as %s\n", $value, $rec->{mnemonic}, $array[$value]->{mnemonic});
        next;
    }
    $array[$value] = $rec;
}

foreach my $index (0..$#array) {
    my $value = $array[$index];
    if ( index($prefixes, chr($index)) == -1 and !defined $value) {
        print STDERR sprintf("[%x] is undefined\n", $index);
    }
}

#######
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
    return $lookup{$value} || int($value);
}

sub makeOperand {
    my ($operands) = @_;
    my $res = 0;

    foreach my $value (@{$operands}) {
        my %lookup = (
            IMM => 1,
            MODRM => 2
        );
        $res |= $lookup{$value} || 0;
    }
    return $res;
}

sub makeNumber {
    my ($operand, $size) = @_;

    if (ref($operand) eq 'HASH') { $operand = 0; }
    if (ref($size) eq 'HASH') { $size = 0; }

    $size = makeSize($size);
    $size &= 0x3f;
    $operand = makeOperand($operand);
    $operand &= 0x03;
    
    return ($operand << 6) | $size;
}

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

@array = map {{}} 0..0x1ff;
foreach $_ (@{$ref}) {
    my $value = int($_->{value});
    $array[$value] = $_;
}

sub shiftout {
    my ($size, $array) = @_;
    local $_ = shift @{$array};
    if ($size > 1 && @array) {
        my @result = shiftout($size - 1, $array);
        return ($_, @result);
    }
    return $_;
}

sub chunkArray {
    my ($size, @array) = @_;
    my (@result);

    while (@array) {
        local @_ = shiftout($size, \@array);
        push @result, [@_];
    }
    return @result;
}

@_ = @array;
@_ = map { makeNumber($_->{operand} || [], $_->{size} || 0) } @_;
#@_ = map { chr($_) } @_;
#print hdump(join("", @_));

my $group=0x10;

@_ = map { sprintf("0x%02x", $_) } @_;
@_ = chunkArray($group, @_);
my $row=0;
@_ = map { sprintf("/*%02X*/ %s", ($row++)*$group, join(",", @{$_})); } @_;
$_ = join(",\n", @_);

print <<EOF
#include "types.h"

byte OperandLookupTable[] = {
$_
};
EOF
