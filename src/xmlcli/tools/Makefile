# apps/python
#
#  copy python scripts
#
SV_ROOT ?= $(PYSV_ROOT)
# This is so that all pythonsv Makefiles know where
# to got to on the image
-include $(SV_ROOT)/includes/header.incl

SUBDIRS := $(shell for dir in $(wildcard */[mM]akefile);	\
				   do										\
						dirname $$dir;						\
				   done )

# to make sure place on the image is same
# as it is in the source tree
COPYTOWHERE = python/$(subst $(PY_ROOT),'',$(shell pwd))

COPYTOIMAGE = $(wildcard *.py)

.PHONY:	all
all: $(SUBDIRS)

-include $(SV_ROOT)/includes/footer.incl
documents:
	@echo no documents to make

unexport PY_ROOT,PYSV_ROOT
