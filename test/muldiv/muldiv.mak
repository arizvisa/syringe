## binaries
NASM=yasm.exe
LINK=${VCBIN}/link.exe
CL=${VCBIN}/cl.exe

## visual C
VCINSTALLDIR=C:/Program Files (x86)/Microsoft Visual Studio 10.0/VC
VCINC=${VCINSTALLDIR}/include
VCLIB=${VCINSTALLDIR}/lib/amd64
VCBIN=${VCINSTALLDIR}/bin

## windows
WINSDKDIR=C:/Program Files (x86)/Microsoft SDKs/Windows/v7.0A
WINSDKINC=${WINSDKDIR}/Include
WINSDKLIB=${WINSDKDIR}/Lib/x64
WINSDKBIN=${WINSDKDIR}/Bin

## globals
INCLUDE="${VCINC};${WINSDKINC}"
LIBPATH="${VCLIB};${WINSDKLIB}"

CFLAGS=-EHsc -DDEBUG
LDFLAGS=-SUBSYSTEM:CONSOLE -LARGEADDRESSAWARE:NO
LIBS="msvcrt.lib"

pathsep := \\

%.obj: %.c
	@echo "${CL}" -TC -nologo -c ${CFLAGS} -Fo$(subst /,$(pathsep),$@) $<
	@INCLUDE=${INCLUDE} "${CL}" -TC -nologo -c ${CFLAGS} -Fo$(subst /,$(pathsep),$@) $<

%.obj: %.cc
	@echo "${CL}" -TP -nologo -c ${CFLAGS} -Fo$(subst /,$(pathsep),$@) $<
	@INCLUDE=${INCLUDE} "${CL}" -TP -nologo -c ${CFLAGS} -Yuprecompiled.h -FI precompiled.h -Fo$(subst /,$(pathsep),$@) $<

%.obj: %.asm
	${NASM} -fwin64 -o $@ $<

%.exe:
	@echo "${LINK}" -nologo ${LDFLAGS} -OUT:$(subst /,$(pathsep),$@) $^ ${LIBS}
	@LIB=${LIBPATH} "${LINK}" -nologo ${LDFLAGS} -OUT:$(subst /,$(pathsep),$@) $^ ${LIBS}

all: muldiv.exe

muldiv.exe: muldiv.obj
muldiv.obj: muldiv.asm
