include ../compile_opts/$(ENLIB_COMP).mk

all: nmat_core_32.so nmat_core_64.so

%.so: %.f90
	$(F2PY) --fcompiler=$(F2PYCOMP) --noopt -c -m $(basename $<) $< $(LAPACK_LINK) $(OMP_LINK)

nmat_core_32.f90: nmat_core.F90
	$(SED) 's/\<_\>/4/g;s/\<C\>/c/g;s/\<D\>/e/g;s/S/s/g;s/##//g' < $< > $@
nmat_core_64.f90: nmat_core.F90
	$(SED) 's/\<_\>/8/g;s/\<C\>/z/g;s/\<D\>/d/g;s/S/d/g;s/##//g' < $< > $@

clean:
	rm -rf *.pyc *.so
