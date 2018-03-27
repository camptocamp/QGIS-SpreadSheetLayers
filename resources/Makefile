
RESOURCE_FILES = resources.qrc

###################### DON'T EDIT FURTHER ###################################

COMPILED_RESOURCES = $(RESOURCE_FILES:%.qrc=%_rc.py)
MOVED_COMPILED_RESOURCES = $(RESOURCE_FILES:%.qrc=../ui/%_rc.py)

default : resources

clean:
	rm -f $(MOVED_COMPILED_RESOURCES)
	rm -f *.pyc

resources: $(COMPILED_RESOURCES)
	mv resources_rc.py ../ui

# Conversion rules

%_rc.py : %.qrc
	pyrcc5 -o $@ $<